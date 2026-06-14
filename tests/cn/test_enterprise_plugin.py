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
