"""Resolve a model point: image coords primary, OCR snap when nearby."""
from __future__ import annotations

from dataclasses import dataclass

from overlay.ocr_targets import ocr_boxes
from overlay.screenshot import Shot, clamp_screen, to_screen

# OCR may refine the model guess only when a matching label sits near it.
SNAP_PX = 140


@dataclass
class OcrBox:
    text: str
    center: tuple[int, int]


def _query_core(target: str) -> str:
    """Strip filler words so 'Foo icon' / 'the Foo app' still OCR-match 'Foo'."""
    raw = target.strip().lower()
    for noise in ("the ", "my ", " icon", " app", " button", " tab", " shortcut", " logo"):
        raw = raw.replace(noise, " ")
    return " ".join(raw.split())


def _match_candidates(target: str, boxes: list) -> list:
    want = _query_core(target or "")
    if not want:
        return []
    exact = [b for b in boxes if b.text.strip().lower() == want]
    if exact:
        return exact
    # Substring either way; prefer longer OCR labels (more specific).
    subs = []
    for b in boxes:
        label = b.text.strip().lower()
        if len(label) < 2:
            continue
        if want in label or label in want:
            subs.append(b)
    return sorted(subs, key=lambda b: len(b.text), reverse=True)


def _dist2(a: tuple[int, int], b: tuple[int, int]) -> int:
    dx, dy = a[0] - b[0], a[1] - b[1]
    return dx * dx + dy * dy


def _nearest(boxes: list, point: tuple[int, int]):
    return min(boxes, key=lambda b: _dist2(b.center, point))


def resolve(target, coords, boxes, shot: Shot):
    """
    Priority (openclicky-inspired):
      1. Model image coords → screen (always preferred when present)
      2. OCR exact/near match *within SNAP_PX* of that guess (pixel-perfect snap)
      3. OCR exact match alone if the model gave no coords
      4. None
    """
    model_pt = None
    if coords is not None:
        model_pt = to_screen(shot, coords[0], coords[1])

    candidates = _match_candidates(target, boxes) if target else []

    if model_pt is not None:
        if candidates:
            near = [b for b in candidates if _dist2(b.center, model_pt) <= SNAP_PX * SNAP_PX]
            if near:
                return clamp_screen(*_nearest(near, model_pt).center)
        return clamp_screen(*model_pt)

    if candidates:
        return clamp_screen(*candidates[0].center)
    return None


def boxes_for(shot: Shot) -> list[OcrBox]:
    if shot.image is None:
        return []
    inv = 1.0 / shot.scale if shot.scale else 1.0
    ox, oy = shot.origin
    out: list[OcrBox] = []
    for text, x, y, w, h in ocr_boxes(shot.image):
        cx = ox + int((x + w / 2) * inv)
        cy = oy + int((y + h / 2) * inv)
        out.append(OcrBox(text=text, center=(cx, cy)))
    return out
