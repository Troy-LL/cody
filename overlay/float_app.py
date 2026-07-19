"""Floating transparent Cody buddy — clicky-style: follows the cursor, sees the
screen on Ctrl+Shift+Space, answers by voice, and points at what you ask for."""

from __future__ import annotations

import ctypes
import logging
import os
import sys
import textwrap
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

from overlay.hotkey import HotkeyFilter

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cody.float")

CLIP_SECONDS = 4.0
HOLD_MS = 2600  # keep the pointing pose after flying
LINGER_TICKS = 220  # ~3.5s full-opacity before fading (16ms/tick)
FADE_STEP = 0.04    # per-tick alpha decay once linger ends


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


def _set_cursor_pos(x: int, y: int) -> None:
    try:
        ctypes.windll.user32.SetCursorPos(int(x), int(y))
    except Exception:
        logger.debug("SetCursorPos failed", exc_info=True)


WIN_W, WIN_H = 300, 120
# Cody arrow tracks lower-right of OS cursor
SLOT = QPoint(6, 8)
ARROW = QPointF(10, 10)  # arrow tip origin inside the window
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
        self._status = "Ctrl+Shift+Space to talk"
        self._reply = ""
        self._busy = False
        self._follow = True  # false while holding a pointing pose
        self._fade = 1.0
        self._linger = 0

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        screen = QGuiApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self._pos = QPointF(g.center().x() - WIN_W / 2, g.center().y() - WIN_H / 2)
            self._target = QPointF(self._pos)
        self._place()

    def _place(self) -> None:
        self.move(int(self._pos.x()), int(self._pos.y()))

    def _tick(self) -> None:
        if self._follow:
            cur = QCursor.pos()
            self._target = QPointF(cur.x() + SLOT.x(), cur.y() + SLOT.y())
        ax = (self._target.x() - self._pos.x()) * SPRING
        ay = (self._target.y() - self._pos.y()) * SPRING
        self._vel = QPointF((self._vel.x() + ax) * DAMP, (self._vel.y() + ay) * DAMP)
        self._pos = QPointF(self._pos.x() + self._vel.x(), self._pos.y() + self._vel.y())
        # Fade the reply bubble once it has lingered (skip while busy/pointing)
        if self._reply and not self._busy and not self._pointing:
            if self._linger > 0:
                self._linger -= 1
            else:
                self._fade = max(0.0, self._fade - FADE_STEP)
                if self._fade <= 0.0:
                    self._reply = ""
        self._place()
        self.update()

    # ---- painting -------------------------------------------------------

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._paint_cursor(p)
        text = self._reply or (self._status if self._busy else "")
        if text:
            self._paint_bubble(p, text)

    def _paint_bubble(self, p: QPainter, text: str) -> None:
        p.setFont(_ui_font(9))
        wrapped = "\n".join(textwrap.wrap(text, width=32)[:5])
        metrics = p.fontMetrics()
        rect = metrics.boundingRect(
            QRectF(0, 0, 200, 200).toRect(),
            int(Qt.TextFlag.TextWordWrap),
            wrapped,
        )
        pad = 9
        bx = ARROW.x() + 34
        by = ARROW.y() - 2
        bw = rect.width() + pad * 2
        bh = rect.height() + pad * 2
        a = self._fade if self._reply else 1.0
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(10, 22, 40, int(235 * a)))
        p.drawRoundedRect(QRectF(bx, by, bw, bh), 10, 10)
        tri = QPainterPath()
        tri.moveTo(bx, by + 12)
        tri.lineTo(bx - 6, by + 16)
        tri.lineTo(bx, by + 20)
        p.drawPath(tri)
        p.setPen(QColor(255, 255, 255, int(230 * a)))
        p.drawText(
            QRectF(bx + pad, by + pad, bw - pad * 2, bh - pad * 2),
            int(Qt.TextFlag.TextWordWrap),
            wrapped,
        )

    def _paint_cursor(self, p: QPainter) -> None:
        p.save()
        p.translate(ARROW.x(), ARROW.y())
        scale = 40 / 48
        p.scale(scale, scale)
        path = QPainterPath()
        path.moveTo(6, 4)
        path.lineTo(6, 36)
        path.lineTo(14.5, 28.5)
        path.lineTo(20, 42)
        path.lineTo(26, 39.5)
        path.lineTo(20.5, 26)
        path.lineTo(32, 26)
        path.closeSubpath()
        glow = 90 if self._busy or self._pointing else 55
        for r, a in ((6, glow // 2), (3, glow)):
            p.setPen(QPen(QColor(27, 79, 216, a), r))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        p.setBrush(QColor("#1B4FD8"))
        p.drawPath(path)
        p.restore()

    # ---- brain flow -----------------------------------------------------

    def trigger_ptt(self) -> None:
        """Ctrl+Shift+Space / tray: record a clip, transcribe, answer."""
        if self._busy:
            return
        self._busy = True
        self._reply = ""
        self._set_ui("Listening…", pointing=False)
        threading.Thread(target=self._capture_worker, daemon=True).start()

    def _capture_worker(self) -> None:
        try:
            from overlay.auth import resolve_openai
            from overlay.stt import record_clip, transcribe

            creds = resolve_openai()
            if creds.source == "none" or not creds.api_key:
                self._finish_msg("Add an OpenAI key (or Codex login).", speak=True)
                return
            wav = record_clip(CLIP_SECONDS)
            text = transcribe(wav, creds.api_key)
            if not text.strip():
                self._finish_msg("Didn't catch that.", speak=False)
                return
            self._set_ui(f"“{text.strip()[:40]}”…", pointing=False)
            self._query_worker(text.strip(), creds.api_key)
        except Exception:
            logger.exception("capture failed")
            self._finish_msg("Something went wrong.", speak=False)

    def _query_worker(self, text: str, api_key: str) -> None:
        try:
            from overlay.input_router import default_deps, handle_query

            outcome = handle_query(text, default_deps(api_key))
            self._apply_outcome(outcome)
        except Exception:
            logger.exception("query failed")
            self._finish_msg("I couldn't reach the model.", speak=True)

    def _apply_outcome(self, outcome) -> None:
        reply = (outcome.reply_text or "").strip()
        point = outcome.point
        reveal_path = outcome.reveal_path

        def ui() -> None:
            self._busy = False
            self._reply = reply
            self._fade = 1.0
            self._linger = LINGER_TICKS
            self._status = "Ctrl+Shift+Space to talk"
            if point is not None:
                self._pointing = True
                self._follow = False
                _set_cursor_pos(point[0], point[1])
                self._target = QPointF(point[0] + SLOT.x(), point[1] + SLOT.y())
                QTimer.singleShot(HOLD_MS, self._resume_follow)
            else:
                self._pointing = False
            self.update()

        QTimer.singleShot(0, ui)

        if reply:
            self._speak(reply)
        if reveal_path:
            try:
                from reveal.reveal import reveal

                reveal(reveal_path)
            except Exception:
                logger.exception("reveal failed")

    def _resume_follow(self) -> None:
        self._pointing = False
        self._follow = True
        self._reply = ""
        self.update()

    def _finish_msg(self, msg: str, *, speak: bool) -> None:
        def ui() -> None:
            self._busy = False
            self._reply = msg
            self._fade = 1.0
            self._linger = LINGER_TICKS
            self._pointing = False
            self._status = "Ctrl+Shift+Space to talk"
            self.update()

        QTimer.singleShot(0, ui)
        if speak:
            self._speak(msg)

    def _set_ui(self, status: str, *, pointing: bool) -> None:
        def ui() -> None:
            self._status = status
            self._pointing = pointing
            self.update()

        QTimer.singleShot(0, ui)

    def _speak(self, text: str) -> None:
        def work() -> None:
            try:
                from voice.speak import speak_text

                speak_text(text, language_mode="en")
            except Exception:
                logger.exception("speak_text failed")

        threading.Thread(target=work, daemon=True).start()


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

    hot = HotkeyFilter(0, on_ptt=win.trigger_ptt, on_quit=app.quit)
    if not hot.register():
        logger.warning("hotkey failed — use tray menu")
    bridge = Bridge(hot)
    app.installNativeEventFilter(bridge)
    app.aboutToQuit.connect(hot.unregister)

    tray = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), app)
        menu = QMenu()
        menu.addAction("Talk to Cody (Ctrl+Shift+Space)", win.trigger_ptt)
        menu.addAction("Quit (Ctrl+Shift+Q)", app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("Cody — AI companion")
        tray.show()
        app._cody_tray = tray  # type: ignore[attr-defined]

    logger.info("Cody float companion running")
    code = app.exec()
    hot.unregister()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
