"""Diagnostics for Code Puppy CN without exposing credentials."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import socket
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

CHINA_PROVIDER_IDS = ("alibaba-cn", "deepseek", "moonshotai-cn", "zai")


@dataclass
class Check:
    id: str
    status: str
    message: str
    details: dict[str, Any] | None = None


def _classify_error(exc: Exception) -> tuple[str, str]:
    text = str(exc).lower()
    if isinstance(exc, (socket.gaierror, httpx.ConnectError)) and any(
        marker in text for marker in ("name or service", "nodename", "dns")
    ):
        return "dns", exc.__class__.__name__
    if isinstance(exc, (ssl.SSLError, httpx.ConnectError)) and any(
        marker in text for marker in ("ssl", "tls", "certificate")
    ):
        return "tls", exc.__class__.__name__
    if isinstance(exc, (httpx.TimeoutException, TimeoutError, FutureTimeoutError)):
        return "timeout", exc.__class__.__name__
    if any(marker in text for marker in ("401", "403", "unauthorized", "api key")):
        return "authentication", exc.__class__.__name__
    if any(marker in text for marker in ("429", "rate limit", "quota")):
        return "rate_limit", exc.__class__.__name__
    return "model", exc.__class__.__name__


def _endpoint_reachable(url: str) -> tuple[bool, str, dict[str, Any]]:
    if not url:
        return False, "endpoint not declared", {"phase": "configuration"}
    hostname = urlparse(url).hostname
    if not hostname:
        return False, "invalid endpoint", {"phase": "configuration"}
    try:
        addresses = sorted(
            {
                item[4][0]
                for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
            }
        )
    except Exception as exc:
        category, message = _classify_error(exc)
        return False, message, {"phase": category, "host": hostname}
    try:
        response = httpx.get(url, timeout=5.0, follow_redirects=True)
        if response.status_code in {401, 403}:
            phase = "authentication"
        elif response.status_code == 429:
            phase = "rate_limit"
        else:
            phase = "http"
        return (
            response.status_code < 500,
            f"HTTP {response.status_code}",
            {
                "phase": phase,
                "host": hostname,
                "addresses": addresses,
            },
        )
    except Exception as exc:
        category, message = _classify_error(exc)
        return (
            False,
            message,
            {
                "phase": category,
                "host": hostname,
                "addresses": addresses,
            },
        )


def _live_model_probe(model_name: str, timeout: float = 60.0) -> Check:
    """Execute a harmless real tool call against one configured model."""

    def execute() -> Check:
        from pydantic_ai import Agent

        from code_puppy.model_factory import ModelFactory

        started = time.perf_counter()
        config = ModelFactory.load_config()
        model = ModelFactory.get_model(model_name, config)
        if model is None:
            return Check(
                "live",
                "error",
                "model could not be initialized",
                {"model": model_name, "category": "configuration"},
            )

        called: dict[str, str] = {}

        def cn_diagnostic_probe(value: str) -> str:
            """Return a deterministic value for connectivity diagnostics."""
            called["value"] = value
            return f"probe:{value}"

        agent = Agent(model, tools=[cn_diagnostic_probe])
        result = agent.run_sync(
            "Call cn_diagnostic_probe exactly once with value 'ok', then reply done."
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        if called.get("value") != "ok":
            return Check(
                "live",
                "warning",
                "response completed without the required tool call",
                {
                    "model": model_name,
                    "category": "tool_call",
                    "duration_ms": elapsed_ms,
                },
            )
        return Check(
            "live",
            "ok",
            "real tool call succeeded",
            {
                "model": model_name,
                "category": "success",
                "duration_ms": elapsed_ms,
                "output": str(result.output)[:200],
            },
        )

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(execute)
    try:
        return future.result(timeout=timeout)
    except Exception as exc:
        category, message = _classify_error(exc)
        return Check(
            "live",
            "error",
            message,
            {"model": model_name, "category": category},
        )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def collect_checks(check_network: bool = True) -> list[Check]:
    from code_puppy import __version__
    from code_puppy.command_line.add_model_menu import AddModelMenu
    from code_puppy.config import get_value
    from code_puppy.i18n import get_locale
    from code_puppy.model_factory import ModelFactory
    from code_puppy.models_dev_parser import ModelsDevRegistry

    checks = [
        Check(
            "upstream",
            "ok" if hasattr(AddModelMenu, "_add_model_to_extra_config") else "error",
            __version__,
        ),
        Check(
            "locale",
            "ok",
            get_locale(),
        ),
        Check(
            "python",
            "ok" if sys.version_info >= (3, 11) else "error",
            platform.python_version(),
            {"executable": sys.executable, "platform": platform.platform()},
        ),
        Check(
            "git",
            "ok" if shutil.which("git") else "error",
            shutil.which("git") or "not found",
        ),
    ]

    try:
        registry_path = (
            Path(__file__).parent / "models_dev_api.json" if not check_network else None
        )
        registry = ModelsDevRegistry(json_path=registry_path)
        checks.append(
            Check(
                "registry",
                "ok",
                registry.data_source,
                {"providers": len(registry.providers), "models": len(registry.models)},
            )
        )
    except Exception as exc:
        checks.append(Check("registry", "error", str(exc)))
        return checks

    selected_model = get_value("model")
    if selected_model:
        model_config = ModelFactory.load_config().get(selected_model, {})
        provider_id = next(
            (
                provider_id
                for provider_id in registry.providers
                if selected_model.startswith(f"{provider_id}-")
            ),
            model_config.get("provider"),
        )
        registry_model = next(
            (
                model
                for model in registry.get_models(provider_id)
                if model.model_id == model_config.get("name")
            ),
            None,
        )
        supports_tools = bool(registry_model and registry_model.tool_call)
        checks.append(
            Check(
                "model",
                "ok" if supports_tools else "warning",
                selected_model,
                {
                    "provider": provider_id,
                    "model_id": model_config.get("name"),
                    "tool_call": supports_tools,
                },
            )
        )
    else:
        checks.append(Check("model", "warning", "not configured"))

    for provider_id in CHINA_PROVIDER_IDS:
        provider = registry.get_provider(provider_id)
        if provider is None:
            checks.append(Check(f"provider:{provider_id}", "error", "not found"))
            continue
        tool_models = [
            model for model in registry.get_models(provider_id) if model.tool_call
        ]
        checks.append(
            Check(
                f"provider:{provider_id}",
                "ok" if tool_models else "warning",
                provider.name,
                {"tool_call_models": len(tool_models), "endpoint": provider.api},
            )
        )
        for env_name in provider.env:
            from code_puppy.provider_credentials import get_credential_value

            present = bool(get_credential_value(env_name))
            checks.append(
                Check(
                    f"credential:{env_name}",
                    "ok" if present else "warning",
                    "configured" if present else "not configured",
                )
            )
        if check_network:
            reachable, message, details = _endpoint_reachable(provider.api)
            checks.append(
                Check(
                    f"endpoint:{provider_id}",
                    "ok" if reachable else "warning",
                    message,
                    {"url": provider.api, **details},
                )
            )
    return checks


def report(
    check_network: bool = True,
    live: bool = False,
    model_name: str | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    checks = collect_checks(check_network=check_network)
    if live:
        from code_puppy.config import get_global_model_name

        selected_model = model_name or get_global_model_name()
        if selected_model:
            checks.append(_live_model_probe(selected_model, timeout=timeout))
        else:
            checks.append(
                Check(
                    "live",
                    "error",
                    "no configured model",
                    {"category": "configuration"},
                )
            )
    passed = sum(check.status == "ok" for check in checks)
    return {
        "schema_version": 1,
        "product": "code-puppy-cn",
        "checks": [asdict(check) for check in checks],
        "summary": {"passed": passed, "total": len(checks)},
    }


def render_human(data: dict[str, Any]) -> str:
    from code_puppy.i18n import t

    lines = [t("doctor.title")]
    for check in data["checks"]:
        label_key = check["id"].split(":", 1)[0]
        detail = check["id"].split(":", 1)[1] if ":" in check["id"] else ""
        key = f"doctor.{label_key}"
        label = t(key, provider=detail, name=detail)
        status_key = {
            "ok": "doctor.ok",
            "warning": "doctor.warn",
            "error": "doctor.error",
        }.get(check["status"], "doctor.warn")
        lines.append(f"[{t(status_key)}] {label}: {check['message']}")
    summary = data["summary"]
    lines.append(t("doctor.summary", passed=summary["passed"], total=summary["total"]))
    lines.append(t("doctor.json_hint"))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Code Puppy CN diagnostics")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--no-network", action="store_true", help="Skip endpoint connectivity checks"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute one minimal real model tool call",
    )
    parser.add_argument("--model", help="Configured model key to test")
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Live call timeout in seconds",
    )
    args = parser.parse_args()
    data = report(
        check_network=not args.no_network,
        live=args.live,
        model_name=args.model,
        timeout=args.timeout,
    )
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_human(data))


if __name__ == "__main__":
    main()
