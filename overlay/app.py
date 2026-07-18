"""Desktop Cody overlay entry: python -m overlay"""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, Slot
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle

from overlay.cursor_window import CursorOverlay
from overlay.find_target import find_notion_installer
from overlay.hotkey import HotkeyFilter
from overlay.icon_bounds import explorer_window_center, find_item_bounds
from reveal.reveal import reveal

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("overlay")


class _HotkeyBridge(QAbstractNativeEventFilter):
    def __init__(self, filter_: HotkeyFilter) -> None:
        super().__init__()
        self._filter = filter_

    def nativeEventFilter(self, eventType, message):
        handled = self._filter.native_event(eventType, message)
        return handled, 0


class OverlayController(QObject):
    def __init__(self, overlay: CursorOverlay, app: QApplication) -> None:
        super().__init__()
        self._overlay = overlay
        self._app = app
        self._busy = False

    @Slot()
    def point_notion(self) -> None:
        if self._busy:
            return
        self._busy = True
        try:
            path = find_notion_installer()
            if path is None:
                self._overlay.point_at_screen(
                    QGuiApplication.primaryScreen().geometry().center().x(),
                    QGuiApplication.primaryScreen().geometry().center().y(),
                    "Can't find Notion Installer in Downloads.",
                )
                return

            ok = reveal(str(path))
            if not ok:
                self._overlay.point_at_screen(
                    QGuiApplication.primaryScreen().geometry().center().x(),
                    QGuiApplication.primaryScreen().geometry().center().y(),
                    "Reveal failed — is this Windows?",
                )
                return

            # Prefer UIA icon; fall back to Explorer window center
            stem = path.stem  # "Notion Installer"
            bounds = find_item_bounds(stem)
            if bounds is not None:
                x, y = bounds.center
                caption = "I think this is Notion Installer."
            else:
                fallback = explorer_window_center()
                if fallback is None:
                    geo = QGuiApplication.primaryScreen().geometry()
                    x, y = geo.center().x(), geo.center().y()
                else:
                    x, y = fallback
                caption = "Selected Notion Installer — icon pinpoint soft-failed."

            self._overlay.point_at_screen(x, y, caption)
            logger.info("pointed at %s -> (%s, %s)", path, x, y)
        finally:
            self._busy = False

    @Slot()
    def follow(self) -> None:
        self._overlay.resume_follow()

    @Slot()
    def quit(self) -> None:
        self._app.quit()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication.instance() or QApplication(argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Cody")

    overlay = CursorOverlay()
    overlay.show()

    ctl = OverlayController(overlay, app)

    # Esc when overlay somehow focused (usually click-through)
    QShortcut(QKeySequence(Qt.Key.Key_Escape), overlay, activated=ctl.follow)

    hwnd = int(overlay.winId())
    hot = HotkeyFilter(hwnd, on_point=ctl.point_notion, on_quit=ctl.quit)
    if not hot.register():
        logger.warning("Global hotkey unavailable — use tray menu")
    bridge = _HotkeyBridge(hot)
    app.installNativeEventFilter(bridge)
    app.aboutToQuit.connect(hot.unregister)

    tray = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), app)
        menu = QMenu()
        menu.addAction("Point Notion Installer (Ctrl+Shift+C)", ctl.point_notion)
        menu.addAction("Follow mouse (Esc)", ctl.follow)
        menu.addSeparator()
        menu.addAction("Quit (Ctrl+Shift+Q)", ctl.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("Cody — Ctrl+Shift+C points at Notion Installer")
        tray.show()
        tray.showMessage(
            "Cody is running",
            "Ctrl+Shift+C → Notion Installer in Downloads",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    logger.info("Cody overlay up — Ctrl+Shift+C to point")
    code = app.exec()
    hot.unregister()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
