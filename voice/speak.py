"""Voice entry point. See voice/README.md and spec.md §6.6."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from voice.config import (
    CONFIG_PATH,
    ConfigLoadError,
    ConfigMissing,
    is_usable_reference,
    is_usable_speaker,
    load_voice_config,
    route_for_mode,
)
from voice.openvoice_engine import OpenVoiceUnavailable, synthesize_to_wav

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


def _play_audio(path: str) -> None:
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

    if loaded["provider"].lower() != "openvoice":
        logger.warning("speak: unsupported provider %r (expected openvoice)", loaded["provider"])
        return False

    route = route_for_mode(loaded, mode)
    if route is None or not is_usable_speaker(route.get("speaker")):
        logger.warning("speak: missing or placeholder speaker for mode %s", mode)
        return False

    if loaded["tone_convert"] and not is_usable_reference(route.get("reference_wav")):
        logger.warning(
            "speak: tone_convert requires an existing reference_wav for mode %s", mode
        )
        return False

    text = render_template(str(filename).strip(), mode)
    try:
        wav_path = synthesize_to_wav(
            text=text,
            speaker=route["speaker"],
            language_mode=mode,
            checkpoints_dir=loaded["checkpoints_dir"],
            device=loaded["device"],
            reference_wav=route.get("reference_wav") or None,
            tone_convert=loaded["tone_convert"],
        )
        if not Path(wav_path).is_file():
            logger.warning("speak: synthesizer produced no file")
            return False
        _play_audio(str(wav_path))
    except OpenVoiceUnavailable as exc:
        logger.warning("speak: OpenVoice unavailable: %s", exc)
        return False
    except OSError as exc:
        logger.warning("speak: playback failed: %s", exc)
        return False
    except Exception as exc:  # noqa: BLE001 — soft-fail contract
        logger.warning("speak: unexpected failure: %s", exc)
        return False

    return True
