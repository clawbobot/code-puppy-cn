from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest

from code_puppy import enterprise
from code_puppy.plugins.enterprise_client import register_callbacks


@pytest.fixture
def enterprise_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CODE_PUPPY_ENTERPRISE_HOME", str(tmp_path))
    enterprise._write(
        enterprise.state_path(),
        {
            "server_url": "https://gateway.example",
            "access_token": "secret",
            "enabled": True,
            "device_id": "device-1",
        },
    )
    enterprise._write(
        enterprise.config_path(),
        {
            "version": 1,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=5)
            ).isoformat(),
            "policy": {
                "shell": {"deny": ["rm -rf"]},
                "audit": {"strict": True},
            },
        },
    )
    return tmp_path


@pytest.mark.asyncio
async def test_tool_audit_records_delivery_status(enterprise_home, monkeypatch):
    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: Client())
    await register_callbacks._post_tool_call(
        "read_file",
        {"path": "secret.py"},
        "contents",
        12.5,
        SimpleNamespace(cwd="/private/project"),
    )
    state = enterprise.get_state()
    assert state["last_audit"]
    assert "audit_error" not in state


@pytest.mark.asyncio
async def test_tool_audit_records_http_failure(enterprise_home, monkeypatch):
    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: Client())
    await register_callbacks._post_tool_call("run_shell_command", {}, None, 1)
    assert "offline" in enterprise.get_state()["audit_error"]


@pytest.mark.asyncio
async def test_pre_tool_call_blocks_policy_denial(enterprise_home, monkeypatch):
    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: Client())
    result = await register_callbacks._pre_tool_call(
        "run_shell_command", {"command": "rm -rf build"}
    )
    assert result["code"] == "policy_denied"


@pytest.mark.asyncio
async def test_pre_tool_call_fails_closed_when_config_expired(
    enterprise_home, monkeypatch
):
    enterprise._write(
        enterprise.config_path(),
        {
            "expires_at": "2000-01-01T00:00:00+00:00",
            "policy": {},
        },
    )
    result = await register_callbacks._pre_tool_call("read_file", {"path": "ok.py"})
    assert result["code"] == "policy_denied"


def test_tool_failure_detection_ignores_empty_error_fields():
    assert register_callbacks._tool_failed({"success": True, "error": None}) is False
    assert register_callbacks._tool_failed({"success": False}) is True
    assert register_callbacks._tool_failed({"error": "failed"}) is True


@pytest.mark.asyncio
async def test_agent_start_blocks_when_strict_audit_is_offline(
    enterprise_home, monkeypatch
):
    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: Client())
    result = await register_callbacks._agent_run_start(
        "code-puppy", "qwen", "session-1"
    )
    assert result["code"] == "policy_denied"


@pytest.mark.asyncio
async def test_agent_end_accepts_full_callback_contract(
    enterprise_home, monkeypatch
):
    delivered = []

    async def capture(event, *, strict):
        delivered.append((event, strict))
        return True

    monkeypatch.setattr(register_callbacks, "_deliver_audit", capture)
    await register_callbacks._agent_run_end(
        "code-puppy",
        "qwen",
        "session-1",
        True,
        None,
        "Task completed",
        {"model": "qwen"},
    )

    event, strict = delivered[0]
    assert strict is False
    assert event["event_type"] == "task_end"
    assert event["session_id"] == "session-1"
    assert event["metadata"]["termination_reason"] == "completed"
    assert event["metadata"]["response_present"] is True
    assert event["metadata"]["runtime_metadata_keys"] == ["model"]
    assert "Task completed" not in str(event)
