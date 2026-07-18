"""Cody companion — keyboard scan + voice 'Hey Cody, where's my ___'."""

from __future__ import annotations

import logging
import threading
import time
import tkinter as tk
from tkinter import ttk

from overlay.ocr_targets import (
    PointTarget,
    enable_dpi_awareness,
    rank_targets_for_query,
    scan_full_screen,
)
from overlay.query_parse import extract_search_phrase, parse_hey_cody

logger = logging.getLogger(__name__)

COMPANION = 20
OFFSET_X = 14
OFFSET_Y = 14
CROSS = 14
METER_W = 7
METER_H = 26
FLY_MS = 1300
HOLD_MS = 2800
BUBBLE_MS = 3200
MAX_FINDS = 16
TICK_MS = 8

POINT_KEYS: dict[str, int] = {
    **{str(i): i - 1 for i in range(1, 10)},
    "z": 9,
    "x": 10,
    "c": 11,
    "v": 12,
    "b": 13,
    "n": 14,
    "m": 15,
}
SLOT_KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "z", "x", "c", "v", "b", "n", "m"]


def _ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4.0 * t * t * t
    u = -2.0 * t + 2.0
    return 1.0 - (u * u * u) / 2.0


def _place_beside_mouse(root: tk.Misc, cursor_x: int, cursor_y: int) -> None:
    root.geometry(f"{COMPANION}x{COMPANION}+{cursor_x + OFFSET_X}+{cursor_y + OFFSET_Y}")


def _place_tip_at(root: tk.Misc, tip_x: int, tip_y: int) -> None:
    root.geometry(f"{COMPANION}x{COMPANION}+{int(tip_x) - 2}+{int(tip_y) - 2}")


def _slot_label(index: int) -> str:
    if 0 <= index < len(SLOT_KEYS):
        return SLOT_KEYS[index]
    return str(index + 1)


class CodyApp:
    def __init__(self) -> None:
        enable_dpi_awareness()
        self.root = tk.Tk()
        self.root.title("Cody")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-transparentcolor", "magenta")
        except tk.TclError:
            pass
        self.root.configure(bg="magenta")
        self.root.geometry(f"{COMPANION}x{COMPANION}+100+100")

        self.canvas = tk.Canvas(
            self.root,
            width=COMPANION,
            height=COMPANION,
            bg="magenta",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._draw_cursor()

        self.panel = tk.Toplevel(self.root)
        self.panel.title("Cody finds")
        self.panel.attributes("-topmost", True)
        self.panel.geometry("320x440+24+24")
        self.panel.protocol("WM_DELETE_WINDOW", self.quit)

        frm = ttk.Frame(self.panel, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Cody finds", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        self.status = ttk.Label(
            frm,
            text="Say: Hey Cody, where's my …",
            wraplength=290,
        )
        self.status.pack(anchor="w", pady=(4, 6))

        key_row = ttk.Frame(frm)
        key_row.pack(fill="x", pady=(0, 6))
        ttk.Label(key_row, text="ElevenLabs key").pack(anchor="w")
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_row, textvariable=self.key_var, show="*")
        self.key_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(key_row, text="Save", command=self._save_api_key).pack(side="left", padx=(6, 0))

        self.listbox = tk.Listbox(frm, height=12, activestyle="dotbox", font=("Segoe UI", 10))
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", self._on_list_activate)
        self.listbox.bind("<Return>", self._on_list_activate)

        btn_row = ttk.Frame(frm)
        btn_row.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_row, text="Scan", command=self._scan).pack(side="left")
        ttk.Button(btn_row, text="Rescan (R)", command=self._scan).pack(side="left", padx=(6, 0))
        ttk.Button(btn_row, text="Listen", command=self._restart_listen).pack(side="left", padx=(6, 0))
        ttk.Label(btn_row, text="1–9 z–m", foreground="#666").pack(side="right")

        # Destination crosshair
        self.dest = tk.Toplevel(self.root)
        self.dest.overrideredirect(True)
        self.dest.attributes("-topmost", True)
        try:
            self.dest.attributes("-transparentcolor", "magenta")
        except tk.TclError:
            pass
        self.dest.configure(bg="magenta")
        self.dest.geometry(f"{CROSS * 2}x{CROSS * 2}+0+0")
        self.dest_canvas = tk.Canvas(
            self.dest,
            width=CROSS * 2,
            height=CROSS * 2,
            bg="magenta",
            highlightthickness=0,
            bd=0,
        )
        self.dest_canvas.pack()
        self._draw_cross()
        self.dest.withdraw()

        # Speech bubble next to Cody
        self.bubble = tk.Toplevel(self.root)
        self.bubble.overrideredirect(True)
        self.bubble.attributes("-topmost", True)
        self.bubble.configure(bg="#fff8e7")
        self.bubble_label = tk.Label(
            self.bubble,
            text="",
            bg="#fff8e7",
            fg="#1a1a1a",
            font=("Segoe UI", 10),
            wraplength=220,
            justify="left",
            padx=10,
            pady=8,
            bd=1,
            relief="solid",
        )
        self.bubble_label.pack()
        self.bubble.withdraw()
        self._bubble_job: str | None = None

        # Mic volume meter (left of Cody)
        self.meter = tk.Toplevel(self.root)
        self.meter.overrideredirect(True)
        self.meter.attributes("-topmost", True)
        try:
            self.meter.attributes("-transparentcolor", "magenta")
        except tk.TclError:
            pass
        self.meter.configure(bg="magenta")
        self.meter.geometry(f"{METER_W}x{METER_H}+80+100")
        self.meter_canvas = tk.Canvas(
            self.meter,
            width=METER_W,
            height=METER_H,
            bg="magenta",
            highlightthickness=0,
            bd=0,
        )
        self.meter_canvas.pack()
        self._meter_level = 0.0
        self._meter_smooth = 0.0
        self._draw_meter(0.0)

        self.targets: list[PointTarget] = []
        self.busy = False
        self.flying = False
        self.pointed = False
        self._hold_job: str | None = None
        self._listener = None

        self.root.bind_all("<KeyPress-Escape>", lambda _e: self.quit())
        self.root.bind_all("<KeyPress-space>", self._on_space)
        self.root.bind_all("<KeyPress-r>", self._on_rescan_key)
        self.root.bind_all("<KeyPress-R>", self._on_rescan_key)
        self.root.bind_all("<F5>", lambda _e: self._scan())
        self.root.bind_all("<KeyPress>", self._on_key)

        self.root.after(TICK_MS, self._tick_follow)
        self.root.after(150, self._boot)

    def _boot(self) -> None:
        self._refresh_voice_status()
        self._start_listener()

    def _typing_focus(self) -> bool:
        focus = self.panel.focus_get()
        return focus in (self.key_entry,)

    def _on_space(self, _event: tk.Event) -> None:
        if self._typing_focus():
            return
        self._scan()

    def _on_rescan_key(self, _event: tk.Event) -> None:
        if self._typing_focus():
            return
        self._scan()

    def _save_api_key(self) -> None:
        key = self.key_var.get().strip()
        if not key:
            self._set_status("Paste your ElevenLabs API key, then Save")
            return
        try:
            from voice.config import save_api_key

            save_api_key(key)
            self.key_var.set("")
            self._set_status("ElevenLabs key saved — voice ready")
            logger.info("ElevenLabs api_key saved to config.local.json")
        except Exception as e:
            logger.exception("save key failed")
            self._set_status(f"Could not save key: {e}")

    def _refresh_voice_status(self) -> None:
        try:
            from voice.speak import elevenlabs_ready

            ok, why = elevenlabs_ready()
        except Exception as e:
            ok, why = False, str(e)
        if ok:
            self._set_status("Listening — Hey Cody, where's my …")
        else:
            self._set_status(f"Paste ElevenLabs key below ({why})")

    def _draw_cursor(self) -> None:
        c = self.canvas
        c.delete("all")
        pad = 2
        tip_x, tip_y = pad, pad
        c.create_polygon(
            tip_x,
            tip_y,
            tip_x + 12,
            tip_y + 4,
            tip_x + 5,
            tip_y + 5,
            tip_x + 4,
            tip_y + 12,
            fill="#111111",
            outline="#ffffff",
            width=1,
            joinstyle="round",
        )
        c.create_oval(tip_x + 1, tip_y + 1, tip_x + 5, tip_y + 5, fill="#ff3b30", outline="")

    def _draw_cross(self) -> None:
        c = self.dest_canvas
        c.delete("all")
        m = CROSS
        c.create_line(m - 8, m, m + 8, m, fill="#ff3b30", width=2)
        c.create_line(m, m - 8, m, m + 8, fill="#ff3b30", width=2)
        c.create_oval(m - 3, m - 3, m + 3, m + 3, outline="#ff3b30", width=2)

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _start_listener(self) -> None:
        try:
            from overlay.listen import HeyCodyListener, listen_available

            ok, why = listen_available()
            if not ok:
                self._set_status(f"Mic off ({why}). Use Scan + 1–9.")
                return
            if self._listener is not None:
                try:
                    self._listener.stop()
                except Exception:
                    pass
            self._listener = HeyCodyListener(self._on_heard, on_level=self._on_mic_level)
            self._listener.start()
            logger.info("voice listener started (%s)", why)
        except Exception as e:
            logger.exception("listener start failed")
            self._set_status(f"Mic failed ({e})")

    def _restart_listen(self) -> None:
        self._start_listener()
        self._refresh_voice_status()

    def _on_heard(self, transcript: str) -> None:
        self.root.after(0, lambda: self._handle_transcript(transcript))

    def _on_mic_level(self, level: float) -> None:
        # Called from listener thread — stash only; UI paints on tick
        self._meter_level = max(0.0, min(1.0, float(level)))

    def _draw_meter(self, level: float) -> None:
        c = self.meter_canvas
        c.delete("all")
        pad = 1
        # Track
        c.create_rectangle(
            pad,
            pad,
            METER_W - pad,
            METER_H - pad,
            outline="#ffffff",
            fill="#2a2a2a",
            width=1,
        )
        fill_h = int((METER_H - pad * 2 - 2) * level)
        if fill_h > 0:
            # Green → amber → red by level
            if level < 0.45:
                color = "#3ddc84"
            elif level < 0.75:
                color = "#f5c542"
            else:
                color = "#ff5a5a"
            top = METER_H - pad - 1 - fill_h
            c.create_rectangle(
                pad + 1,
                top,
                METER_W - pad - 1,
                METER_H - pad - 1,
                outline="",
                fill=color,
            )

    def _position_meter(self) -> None:
        try:
            cx = self.root.winfo_x()
            cy = self.root.winfo_y()
            self.meter.geometry(
                f"{METER_W}x{METER_H}+{cx - METER_W - 5}+{cy + (COMPANION - METER_H) // 2}"
            )
            self.meter.lift()
        except Exception:
            pass

    def _handle_transcript(self, transcript: str) -> None:
        logger.info("heard: %s", transcript)
        phrase = parse_hey_cody(transcript)
        if phrase is None:
            low = transcript.casefold()
            if "where" in low and ("my " in low or "the " in low):
                phrase = extract_search_phrase(transcript)
            else:
                self._set_status(f'Heard "{transcript[:48]}" — say Hey Cody, where\'s my …')
                return
        if not phrase:
            self._set_status("Heard Hey Cody — finish with where's my ____")
            return
        self._voice_find(phrase)

    def _voice_find(self, query: str) -> None:
        if self.busy:
            return
        self.busy = True
        self._set_status(f'Finding “{query}”…')

        def work() -> None:
            try:
                # Prefer matching current list; else full-screen OCR ranked by query
                ranked = rank_targets_for_query(self.targets, query, k=MAX_FINDS)
                if not ranked:
                    ranked = scan_full_screen(query=query, k=MAX_FINDS)
            except Exception as e:
                logger.exception("voice find failed")
                self.root.after(0, lambda: self._scan_failed(str(e)))
                return
            self.root.after(0, lambda: self._voice_find_done(ranked, query))

        threading.Thread(target=work, daemon=True).start()

    def _voice_find_done(self, targets: list[PointTarget], query: str) -> None:
        self.busy = False
        if not targets:
            self._set_status(f'No match for “{query}” — Scan then try again')
            return
        # Merge into list (best first) so keys still work
        self.targets = targets
        self.listbox.delete(0, tk.END)
        for i, t in enumerate(targets):
            self.listbox.insert(tk.END, f"{_slot_label(i)}. {t.label}")
        self._set_status(f'Found “{targets[0].label}” for “{query}”')
        self._point(0)

    def _scan(self) -> None:
        if self.busy:
            return
        self._cancel_hold()
        self._hide_bubble()
        self.pointed = False
        self.flying = False
        self.busy = True
        self._set_status("OCR whole screen…")
        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, "Scanning…")

        def work() -> None:
            try:
                targets = scan_full_screen(query=None, k=MAX_FINDS)
            except Exception as e:
                logger.exception("OCR failed")
                self.root.after(0, lambda: self._scan_failed(str(e)))
                return
            self.root.after(0, lambda: self._scan_done(targets))

        threading.Thread(target=work, daemon=True).start()

    def _scan_failed(self, err: str) -> None:
        self.busy = False
        self.targets = []
        self.listbox.delete(0, tk.END)
        self._set_status(f"OCR failed: {err}")

    def _scan_done(self, targets: list[PointTarget]) -> None:
        self.busy = False
        self.targets = targets
        self.listbox.delete(0, tk.END)
        if not targets:
            self._set_status("No text found — Space/R to scan again")
            self.listbox.insert(tk.END, "(no finds)")
            return
        for i, t in enumerate(targets):
            self.listbox.insert(tk.END, f"{_slot_label(i)}. {t.label}")
        self._set_status(f"{len(targets)} finds — voice or 1–9 / z–m")

    def _on_key(self, event: tk.Event) -> None:
        if self._typing_focus():
            return
        ch = (event.char or "").casefold()
        if ch in POINT_KEYS:
            self._point(POINT_KEYS[ch])

    def _on_list_activate(self, _event: tk.Event | None = None) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        self._point(int(sel[0]))

    def _point(self, index: int) -> None:
        if index < 0 or index >= len(self.targets) or self.flying:
            return
        t = self.targets[index]
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.see(index)
        self._set_status(f"→ {t.label}")
        self._speak_and_bubble(t.label)
        self._fly_to(t.x, t.y)

    def _speak_and_bubble(self, label: str) -> None:
        def work() -> None:
            try:
                from voice.speak import speak_point_line

                text, ok = speak_point_line(label, language_mode="en")
            except Exception:
                logger.exception("speak failed")
                text, ok = f"Here's {label}.", False
            self.root.after(0, lambda: self._show_bubble(text, ok))

        threading.Thread(target=work, daemon=True).start()

    def _show_bubble(self, text: str, tts_ok: bool) -> None:
        if not text:
            return
        self.bubble_label.configure(text=text)
        self.bubble.update_idletasks()
        self._position_bubble()
        self.bubble.deiconify()
        self.bubble.lift()
        if self._bubble_job is not None:
            try:
                self.root.after_cancel(self._bubble_job)
            except Exception:
                pass
        self._bubble_job = self.root.after(BUBBLE_MS, self._hide_bubble)
        if not tts_ok:
            self._set_status(f'{text} (TTS off — save ElevenLabs key)')

    def _hide_bubble(self) -> None:
        self._bubble_job = None
        try:
            self.bubble.withdraw()
        except Exception:
            pass

    def _position_bubble(self) -> None:
        try:
            cx = self.root.winfo_x()
            cy = self.root.winfo_y()
            self.bubble.update_idletasks()
            bw = max(self.bubble.winfo_reqwidth(), 80)
            bh = max(self.bubble.winfo_reqheight(), 28)
            # Sit to the right of Cody
            self.bubble.geometry(f"{bw}x{bh}+{cx + COMPANION + 8}+{cy - 4}")
        except Exception:
            pass

    def _cancel_hold(self) -> None:
        if self._hold_job is not None:
            try:
                self.root.after_cancel(self._hold_job)
            except Exception:
                pass
            self._hold_job = None

    def _resume_follow(self) -> None:
        self._hold_job = None
        self.pointed = False
        self.flying = False
        try:
            self.dest.withdraw()
        except Exception:
            pass

    def _fly_to(self, tx: int, ty: int) -> None:
        self._cancel_hold()
        self.flying = True
        self.pointed = False

        self.dest.geometry(f"{CROSS * 2}x{CROSS * 2}+{tx - CROSS}+{ty - CROSS}")
        self.dest.deiconify()
        self.dest.lift()
        self.root.lift()

        sx = self.root.winfo_x() + 2
        sy = self.root.winfo_y() + 2
        ex, ey = int(tx), int(ty)
        t0 = time.perf_counter()

        def step() -> None:
            elapsed = (time.perf_counter() - t0) * 1000.0
            u = min(1.0, elapsed / FLY_MS)
            e = _ease_in_out_cubic(u)
            x = int(sx + (ex - sx) * e)
            y = int(sy + (ey - sy) * e)
            _place_tip_at(self.root, x, y)
            self._position_bubble()
            self._position_meter()
            if u < 1.0:
                self.root.after(TICK_MS, step)
            else:
                _place_tip_at(self.root, ex, ey)
                self._position_bubble()
                self._position_meter()
                self.flying = False
                self.pointed = True
                self._hold_job = self.root.after(HOLD_MS, self._resume_follow)

        step()

    def _tick_follow(self) -> None:
        if not self.flying and not self.pointed:
            x, y = self.root.winfo_pointerxy()
            _place_beside_mouse(self.root, x, y)
            if self.bubble.winfo_ismapped():
                self._position_bubble()
        elif self.pointed and self.bubble.winfo_ismapped():
            self._position_bubble()
        # Smooth + decay mic meter beside Cody
        self._meter_level *= 0.94
        self._meter_smooth = self._meter_smooth * 0.55 + self._meter_level * 0.45
        self._draw_meter(self._meter_smooth)
        self._position_meter()
        self.root.after(TICK_MS, self._tick_follow)

    def quit(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    CodyApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
