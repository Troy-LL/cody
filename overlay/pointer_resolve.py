"""Resolve a model point: image coords primary, OCR snap when nearby."""
from __future__ import annotations

from dataclasses import dataclass

from overlay.grid import cell_center
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


def _uia_center(el) -> tuple[int, int]:
    left, top, right, bottom = el.bounds
    return ((left + right) // 2, (top + bottom) // 2)


def resolve(
    target,
    coords,
    boxes,
    shot: Shot,
    *,
    uia=None,
    cell: str | None = None,
    grid_spec=None,
):
    """
    Priority:
      1. UIA name match → bounds center
      2. Model coords + OCR snap-near (SNAP_PX)
      3. Cell center (grid_spec required)
      4. Model coords → screen
      5. OCR exact without coords
      6. None
    """
    if uia:
        from overlay.scene import match_uia

        hit = match_uia(target, uia)
        if hit is not None:
            return clamp_screen(*_uia_center(hit))

    model_pt = None
    if coords is not None:
        model_pt = to_screen(shot, coords[0], coords[1])

    candidates = _match_candidates(target, boxes) if target else []

    if model_pt is not None:
        if candidates:
            near = [b for b in candidates if _dist2(b.center, model_pt) <= SNAP_PX * SNAP_PX]
            if near:
                return clamp_screen(*_nearest(near, model_pt).center)
        if cell and grid_spec is not None:
            pt = cell_center(grid_spec, cell)
            if pt is not None:
                return clamp_screen(*to_screen(shot, pt[0], pt[1]))
        return clamp_screen(*model_pt)

    if cell and grid_spec is not None:
        pt = cell_center(grid_spec, cell)
        if pt is not None:
            return clamp_screen(*to_screen(shot, pt[0], pt[1]))

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
