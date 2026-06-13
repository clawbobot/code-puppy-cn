import json
import asyncio
import threading
from types import SimpleNamespace


def _registry():
    from code_puppy.models_dev_parser import ModelsDevRegistry

    return ModelsDevRegistry(json_path="code_puppy/models_dev_api.json")


def test_ranking_requires_tools_and_prefers_coding_and_recency():
    from code_puppy.cn_setup import ranked_models, score_model

    models = ranked_models(_registry(), "deepseek")
    assert models
    assert all(model.tool_call for model in models)
    assert models == sorted(models, key=score_model, reverse=True)


def test_configure_model_reuses_upstream_and_activates(monkeypatch, tmp_path):
    import code_puppy.command_line.add_model_menu as add_model_menu
    import code_puppy.config as config
    from code_puppy.cn_setup import configure_model

    extra_models = tmp_path / "extra_models.json"
    config_file = tmp_path / "puppy.cfg"
    monkeypatch.setattr(add_model_menu, "EXTRA_MODELS_FILE", str(extra_models))
    monkeypatch.setattr(config, "CONFIG_FILE", str(config_file))

    registry = _registry()
    model = next(model for model in registry.get_models("deepseek") if model.tool_call)
    result = configure_model(registry, "deepseek", model.model_id)

    assert result.status == "configured"
    assert result.model_key == f"deepseek-{model.model_id}"
    assert config.get_value("model") == result.model_key

    first = json.loads(extra_models.read_text(encoding="utf-8"))
    assert configure_model(registry, "deepseek", model.model_id).status == "configured"
    second = json.loads(extra_models.read_text(encoding="utf-8"))
    assert first == second
    assert not result.model_key.startswith("cn-")


def test_configure_model_rejects_non_tool_model():
    from code_puppy.cn_setup import configure_model

    provider = SimpleNamespace(id="deepseek", env=[])
    model = SimpleNamespace(model_id="no-tools", tool_call=False)
    registry = SimpleNamespace(
        get_provider=lambda provider_id: provider,
        get_models=lambda provider_id: [model],
    )
    result = configure_model(registry, "deepseek", "no-tools")
    assert result.status == "unsupported"


def test_noninteractive_wizard_fails_closed(monkeypatch):
    from code_puppy.cn_setup import run_setup_wizard

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert run_setup_wizard(_registry()).status == "non_interactive"


def test_wizard_uses_worker_thread_inside_running_event_loop(monkeypatch):
    import code_puppy.cn_setup as setup

    caller_thread = threading.get_ident()
    worker_threads = []

    def fake_wizard(registry):
        worker_threads.append(threading.get_ident())
        return setup.SetupResult(status="cancelled")

    monkeypatch.setattr(setup, "_run_setup_wizard", fake_wizard)

    async def invoke():
        return setup.run_setup_wizard(object())

    result = asyncio.run(invoke())
    assert result.status == "cancelled"
    assert worker_threads
    assert worker_threads[0] != caller_thread
