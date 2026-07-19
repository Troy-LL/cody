"""Tests for voice.speak — spec.md §6.6."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from voice.config import ConfigLoadError
from voice.speak import render_point_prompt, render_template, speak, speak_point, speak_text


def _write_cfg(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _enabled_cfg(tmp_path: Path, **overrides: object) -> Path:
    data: dict = {
        "enabled": True,
        "provider": "elevenlabs",
        "routing": {
            "en": {"voice_id": "en-voice"},
            "tl": {"voice_id": "tl-voice"},
            "taglish": {"voice_id": "tl-voice"},
        },
    }
    data.update(overrides)
    return _write_cfg(tmp_path / "config.local.json", data)


def test_empty_filename_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with patch("voice.speak.CONFIG_PATH", cfg), patch(
        "voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}
    ):
        assert speak("  ", "en") is False


def test_auto_language_mode_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with patch("voice.speak.CONFIG_PATH", cfg), patch(
        "voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}
    ):
        assert speak("receipt_lazada.pdf", "auto") is False


def test_templates() -> None:
    assert render_template("a.pdf", "en") == "Found it — a.pdf."
    assert render_template("a.pdf", "tl") == "Nakita ko na — a.pdf."
    assert render_template("a.pdf", "taglish") == "Nakita ko na — a.pdf."


def test_point_prompt_contains_label() -> None:
    line = render_point_prompt("Sort", "en")
    assert "Sort" in line
    assert line.endswith(".")


def test_speak_point_empty_soft_fails() -> None:
    assert speak_point("  ", "en") is False


def test_missing_config_is_planned_noop(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"
    with patch("voice.speak.CONFIG_PATH", missing):
        assert speak("receipt_lazada.pdf", "en") is True


def test_disabled_returns_true(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path, enabled=False)
    with patch("voice.speak.CONFIG_PATH", cfg), patch(
        "voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}
    ):
        assert speak("receipt_lazada.pdf", "en") is True


def test_missing_api_key_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with patch("voice.speak.CONFIG_PATH", cfg), patch("voice.speak.os.environ", {}):
        assert speak("receipt_lazada.pdf", "en") is False


def test_placeholder_voice_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(
        tmp_path,
        routing={"en": {"voice_id": "<en_voice_id>"}, "tl": {"voice_id": "x"}},
    )
    with patch("voice.speak.CONFIG_PATH", cfg), patch(
        "voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}
    ):
        assert speak("receipt_lazada.pdf", "en") is False


def test_unsupported_provider_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path, provider="azure")
    with patch("voice.speak.CONFIG_PATH", cfg), patch(
        "voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}
    ):
        assert speak("receipt_lazada.pdf", "en") is False


def test_malformed_config_soft_fails(tmp_path: Path) -> None:
    bad = tmp_path / "config.local.json"
    bad.write_text("{bad", encoding="utf-8")
    with patch("voice.speak.CONFIG_PATH", bad):
        assert speak("receipt_lazada.pdf", "en") is False


def test_happy_path_calls_tts_and_startfile(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    audio = b"ID3fake"
    with (
        patch("voice.speak.CONFIG_PATH", cfg),
        patch("voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}),
        patch("voice.speak._fetch_tts", return_value=audio) as fetch,
        patch("voice.speak.os.startfile") as startfile,
        patch("voice.speak.tempfile.NamedTemporaryFile") as ntf,
    ):
        tmp = MagicMock()
        tmp.name = str(tmp_path / "out.mp3")
        tmp.__enter__.return_value = tmp
        tmp.__exit__.return_value = False
        ntf.return_value = tmp

        assert speak("receipt_lazada.pdf", "EN") is True

    fetch.assert_called_once()
    assert fetch.call_args.kwargs["text"] == "Found it — receipt_lazada.pdf."
    assert fetch.call_args.kwargs["voice_id"] == "en-voice"
    startfile.assert_called_once_with(tmp.name)


def test_taglish_uses_tl_template(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with (
        patch("voice.speak.CONFIG_PATH", cfg),
        patch("voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}),
        patch("voice.speak._fetch_tts", return_value=b"x") as fetch,
        patch("voice.speak.os.startfile"),
        patch("voice.speak.tempfile.NamedTemporaryFile") as ntf,
    ):
        tmp = MagicMock()
        tmp.name = str(tmp_path / "out.mp3")
        tmp.__enter__.return_value = tmp
        tmp.__exit__.return_value = False
        ntf.return_value = tmp
        assert speak("a.pdf", "taglish") is True
    assert fetch.call_args.kwargs["text"] == "Nakita ko na — a.pdf."
    assert fetch.call_args.kwargs["voice_id"] == "tl-voice"


def test_speak_text_passes_through(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with (
        patch("voice.speak.CONFIG_PATH", cfg),
        patch("voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}),
        patch("voice.speak._fetch_tts", return_value=b"x") as fetch,
        patch("voice.speak.os.startfile"),
        patch("voice.speak.tempfile.NamedTemporaryFile") as ntf,
    ):
        tmp = MagicMock()
        tmp.name = str(tmp_path / "out.mp3")
        tmp.__enter__.return_value = tmp
        tmp.__exit__.return_value = False
        ntf.return_value = tmp
        assert speak_text("The address bar is at the top.", "en") is True
    assert fetch.call_args.kwargs["text"] == "The address bar is at the top."


def test_tts_failure_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with (
        patch("voice.speak.CONFIG_PATH", cfg),
        patch("voice.speak.os.environ", {"ELEVENLABS_API_KEY": "k"}),
        patch("voice.speak._fetch_tts", side_effect=TimeoutError("slow")),
    ):
        assert speak("receipt_lazada.pdf", "tl") is False
