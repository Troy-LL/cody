"""Floating transparent framed window — Cody follows the real mouse. Build as Cody.exe."""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path

# Quiet Qt platform noise before QApplication starts
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")
# PySide6-Essentials no longer ships fonts — use Windows Fonts
_win_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
if _win_fonts.is_dir():
    os.environ.setdefault("QT_QPA_FONTDIR", str(_win_fonts))

from PySide6.QtCore import QPoint, QPointF, Qt, QTimer, QRectF, QAbstractNativeEventFilter
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QStyle

from overlay.find_target import find_notion_installer
from overlay.hotkey import HotkeyFilter
from reveal.reveal import reveal

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cody.float")


def _ensure_pyside_fonts_dir() -> None:
    """Avoid QFontDatabase warning when Essentials has no lib/fonts."""
    try:
        import PySide6

        fonts = Path(PySide6.__file__).resolve().parent / "lib" / "fonts"
        fonts.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _ui_font(size: int = 9, bold: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(["Segoe UI", "Arial", "Sans Serif"])
    font.setPointSize(size)
    if bold:
        font.setWeight(QFont.Weight.DemiBold)
    return font

WIN_W, WIN_H = 200, 200
# Cody sits in the frame; frame tracks lower-right of OS cursor
SLOT = QPoint(24, 28)
SPRING = 0.22
DAMP = 0.75


class CodyFloat(QWidget):
    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowTitle("Cody")
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._target = QPointF(400, 300)
        self._pos = QPointF(400, 300)
        self._vel = QPointF(0, 0)
        self._pointing = False
        self._caption = "Cody"
        self._status = "Following you"
        self._busy = False

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        # Center on primary screen at launch so you can see the frame
        screen = QGuiApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self._pos = QPointF(g.center().x() - WIN_W / 2, g.center().y() - WIN_H / 2)
            self._target = QPointF(self._pos)
        self._place()

    def _place(self) -> None:
        self.move(int(self._pos.x()), int(self._pos.y()))

    def _tick(self) -> None:
        cur = QCursor.pos()
        self._target = QPointF(cur.x() + SLOT.x(), cur.y() + SLOT.y())
        ax = (self._target.x() - self._pos.x()) * SPRING
        ay = (self._target.y() - self._pos.y()) * SPRING
        self._vel = QPointF((self._vel.x() + ax) * DAMP, (self._vel.y() + ay) * DAMP)
        self._pos = QPointF(self._pos.x() + self._vel.x(), self._pos.y() + self._vel.y())
        self._place()
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Visible glass frame so you know the exe is alive
        frame = QRectF(4, 4, WIN_W - 8, WIN_H - 8)
        p.setPen(QPen(QColor(27, 79, 216, 200), 2.5))
        p.setBrush(QColor(10, 22, 40, 90))
        p.drawRoundedRect(frame, 18, 18)

        # Title chip
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(10, 22, 40, 210))
        p.drawRoundedRect(QRectF(14, 12, 72, 22), 8, 8)
        p.setPen(QColor("#e8f0fe"))
        p.setFont(_ui_font(9, bold=True))
        p.drawText(QRectF(14, 12, 72, 22), int(Qt.AlignmentFlag.AlignCenter), "Cody")

        # Status
        p.setFont(_ui_font(8))
        p.setPen(QColor(255, 255, 255, 200))
        p.drawText(QRectF(14, WIN_H - 28, WIN_W - 28, 18), int(Qt.AlignmentFlag.AlignLeft), self._status)

        self._paint_cursor(p)

    def _paint_cursor(self, p: QPainter) -> None:
        # Draw Cody in the middle of the floating frame
        cx, cy = WIN_W / 2 - 20, WIN_H / 2 - 18
        scale = 40 / 48
        p.save()
        p.translate(cx, cy)
        p.scale(scale, scale)
        path = QPainterPath()
        if self._pointing:
            path.moveTo(6, 4)
            path.lineTo(4, 34)
            path.lineTo(13, 27)
            path.lineTo(17.5, 41)
            path.lineTo(24, 38)
            path.lineTo(19.5, 24.5)
            path.lineTo(31, 22)
            path.closeSubpath()
            face = QPointF(36, 12)
        else:
            path.moveTo(6, 4)
            path.lineTo(6, 36)
            path.lineTo(14.5, 28.5)
            path.lineTo(20, 42)
            path.lineTo(26, 39.5)
            path.lineTo(20.5, 26)
            path.lineTo(32, 26)
            path.closeSubpath()
            face = QPointF(34, 14)
        p.setPen(QPen(QColor("#0A1628"), 1.5))
        p.setBrush(QColor("#1B4FD8"))
        p.drawPath(path)
        p.setBrush(QColor("#E8F0FE"))
        p.setPen(QPen(QColor("#1B4FD8"), 2))
        p.drawEllipse(face, 9, 9)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#0A1628"))
        p.drawEllipse(face + QPointF(-2.5, -1), 1.4, 1.4)
        p.drawEllipse(face + QPointF(2.5, -1), 1.4, 1.4)
        p.setPen(QPen(QColor("#0A1628"), 1.4))
        smile = QPainterPath()
        smile.moveTo(face.x() - 3, face.y() + 2.5)
        smile.quadTo(face.x(), face.y() + 5.5, face.x() + 3, face.y() + 2.5)
        p.drawPath(smile)
        if self._pointing:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#FFD166"))
            p.drawEllipse(QPointF(10, 10), 3, 3)
        p.restore()

    def point_notion(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._status = "Finding Notion…"
        self._pointing = True
        self.update()

        def work() -> None:
            path = find_notion_installer()
            if path is None:
                self._finish(False, "Not in Downloads")
                return
            ok = reveal(str(path))
            self._finish(ok, "Pointed!" if ok else "Reveal failed")

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, ok: bool, msg: str) -> None:
        def ui() -> None:
            self._status = msg
            self._pointing = ok
            self._busy = False
            self.update()
            if ok:
                QTimer.singleShot(2500, self._clear_point)

        QTimer.singleShot(0, ui)

    def _clear_point(self) -> None:
        self._pointing = False
        self._status = "Following you"
        self.update()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    _ensure_pyside_fonts_dir()
    app = QApplication.instance() or QApplication(argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Cody")
    app.setFont(_ui_font(10))

    win = CodyFloat()
    win.show()  # do not call raise_() — some Qt plugins log "does not support raise()"

    class Bridge(QAbstractNativeEventFilter):
        def __init__(self, hot: HotkeyFilter) -> None:
            super().__init__()
            self._hot = hot

        def nativeEventFilter(self, eventType, message):
            return self._hot.native_event(eventType, message), 0

    hot = HotkeyFilter(0, on_point=win.point_notion, on_quit=app.quit)
    if not hot.register():
        logger.warning("hotkey failed — use tray menu")
    bridge = Bridge(hot)
    app.installNativeEventFilter(bridge)
    app.aboutToQuit.connect(hot.unregister)

    tray = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), app)
        menu = QMenu()
        menu.addAction("Point Notion Installer (Ctrl+Shift+C)", win.point_notion)
        menu.addAction("Quit (Ctrl+Shift+Q)", app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("Cody — floating companion")
        tray.show()
        # Keep tray ref alive
        app._cody_tray = tray  # type: ignore[attr-defined]

    logger.info("Cody float window running")
    code = app.exec()
    hot.unregister()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
