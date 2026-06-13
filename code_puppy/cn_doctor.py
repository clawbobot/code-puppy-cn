"""Diagnostics for Code Puppy CN without exposing credentials."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx

CHINA_PROVIDER_IDS = ("alibaba-cn", "deepseek", "moonshotai-cn", "zai")


@dataclass
class Check:
    id: str
    status: str
    message: str
    details: dict[str, Any] | None = None


def _endpoint_reachable(url: str) -> tuple[bool, str]:
    if not url:
        return False, "endpoint not declared"
    try:
        response = httpx.get(url, timeout=5.0, follow_redirects=True)
        return response.status_code < 500, f"HTTP {response.status_code}"
    except Exception as exc:
        return False, exc.__class__.__name__


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
            present = bool(os.environ.get(env_name))
            checks.append(
                Check(
                    f"credential:{env_name}",
                    "ok" if present else "warning",
                    "configured" if present else "not configured",
                )
            )
        if check_network:
            reachable, message = _endpoint_reachable(provider.api)
            checks.append(
                Check(
                    f"endpoint:{provider_id}",
                    "ok" if reachable else "warning",
                    message,
                    {"url": provider.api},
                )
            )
    return checks


def report(check_network: bool = True) -> dict[str, Any]:
    checks = collect_checks(check_network=check_network)
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
        status_key = "doctor.ok" if check["status"] == "ok" else "doctor.warn"
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
    args = parser.parse_args()
    data = report(check_network=not args.no_network)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_human(data))


if __name__ == "__main__":
    main()
