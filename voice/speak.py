"""Voice entry point. See voice/README.md and spec.md §6.6."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

TEMPLATES = {
    "en": "Found it — {filename}.",
    "tl": "Nakita ko na — {filename}.",
    "taglish": "Nakita ko na — {filename}.",
}


def render_template(filename: str, language_mode: str) -> str:
    mode = language_mode.lower()
    template = TEMPLATES[mode]
    return template.format(filename=filename)


def speak(filename: str, language_mode: str) -> bool:
    """Speak a templated confirmation for *filename* in *language_mode*.

    Stub returns ``True`` (fixture-shaped contract) until full TTS lands.
    """
    del filename, language_mode
    return True
