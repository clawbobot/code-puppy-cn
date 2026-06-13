"""Locale detection and persistence."""

from __future__ import annotations

import locale as stdlib_locale
import os
import sys

SUPPORTED_LOCALES = ("en-US", "zh-CN")


def available_locales() -> tuple[str, ...]:
    return SUPPORTED_LOCALES


def normalize_locale(value: str | None) -> str:
    normalized = (value or "").strip().replace("_", "-").lower()
    if normalized.startswith(("zh-cn", "zh-sg", "zh-hans")):
        return "zh-CN"
    return "en-US"


def detect_system_locale() -> str:
    candidates = [
        os.environ.get("LC_ALL"),
        os.environ.get("LC_MESSAGES"),
        os.environ.get("LANG"),
    ]
    try:
        candidates.append(stdlib_locale.getlocale()[0])
    except Exception:
        pass
    for candidate in candidates:
        if candidate:
            return normalize_locale(candidate.split(".", 1)[0])
    return "en-US"


def get_locale() -> str:
    from code_puppy.config import get_value

    return normalize_locale(get_value("locale") or detect_system_locale())


def set_locale(value: str) -> str:
    from pathlib import Path

    from code_puppy.config import CONFIG_FILE, set_value

    selected = normalize_locale(value)
    Path(CONFIG_FILE).parent.mkdir(parents=True, exist_ok=True)
    set_value("locale", selected)
    return selected


def ensure_locale_configured(interactive: bool = True) -> str:
    """Persist a locale on first run, optionally asking on an interactive TTY."""
    from code_puppy.config import get_value

    configured = get_value("locale")
    if configured:
        return normalize_locale(configured)

    detected = detect_system_locale()
    selected = detected
    if interactive and sys.stdin.isatty():
        default_choice = "2" if detected == "zh-CN" else "1"
        print("Choose interface language / 选择界面语言")
        print("  1. English (en-US)")
        print("  2. 简体中文 (zh-CN)")
        try:
            answer = input(f"Selection / 选择 [{default_choice}]: ").strip()
            if answer in {"2", "zh", "zh-CN", "zh_CN"}:
                selected = "zh-CN"
            elif answer in {"1", "en", "en-US", "en_US"}:
                selected = "en-US"
        except (EOFError, KeyboardInterrupt):
            selected = detected
    return set_locale(selected)
