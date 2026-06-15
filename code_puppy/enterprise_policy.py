"""Enterprise tool policy evaluation with no provider-specific behavior."""

from __future__ import annotations

import fnmatch
import os
import re
import shlex
from pathlib import Path
from urllib.parse import urlparse

POLICY_DENIED = "policy_denied"
_NETWORK_COMMANDS = {"curl", "wget", "ssh", "scp", "rsync", "nc", "telnet", "ftp"}
_PACKAGE_COMMANDS = {
    ("pip", "install"),
    ("pip3", "install"),
    ("npm", "install"),
    ("npm", "ci"),
    ("pnpm", "install"),
    ("yarn", "install"),
    ("uv", "add"),
    ("uv", "sync"),
}


def _blocked(reason: str) -> dict:
    return {
        "blocked": True,
        "code": POLICY_DENIED,
        "reason": reason,
        "error_message": f"[BLOCKED] {POLICY_DENIED}: {reason}",
    }


def _matches(value: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _path_matches(value: str, patterns: list[str]) -> bool:
    path = Path(os.path.expanduser(value))
    return (
        _matches(value, patterns)
        or _matches(path.name, patterns)
        or any(_matches(component, patterns) for component in path.parts)
    )


def _file_path(tool_args: dict) -> Path | None:
    payload = tool_args.get("payload")
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    nested = payload if isinstance(payload, dict) else {}
    raw = next(
        (
            tool_args.get(key) or nested.get(key)
            for key in ("file_path", "path", "target_path")
            if tool_args.get(key) or nested.get(key)
        ),
        None,
    )
    if not isinstance(raw, str):
        return None
    candidate = Path(os.path.expanduser(raw))
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return candidate.resolve(strict=False)


def _host_allowed(value: str, allowed: set[str]) -> bool:
    host = urlparse(value).hostname or value.split("@")[-1].split(":")[0]
    return any(
        item == value
        or item == host
        or urlparse(item).hostname == host
        for item in allowed
    )


def _shell_network_denial(policy: dict, command: str) -> dict | None:
    network = policy.get("network") or {}
    if network.get("default") != "deny":
        return None
    allowed = set(network.get("allow") or [])
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    lowered = [token.lower() for token in tokens]
    lowered_command = " ".join(lowered)
    network_operation = bool(
        lowered
        and (
            lowered[0] in _NETWORK_COMMANDS
            or tuple(lowered[:2]) in _PACKAGE_COMMANDS
            or any(
                " ".join(command_pair) in lowered_command
                for command_pair in _PACKAGE_COMMANDS
            )
            or (
                lowered[0] == "git"
                and len(lowered) > 1
                and lowered[1] in {"clone", "fetch", "pull", "push"}
            )
        )
    )
    candidates = re.findall(r"https?://[^\s'\"<>]+", command)
    if not network_operation and not candidates:
        return None
    if candidates and all(_host_allowed(value, allowed) for value in candidates):
        return None
    return _blocked("network access is not allowed by enterprise policy")


def evaluate_tool_policy(
    policy: dict,
    tool_name: str,
    tool_args: dict,
    *,
    repeated_failure_count: int = 0,
) -> dict | None:
    normalized = tool_name.lower()

    if normalized in {"agent_run_shell_command", "run_shell_command"}:
        command = str(tool_args.get("command") or "")
        denied = list((policy.get("shell") or {}).get("deny") or [])
        if any(pattern in command for pattern in denied):
            return _blocked("shell command is denied by enterprise policy")
        file_denied = list((policy.get("files") or {}).get("deny") or [])
        try:
            command_tokens = shlex.split(command)
        except ValueError:
            command_tokens = command.split()
        if any(_path_matches(token, file_denied) for token in command_tokens):
            return _blocked("shell command references a denied file path")
        network_denial = _shell_network_denial(policy, command)
        if network_denial:
            return network_denial
        if repeated_failure_count >= 2:
            return _blocked("same failing shell command cannot be retried again")

    file_path = _file_path(tool_args)
    if file_path is not None:
        denied = list((policy.get("files") or {}).get("deny") or [])
        rendered = file_path.as_posix()
        components = file_path.parts
        if (
            _matches(file_path.name, denied)
            or _matches(rendered, denied)
            or any(_matches(component, denied) for component in components)
        ):
            return _blocked("file path is denied by enterprise policy")

    raw_url = next(
        (
            tool_args.get(key)
            for key in ("url", "uri", "endpoint")
            if tool_args.get(key)
        ),
        None,
    )
    if isinstance(raw_url, str) and "://" in raw_url:
        network = policy.get("network") or {}
        allowed = set(network.get("allow") or [])
        if network.get("default") == "deny" and not _host_allowed(raw_url, allowed):
            return _blocked("network host is not allowed by enterprise policy")

    if normalized == "activate_skill":
        skill_name = str(tool_args.get("skill_name") or "")
        allowed = set((policy.get("skills") or {}).get("allow") or [])
        if skill_name not in allowed:
            return _blocked("skill is not allowed by enterprise policy")

    if "mcp" in normalized and (policy.get("mcp") or {}).get("default") == "deny":
        return _blocked("MCP execution is disabled by enterprise policy")

    return None
