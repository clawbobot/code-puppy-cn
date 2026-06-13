"""Interactive China-region model setup built on upstream model configuration."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from code_puppy.i18n import t

CHINA_PROVIDER_IDS = ("alibaba-cn", "deepseek", "moonshotai-cn", "zai")


@dataclass(frozen=True)
class SetupResult:
    status: str
    provider_id: str | None = None
    model_id: str | None = None
    model_key: str | None = None
    message: str | None = None


def score_model(model: Any) -> tuple[int, int, str]:
    """Rank models using registry capabilities, recency, and context size."""
    score = 0
    if model.tool_call:
        score += 100
    if model.reasoning:
        score += 20
    if model.structured_output:
        score += 10
    if "code" in f"{model.model_id} {model.name}".lower():
        score += 15
    if model.context_length >= 128_000:
        score += 8
    elif model.context_length >= 32_000:
        score += 4
    if model.max_output >= 16_000:
        score += 3
    release_digits = "".join(
        character for character in (model.release_date or "") if character.isdigit()
    )
    recency = int(release_digits[:8] or 0)
    return score, recency, model.model_id


def ranked_models(registry: Any, provider_id: str) -> list[Any]:
    models = [model for model in registry.get_models(provider_id) if model.tool_call]
    return sorted(models, key=score_model, reverse=True)


def model_key(provider_id: str, model_id: str) -> str:
    return f"{provider_id}-{model_id}".replace("/", "-").replace(":", "-")


def configure_model(
    registry: Any,
    provider_id: str,
    model_id: str,
    credentials: dict[str, str] | None = None,
    activate: bool = True,
) -> SetupResult:
    """Configure one registry model through upstream AddModelMenu helpers."""
    from code_puppy.command_line.add_model_menu import AddModelMenu
    from code_puppy.config import set_model_name
    from code_puppy.provider_credentials import save_credential

    provider = registry.get_provider(provider_id)
    model = next(
        (
            item
            for item in registry.get_models(provider_id)
            if item.model_id == model_id
        ),
        None,
    )
    if provider is None or model is None:
        return SetupResult(
            status="not_found",
            provider_id=provider_id,
            model_id=model_id,
        )
    if not model.tool_call:
        return SetupResult(
            status="unsupported",
            provider_id=provider_id,
            model_id=model_id,
            message="tool_call is not supported",
        )

    for env_name, value in (credentials or {}).items():
        if env_name in provider.env and value:
            save_credential(env_name, value)

    menu = AddModelMenu.__new__(AddModelMenu)
    if not menu._add_model_to_extra_config(model, provider):
        return SetupResult(
            status="error",
            provider_id=provider_id,
            model_id=model_id,
        )

    key = model_key(provider.id, model.model_id)
    if activate:
        set_model_name(key)
    return SetupResult(
        status="configured",
        provider_id=provider.id,
        model_id=model.model_id,
        model_key=key,
    )


def _provider_choices(registry: Any) -> list[tuple[str, str]]:
    choices = []
    for provider_id in CHINA_PROVIDER_IDS:
        provider = registry.get_provider(provider_id)
        if provider is None:
            continue
        count = len(ranked_models(registry, provider_id))
        choices.append(
            (
                provider_id,
                t(
                    "cn_setup.provider_choice",
                    name=provider.name,
                    id=provider.id,
                    count=count,
                ),
            )
        )
    return choices


def _model_choices(registry: Any, provider_id: str) -> list[tuple[str, str]]:
    choices = []
    for index, model in enumerate(ranked_models(registry, provider_id), start=1):
        badge = t("cn_setup.recommended") if index <= 3 else ""
        choices.append(
            (
                model.model_id,
                t(
                    "cn_setup.model_choice",
                    name=model.name,
                    id=model.model_id,
                    context=model.context_length or "unknown",
                    badge=badge,
                ).strip(),
            )
        )
    return choices


def _choose(title: str, text: str, values: list[tuple[str, str]]) -> str | None:
    from prompt_toolkit.shortcuts import radiolist_dialog
    from code_puppy.agents._key_listeners import suspended_key_listener

    if not values:
        return None
    with suspended_key_listener():
        return radiolist_dialog(
            title=title,
            text=text,
            values=values,
            ok_text=t("cn_setup.next"),
            cancel_text=t("cn_setup.cancel"),
        ).run()


def _ask_secret(title: str, text: str) -> str | None:
    from prompt_toolkit.shortcuts import input_dialog
    from code_puppy.agents._key_listeners import suspended_key_listener

    with suspended_key_listener():
        return input_dialog(
            title=title,
            text=text,
            password=True,
            ok_text=t("cn_setup.save"),
            cancel_text=t("cn_setup.skip"),
        ).run()


def run_setup_wizard(registry: Any | None = None) -> SetupResult:
    """Run the localized provider -> model -> credential -> activate flow."""
    from code_puppy.models_dev_parser import ModelsDevRegistry
    from code_puppy.provider_credentials import is_credential_set

    registry = registry or ModelsDevRegistry()
    if not sys.stdin.isatty():
        return SetupResult(status="non_interactive")

    provider_id = _choose(
        t("cn_setup.title"),
        t("cn_setup.choose_provider"),
        _provider_choices(registry),
    )
    if not provider_id:
        return SetupResult(status="cancelled")

    model_id = _choose(
        t("cn_setup.title"),
        t("cn_setup.choose_model"),
        _model_choices(registry, provider_id),
    )
    if not model_id:
        return SetupResult(status="cancelled", provider_id=provider_id)

    provider = registry.get_provider(provider_id)
    credentials: dict[str, str] = {}
    for env_name in provider.env:
        if is_credential_set(env_name):
            continue
        value = _ask_secret(
            t("cn_setup.credential_title"),
            t("cn_setup.credential_prompt", name=env_name),
        )
        if value:
            credentials[env_name] = value

    return configure_model(
        registry,
        provider_id,
        model_id,
        credentials=credentials,
        activate=True,
    )
