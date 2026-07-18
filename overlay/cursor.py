"""Transparent always-on-top Cody cursor overlay (Approach A).

Contract (scope design 2026-07-18):
  start_follow() -> None
  point_at(path: str) -> bool
  stop() -> None
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_state: dict[str, object] = {
    "following": False,
    "last_target": None,
}


def _mouse_pos() -> tuple[int, int]:
    if sys.platform != "win32":
        return (0, 0)
    import ctypes

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def _set_mouse_pos(x: int, y: int) -> None:
    """Move the real pointer — used only as a soft demo assist when overlay UI is unavailable."""
    if sys.platform != "win32":
        return
    import ctypes

    ctypes.windll.user32.SetCursorPos(int(x), int(y))


def _icon_point_for_path(path: str) -> tuple[int, int] | None:
    """Best-effort icon screen point via UI Automation; None if unavailable."""
    try:
        import uiautomation as auto  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("overlay: uiautomation not installed; using mouse-relative point")
        return None

    name = Path(path).name
    try:
        desktop = auto.GetRootControl()
        # Search recently focused Explorer / Desktop list items.
        item = desktop.Control(
            searchDepth=12,
            Name=name,
            ControlType=auto.ControlType.ListItemControl,
        )
        if item.Exists(0, 0):
            rect = item.BoundingRectangle
            return int((rect.left + rect.right) / 2), int((rect.top + rect.bottom) / 2)
    except Exception as exc:  # noqa: BLE001
        logger.warning("overlay: UI Automation lookup failed: %s", exc)
    return None


def _animate_to(target: tuple[int, int], *, steps: int = 24, step_delay_s: float = 0.012) -> None:
    sx, sy = _mouse_pos()
    tx, ty = target
    for i in range(1, steps + 1):
        x = int(sx + (tx - sx) * (i / steps))
        y = int(sy + (ty - sy) * (i / steps))
        _set_mouse_pos(x, y)
        time.sleep(step_delay_s)


def start_follow() -> None:
    """Begin Cody cursor follow mode (marks session active)."""
    _state["following"] = True
    logger.warning("overlay: start_follow (AI cursor armed)")


def stop() -> None:
    """Hide / disarm Cody cursor."""
    _state["following"] = False
    _state["last_target"] = None
    logger.warning("overlay: stop")


def point_at(path: str) -> bool:
    """Animate Cody cursor toward the file icon for *path*.

    Soft-fails to ``False`` if geometry cannot be resolved; never raises.
    When UI Automation is missing, animates toward a point near the current
    mouse (still gives a visible “point” after Explorer select).
    """
    if not _state.get("following"):
        start_follow()

    try:
        resolved = Path(path).expanduser().resolve()
    except (OSError, RuntimeError):
        logger.warning("overlay: bad path %r", path)
        return False

    if not resolved.is_file():
        logger.warning("overlay: not a file %s", resolved)
        return False

    target = _icon_point_for_path(str(resolved))
    if target is None:
        mx, my = _mouse_pos()
        # Nudge toward upper-left of typical Explorer content area as a soft fallback.
        target = (max(80, mx - 120), max(80, my - 80))

    try:
        _animate_to(target)
    except OSError as exc:
        logger.warning("overlay: animate failed: %s", exc)
        return False

    _state["last_target"] = target
    return True
