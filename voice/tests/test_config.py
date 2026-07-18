"""Tests for voice.config loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from voice.config import (
    DEFAULT_PROVIDER,
    ConfigLoadError,
    ConfigMissing,
    is_usable_reference,
    is_usable_speaker,
    load_voice_config,
)


def _write_cfg(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_missing_config_returns_sentinel(tmp_path: Path) -> None:
    result = load_voice_config(tmp_path / "nope.json", environ={})
    assert isinstance(result, ConfigMissing)


def test_malformed_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "config.local.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_voice_config(bad, environ={})


def test_defaults_provider_and_device(tmp_path: Path) -> None:
    cfg_path = _write_cfg(
        tmp_path / "config.local.json",
        {
            "enabled": True,
            "routing": {"en": {"speaker": "EN-US"}},
        },
    )
    cfg = load_voice_config(cfg_path, environ={})
    assert not isinstance(cfg, ConfigMissing)
    assert cfg["provider"] == DEFAULT_PROVIDER
    assert cfg["device"] == "cpu"
    assert cfg["tone_convert"] is True
    assert cfg["routing"]["en"]["speaker"] == "EN-US"


def test_legacy_voice_id_maps_to_speaker(tmp_path: Path) -> None:
    cfg_path = _write_cfg(
        tmp_path / "config.local.json",
        {"enabled": True, "routing": {"en": {"voice_id": "EN-US"}}},
    )
    cfg = load_voice_config(cfg_path, environ={})
    assert not isinstance(cfg, ConfigMissing)
    assert cfg["routing"]["en"]["speaker"] == "EN-US"


def test_speaker_and_reference_helpers(tmp_path: Path) -> None:
    wav = tmp_path / "ref.wav"
    wav.write_bytes(b"RIFF")
    assert is_usable_speaker("EN-US")
    assert not is_usable_speaker("<speaker>")
    assert is_usable_reference(str(wav))
    assert not is_usable_reference("voice/refs/missing.wav")
