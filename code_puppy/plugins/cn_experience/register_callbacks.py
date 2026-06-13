"""Commands, skill registration, and optional audit for the CN distribution."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from code_puppy.callbacks import register_callback
from code_puppy.cn_setup import CHINA_PROVIDER_IDS
from code_puppy.i18n import get_locale, set_locale, t
from code_puppy.messaging import emit_error, emit_info, emit_success


def _custom_help() -> list[tuple[str, str]]:
    return [
        ("language", t("command.language_desc")),
        ("语言", t("command.language_desc")),
        ("cn-setup", t("command.cn_setup_desc")),
        ("doctor-cn", t("command.doctor_desc")),
    ]


def _handle_language(command: str) -> bool:
    parts = command.split(maxsplit=1)
    if len(parts) == 1:
        emit_info(t("command.language_current", locale=get_locale()))
        emit_info(t("command.language_usage"))
        return True
    raw = parts[1].strip()
    if raw not in {"en-US", "en_US", "en", "zh-CN", "zh_CN", "zh"}:
        emit_error(t("command.language_usage"))
        return True
    selected = set_locale(raw)
    emit_success(t("command.language_changed", locale=selected))
    return True


def _tool_models(registry, provider_id: str):
    from code_puppy.cn_setup import ranked_models

    return ranked_models(registry, provider_id)


def _handle_cn_setup(command: str) -> bool:
    from code_puppy.cn_setup import configure_model, run_setup_wizard
    from code_puppy.models_dev_parser import ModelsDevRegistry

    try:
        registry = ModelsDevRegistry()
    except Exception as exc:
        emit_error(str(exc))
        return True

    parts = command.split()
    if len(parts) == 1:
        result = run_setup_wizard(registry)
        if result.status == "configured":
            emit_success(t("cn_setup.activated", model=result.model_key))
        elif result.status == "non_interactive":
            emit_error(t("cn_setup.non_interactive"))
            emit_info(t("cn_setup.hint"))
        elif result.status not in {"cancelled"}:
            emit_error(t("cn_setup.failed", model=result.model_id or ""))
        return True

    if len(parts) < 3 or parts[1] in {"list", "--list"}:
        emit_info(t("cn_setup.title"))
        emit_info(t("cn_setup.source", source=registry.data_source))
        for provider_id in CHINA_PROVIDER_IDS:
            provider = registry.get_provider(provider_id)
            if provider is None:
                continue
            models = _tool_models(registry, provider_id)
            emit_info(
                t(
                    "cn_setup.provider",
                    name=provider.name,
                    id=provider.id,
                    count=len(models),
                )
            )
            for model in models[:8]:
                emit_info(
                    t(
                        "cn_setup.model",
                        id=model.model_id,
                        context=model.context_length or "unknown",
                    )
                )
        emit_info(t("cn_setup.hint"))
        return True

    provider_id, model_id = parts[1], parts[2]
    result = configure_model(registry, provider_id, model_id)
    if result.status == "not_found":
        emit_error(t("cn_setup.not_found", provider=provider_id, model=model_id))
        return True
    if result.status == "unsupported":
        emit_error(t("cn_setup.unsupported", model=model_id))
    elif result.status == "configured":
        emit_success(t("cn_setup.activated", model=result.model_key))
    else:
        emit_error(t("cn_setup.failed", model=model_id))
    return True


def _handle_doctor(command: str) -> bool:
    from code_puppy.cn_doctor import render_human, report

    parts = command.split()
    live = "--live" in parts
    emit_info(render_human(report(live=live)))
    return True


def _custom_command(command: str, name: str) -> bool | None:
    if name in {"language", "语言"}:
        return _handle_language(command)
    if name == "cn-setup":
        return _handle_cn_setup(command)
    if name == "doctor-cn":
        return _handle_doctor(command)
    return None


def _code_fix_skill() -> list[dict[str, Any]]:
    locale = get_locale()
    if locale == "zh-CN":
        description = "读取项目、修复确定性缺陷、运行测试并用中文总结"
        body = """
# Code Fix

1. 阅读项目说明、相关代码和测试。
2. 先复现失败，再定位根因。
3. 只修改解决问题所需的最少文件。
4. 运行相关测试；失败时根据证据继续修正。
5. 最终报告修改文件、测试结果和剩余风险。
6. 除代码、命令和专有名词外，使用中文说明。
"""
    else:
        description = (
            "Inspect a project, fix a deterministic defect, run tests, and summarize"
        )
        body = """
# Code Fix

1. Read the project instructions, relevant code, and tests.
2. Reproduce the failure before identifying its root cause.
3. Change only the files required to solve the problem.
4. Run relevant tests and iterate based on evidence.
5. Report changed files, test results, and remaining risks.
"""
    return [
        {
            "name": "code-fix",
            "frontmatter": {
                "name": "code-fix",
                "description": description,
                "version": "0.1.0",
                "author": "Code Puppy CN",
                "tags": ["coding", "debugging", "testing"],
            },
            "body": body.strip(),
        }
    ]


def _audit_enabled() -> bool:
    return os.environ.get("CODE_PUPPY_CN_AUDIT", "").lower() in {
        "1",
        "true",
        "yes",
    }


def _write_audit(event: dict[str, Any]) -> None:
    if not _audit_enabled():
        return
    from code_puppy.config import STATE_DIR

    path = Path(STATE_DIR) / "cn" / "audit" / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")


async def _agent_run_start(agent_name: str, model_name: str, session_id: str) -> None:
    _write_audit(
        {
            "event": "agent_run_start",
            "timestamp": time.time(),
            "agent": agent_name,
            "model": model_name,
            "session_id": session_id,
        }
    )


async def _post_tool_call(
    tool_name: str,
    tool_args: dict,
    result: Any,
    duration_ms: float,
    context: Any = None,
) -> None:
    _write_audit(
        {
            "event": "tool_complete",
            "timestamp": time.time(),
            "tool": tool_name,
            "duration_ms": duration_ms,
            "success": not isinstance(result, Exception),
        }
    )


register_callback("custom_command_help", _custom_help)
register_callback("custom_command", _custom_command)
register_callback("register_skills", _code_fix_skill)
register_callback("agent_run_start", _agent_run_start)
register_callback("post_tool_call", _post_tool_call)
