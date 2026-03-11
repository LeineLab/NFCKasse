#!/usr/bin/env python3
"""
Minimal i18n for NFCKasse.

Usage:
    import i18n
    from i18n import _

    i18n.load(['de', 'en'])   # call once at startup
    i18n.set_language('de')

    _('btn.scan')                              # -> "Artikel scannen"
    _('msg.scan_item', balance=4.20)           # -> "Artikel scannen\n..."
    i18n.lang_name('en')                       # -> "English"
"""

import json
import os

_locales: dict = {}
_current: str = "de"


def load(languages: list) -> None:
    """Load locale JSON files for the given language codes."""
    global _locales
    base = os.path.dirname(os.path.abspath(__file__))
    for lang in languages:
        path = os.path.join(base, "locales", f"{lang}.json")
        with open(path, encoding="utf-8") as f:
            _locales[lang] = json.load(f)


def set_language(lang: str) -> None:
    global _current
    _current = lang


def lang_name(lang_code: str) -> str:
    """Return the display name of a language (value of "lang.name" in its locale file)."""
    return _locales.get(lang_code, {}).get("lang.name", lang_code.upper())


def _(key: str, **kwargs) -> str:
    """Translate key in the current language. Format args are passed as keyword arguments."""
    text = _locales.get(_current, {}).get(key, key)
    return text.format(**kwargs) if kwargs else text
