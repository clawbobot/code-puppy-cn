"""Enterprise model injection, commands, and metadata-only audit."""

from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Any

import httpx

from code_puppy.callbacks import register_callback
from code_puppy.enterprise import (
    get_config,
    get_state,
    heartbeat,
    is_enabled,
    model_configs,
    record_delivery_status,
    refresh_access_token,
    status,
    sync,
)
from code_puppy.i18n import t
from code_puppy.messaging import emit_error, emit_info, emit_success


def _help() -> list[tuple[str, str]]:
    return [
        ("enterprise", t("command.enterprise_desc")),
        ("policy", t("command.policy_desc")),
        ("usage", t("command.usage_desc")),
        ("audit-status", t("command.audit_status_desc")),
    ]


def _custom_command(command: str, name: str) -> bool | None:
    if name == "enterprise":
        if command.strip() == "/enterprise sync":
            try:
                config = sync()
                emit_success(t("enterprise.synced", version=config["version"]))
            except Exception as exc:
                emit_error(str(exc))
        else:
            emit_info(str(status()))
        return True
    if name == "policy":
        config = get_config(require_valid=False)
        emit_info(str(config.get("policy") or t("enterprise.not_configured")))
        return True
    if name == "usage":
        state = get_state()
        if not is_enabled():
            emit_error(t("enterprise.not_configured"))
            return True
        try:
            response = httpx.get(
                f"{state['server_url']}/v1/usage/summary",
                headers={"Authorization": f"Bearer {state['access_token']}"},
                timeout=10,
            )
            response.raise_for_status()
            emit_info(str(response.json()))
        except httpx.HTTPError as exc:
            emit_error(str(exc))
        return True
    if name == "audit-status":
        current = status()
        emit_info(
            t(
                "enterprise.audit_status",
                enabled=current["enabled"],
                last_sync=current["last_sync"] or "-",
                last_heartbeat=current["last_heartbeat"] or "-",
                last_audit=current["last_audit"] or "-",
            )
        )
        return True
    return None


def _project_hash(context: Any) -> str:
    raw = str(getattr(context, "cwd", None) or Path.cwd())
    return hashlib.sha256(raw.encode()).hexdigest()


async def _on_startup() -> None:
    if not is_enabled():
        return
    try:
        await asyncio.to_thread(heartbeat)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        record_delivery_status("heartbeat", str(exc))


async def _post_tool_call(
    tool_name: str,
    tool_args: dict,
    result: Any,
    duration_ms: float,
    context: Any = None,
) -> None:
    if not is_enabled():
        return
    state = get_state()
    event = {
        "device_id": state.get("device_id"),
        "events": [
            {
                "event_type": "tool_complete",
                "decision": "allowed",
                "project_hash": _project_hash(context),
                "summary": f"{tool_name} completed",
                "metadata": {
                    "tool": tool_name,
                    "duration_ms": duration_ms,
                    "success": not isinstance(result, Exception),
                },
            }
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{state['server_url']}/v1/audit/events",
                headers={"Authorization": f"Bearer {state['access_token']}"},
                json=event,
            )
            if response.status_code == 401 and state.get("refresh_token"):
                state = await asyncio.to_thread(refresh_access_token)
                response = await client.post(
                    f"{state['server_url']}/v1/audit/events",
                    headers={"Authorization": f"Bearer {state['access_token']}"},
                    json=event,
                )
            response.raise_for_status()
        record_delivery_status("audit")
    except httpx.HTTPError as exc:
        record_delivery_status("audit", str(exc))
        if os.environ.get("CODE_PUPPY_ENTERPRISE_STRICT_AUDIT") == "1":
            raise


register_callback("load_models_config", model_configs)
register_callback("startup", _on_startup)
register_callback("custom_command_help", _help)
register_callback("custom_command", _custom_command)
register_callback("post_tool_call", _post_tool_call)
