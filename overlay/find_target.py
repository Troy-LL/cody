"""Resolve the demo hotkey target under Downloads."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_PATTERN = "Notion Installer*"


def downloads_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"


def find_notion_installer(
    downloads: str | None = None,
    pattern: str = DEFAULT_PATTERN,
) -> Path | None:
    """Return first matching file under Downloads, or None."""
    root = downloads_dir(downloads)
    if not root.is_dir():
        return None
    matches = sorted(root.glob(pattern), key=lambda p: p.name.lower())
    for path in matches:
        if path.is_file():
            return path.resolve()
    return None
