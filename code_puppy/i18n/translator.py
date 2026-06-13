"""JSON-backed translations with English fallback."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
_LOCALES_DIR = Path(__file__).parent / "locales"


@lru_cache(maxsize=4)
def _load_catalog(locale: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{locale}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to load locale catalog %s: %s", locale, exc)
        return {}
    return {str(key): str(value) for key, value in data.items()}


def t(key: str, **params: Any) -> str:
    from .locale import get_locale

    locale = get_locale()
    english = _load_catalog("en-US")
    template = _load_catalog(locale).get(key) or english.get(key)
    if template is None:
        logger.warning("Missing English translation key: %s", key)
        return key
    try:
        return template.format(**params)
    except (KeyError, ValueError, IndexError) as exc:
        logger.error("Translation formatting failed for %s: %s", key, exc)
        return template
