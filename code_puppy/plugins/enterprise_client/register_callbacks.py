"""Enterprise model injection, commands, and metadata-only audit."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any

import httpx

from code_puppy.callbacks import register_callback
from code_puppy.enterprise import (
    active_session_id,
    get_config,
    get_state,
    heartbeat,
    is_enabled,
    model_configs,
    record_delivery_status,
    refresh_access_token,
    strict_audit_enabled,
    status,
    sync,
)
from code_puppy.enterprise_policy import evaluate_tool_policy
from code_puppy.i18n import t
from code_puppy.messaging import emit_error, emit_info, emit_success

_LAST_FAILED_TOOL_SIGNATURE: str | None = None
_FAILED_TOOL_CALL_COUNT = 0


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


async def _deliver_audit(event: dict, *, strict: bool) -> bool:
    state = get_state()
    payload = {"device_id": state.get("device_id"), "events": [event]}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{state['server_url']}/v1/audit/events",
                headers={"Authorization": f"Bearer {state['access_token']}"},
                json=payload,
            )
            if response.status_code == 401 and state.get("refresh_token"):
                state = await asyncio.to_thread(refresh_access_token)
                response = await client.post(
                    f"{state['server_url']}/v1/audit/events",
                    headers={"Authorization": f"Bearer {state['access_token']}"},
                    json=payload,
                )
            response.raise_for_status()
        record_delivery_status("audit")
        return True
    except httpx.HTTPError as exc:
        record_delivery_status("audit", str(exc))
        return not strict


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
    global _FAILED_TOOL_CALL_COUNT, _LAST_FAILED_TOOL_SIGNATURE
    if not is_enabled():
        return
    event = {
        "event_type": "tool_complete",
        "decision": "allowed",
        "project_hash": _project_hash(context),
        "session_id": active_session_id(),
        "summary": f"{tool_name} completed",
        "metadata": {
            "tool": tool_name,
            "duration_ms": duration_ms,
            "success": not isinstance(result, Exception),
        },
    }
    await _deliver_audit(event, strict=False)

    signature = _tool_signature(tool_name, tool_args)
    if _tool_failed(result):
        if signature == _LAST_FAILED_TOOL_SIGNATURE:
            _FAILED_TOOL_CALL_COUNT += 1
        else:
            _LAST_FAILED_TOOL_SIGNATURE = signature
            _FAILED_TOOL_CALL_COUNT = 1
    else:
        _LAST_FAILED_TOOL_SIGNATURE = None
        _FAILED_TOOL_CALL_COUNT = 0


def _tool_signature(tool_name: str, tool_args: dict) -> str:
    command = tool_args.get("command")
    return f"{tool_name}:{command if command is not None else tool_args}"


def _tool_failed(result: Any) -> bool:
    if isinstance(result, Exception):
        return True
    if isinstance(result, dict):
        return bool(result.get("error")) or result.get("success") is False
    error = getattr(result, "error", None)
    success = getattr(result, "success", None)
    return bool(error) or success is False


async def _pre_tool_call(
    tool_name: str,
    tool_args: dict,
    context: Any = None,
) -> dict | None:
    if not is_enabled():
        return None
    try:
        config = get_config()
    except (RuntimeError, ValueError, KeyError) as exc:
        return {
            "blocked": True,
            "code": "policy_denied",
            "reason": str(exc),
            "error_message": f"[BLOCKED] policy_denied: {exc}",
        }
    signature = _tool_signature(tool_name, tool_args)
    decision = evaluate_tool_policy(
        config.get("policy") or {},
        tool_name,
        tool_args,
        repeated_failure_count=(
            _FAILED_TOOL_CALL_COUNT
            if signature == _LAST_FAILED_TOOL_SIGNATURE
            else 0
        ),
    )
    audit_decision = "denied" if decision else "allowed"
    event = {
        "event_type": "tool_policy",
        "decision": audit_decision,
        "project_hash": _project_hash(context),
        "session_id": active_session_id(),
        "summary": f"{tool_name} {audit_decision} by enterprise policy",
        "metadata": {
            "tool": tool_name,
            "policy_version": config.get("version"),
            "code": decision.get("code") if decision else None,
        },
    }
    if not await _deliver_audit(event, strict=strict_audit_enabled(config)):
        return {
            "blocked": True,
            "code": "policy_denied",
            "reason": "enterprise audit delivery failed",
            "error_message": "[BLOCKED] policy_denied: enterprise audit delivery failed",
        }
    return decision


async def _agent_run_start(
    agent_name: str,
    model_name: str,
    session_id: str,
    **_: Any,
) -> dict | None:
    global _FAILED_TOOL_CALL_COUNT, _LAST_FAILED_TOOL_SIGNATURE
    if not is_enabled():
        return None
    _LAST_FAILED_TOOL_SIGNATURE = None
    _FAILED_TOOL_CALL_COUNT = 0
    delivered = await _deliver_audit(
        {
            "event_type": "task_start",
            "decision": "allowed",
            "project_hash": _project_hash(None),
            "session_id": session_id,
            "summary": "Enterprise agent task started",
            "metadata": {"agent": agent_name, "model": model_name},
        },
        strict=True,
    )
    if not delivered:
        return {
            "blocked": True,
            "code": "policy_denied",
            "reason": "enterprise audit delivery failed",
        }
    return None


async def _agent_run_end(
    agent_name: str,
    model_name: str,
    session_id: str,
    success: bool,
    error: Any = None,
    **_: Any,
) -> None:
    if not is_enabled():
        return
    code = (
        "task_limit_exceeded"
        if error and "task_limit_exceeded" in str(error)
        else None
    )
    await _deliver_audit(
        {
            "event_type": "task_end",
            "decision": "allowed" if success else "failed",
            "project_hash": _project_hash(None),
            "session_id": session_id,
            "summary": "Enterprise agent task completed",
            "metadata": {
                "agent": agent_name,
                "model": model_name,
                "success": success,
                "termination_reason": code or ("completed" if success else "error"),
            },
        },
        strict=False,
    )


register_callback("load_models_config", model_configs)
register_callback("startup", _on_startup)
register_callback("agent_run_start", _agent_run_start)
register_callback("agent_run_end", _agent_run_end)
register_callback("pre_tool_call", _pre_tool_call)
register_callback("custom_command_help", _help)
register_callback("custom_command", _custom_command)
register_callback("post_tool_call", _post_tool_call)
