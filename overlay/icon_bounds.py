"""Best-effort Explorer icon screen bounds via UI Automation."""

from __future__ import annotations

import logging
import sys
import time
from typing import NamedTuple

logger = logging.getLogger(__name__)


class ScreenRect(NamedTuple):
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


def find_item_bounds(name_substr: str, *, retries: int = 8, delay_s: float = 0.25) -> ScreenRect | None:
    """Return screen rect for an Explorer item whose name contains *name_substr*."""
    if sys.platform != "win32":
        return None
    needle = name_substr.casefold()
    for attempt in range(retries):
        rect = _uia_search(needle)
        if rect is not None:
            return rect
        time.sleep(delay_s)
        logger.debug("icon_bounds retry %s for %r", attempt + 1, name_substr)
    return None


def explorer_window_center() -> tuple[int, int] | None:
    """Fallback: center of a visible Explorer (CabinetWClass) window."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        found: list[tuple[int, int]] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def enum_proc(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            if class_buf.value != "CabinetWClass":
                return True
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w < 200 or h < 200:
                return True
            found.append((rect.left + w // 2, rect.top + h // 2))
            return False

        user32.EnumWindows(enum_proc, 0)
        return found[0] if found else None
    except Exception:
        logger.warning("explorer_window_center failed", exc_info=True)
        return None


def _uia_search(needle: str) -> ScreenRect | None:
    try:
        import uiautomation as auto
    except ImportError:
        logger.info("uiautomation not installed — skip precise icon bounds")
        return None

    try:
        root = auto.GetRootControl()
        for win in root.GetChildren():
            try:
                if win.ClassName != "CabinetWClass":
                    continue
            except Exception:
                continue
            hit = _walk(win, needle, depth=0, max_depth=12)
            if hit is not None:
                return hit
    except Exception:
        logger.warning("UIA search failed", exc_info=True)
    return None


def _walk(control, needle: str, depth: int, max_depth: int) -> ScreenRect | None:
    if depth > max_depth:
        return None
    try:
        name = control.Name or ""
        ctrl_type = control.ControlTypeName or ""
    except Exception:
        return None

    if needle in name.casefold() and ctrl_type in {
        "ListItemControl",
        "ListItem",
        "TreeItemControl",
        "TreeItem",
        "DataItemControl",
        "DataItem",
    }:
        try:
            r = control.BoundingRectangle
            if r.width() >= 8 and r.height() >= 8:
                return ScreenRect(int(r.left), int(r.top), int(r.width()), int(r.height()))
        except Exception:
            pass

    try:
        children = control.GetChildren()
    except Exception:
        return None
    for child in children:
        hit = _walk(child, needle, depth + 1, max_depth)
        if hit is not None:
            return hit
    return None
