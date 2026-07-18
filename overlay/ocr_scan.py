"""Capture the screen region under the lens and OCR it (Windows-friendly)."""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    text: str
    tokens: list[str]
    window_title: str | None
    window_hwnd: int | None
    point: tuple[int, int]


def capture_region_png_bytes(x: int, y: int, w: int, h: int) -> bytes | None:
    """Grab a screen rect to PNG bytes (Qt). Caller should hide overlay first."""
    try:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtCore import QRect

        screen = QGuiApplication.screenAt(__import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(x + w // 2, y + h // 2))
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        geo = screen.geometry()
        # Convert global → screen-local
        local = QRect(x - geo.x(), y - geo.y(), w, h)
        pix = screen.grabWindow(0, local.x(), local.y(), local.width(), local.height())
        from PySide6.QtCore import QBuffer, QIODevice

        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        pix.save(buf, "PNG")
        return bytes(buf.data())
    except Exception:
        logger.warning("capture_region failed", exc_info=True)
        return None


def ocr_png(png: bytes) -> str:
    """OCR PNG bytes. Prefers pytesseract; returns '' if unavailable."""
    if not png:
        return ""
    try:
        from io import BytesIO

        from PIL import Image
        import pytesseract

        img = Image.open(BytesIO(png))
        # Upscale a bit for small UI text
        img = img.resize((img.width * 2, img.height * 2))
        text = pytesseract.image_to_string(img) or ""
        return text.strip()
    except Exception as exc:
        logger.info("OCR unavailable (%s) — using window-under-lens fallback", exc)
        return ""


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-.]{1,}", text)
    # Drop tiny noise tokens
    return [w for w in words if len(w) >= 3]


def window_at_point(x: int, y: int) -> tuple[int | None, str | None]:
    if sys.platform != "win32":
        return None, None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        point = wintypes.POINT(x, y)
        hwnd = user32.WindowFromPoint(point)
        if not hwnd:
            return None, None
        # Walk up to root owner
        root = user32.GetAncestor(hwnd, 2)  # GA_ROOT
        if root:
            hwnd = root
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value.strip() or None
        return int(hwnd), title
    except Exception:
        logger.warning("window_at_point failed", exc_info=True)
        return None, None


def find_window_matching(tokens: list[str]) -> tuple[int | None, str | None]:
    """Find a visible top-level window whose title matches any OCR token."""
    if sys.platform != "win32" or not tokens:
        return None, None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        needles = [t.casefold() for t in tokens]
        best: tuple[int, str, int] | None = None  # hwnd, title, score

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def enum_proc(hwnd, _lp):
            nonlocal best
            if not user32.IsWindowVisible(hwnd):
                return True
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.strip()
            if not title:
                return True
            low = title.casefold()
            score = sum(1 for n in needles if n in low)
            if score <= 0:
                return True
            if best is None or score > best[2]:
                best = (int(hwnd), title, score)
            return True

        user32.EnumWindows(enum_proc, 0)
        if best:
            return best[0], best[1]
        return None, None
    except Exception:
        logger.warning("find_window_matching failed", exc_info=True)
        return None, None


def activate_window(hwnd: int) -> tuple[int, int] | None:
    """Bring window forward; return its center screen point."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        return cx, cy
    except Exception:
        logger.warning("activate_window failed", exc_info=True)
        return None


def scan_lens(x: int, y: int, w: int, h: int, png: bytes | None) -> ScanResult:
    """OCR + match a target window for the lens rect."""
    text = ocr_png(png) if png else ""
    tokens = tokenize(text)
    cx, cy = x + w // 2, y + h // 2

    hwnd, title = find_window_matching(tokens) if tokens else (None, None)
    if hwnd is None:
        hwnd, title = window_at_point(cx, cy)

    return ScanResult(
        text=text,
        tokens=tokens,
        window_title=title,
        window_hwnd=hwnd,
        point=(cx, cy),
    )
