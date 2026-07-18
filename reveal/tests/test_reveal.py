"""Tests for reveal.reveal — spec.md §6.5."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reveal.reveal import reveal


def test_missing_path_returns_false(tmp_path: Path) -> None:
    missing = tmp_path / "gone.pdf"
    assert reveal(str(missing)) is False


def test_directory_returns_false(tmp_path: Path) -> None:
    assert reveal(str(tmp_path)) is False


def test_non_windows_returns_false(tmp_path: Path) -> None:
    target = tmp_path / "file.pdf"
    target.write_bytes(b"x")
    with patch("reveal.reveal.sys.platform", "linux"):
        assert reveal(str(target)) is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows reveal path")
def test_existing_file_spawns_explorer_select(tmp_path: Path) -> None:
    target = tmp_path / "receipt lazada.pdf"
    target.write_bytes(b"%PDF")
    resolved = str(target.resolve())

    with patch("reveal.reveal.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1)
        assert reveal(str(target)) is True

    run.assert_called_once()
    args = run.call_args.args[0]
    assert args[0] == "explorer"
    assert args[1] == f"/select,{resolved}"
    assert run.call_args.kwargs.get("shell") is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows reveal path")
def test_spawn_oserror_returns_false(tmp_path: Path) -> None:
    target = tmp_path / "file.pdf"
    target.write_bytes(b"x")
    with patch("reveal.reveal.subprocess.run", side_effect=OSError("boom")):
        assert reveal(str(target)) is False


def test_never_raises_on_bad_input() -> None:
    assert reveal("") is False
