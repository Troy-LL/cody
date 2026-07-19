"""Capture all monitors as one downscaled image; invert model coords to screen px."""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass
class Shot:
    image: Image.Image | None
    scale: float           # downscaled_px / screen_px
    origin: tuple[int, int]  # virtual-desktop top-left in screen coords
    full: Image.Image | None = None  # full-res capture for pixel-accurate OCR


def to_screen(shot: Shot, x: float, y: float) -> tuple[int, int]:
    sx = shot.origin[0] + round(x / shot.scale)
    sy = shot.origin[1] + round(y / shot.scale)
    return (sx, sy)


def desktop_bounds() -> tuple[int, int, int, int]:
    try:
        import mss

        with mss.mss() as sct:
            mon = sct.monitors[0]
            return (mon["left"], mon["top"], mon["left"] + mon["width"] - 1, mon["top"] + mon["height"] - 1)
    except Exception:
        return (0, 0, 65535, 65535)


def clamp_screen(x: int, y: int) -> tuple[int, int]:
    left, top, right, bottom = desktop_bounds()
    return (max(left, min(right, x)), max(top, min(bottom, y)))


def capture(max_width: int = 1536) -> Shot:
    import mss

    with mss.mss() as sct:
        mon = sct.monitors[0]  # [0] = full virtual desktop across all monitors
        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
    origin = (mon["left"], mon["top"])
    full = img  # keep full-res for OCR precision
    scale = 1.0
    small = img
    if img.width > max_width:
        scale = max_width / img.width
        small = img.resize((max_width, round(img.height * scale)))
    return Shot(image=small, scale=scale, origin=origin, full=full)


if __name__ == "__main__":
    shot = capture()
    print("scale", shot.scale, "origin", shot.origin, "img", shot.image.size)
    cx, cy = shot.image.width / 2, shot.image.height / 2
    print("center image ->", to_screen(shot, cx, cy))
    shot.image.save("shot_debug.png")
