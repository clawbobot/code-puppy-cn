import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from code_puppy import enterprise


@pytest.fixture
def enterprise_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CODE_PUPPY_ENTERPRISE_HOME", str(tmp_path))
    return tmp_path


def test_signed_config_injects_only_managed_models(enterprise_home, monkeypatch):
    key = Ed25519PrivateKey.generate()
    document = {
        "version": 3,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "gateway_url": "https://gateway.example",
        "models": [
            {"alias": "qwen-coder", "model": "qwen-coder", "provider": "ollama"}
        ],
        "policy": {},
    }
    payload = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    envelope = {
        "payload": base64.b64encode(payload).decode(),
        "signature": base64.b64encode(key.sign(payload)).decode(),
        "public_key": base64.b64encode(key.public_key().public_bytes_raw()).decode(),
    }

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return envelope

    enterprise._write(
        enterprise.state_path(),
        {
            "server_url": "https://gateway.example",
            "access_token": "secret",
            "enabled": True,
            "device_id": "device-1",
        },
    )
    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: Response())
    assert enterprise.sync()["version"] == 3
    models = enterprise.model_configs()
    assert list(models) == ["qwen-coder"]
    assert models["qwen-coder"]["custom_endpoint"]["api_key"].startswith("$")
    enterprise.enforce_model("qwen-coder")
    with pytest.raises(ValueError, match="only permits"):
        enterprise.enforce_model("gpt-5")


def test_expired_config_fails_closed(enterprise_home):
    enterprise._write(
        enterprise.config_path(),
        {
            "expires_at": (
                datetime.now(timezone.utc) - timedelta(minutes=1)
            ).isoformat()
        },
    )
    with pytest.raises(RuntimeError, match="expired"):
        enterprise.get_config()
    assert enterprise.status()["config_expires_at"]


def test_run_limits_use_defaults_and_validate_values(enterprise_home):
    enterprise._write(
        enterprise.state_path(),
        {"access_token": "secret", "enabled": True},
    )
    enterprise._write(
        enterprise.config_path(),
        {
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=5)
            ).isoformat(),
            "run_limits": {
                "request_limit": "4",
                "tool_calls_limit": 0,
                "total_tokens_limit": "invalid",
            },
        },
    )
    assert enterprise.get_run_limits() == {
        "request_limit": 4,
        "tool_calls_limit": 20,
        "total_tokens_limit": 100_000,
        "timeout_seconds": 600,
    }


def test_model_config_carries_active_session(enterprise_home):
    enterprise._write(
        enterprise.state_path(),
        {
            "access_token": "secret",
            "enabled": True,
            "device_id": "device-1",
        },
    )
    enterprise._write(
        enterprise.config_path(),
        {
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=5)
            ).isoformat(),
            "gateway_url": "https://gateway.example",
            "models": [{"alias": "qwen", "model": "qwen", "provider": "ollama"}],
        },
    )
    enterprise.set_active_session("session-1")
    headers = enterprise.model_configs()["qwen"]["custom_endpoint"]["headers"]
    assert headers["X-Session-Id"] == "session-1"
    enterprise.set_active_session(None)


def test_heartbeat_reports_client_and_config_version(enterprise_home, monkeypatch):
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
            "version": 7,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(hours=1)
            ).isoformat(),
        },
    )
    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "ok"}

    def post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return Response()

    monkeypatch.setattr("httpx.post", post)
    assert enterprise.heartbeat()["status"] == "ok"
    assert captured["url"].endswith("/v1/client/heartbeat")
    assert captured["json"]["device_id"] == "device-1"
    assert captured["json"]["config_version"] == 7
    assert enterprise.status()["last_heartbeat"]


def test_heartbeat_refreshes_expired_access_token(enterprise_home, monkeypatch):
    enterprise._write(
        enterprise.state_path(),
        {
            "server_url": "https://gateway.example",
            "access_token": "expired",
            "refresh_token": "refresh",
            "enabled": True,
            "device_id": "device-1",
        },
    )
    enterprise._write(
        enterprise.config_path(),
        {
            "version": 7,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(hours=1)
            ).isoformat(),
        },
    )
    calls = []

    class Response:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self.payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise AssertionError(self.status_code)

        def json(self):
            return self.payload

    def post(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/v1/device/refresh"):
            return Response(
                200,
                {
                    "access_token": "renewed",
                    "refresh_token": "next-refresh",
                    "device_id": "device-1",
                },
            )
        if kwargs["headers"]["Authorization"] == "Bearer expired":
            return Response(401, {})
        return Response(200, {"status": "ok"})

    monkeypatch.setattr("httpx.post", post)
    assert enterprise.heartbeat()["status"] == "ok"
    assert enterprise.get_state()["access_token"] == "renewed"
    assert len(calls) == 3
