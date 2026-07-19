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
HOTKEY_PTT = 3
VK_SPACE = 0x20


class HotkeyFilter:
    """Register global hotkeys (Ctrl+Shift+C/Q and/or Ctrl+Shift+Space PTT)."""

    def __init__(
        self,
        hwnd: int,
        on_point=None,
        on_quit=None,
        on_ptt=None,
    ) -> None:
        self._hwnd = hwnd
        self._on_point = on_point
        self._on_quit = on_quit
        self._on_ptt = on_ptt
        self._user32 = ctypes.windll.user32
        self._registered: list[int] = []

    def register(self) -> bool:
        if sys.platform != "win32":
            return False
        # hwnd=0 → thread message queue (more reliable than Tool/transparent windows)
        target = 0
        ok_any = False
        if self._on_point is not None:
            ok_c = self._user32.RegisterHotKey(
                target, HOTKEY_POINT, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 0x43  # 'C'
            )
            if ok_c:
                self._registered.append(HOTKEY_POINT)
                ok_any = True
            else:
                logger.warning("RegisterHotKey Ctrl+Shift+C failed")
        if self._on_quit is not None:
            ok_q = self._user32.RegisterHotKey(
                target, HOTKEY_QUIT, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 0x51  # 'Q'
            )
            if ok_q:
                self._registered.append(HOTKEY_QUIT)
                ok_any = True
            else:
                logger.warning("RegisterHotKey Ctrl+Shift+Q failed")
        if self._on_ptt is not None:
            ok_p = self._user32.RegisterHotKey(
                target, HOTKEY_PTT, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_SPACE
            )
            if ok_p:
                self._registered.append(HOTKEY_PTT)
                ok_any = True
            else:
                logger.warning("RegisterHotKey Ctrl+Shift+Space failed")
        return ok_any

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
            if msg.wParam == HOTKEY_POINT and self._on_point is not None:
                self._on_point()
                return True
            if msg.wParam == HOTKEY_QUIT and self._on_quit is not None:
                self._on_quit()
                return True
            if msg.wParam == HOTKEY_PTT and self._on_ptt is not None:
                self._on_ptt()
                return True
        except Exception:
            logger.warning("hotkey native_event failed", exc_info=True)
        return False
