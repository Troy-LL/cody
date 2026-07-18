"""Tests for overlay.cursor AI cursor contract."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from overlay.cursor import point_at, start_follow, stop


def test_start_follow_and_stop() -> None:
    start_follow()
    stop()


def test_point_at_missing_file_returns_false(tmp_path: Path) -> None:
    start_follow()
    assert point_at(str(tmp_path / "missing.pdf")) is False
    stop()


def test_point_at_existing_file_animates(tmp_path: Path) -> None:
    target = tmp_path / "receipt.pdf"
    target.write_bytes(b"%PDF")
    start_follow()
    with (
        patch("overlay.cursor._icon_point_for_path", return_value=None),
        patch("overlay.cursor._mouse_pos", return_value=(400, 400)),
        patch("overlay.cursor._set_mouse_pos") as move,
        patch("overlay.cursor.time.sleep"),
    ):
        assert point_at(str(target)) is True
    assert move.called
    stop()
