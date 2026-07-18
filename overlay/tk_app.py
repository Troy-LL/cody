"""Visible Cody window (tkinter) — Point Notion Installer + global hotkey."""

from __future__ import annotations

import logging
import sys
import threading
import tkinter as tk
from tkinter import ttk

from overlay.find_target import find_notion_installer
from overlay.hotkey import HotkeyFilter
from reveal.reveal import reveal

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cody.tk")


class CodyApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Cody")
        self.root.geometry("420x220")
        self.root.minsize(360, 180)
        self.root.configure(bg="#0a1628")
        self.root.attributes("-topmost", True)

        self._busy = False
        self._hot: HotkeyFilter | None = None

        pad = {"padx": 16, "pady": 8}
        title = tk.Label(
            self.root,
            text="Cody",
            font=("Segoe UI", 22, "bold"),
            fg="#e8f0fe",
            bg="#0a1628",
        )
        title.pack(anchor="w", padx=16, pady=(16, 0))

        sub = tk.Label(
            self.root,
            text="Finds a file and points to it in Explorer.",
            font=("Segoe UI", 10),
            fg="#9bb0d0",
            bg="#0a1628",
        )
        sub.pack(anchor="w", **pad)

        self.status = tk.Label(
            self.root,
            text="Ready — Ctrl+Shift+C or tap the button.",
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#1b4fd8",
            anchor="w",
            padx=12,
            pady=10,
        )
        self.status.pack(fill="x", padx=16, pady=8)

        btn_row = tk.Frame(self.root, bg="#0a1628")
        btn_row.pack(fill="x", padx=16, pady=8)

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Cody.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=10,
        )

        self.btn = ttk.Button(
            btn_row,
            text="Point → Notion Installer",
            style="Cody.TButton",
            command=self.point_notion,
        )
        self.btn.pack(side="left")

        quit_btn = ttk.Button(btn_row, text="Quit", command=self.quit)
        quit_btn.pack(side="right")

        hint = tk.Label(
            self.root,
            text="Target: Downloads\\Notion Installer*   ·   Hotkey: Ctrl+Shift+C",
            font=("Segoe UI", 9),
            fg="#6b849e",
            bg="#0a1628",
        )
        hint.pack(anchor="w", padx=16, pady=(0, 12))

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.after(200, self._register_hotkeys)
        # Pump Win32 messages so RegisterHotKey(hwnd=0) delivers WM_HOTKEY
        self.root.after(50, self._poll_win_messages)

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _register_hotkeys(self) -> None:
        if sys.platform != "win32":
            self._set_status("Hotkeys need Windows — use the button.")
            return
        self.root.update_idletasks()
        hwnd = int(self.root.winfo_id())
        self._hot = HotkeyFilter(hwnd, on_point=self._hotkey_point, on_quit=self.quit)
        if self._hot.register():
            self._set_status("Ready — Ctrl+Shift+C or tap the button.")
        else:
            self._set_status("Hotkey busy — use the button.")

    def _hotkey_point(self) -> None:
        # Called from native filter / message pump — marshal to Tk thread
        self.root.after(0, self.point_notion)

    def _poll_win_messages(self) -> None:
        if sys.platform != "win32" or self._hot is None:
            return
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            msg = wintypes.MSG()
            # Peek thread-queue hotkeys (hwnd=0 registrations)
            while user32.PeekMessageW(ctypes.byref(msg), 0, 0x0312, 0x0312, 1):
                self._hot.native_event("windows_generic_MSG", ctypes.addressof(msg))
        except Exception:
            logger.debug("poll hotkey failed", exc_info=True)
        self.root.after(50, self._poll_win_messages)

    def point_notion(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.btn.configure(state="disabled")
        self._set_status("Looking in Downloads…")

        def work() -> None:
            try:
                path = find_notion_installer()
                if path is None:
                    self.root.after(
                        0,
                        lambda: self._done("Can't find Notion Installer in Downloads."),
                    )
                    return
                ok = reveal(str(path))
                if ok:
                    self.root.after(
                        0,
                        lambda: self._done(f"Pointed at {path.name} in Explorer."),
                    )
                else:
                    self.root.after(0, lambda: self._done("Reveal failed."))
            except Exception as exc:
                self.root.after(0, lambda: self._done(f"Error: {exc}"))

        threading.Thread(target=work, daemon=True).start()

    def _done(self, message: str) -> None:
        self._set_status(message)
        self.btn.configure(state="normal")
        self._busy = False
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(80, lambda: self.root.attributes("-topmost", True))
        except tk.TclError:
            pass

    def quit(self) -> None:
        if self._hot is not None:
            self._hot.unregister()
        self.root.destroy()

    def run(self) -> int:
        self.root.mainloop()
        return 0


def main(argv: list[str] | None = None) -> int:
    del argv
    return CodyApp().run()


if __name__ == "__main__":
    raise SystemExit(main())
