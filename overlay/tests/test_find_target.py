"""Tests for overlay.find_target."""

from __future__ import annotations

from pathlib import Path

from overlay.find_target import find_notion_installer


def test_find_notion_installer_matches_exe(tmp_path: Path) -> None:
    target = tmp_path / "Notion Installer.exe"
    target.write_bytes(b"mz")
    (tmp_path / "other.txt").write_text("nope", encoding="utf-8")
    assert find_notion_installer(str(tmp_path)) == target.resolve()


def test_find_notion_installer_missing(tmp_path: Path) -> None:
    assert find_notion_installer(str(tmp_path)) is None


def test_find_notion_installer_ignores_dirs(tmp_path: Path) -> None:
    (tmp_path / "Notion Installer").mkdir()
    assert find_notion_installer(str(tmp_path)) is None
