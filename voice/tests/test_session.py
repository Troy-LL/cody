"""Tests for voice-controlled session loop."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from voice.session import handle_transcript


def test_handle_transcript_finds_and_points(tmp_path: Path) -> None:
    target = tmp_path / "receipt_lazada.pdf"
    target.write_bytes(b"%PDF")

    with (
        patch("voice.session.speak_text", return_value=True) as speak_text,
        patch("voice.session.speak", return_value=True),
        patch("voice.session.start_follow") as follow,
        patch("voice.session.reveal", return_value=True) as reveal,
        patch("voice.session.point_at", return_value=True) as point,
    ):
        result = handle_transcript(
            "find receipt_lazada.pdf",
            root=tmp_path,
            language_mode="en",
        )

    assert result.path == str(target)
    assert result.revealed is True
    assert result.pointed is True
    assert result.spoke is True
    follow.assert_called_once()
    reveal.assert_called_once()
    point.assert_called_once()
    assert speak_text.called


def test_handle_transcript_not_found(tmp_path: Path) -> None:
    with (
        patch("voice.session.speak_text", return_value=True) as speak_text,
        patch("voice.session.reveal") as reveal,
        patch("voice.session.point_at") as point,
    ):
        result = handle_transcript("find missing_thing.pdf", root=tmp_path)

    assert result.path is None
    assert result.revealed is False
    reveal.assert_not_called()
    point.assert_not_called()
    assert "could not find" in speak_text.call_args.args[0].lower()
