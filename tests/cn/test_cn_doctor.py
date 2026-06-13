def test_doctor_json_schema_without_network(monkeypatch):
    import code_puppy.cn_doctor as doctor

    secret = "diagnostic-secret-must-not-leak"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    data = doctor.report(check_network=False)
    assert data["schema_version"] == 1
    assert data["product"] == "code-puppy-cn"
    assert isinstance(data["checks"], list)
    assert data["summary"]["total"] == len(data["checks"])
    serialized = str(data)
    assert secret not in serialized
    assert "sk-" not in serialized
    assert any(
        check["id"] == "credential:DEEPSEEK_API_KEY"
        and check["message"] == "configured"
        for check in data["checks"]
    )


def test_endpoint_diagnostics_classify_rate_limit(monkeypatch):
    import code_puppy.cn_doctor as doctor

    monkeypatch.setattr(
        doctor.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("127.0.0.1", 443))],
    )
    monkeypatch.setattr(
        doctor.httpx,
        "get",
        lambda *args, **kwargs: type("Response", (), {"status_code": 429})(),
    )
    reachable, message, details = doctor._endpoint_reachable("https://example.com")
    assert reachable
    assert message == "HTTP 429"
    assert details["phase"] == "rate_limit"


def test_report_can_include_mocked_live_check(monkeypatch):
    import code_puppy.cn_doctor as doctor

    monkeypatch.setattr(
        doctor,
        "_live_model_probe",
        lambda model_name, timeout: doctor.Check(
            "live",
            "ok",
            "real tool call succeeded",
            {"model": model_name, "category": "success"},
        ),
    )
    data = doctor.report(
        check_network=False,
        live=True,
        model_name="deepseek-test-model",
    )
    live = next(check for check in data["checks"] if check["id"] == "live")
    assert live["status"] == "ok"
    assert live["details"]["category"] == "success"
