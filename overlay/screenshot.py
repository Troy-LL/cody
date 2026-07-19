"""Capture the cursor's monitor (downscaled); invert model coords to screen px."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from PIL import Image


@dataclass
class Shot:
    image: Image.Image | None
    scale: float  # downscaled_px / screen_px
    origin: tuple[int, int]  # monitor top-left in screen (physical) coords
    screen_size: tuple[int, int] = (0, 0)  # full-res monitor size before downscale


def to_screen(shot: Shot, x: float, y: float) -> tuple[int, int]:
    """Map a point in downscaled-image pixels → absolute screen (physical) pixels."""
    sx = shot.origin[0] + round(x / shot.scale)
    sy = shot.origin[1] + round(y / shot.scale)
    return (sx, sy)


def desktop_bounds() -> tuple[int, int, int, int]:
    try:
        import mss

        with mss.MSS() as sct:
            mon = sct.monitors[0]
            return (
                mon["left"],
                mon["top"],
                mon["left"] + mon["width"] - 1,
                mon["top"] + mon["height"] - 1,
            )
    except Exception:
        return (0, 0, 65535, 65535)


def clamp_screen(x: int, y: int) -> tuple[int, int]:
    left, top, right, bottom = desktop_bounds()
    return (max(left, min(right, x)), max(top, min(bottom, y)))


def _cursor_pos() -> tuple[int, int]:
    pt = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def _monitor_under_cursor(sct) -> dict:
    """Pick the individual mss monitor that contains the cursor (not virtual desktop)."""
    cx, cy = _cursor_pos()
    for mon in sct.monitors[1:]:
        left, top = mon["left"], mon["top"]
        if left <= cx < left + mon["width"] and top <= cy < top + mon["height"]:
            return mon
    if len(sct.monitors) > 1:
        return sct.monitors[1]
    return sct.monitors[0]


def _downscale(img: Image.Image, max_width: int) -> tuple[Image.Image, float]:
    scale = 1.0
    if img.width > max_width:
        scale = max_width / img.width
        img = img.resize((max_width, round(img.height * scale)))
    return img, scale


def capture(max_width: int = 1280) -> Shot:
    """Capture the monitor under the cursor (openclicky-style single-screen context)."""
    import mss

    with mss.MSS() as sct:
        mon = _monitor_under_cursor(sct)
        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
    origin = (mon["left"], mon["top"])
    screen_size = (img.width, img.height)
    img, scale = _downscale(img, max_width)
    return Shot(image=img, scale=scale, origin=origin, screen_size=screen_size)


def capture_all(max_width: int = 1536) -> Shot:
    """Capture the full virtual desktop (debug / multi-monitor stitch)."""
    import mss

    with mss.MSS() as sct:
        mon = sct.monitors[0]
        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
    origin = (mon["left"], mon["top"])
    screen_size = (img.width, img.height)
    img, scale = _downscale(img, max_width)
    return Shot(image=img, scale=scale, origin=origin, screen_size=screen_size)


if __name__ == "__main__":
    shot = capture()
    print("scale", shot.scale, "origin", shot.origin, "img", shot.image.size, "screen", shot.screen_size)
    cx, cy = shot.image.width / 2, shot.image.height / 2
    print("center image ->", to_screen(shot, cx, cy))
    shot.image.save("shot_debug.png")
