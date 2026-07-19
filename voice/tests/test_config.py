"""Tests for voice.config loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from voice.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL_ID,
    ConfigLoadError,
    ConfigMissing,
    is_usable_voice_id,
    load_voice_config,
    save_openai_key,
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


def test_defaults_base_url_and_model(tmp_path: Path) -> None:
    cfg_path = _write_cfg(
        tmp_path / "config.local.json",
        {
            "enabled": True,
            "provider": "elevenlabs",
            "routing": {"en": {"voice_id": "abc"}},
        },
    )
    cfg = load_voice_config(cfg_path, environ={"ELEVENLABS_API_KEY": "secret"})
    assert not isinstance(cfg, ConfigMissing)
    assert cfg["base_url"] == DEFAULT_BASE_URL
    assert cfg["model_id"] == DEFAULT_MODEL_ID
    assert cfg["api_key"] == "secret"


def test_placeholder_voice_id_detection() -> None:
    assert is_usable_voice_id("real-voice-123")
    assert not is_usable_voice_id("")
    assert not is_usable_voice_id("<tl_voice_id>")
    assert not is_usable_voice_id("voice_id")


def test_save_openai_key_preserves_fields(tmp_path: Path) -> None:
    p = tmp_path / "config.local.json"
    p.write_text(json.dumps({"api_key": "eleven", "provider": "elevenlabs"}), encoding="utf-8")
    save_openai_key("sk-abc", path=p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["openai_api_key"] == "sk-abc"
    assert data["api_key"] == "eleven"
