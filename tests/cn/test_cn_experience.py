import json


def test_provider_scope_is_intentionally_small():
    from code_puppy.plugins.cn_experience.register_callbacks import (
        CHINA_PROVIDER_IDS,
    )

    assert CHINA_PROVIDER_IDS == (
        "alibaba-cn",
        "deepseek",
        "moonshotai-cn",
        "zai",
    )


def test_bundled_registry_has_target_providers_and_tool_models():
    from code_puppy.models_dev_parser import ModelsDevRegistry
    from code_puppy.plugins.cn_experience.register_callbacks import (
        CHINA_PROVIDER_IDS,
    )

    registry = ModelsDevRegistry(json_path="code_puppy/models_dev_api.json")
    for provider_id in CHINA_PROVIDER_IDS:
        assert registry.get_provider(provider_id) is not None
        assert any(model.tool_call for model in registry.get_models(provider_id))


def test_model_key_uses_upstream_provider_and_model_names(monkeypatch, tmp_path):
    import code_puppy.command_line.add_model_menu as add_model_menu
    from code_puppy.models_dev_parser import ModelsDevRegistry

    target = tmp_path / "extra_models.json"
    monkeypatch.setattr(add_model_menu, "EXTRA_MODELS_FILE", str(target))
    registry = ModelsDevRegistry(json_path="code_puppy/models_dev_api.json")
    provider = registry.get_provider("deepseek")
    model = registry.get_models("deepseek")[0]

    menu = add_model_menu.AddModelMenu.__new__(add_model_menu.AddModelMenu)
    assert menu._add_model_to_extra_config(model, provider)

    data = json.loads(target.read_text(encoding="utf-8"))
    expected_key = f"deepseek-{model.model_id}"
    assert expected_key in data
    assert not expected_key.startswith("cn-")
    assert data[expected_key]["type"] == "custom_openai"

    assert menu._add_model_to_extra_config(model, provider)
    assert len(json.loads(target.read_text(encoding="utf-8"))) == 1


def test_code_fix_skill_tracks_active_locale(monkeypatch, tmp_path):
    import code_puppy.config as config
    from code_puppy.i18n import set_locale
    from code_puppy.plugins.cn_experience import register_callbacks as plugin

    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "puppy.cfg"))
    set_locale("zh-CN")
    chinese = plugin._code_fix_skill()[0]
    assert chinese["name"] == "code-fix"
    assert "中文" in chinese["body"]

    set_locale("en-US")
    english = plugin._code_fix_skill()[0]
    assert "Report changed files" in english["body"]


def test_audit_is_opt_in_and_metadata_only(monkeypatch, tmp_path):
    import code_puppy.config as config
    from code_puppy.plugins.cn_experience import register_callbacks as plugin

    monkeypatch.setattr(config, "STATE_DIR", str(tmp_path))
    monkeypatch.delenv("CODE_PUPPY_CN_AUDIT", raising=False)
    plugin._write_audit({"event": "hidden"})
    path = tmp_path / "cn" / "audit" / "events.jsonl"
    assert not path.exists()

    monkeypatch.setenv("CODE_PUPPY_CN_AUDIT", "1")
    plugin._write_audit({"event": "tool_complete", "tool": "read_file"})
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record == {"event": "tool_complete", "tool": "read_file"}
