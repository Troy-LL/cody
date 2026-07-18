"""Voice entry point. See voice/README.md and spec.md §6.6."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import urllib.error
import urllib.request
from typing import Any

from voice.config import (
    CONFIG_PATH,
    ConfigLoadError,
    ConfigMissing,
    is_usable_voice_id,
    load_voice_config,
    voice_id_for_mode,
)

logger = logging.getLogger(__name__)

TEMPLATES = {
    "en": "Found it — {filename}.",
    "tl": "Nakita ko na — {filename}.",
    "taglish": "Nakita ko na — {filename}.",
}

HTTP_TIMEOUT_S = 10.0


def render_template(filename: str, language_mode: str) -> str:
    mode = language_mode.lower()
    template = TEMPLATES[mode]
    return template.format(filename=filename)


def _fetch_tts(
    *,
    base_url: str,
    voice_id: str,
    api_key: str,
    model_id: str,
    text: str,
) -> bytes:
    url = f"{base_url.rstrip('/')}/v1/text-to-speech/{voice_id}"
    payload = json.dumps({"text": text, "model_id": model_id}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
        return response.read()


def _play_mp3(audio: bytes) -> None:
    # delete=False: leave file so the OS player can open it after we return.
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as handle:
        handle.write(audio)
        path = handle.name
    os.startfile(path)  # type: ignore[attr-defined]


def speak(filename: str, language_mode: str) -> bool:
    """Speak a templated confirmation for *filename* in *language_mode*."""
    if not str(filename).strip():
        logger.warning("speak: empty filename")
        return False

    mode = str(language_mode).strip().lower()
    if mode not in TEMPLATES:
        logger.warning("speak: unsupported language_mode %r", language_mode)
        return False

    try:
        loaded = load_voice_config(CONFIG_PATH, environ=dict(os.environ))
    except ConfigLoadError as exc:
        logger.warning("speak: %s", exc)
        return False

    if isinstance(loaded, ConfigMissing):
        logger.warning("speak: no config.local.json; treating as disabled")
        return True

    if not loaded["enabled"]:
        logger.warning("speak: enabled=false; planned no-op")
        return True

    if loaded["provider"].lower() != "elevenlabs":
        logger.warning("speak: unsupported provider %r", loaded["provider"])
        return False

    api_key = loaded["api_key"]
    if not api_key:
        logger.warning("speak: missing ELEVENLABS_API_KEY")
        return False

    voice_id = voice_id_for_mode(loaded, mode)
    if not is_usable_voice_id(voice_id):
        logger.warning("speak: missing or placeholder voice_id for mode %s", mode)
        return False

    text = render_template(str(filename).strip(), mode)
    try:
        audio = _fetch_tts(
            base_url=loaded["base_url"],
            voice_id=str(voice_id),
            api_key=api_key,
            model_id=loaded["model_id"],
            text=text,
        )
        if not audio:
            logger.warning("speak: empty TTS response")
            return False
        _play_mp3(audio)
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        logger.warning("speak: TTS/playback failed: %s", exc)
        return False
    except Exception as exc:  # noqa: BLE001 — soft-fail contract
        logger.warning("speak: unexpected failure: %s", exc)
        return False

    return True
