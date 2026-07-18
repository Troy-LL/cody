"""Desktop Cody cursor overlay (Windows)."""

from __future__ import annotations

__all__ = ["find_notion_installer"]


def find_notion_installer(downloads: str | None = None):
    from overlay.find_target import find_notion_installer as _find

    return _find(downloads)
