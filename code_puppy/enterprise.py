"""Enterprise client state, signed configuration, and command-line workflow."""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from code_puppy import __version__

TOKEN_ENV = "CODE_PUPPY_ENTERPRISE_TOKEN"


def enterprise_dir() -> Path:
    configured = os.environ.get("CODE_PUPPY_ENTERPRISE_HOME")
    if configured:
        return Path(configured).expanduser()
    from code_puppy.config import STATE_DIR

    return Path(STATE_DIR) / "enterprise"


def state_path() -> Path:
    return enterprise_dir() / "state.json"


def config_path() -> Path:
    return enterprise_dir() / "config.json"


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def get_state() -> dict[str, Any]:
    state = _read(state_path())
    if state.get("access_token"):
        os.environ[TOKEN_ENV] = state["access_token"]
    return state


def get_config(require_valid: bool = True) -> dict[str, Any]:
    config = _read(config_path())
    if require_valid and config:
        expires = datetime.fromisoformat(config["expires_at"].replace("Z", "+00:00"))
        if expires <= datetime.now(timezone.utc):
            raise RuntimeError(
                "Enterprise configuration has expired; run `pup-cn enterprise sync`."
            )
    return config


def is_enabled() -> bool:
    state = get_state()
    return bool(state.get("enabled") and state.get("access_token"))


def _headers(state: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {state['access_token']}"}


def refresh_access_token() -> dict[str, Any]:
    state = get_state()
    if not state.get("refresh_token"):
        raise RuntimeError("Enterprise refresh token is unavailable; log in again.")
    refreshed = httpx.post(
        f"{state['server_url']}/v1/device/refresh",
        json={"refresh_token": state["refresh_token"]},
        timeout=15,
    )
    refreshed.raise_for_status()
    state.update(refreshed.json())
    _write(state_path(), state)
    os.environ[TOKEN_ENV] = state["access_token"]
    return state


def login(server: str, dev_subject: str | None = None) -> dict[str, Any]:
    server = server.rstrip("/")
    with httpx.Client(timeout=15) as client:
        response = client.post(
            f"{server}/v1/device/authorize",
            json={
                "device_name": socket.gethostname(),
                "platform": f"{platform.system().lower()}-{platform.machine().lower()}",
                "client_version": __version__,
            },
        )
        response.raise_for_status()
        authorization = response.json()
        print(f"Open {authorization['verification_uri']}")
        print(f"Device code: {authorization['user_code']}")
        if dev_subject:
            approval = client.post(
                f"{server}/v1/device/approve/{authorization['user_code']}",
                params={"subject": dev_subject},
                headers={"X-Dev-User": "admin"},
            )
            approval.raise_for_status()
        deadline = time.monotonic() + authorization["expires_in"]
        while time.monotonic() < deadline:
            token = client.post(
                f"{server}/v1/device/token",
                json={"device_code": authorization["device_code"]},
            )
            if token.status_code == 200:
                state = {
                    **token.json(),
                    "server_url": server,
                    "enabled": True,
                    "logged_in_at": datetime.now(timezone.utc).isoformat(),
                }
                _write(state_path(), state)
                os.environ[TOKEN_ENV] = state["access_token"]
                sync()
                heartbeat()
                return state
            if token.status_code != 428:
                token.raise_for_status()
            time.sleep(authorization.get("interval", 3))
    raise RuntimeError("Device authorization expired.")


def sync() -> dict[str, Any]:
    state = get_state()
    if not state.get("access_token"):
        raise RuntimeError("Not logged in. Run `pup-cn enterprise login`.")
    response = httpx.get(
        f"{state['server_url']}/v1/client/config",
        headers=_headers(state),
        timeout=15,
    )
    if response.status_code == 401 and state.get("refresh_token"):
        state = refresh_access_token()
        response = httpx.get(
            f"{state['server_url']}/v1/client/config",
            headers=_headers(state),
            timeout=15,
        )
    response.raise_for_status()
    envelope = response.json()
    payload = base64.b64decode(envelope["payload"])
    public_key = envelope["public_key"]
    pinned_key = state.get("public_key")
    if pinned_key and pinned_key != public_key:
        raise RuntimeError(
            "Enterprise signing key changed; administrator approval is required."
        )
    Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key)).verify(
        base64.b64decode(envelope["signature"]), payload
    )
    document = json.loads(payload)
    expires = datetime.fromisoformat(document["expires_at"].replace("Z", "+00:00"))
    if expires <= datetime.now(timezone.utc):
        raise RuntimeError("Received an expired enterprise configuration.")
    state["public_key"] = public_key
    state["synced_at"] = datetime.now(timezone.utc).isoformat()
    _write(state_path(), state)
    _write(config_path(), document)
    if document.get("models"):
        from code_puppy.config import CONFIG_DIR, set_model_name

        Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
        set_model_name(document["models"][0]["alias"])
    return document


def heartbeat() -> dict[str, Any]:
    state = get_state()
    if not state.get("access_token") or not state.get("device_id"):
        raise RuntimeError("Not logged in. Run `pup-cn enterprise login`.")
    config = get_config(require_valid=False)
    response = httpx.post(
        f"{state['server_url']}/v1/client/heartbeat",
        headers=_headers(state),
        json={
            "device_id": state["device_id"],
            "client_version": __version__,
            "config_version": config.get("version", 0),
        },
        timeout=10,
    )
    if response.status_code == 401 and state.get("refresh_token"):
        state = refresh_access_token()
        response = httpx.post(
            f"{state['server_url']}/v1/client/heartbeat",
            headers=_headers(state),
            json={
                "device_id": state["device_id"],
                "client_version": __version__,
                "config_version": config.get("version", 0),
            },
            timeout=10,
        )
    response.raise_for_status()
    result = response.json()
    state["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    state.pop("heartbeat_error", None)
    _write(state_path(), state)
    return result


def record_delivery_status(kind: str, error: str | None = None) -> None:
    state = get_state()
    state[f"last_{kind}"] = datetime.now(timezone.utc).isoformat()
    if error:
        state[f"{kind}_error"] = error[:500]
    else:
        state.pop(f"{kind}_error", None)
    _write(state_path(), state)


def logout() -> None:
    for path in (state_path(), config_path()):
        path.unlink(missing_ok=True)
    os.environ.pop(TOKEN_ENV, None)


def model_configs() -> dict[str, Any]:
    if not is_enabled():
        return {}
    config = get_config()
    gateway = config["gateway_url"].rstrip("/")
    state = get_state()
    project_id = (config.get("projects") or [{}])[0].get("id", "")
    return {
        model["alias"]: {
            "name": model["model"],
            "type": "custom_openai",
            "description": f"Enterprise managed model via {model['provider']}",
            "custom_endpoint": {
                "url": f"{gateway}/v1",
                "api_key": f"${TOKEN_ENV}",
                "headers": {
                    "X-Device-Id": state.get("device_id", ""),
                    "X-Project-Id": project_id,
                },
            },
        }
        for model in config.get("models", [])
    }


def enforce_model(model_name: str) -> None:
    if not is_enabled():
        return
    allowed = set(model_configs())
    if model_name not in allowed:
        raise ValueError(
            "Enterprise mode only permits platform-managed models: "
            + ", ".join(sorted(allowed))
        )


def status() -> dict[str, Any]:
    state = get_state()
    config = get_config(require_valid=False)
    return {
        "enabled": bool(state.get("enabled")),
        "server_url": state.get("server_url"),
        "device_id": state.get("device_id"),
        "config_version": config.get("version"),
        "config_expires_at": config.get("expires_at"),
        "models": [item.get("alias") for item in config.get("models", [])],
        "last_sync": state.get("synced_at"),
        "last_heartbeat": state.get("last_heartbeat"),
        "heartbeat_error": state.get("heartbeat_error"),
        "last_audit": state.get("last_audit"),
        "audit_error": state.get("audit_error"),
    }


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pup-cn enterprise")
    subparsers = parser.add_subparsers(dest="command", required=True)
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--server", default="http://localhost:8000")
    login_parser.add_argument("--dev-subject", help=argparse.SUPPRESS)
    subparsers.add_parser("status")
    subparsers.add_parser("sync")
    subparsers.add_parser("logout")
    args = parser.parse_args(argv)
    try:
        if args.command == "login":
            login(args.server, args.dev_subject)
            print("Enterprise login and configuration sync completed.")
        elif args.command == "status":
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.command == "sync":
            config = sync()
            heartbeat()
            print(f"Enterprise configuration version {config['version']} synchronized.")
        elif args.command == "logout":
            logout()
            print("Enterprise credentials and configuration removed.")
        return 0
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        print(f"Enterprise command failed: {exc}", file=sys.stderr)
        return 1
