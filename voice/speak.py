"""Voice entry point. See voice/README.md and spec.md §6.6."""

from __future__ import annotations

import json
import logging
import os
import random
import urllib.error
import urllib.request

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

# Overlay pointing prompts (blank filled with OCR / list label)
POINT_TEMPLATES = {
    "en": [
        "Here's {label}.",
        "Here is {label}.",
        "Here's your {label}.",
        "I think this is {label}.",
        "Looks like {label}.",
        "Found it — {label}.",
        "Here — {label}.",
        "This one looks like {label}.",
        "Pretty sure that's {label}.",
    ],
    "tl": [
        "Eto ang {label}.",
        "Here's {label}.",
        "Sa tingin ko ito ang {label}.",
        "Parang {label} ito.",
        "Nakita ko na — {label}.",
        "Eto yata — {label}.",
    ],
    "taglish": [
        "Here's {label}.",
        "Eto yung {label}.",
        "I think this is {label}.",
        "Parang {label} to.",
        "Nakita ko na — {label}.",
        "Looks like {label}.",
    ],
}

HTTP_TIMEOUT_S = 10.0


def render_template(filename: str, language_mode: str) -> str:
    mode = language_mode.lower()
    template = TEMPLATES[mode]
    return template.format(filename=filename)


def render_point_prompt(label: str, language_mode: str = "en") -> str:
    """Pick a random pointing prompt with the blank filled."""
    mode = language_mode.lower()
    if mode not in POINT_TEMPLATES:
        mode = "en"
    template = random.choice(POINT_TEMPLATES[mode])
    return template.format(label=str(label).strip() or "this")


def _fetch_tts(
    *,
    base_url: str,
    voice_id: str,
    api_key: str,
    model_id: str,
    text: str,
) -> bytes:
    # pcm_16000 → raw 16-bit mono PCM we can play in-process (no external player).
    url = f"{base_url.rstrip('/')}/v1/text-to-speech/{voice_id}?output_format=pcm_16000"
    payload = json.dumps({"text": text, "model_id": model_id}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/pcm",
        },
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
        return response.read()


def _play_pcm(pcm: bytes, samplerate: int = 16000) -> None:
    """Play raw 16-bit mono PCM in-process — no external player window."""
    import io
    import wave
    import winsound

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(pcm)
    # SND_MEMORY: play the WAV straight from memory, blocking until done
    # (this runs on the speak worker thread, so blocking is fine).
    winsound.PlaySound(buf.getvalue(), winsound.SND_MEMORY | winsound.SND_NODEFAULT)


def _elevenlabs_utterance(text: str, language_mode: str) -> str:
    """Return 'ok' | 'skip' | 'fail' for ElevenLabs path."""
    mode = str(language_mode).strip().lower()
    if mode not in TEMPLATES and mode not in POINT_TEMPLATES:
        return "fail"

    try:
        loaded = load_voice_config(CONFIG_PATH, environ=dict(os.environ))
    except ConfigLoadError as exc:
        logger.warning("speak: %s", exc)
        return "fail"

    if isinstance(loaded, ConfigMissing):
        logger.info("speak: no config.local.json; skip ElevenLabs")
        return "skip"

    if not loaded["enabled"]:
        logger.info("speak: enabled=false; skip ElevenLabs")
        return "skip"

    if loaded["provider"].lower() != "elevenlabs":
        logger.warning("speak: unsupported provider %r", loaded["provider"])
        return "fail"

    api_key = loaded["api_key"]
    if not api_key:
        logger.warning("speak: missing ELEVENLABS_API_KEY")
        return "fail"

    # Prefer en/tl routing; taglish uses tl voice ids in config
    route_mode = mode if mode in ("en", "tl", "taglish") else "en"
    voice_id = voice_id_for_mode(loaded, route_mode)
    if not is_usable_voice_id(voice_id):
        logger.warning("speak: missing or placeholder voice_id for mode %s", route_mode)
        return "fail"

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
            return "fail"
        _play_pcm(audio)
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        logger.warning("speak: TTS/playback failed: %s", exc)
        return "fail"
    except Exception as exc:  # noqa: BLE001 — soft-fail contract
        logger.warning("speak: unexpected failure: %s", exc)
        return "fail"

    return "ok"


def speak_text(text: str, language_mode: str = "en") -> bool:
    """Speak arbitrary reply text via ElevenLabs. Soft-fail when TTS is unavailable."""
    if not str(text).strip():
        logger.warning("speak_text: empty text")
        return False

    mode = str(language_mode).strip().lower()
    if mode not in TEMPLATES and mode not in POINT_TEMPLATES:
        mode = "en"

    result = _elevenlabs_utterance(str(text).strip(), mode)
    if result == "ok":
        return True
    if result == "skip":
        return True
    return False


def speak(filename: str, language_mode: str) -> bool:
    """Speak a templated confirmation for *filename* in *language_mode*."""
    if not str(filename).strip():
        logger.warning("speak: empty filename")
        return False

    mode = str(language_mode).strip().lower()
    if mode not in TEMPLATES:
        logger.warning("speak: unsupported language_mode %r", language_mode)
        return False

    text = render_template(str(filename).strip(), mode)
    result = _elevenlabs_utterance(text, mode)
    if result == "ok":
        return True
    if result == "skip":
        # Preserve planned no-op when voice is disabled / unconfigured
        return True
    return False


def speak_point(label: str, language_mode: str = "en") -> bool:
    """Speak a varied pointing prompt via ElevenLabs. Returns True if audio played."""
    text, ok = speak_point_line(label, language_mode=language_mode)
    return ok and bool(text)


def speak_point_line(label: str, language_mode: str = "en") -> tuple[str, bool]:
    """Return (prompt_text, elevenlabs_ok). Always builds a variation for the bubble."""
    if not str(label).strip():
        logger.warning("speak_point: empty label")
        return "", False

    mode = str(language_mode).strip().lower()
    if mode not in POINT_TEMPLATES:
        mode = "en"

    text = render_point_prompt(str(label).strip(), mode)
    ok = _elevenlabs_utterance(text, mode) == "ok"
    return text, ok


def elevenlabs_ready() -> tuple[bool, str]:
    """Check whether overlay pointing can use ElevenLabs TTS."""
    try:
        loaded = load_voice_config(CONFIG_PATH, environ=dict(os.environ))
    except ConfigLoadError as exc:
        return False, str(exc)
    if isinstance(loaded, ConfigMissing):
        return False, "missing voice/config.local.json"
    if not loaded["enabled"]:
        return False, "voice enabled=false"
    if loaded["provider"].lower() != "elevenlabs":
        return False, f"provider={loaded['provider']!r} (need elevenlabs)"
    if not loaded["api_key"]:
        return False, "set ELEVENLABS_API_KEY (or api_key in config.local.json)"
    voice_id = voice_id_for_mode(loaded, "en")
    if not is_usable_voice_id(voice_id):
        return False, "set routing.en.voice_id in config.local.json"
    return True, "ElevenLabs ready"
