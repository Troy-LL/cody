"""Load VoiceConfig for the local OpenVoice engine."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE_DIR / "config.local.json"
DEFAULT_CHECKPOINTS_DIR = str(PACKAGE_DIR / "checkpoints_v2")
DEFAULT_DEVICE = "cpu"
DEFAULT_PROVIDER = "openvoice"


class RouteConfig(TypedDict):
    speaker: str
    reference_wav: str


class VoiceConfig(TypedDict):
    enabled: bool
    provider: str
    device: str
    checkpoints_dir: str
    tone_convert: bool
    routing: dict[str, RouteConfig]


class ConfigLoadError(Exception):
    """config.local.json exists but cannot be used."""


class ConfigMissing:
    """Sentinel: no local config file (treat as disabled)."""


def _is_placeholder(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    return "<" in text or ">" in text


def is_usable_speaker(speaker: str | None) -> bool:
    if speaker is None:
        return False
    return not _is_placeholder(speaker)


def is_usable_reference(path: str | None) -> bool:
    if path is None or _is_placeholder(path):
        return False
    return Path(path).expanduser().is_file()


def load_voice_config(
    path: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> VoiceConfig | ConfigMissing:
    """Load config.

    Returns ConfigMissing when the file is absent (planned disabled).
    Raises ConfigLoadError when the file exists but is invalid JSON/shape.
    """
    del environ  # no secrets for local OpenVoice; kept for call-site compatibility
    cfg_path = path if path is not None else CONFIG_PATH

    if not cfg_path.is_file():
        return ConfigMissing()

    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigLoadError(f"invalid voice config at {cfg_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigLoadError("voice config root must be an object")

    enabled = bool(raw.get("enabled", False))
    provider = str(raw.get("provider", DEFAULT_PROVIDER)).strip()
    device = str(raw.get("device") or os.environ.get("OPENVOICE_DEVICE") or DEFAULT_DEVICE)
    checkpoints_dir = str(raw.get("checkpoints_dir") or DEFAULT_CHECKPOINTS_DIR)
    tone_convert = bool(raw.get("tone_convert", True))

    routing_raw = raw.get("routing", {})
    if routing_raw is None:
        routing_raw = {}
    if not isinstance(routing_raw, dict):
        raise ConfigLoadError("routing must be an object")

    routing: dict[str, RouteConfig] = {}
    for key, value in routing_raw.items():
        if not isinstance(value, dict):
            raise ConfigLoadError(f"routing.{key} must be an object")
        # Accept legacy voice_id as speaker alias.
        speaker = str(value.get("speaker") or value.get("voice_id") or "")
        reference_wav = str(value.get("reference_wav") or "")
        routing[str(key).lower()] = {
            "speaker": speaker,
            "reference_wav": reference_wav,
        }

    return VoiceConfig(
        enabled=enabled,
        provider=provider,
        device=device,
        checkpoints_dir=checkpoints_dir,
        tone_convert=tone_convert,
        routing=routing,
    )


def route_for_mode(config: VoiceConfig, language_mode: str) -> RouteConfig | None:
    return config["routing"].get(language_mode)
