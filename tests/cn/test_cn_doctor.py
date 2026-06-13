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
