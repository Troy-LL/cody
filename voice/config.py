"""Load VoiceConfig from local JSON + ELEVENLABS_API_KEY env."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, TypedDict

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.elevenlabs.io"
DEFAULT_MODEL_ID = "eleven_flash_v2_5"
CONFIG_PATH = Path(__file__).resolve().parent / "config.local.json"


class VoiceConfig(TypedDict):
    enabled: bool
    provider: str
    base_url: str
    model_id: str
    api_key: str
    routing: dict[str, dict[str, str]]


class ConfigLoadError(Exception):
    """config.local.json exists but cannot be used."""


class ConfigMissing:
    """Sentinel: no local config file (treat as disabled)."""


def _is_placeholder_voice_id(voice_id: str) -> bool:
    value = voice_id.strip()
    if not value:
        return True
    lower = value.lower()
    return "<" in value or ">" in value or "voice_id" in lower


def is_usable_voice_id(voice_id: str | None) -> bool:
    if voice_id is None:
        return False
    return not _is_placeholder_voice_id(voice_id)


def load_voice_config(
    path: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> VoiceConfig | ConfigMissing:
    """Load config.

    Returns ConfigMissing when the file is absent (planned disabled).
    Raises ConfigLoadError when the file exists but is invalid JSON/shape.
    """
    cfg_path = path if path is not None else CONFIG_PATH
    env = environ if environ is not None else os.environ

    if not cfg_path.is_file():
        return ConfigMissing()

    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigLoadError(f"invalid voice config at {cfg_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigLoadError("voice config root must be an object")

    enabled = bool(raw.get("enabled", False))
    provider = str(raw.get("provider", "elevenlabs")).strip()
    base_url = str(raw.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    model_id = str(raw.get("model_id") or DEFAULT_MODEL_ID)
    routing_raw = raw.get("routing", {})
    if routing_raw is None:
        routing_raw = {}
    if not isinstance(routing_raw, dict):
        raise ConfigLoadError("routing must be an object")

    routing: dict[str, dict[str, str]] = {}
    for key, value in routing_raw.items():
        if not isinstance(value, dict):
            raise ConfigLoadError(f"routing.{key} must be an object")
        voice_id = str(value.get("voice_id", ""))
        routing[str(key).lower()] = {"voice_id": voice_id}

    api_key = str(env.get("ELEVENLABS_API_KEY", "")).strip()

    return VoiceConfig(
        enabled=enabled,
        provider=provider,
        base_url=base_url,
        model_id=model_id,
        api_key=api_key,
        routing=routing,
    )


def voice_id_for_mode(config: VoiceConfig, language_mode: str) -> str | None:
    row = config["routing"].get(language_mode)
    if not row:
        return None
    return row.get("voice_id")
