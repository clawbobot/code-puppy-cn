"""Runtime internationalization for Code Puppy CN."""

from .locale import (
    available_locales,
    detect_system_locale,
    ensure_locale_configured,
    get_locale,
    normalize_locale,
    set_locale,
)
from .translator import t, t_or

__all__ = [
    "available_locales",
    "detect_system_locale",
    "ensure_locale_configured",
    "get_locale",
    "normalize_locale",
    "set_locale",
    "t",
    "t_or",
]
