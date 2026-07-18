"""Tests for voice.speak — spec.md §6.6 (OpenVoice engine)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from voice.openvoice_engine import OpenVoiceUnavailable
from voice.speak import render_template, speak


def _write_cfg(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _enabled_cfg(tmp_path: Path, **overrides: object) -> Path:
    ref = tmp_path / "speaker.wav"
    ref.write_bytes(b"RIFF")
    data: dict = {
        "enabled": True,
        "provider": "openvoice",
        "tone_convert": False,
        "checkpoints_dir": str(tmp_path / "checkpoints_v2"),
        "routing": {
            "en": {"speaker": "EN-US", "reference_wav": str(ref)},
            "tl": {"speaker": "EN-US", "reference_wav": str(ref)},
            "taglish": {"speaker": "EN-US", "reference_wav": str(ref)},
        },
    }
    data.update(overrides)
    return _write_cfg(tmp_path / "config.local.json", data)


def test_empty_filename_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with patch("voice.speak.CONFIG_PATH", cfg):
        assert speak("  ", "en") is False


def test_auto_language_mode_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with patch("voice.speak.CONFIG_PATH", cfg):
        assert speak("receipt_lazada.pdf", "auto") is False


def test_templates() -> None:
    assert render_template("a.pdf", "en") == "Found it — a.pdf."
    assert render_template("a.pdf", "tl") == "Nakita ko na — a.pdf."
    assert render_template("a.pdf", "taglish") == "Nakita ko na — a.pdf."


def test_missing_config_is_planned_noop(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"
    with patch("voice.speak.CONFIG_PATH", missing):
        assert speak("receipt_lazada.pdf", "en") is True


def test_disabled_returns_true(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path, enabled=False)
    with patch("voice.speak.CONFIG_PATH", cfg):
        assert speak("receipt_lazada.pdf", "en") is True


def test_placeholder_speaker_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(
        tmp_path,
        routing={
            "en": {"speaker": "<EN-US>", "reference_wav": "x"},
            "tl": {"speaker": "EN-US", "reference_wav": "x"},
        },
    )
    with patch("voice.speak.CONFIG_PATH", cfg):
        assert speak("receipt_lazada.pdf", "en") is False


def test_tone_convert_requires_reference(tmp_path: Path) -> None:
    cfg = _enabled_cfg(
        tmp_path,
        tone_convert=True,
        routing={
            "en": {"speaker": "EN-US", "reference_wav": "voice/refs/missing.wav"},
            "tl": {"speaker": "EN-US", "reference_wav": "voice/refs/missing.wav"},
            "taglish": {"speaker": "EN-US", "reference_wav": "voice/refs/missing.wav"},
        },
    )
    with patch("voice.speak.CONFIG_PATH", cfg):
        assert speak("receipt_lazada.pdf", "en") is False


def test_unsupported_provider_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path, provider="elevenlabs")
    with patch("voice.speak.CONFIG_PATH", cfg):
        assert speak("receipt_lazada.pdf", "en") is False


def test_malformed_config_soft_fails(tmp_path: Path) -> None:
    bad = tmp_path / "config.local.json"
    bad.write_text("{bad", encoding="utf-8")
    with patch("voice.speak.CONFIG_PATH", bad):
        assert speak("receipt_lazada.pdf", "en") is False


def test_happy_path_calls_openvoice_and_startfile(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    wav = tmp_path / "out.wav"
    wav.write_bytes(b"RIFF")
    with (
        patch("voice.speak.CONFIG_PATH", cfg),
        patch("voice.speak.synthesize_to_wav", return_value=wav) as synth,
        patch("voice.speak._play_audio") as play,
    ):
        assert speak("receipt_lazada.pdf", "EN") is True

    synth.assert_called_once()
    assert synth.call_args.kwargs["text"] == "Found it — receipt_lazada.pdf."
    assert synth.call_args.kwargs["speaker"] == "EN-US"
    assert synth.call_args.kwargs["tone_convert"] is False
    play.assert_called_once_with(str(wav))


def test_taglish_uses_tl_template(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    wav = tmp_path / "out.wav"
    wav.write_bytes(b"RIFF")
    with (
        patch("voice.speak.CONFIG_PATH", cfg),
        patch("voice.speak.synthesize_to_wav", return_value=wav) as synth,
        patch("voice.speak._play_audio"),
    ):
        assert speak("a.pdf", "taglish") is True
    assert synth.call_args.kwargs["text"] == "Nakita ko na — a.pdf."


def test_openvoice_unavailable_soft_fails(tmp_path: Path) -> None:
    cfg = _enabled_cfg(tmp_path)
    with (
        patch("voice.speak.CONFIG_PATH", cfg),
        patch(
            "voice.speak.synthesize_to_wav",
            side_effect=OpenVoiceUnavailable("no melo"),
        ),
    ):
        assert speak("receipt_lazada.pdf", "tl") is False
