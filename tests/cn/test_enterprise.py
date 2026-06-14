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
