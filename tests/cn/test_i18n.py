import json


def _point_config_to_tmp(monkeypatch, tmp_path):
    import code_puppy.config as config

    config_path = tmp_path / "puppy.cfg"
    monkeypatch.setattr(config, "CONFIG_FILE", str(config_path))
    return config_path


def test_normalize_locale():
    from code_puppy.i18n import normalize_locale

    assert normalize_locale("zh_CN.UTF-8") == "zh-CN"
    assert normalize_locale("zh-SG") == "zh-CN"
    assert normalize_locale("zh-Hans") == "zh-CN"
    assert normalize_locale("fr-FR") == "en-US"


def test_set_locale_persists_and_translation_switches(monkeypatch, tmp_path):
    _point_config_to_tmp(monkeypatch, tmp_path)
    from code_puppy.i18n import get_locale, set_locale, t

    set_locale("zh-CN")
    assert get_locale() == "zh-CN"
    assert t("app.prompt") == "请输入你的编码任务："

    set_locale("en-US")
    assert get_locale() == "en-US"
    assert t("app.prompt") == "Enter your coding task:"


def test_translation_catalog_keys_match():
    from pathlib import Path

    root = Path(__file__).parents[2] / "code_puppy" / "i18n" / "locales"
    english = json.loads((root / "en-US.json").read_text(encoding="utf-8"))
    chinese = json.loads((root / "zh-CN.json").read_text(encoding="utf-8"))
    assert english.keys() == chinese.keys()


def test_missing_key_and_format_parameter_do_not_crash(monkeypatch, tmp_path):
    _point_config_to_tmp(monkeypatch, tmp_path)
    from code_puppy.i18n import set_locale, t

    set_locale("zh-CN")
    assert t("not.a.real.key") == "not.a.real.key"
    assert "{model}" in t("cn_setup.added")
