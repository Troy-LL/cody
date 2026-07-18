"""Transparent always-on-top window that hosts the HTML Cody lens (hole → desktop)."""

from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path

logger = logging.getLogger("cody.html_host")

REPO = Path(__file__).resolve().parents[1]
LENS_URL_PATH = "/demo/cody-cursor/lens-frame.html"
DEFAULT_PORT = 8765
WIN_W, WIN_H = 380, 380


def _ensure_server(port: int = DEFAULT_PORT) -> str:
    import urllib.request

    base = f"http://127.0.0.1:{port}"
    try:
        urllib.request.urlopen(base + LENS_URL_PATH, timeout=0.4)
        return base + LENS_URL_PATH
    except Exception:
        pass

    def serve() -> None:
        import http.server
        import socketserver

        os_chdir = REPO
        handler = http.server.SimpleHTTPRequestHandler

        class Quiet(handler):
            def log_message(self, fmt, *args):  # noqa: A003
                return

        # Bind from repo root
        import os

        os.chdir(os_chdir)
        with socketserver.TCPServer(("127.0.0.1", port), Quiet) as httpd:
            httpd.serve_forever()

    threading.Thread(target=serve, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(base + LENS_URL_PATH, timeout=0.3)
            return base + LENS_URL_PATH
        except Exception:
            time.sleep(0.05)
    return base + LENS_URL_PATH


def main(argv: list[str] | None = None) -> int:
    del argv
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        import webview
    except ImportError:
        print("Install pywebview:  .venv\\Scripts\\pip install pywebview", file=sys.stderr)
        # Fallback: open in default browser (no desktop hole)
        url = _ensure_server()
        import webbrowser

        webbrowser.open(url)
        print("Opened in browser (no transparent hole). Install pywebview for the real lens.")
        return 0

    url = _ensure_server()
    logger.info("Hosting %s", url)

    window = webview.create_window(
        title="Cody Lens",
        url=url,
        width=WIN_W,
        height=WIN_H,
        frameless=True,
        on_top=True,
        transparent=True,
        easy_drag=True,
        background_color="#00000000",
    )

    def follow_mouse() -> None:
        """Keep the glass near the real OS cursor (Windows)."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            pt = wintypes.POINT()
            # Wait until window exists
            time.sleep(0.6)
            while True:
                user32.GetCursorPos(ctypes.byref(pt))
                # Lower-right of cursor — like a magnifier held beside the pointer
                x = int(pt.x + 28)
                y = int(pt.y + 32)
                try:
                    window.move(x, y)
                except Exception:
                    break
                time.sleep(0.016)
        except Exception:
            logger.exception("follow_mouse failed")

    threading.Thread(target=follow_mouse, daemon=True).start()
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
