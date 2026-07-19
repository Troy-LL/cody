"""Fullscreen transparent Cody companion cursor."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

SLOT = QPointF(28, 32)
SIZE = 56.0  # large enough to spot on a busy desktop
SPRING = 0.14
DAMP = 0.78
ANIM_MS = 900


class CursorOverlay(QWidget):
    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self._mode = "follow"  # follow | animating | pointed
        cur = QCursor.pos()
        self._pos = QPointF(cur.x() + SLOT.x(), cur.y() + SLOT.y())
        self._vel = QPointF(0, 0)
        self._anim_from = QPointF(0, 0)
        self._anim_to = QPointF(0, 0)
        self._anim_t0 = 0
        self._pointing = False
        self._caption = "Cody is live — Ctrl+Shift+C points at Notion Installer"
        self._ring_t = -1.0
        self._status = "Cody live · Ctrl+Shift+C"

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._cover_screens()
        # Map initial pos into this widget's local coords
        local = self.mapFromGlobal(cur)
        self._pos = QPointF(local.x() + SLOT.x(), local.y() + SLOT.y())

    def _cover_screens(self) -> None:
        geo = QRectF()
        for screen in QGuiApplication.screens():
            geo = geo.united(QRectF(screen.geometry()))
        if geo.isNull():
            geo = QRectF(0, 0, 1920, 1080)
        self.setGeometry(geo.toRect())

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.raise_()
        self._force_topmost()

    def _force_topmost(self) -> None:
        try:
            import ctypes

            hwnd = int(self.winId())
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            )
        except Exception:
            pass

    def resume_follow(self) -> None:
        self._mode = "follow"
        self._pointing = False
        self._caption = ""
        self._status = "Cody live · Ctrl+Shift+C"
        self._vel = QPointF(0, 0)
        self._ring_t = -1.0
        self.update()

    def point_at_screen(self, x: int, y: int, caption: str) -> None:
        # Incoming coords are global screen; convert to widget-local
        local = self.mapFromGlobal(QPoint(int(x), int(y)))
        self._mode = "animating"
        self._pointing = True
        self._caption = caption or ""
        self._status = caption or "Pointing…"
        self._anim_from = QPointF(self._pos)
        self._anim_to = QPointF(local.x() - SIZE * 0.25, local.y() - SIZE * 0.25)
        self._anim_t0 = 0
        self._vel = QPointF(0, 0)
        self._ring_t = -1.0
        self.raise_()
        self._force_topmost()
        self.update()

    def _tick(self) -> None:
        if self._mode == "follow":
            global_pos = QCursor.pos()
            local = self.mapFromGlobal(global_pos)
            slot = QPointF(local.x() + SLOT.x(), local.y() + SLOT.y())
            ax = (slot.x() - self._pos.x()) * SPRING
            ay = (slot.y() - self._pos.y()) * SPRING
            self._vel = QPointF(
                (self._vel.x() + ax) * DAMP,
                (self._vel.y() + ay) * DAMP,
            )
            self._pos = QPointF(self._pos.x() + self._vel.x(), self._pos.y() + self._vel.y())
        elif self._mode == "animating":
            self._anim_t0 += 16
            t = min(1.0, self._anim_t0 / ANIM_MS)
            e = _ease(t)
            self._pos = QPointF(
                self._anim_from.x() + (self._anim_to.x() - self._anim_from.x()) * e,
                self._anim_from.y() + (self._anim_to.y() - self._anim_from.y()) * e,
            )
            if t >= 1.0:
                self._mode = "pointed"
                self._ring_t = 0.0
        elif self._mode == "pointed":
            if self._ring_t >= 0:
                self._ring_t += 16
                if self._ring_t > 600:
                    self._ring_t = -1.0
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._paint_hud(p)
        self._paint_cursor(p)
        if self._caption:
            self._paint_caption(p)
        if self._ring_t >= 0:
            self._paint_ring(p)

    def _paint_hud(self, p: QPainter) -> None:
        """Bottom-left chip so the user can tell Cody is running."""
        font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        p.setFont(font)
        text = self._status or "Cody live"
        metrics = p.fontMetrics()
        pad_x, pad_y = 14, 10
        tw = metrics.horizontalAdvance(text) + pad_x * 2
        th = metrics.height() + pad_y * 2
        # Anchor to primary screen bottom-left inside this virtual desktop widget
        primary = QGuiApplication.primaryScreen()
        if primary is None:
            bx, by = 24, self.height() - th - 24
        else:
            g = primary.geometry()
            top_left = self.mapFromGlobal(g.topLeft())
            bx = top_left.x() + 24
            by = top_left.y() + g.height() - th - 28
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(10, 22, 40, 230))
        p.drawRoundedRect(QRectF(bx, by, tw, th), 12, 12)
        p.setBrush(QColor("#1B4FD8"))
        p.drawEllipse(QPointF(bx + 16, by + th / 2), 5, 5)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(bx + 28, by, tw - 36, th), int(Qt.AlignmentFlag.AlignVCenter), text)

    def _paint_cursor(self, p: QPainter) -> None:
        x, y = self._pos.x(), self._pos.y()
        scale = SIZE / 48.0
        p.save()
        p.translate(x, y)
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
        # soft glow
        for r, a in ((5, 40), (3, 70)):
            p.setPen(QPen(QColor(27, 79, 216, a), r))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
        # arrow
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        p.setBrush(QColor("#1B4FD8"))
        p.drawPath(path)
        p.restore()

    def _paint_caption(self, p: QPainter) -> None:
        font = QFont("Segoe UI", 10)
        p.setFont(font)
        text = self._caption
        metrics = p.fontMetrics()
        pad_x, pad_y = 10, 6
        tw = min(220, metrics.horizontalAdvance(text) + pad_x * 2)
        # word wrap height estimate
        rect = metrics.boundingRect(0, 0, tw - pad_x * 2, 200, Qt.TextFlag.TextWordWrap, text)
        bw = rect.width() + pad_x * 2
        bh = rect.height() + pad_y * 2
        bx = self._pos.x() + 34
        by = self._pos.y() - 4
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(10, 22, 40, 235))
        p.drawRoundedRect(QRectF(bx, by, bw, bh), 10, 10)
        # tail
        tri = QPainterPath()
        tri.moveTo(bx, by + 12)
        tri.lineTo(bx - 6, by + 16)
        tri.lineTo(bx, by + 20)
        p.drawPath(tri)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(bx + pad_x, by + pad_y, bw - pad_x * 2, bh - pad_y * 2), Qt.TextFlag.TextWordWrap, text)

    def _paint_ring(self, p: QPainter) -> None:
        t = min(1.0, self._ring_t / 600.0)
        cx = self._anim_to.x() + SIZE * 0.25
        cy = self._anim_to.y() + SIZE * 0.25
        r = 12 + t * 28
        alpha = int(220 * (1 - t))
        pen = QPen(QColor(27, 79, 216, alpha), 3)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)


def _ease(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    return 1 - ((-2 * t + 2) ** 3) / 2


def asset_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "cody-cursor"
