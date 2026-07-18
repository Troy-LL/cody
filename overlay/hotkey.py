"""Global Win32 hotkeys for the overlay process."""

from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

logger = logging.getLogger(__name__)

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

HOTKEY_POINT = 1
HOTKEY_QUIT = 2


class HotkeyFilter:
    """Register Ctrl+Shift+C (point) and Ctrl+Shift+Q (quit)."""

    def __init__(self, hwnd: int, on_point, on_quit) -> None:
        self._hwnd = hwnd
        self._on_point = on_point
        self._on_quit = on_quit
        self._user32 = ctypes.windll.user32
        self._registered: list[int] = []

    def register(self) -> bool:
        if sys.platform != "win32":
            return False
        # hwnd=0 → thread message queue (more reliable than Tool/transparent windows)
        target = 0
        ok_c = self._user32.RegisterHotKey(
            target, HOTKEY_POINT, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 0x43  # 'C'
        )
        ok_q = self._user32.RegisterHotKey(
            target, HOTKEY_QUIT, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 0x51  # 'Q'
        )
        if ok_c:
            self._registered.append(HOTKEY_POINT)
        if ok_q:
            self._registered.append(HOTKEY_QUIT)
        if not ok_c:
            logger.warning("RegisterHotKey Ctrl+Shift+C failed")
        return bool(ok_c)

    def unregister(self) -> None:
        if sys.platform != "win32":
            return
        for hot_id in self._registered:
            self._user32.UnregisterHotKey(0, hot_id)
        self._registered.clear()

    def native_event(self, event_type: bytes | str, message) -> bool:
        """Return True if the message was a handled hotkey."""
        try:
            if isinstance(event_type, bytes):
                et = event_type.decode("latin1")
            else:
                et = event_type
            if et not in ("windows_generic_MSG", "windows_dispatcher_MSG"):
                return False
            msg = wintypes.MSG.from_address(int(message))
            if msg.message != WM_HOTKEY:
                return False
            if msg.wParam == HOTKEY_POINT:
                self._on_point()
                return True
            if msg.wParam == HOTKEY_QUIT:
                self._on_quit()
                return True
        except Exception:
            logger.warning("hotkey native_event failed", exc_info=True)
        return False
