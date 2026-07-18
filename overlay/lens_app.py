"""Magnifying-glass overlay: follows mouse, F8 OCRs what's behind, Cody jumps to that app."""

from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
from ctypes import wintypes
from pathlib import Path

os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")
_win_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
if _win_fonts.is_dir():
    os.environ.setdefault("QT_QPA_FONTDIR", str(_win_fonts))

from PySide6.QtCore import QPoint, QPointF, Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QStyle

from overlay.ocr_scan import (
    activate_window,
    capture_region_png_bytes,
    scan_lens,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cody.lens")

WIN_W, WIN_H = 340, 340
SLOT = QPoint(36, 40)
SPRING = 0.18
DAMP = 0.78

# F8 = OCR scan, F9 = quit (avoid Ctrl+Shift+C stolen by Cursor/IDE)
VK_F8 = 0x77
VK_F9 = 0x78
HOTKEY_SCAN = 1
HOTKEY_QUIT = 2
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312


def _ui_font(size: int = 9, bold: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(["Segoe UI", "Arial", "Sans Serif"])
    font.setPointSize(size)
    if bold:
        font.setWeight(QFont.Weight.DemiBold)
    return font


def _ensure_fonts_dir() -> None:
    try:
        import PySide6

        (Path(PySide6.__file__).resolve().parent / "lib" / "fonts").mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


class CodyLens(QWidget):
    """Circular glass lens that follows the mouse; F8 scans behind it."""

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowTitle("Cody Lens")
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._pos = QPointF(200, 200)
        self._vel = QPointF(0, 0)
        self._follow = True
        self._busy = False
        self._pointing = False
        self._status = "F8 = OCR scan behind lens"
        self._heard = ""

        screen = QGuiApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self._pos = QPointF(g.center().x() - WIN_W / 2, g.center().y() - WIN_H / 2)
        self.move(int(self._pos.x()), int(self._pos.y()))

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._hot_timer = QTimer(self)
        self._hot_timer.setInterval(40)
        self._hot_timer.timeout.connect(self._poll_hotkeys)
        self._hot_timer.start()

        self._registered: list[int] = []

    def register_hotkeys(self) -> bool:
        user32 = ctypes.windll.user32
        # Clear any stale registrations on this thread
        user32.UnregisterHotKey(0, HOTKEY_SCAN)
        user32.UnregisterHotKey(0, HOTKEY_QUIT)
        ok = user32.RegisterHotKey(0, HOTKEY_SCAN, MOD_NOREPEAT, VK_F8)
        ok_q = user32.RegisterHotKey(0, HOTKEY_QUIT, MOD_NOREPEAT, VK_F9)
        if ok:
            self._registered.append(HOTKEY_SCAN)
        if ok_q:
            self._registered.append(HOTKEY_QUIT)
        if not ok:
            logger.warning("RegisterHotKey F8 failed — use tray menu")
        return bool(ok)

    def unregister_hotkeys(self) -> None:
        user32 = ctypes.windll.user32
        for hid in self._registered:
            user32.UnregisterHotKey(0, hid)
        self._registered.clear()

    def _poll_hotkeys(self) -> None:
        if sys.platform != "win32":
            return
        user32 = ctypes.windll.user32
        msg = wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), 0, WM_HOTKEY, WM_HOTKEY, 1):
            if msg.wParam == HOTKEY_SCAN:
                self.scan_now()
            elif msg.wParam == HOTKEY_QUIT:
                QApplication.instance().quit()

    def _tick(self) -> None:
        try:
            if self._follow and not self._busy:
                cur = QCursor.pos()
                target = QPointF(cur.x() + SLOT.x(), cur.y() + SLOT.y())
                ax = (target.x() - self._pos.x()) * SPRING
                ay = (target.y() - self._pos.y()) * SPRING
                self._vel = QPointF((self._vel.x() + ax) * DAMP, (self._vel.y() + ay) * DAMP)
                self._pos = QPointF(self._pos.x() + self._vel.x(), self._pos.y() + self._vel.y())
                self.move(int(self._pos.x()), int(self._pos.y()))
            self.update()
        except Exception:
            logger.exception("tick failed")

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cx, cy = WIN_W / 2, WIN_H / 2
        r = min(WIN_W, WIN_H) / 2 - 6

        # Outer ring (magnifying glass)
        p.setPen(QPen(QColor(27, 79, 216, 230), 5))
        p.setBrush(QColor(232, 240, 254, 40))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Inner clear-ish disc
        p.setPen(QPen(QColor(255, 255, 255, 90), 1.5))
        p.setBrush(QColor(10, 22, 40, 55))
        p.drawEllipse(QPointF(cx, cy), r - 10, r - 10)

        # Handle
        handle = QPainterPath()
        handle.moveTo(cx + r * 0.62, cy + r * 0.62)
        handle.lineTo(cx + r * 0.95, cy + r * 0.95)
        p.setPen(QPen(QColor(27, 79, 216, 240), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(handle)

        # Badge
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(10, 22, 40, 220))
        p.drawRoundedRect(QRectF(cx - 36, 18, 72, 24), 8, 8)
        p.setPen(QColor("#e8f0fe"))
        p.setFont(_ui_font(10, bold=True))
        p.drawText(QRectF(cx - 36, 18, 72, 24), int(Qt.AlignmentFlag.AlignCenter), "Cody")

        # Status under lens
        p.setFont(_ui_font(8))
        p.setPen(QColor(255, 255, 255, 230))
        p.drawText(
            QRectF(20, WIN_H - 48, WIN_W - 40, 36),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap),
            self._status,
        )

        # Mini Cody face in center when pointing
        if self._pointing:
            self._paint_mini_cody(p, cx - 14, cy - 16)

    def _paint_mini_cody(self, p: QPainter, x: float, y: float) -> None:
        p.save()
        p.translate(x, y)
        p.scale(0.7, 0.7)
        path = QPainterPath()
        path.moveTo(6, 4)
        path.lineTo(4, 34)
        path.lineTo(13, 27)
        path.lineTo(17.5, 41)
        path.lineTo(24, 38)
        path.lineTo(19.5, 24.5)
        path.lineTo(31, 22)
        path.closeSubpath()
        p.setPen(QPen(QColor("#0A1628"), 1.5))
        p.setBrush(QColor("#1B4FD8"))
        p.drawPath(path)
        p.restore()

    def scan_now(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._follow = False
        self._status = "Scanning…"
        self.update()
        QApplication.processEvents()

        # Hide so OCR sees the desktop behind the glass
        geo = self.frameGeometry()
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        self.hide()
        QApplication.processEvents()
        QTimer.singleShot(60, lambda: self._do_scan(x, y, w, h))

    def _do_scan(self, x: int, y: int, w: int, h: int) -> None:
        png = capture_region_png_bytes(x, y, w, h)
        self.show()  # no raise_()

        def work() -> None:
            result = scan_lens(x, y, w, h, png)
            self._apply_result(result)

        threading.Thread(target=work, daemon=True).start()

    def _apply_result(self, result) -> None:
        def ui() -> None:
            heard = (result.text or "").replace("\n", " ").strip()
            if len(heard) > 80:
                heard = heard[:77] + "…"
            self._heard = heard

            if result.window_hwnd:
                center = activate_window(result.window_hwnd)
                title = result.window_title or "window"
                if center:
                    # Park lens on that app
                    self._pos = QPointF(center[0] - WIN_W / 2, center[1] - WIN_H / 2)
                    self.move(int(self._pos.x()), int(self._pos.y()))
                self._pointing = True
                self._status = f"→ {title}"
                if heard:
                    self._status = f"OCR: {heard}\n→ {title}"
            else:
                self._pointing = False
                self._status = f"OCR: {heard or '(no text)'} — no app match"

            self._busy = False
            self._follow = True
            self.update()
            QTimer.singleShot(3500, self._clear_point)

        QTimer.singleShot(0, ui)

    def _clear_point(self) -> None:
        self._pointing = False
        self._status = "F8 = OCR scan behind lens"
        self.update()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    _ensure_fonts_dir()
    app = QApplication.instance() or QApplication(argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Cody")
    app.setFont(_ui_font(10))

    lens = CodyLens()
    lens.show()
    lens.register_hotkeys()
    app.aboutToQuit.connect(lens.unregister_hotkeys)

    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), app)
        menu = QMenu()
        menu.addAction("OCR scan (F8)", lens.scan_now)
        menu.addAction("Quit (F9)", app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("Cody Lens — F8 OCR scan")
        tray.show()
        app._cody_tray = tray  # type: ignore[attr-defined]

    logger.info("Cody lens running — F8 OCR, F9 quit")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
