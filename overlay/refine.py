"""Optional second vision pass on a cropped region for coarse cell points."""
from __future__ import annotations

from overlay.brain import ask
from overlay.grid import cell_center
from overlay.pointer_resolve import SNAP_PX, _dist2, _match_candidates, _nearest
from overlay.scene import match_uia
from overlay.screenshot import Shot, to_screen

# ponytail: coarse = coords within half a cell of cell_center; add parse flag when model sends one


def crop_around(
    shot: Shot, x: float, y: float, pad: float = 0.15
) -> tuple:
    """Return cropped image and (left, top, right, bottom) in full-image pixels."""
    if shot.image is None:
        raise ValueError("shot has no image")
    w, h = shot.image.size
    left = max(0, round(x - pad * w))
    top = max(0, round(y - pad * h))
    right = min(w, round(x + pad * w))
    bottom = min(h, round(y + pad * h))
    if right <= left:
        right = min(w, left + 1)
    if bottom <= top:
        bottom = min(h, top + 1)
    box = (left, top, right, bottom)
    return shot.image.crop(box), box


def map_from_crop(xy: tuple[float, float], box: tuple[int, int, int, int]) -> tuple[float, float]:
    left, top, _, _ = box
    return (xy[0] + left, xy[1] + top)


def _ocr_would_snap(target: str | None, coords: tuple[float, float], boxes, shot: Shot) -> bool:
    if not target or not boxes:
        return False
    model_pt = to_screen(shot, coords[0], coords[1])
    candidates = _match_candidates(target, boxes)
    if not candidates:
        return False
    near = [b for b in candidates if _dist2(b.center, model_pt) <= SNAP_PX * SNAP_PX]
    return bool(near)


def _cell_only_coarse(answer, grid_spec) -> bool:
    if not answer.cell or grid_spec is None:
        return False
    center = cell_center(grid_spec, answer.cell)
    if center is None:
        return False
    if answer.coords is None:
        return True
    cw = grid_spec.img_w / grid_spec.cols
    ch = grid_spec.img_h / grid_spec.rows
    dx = abs(answer.coords[0] - center[0])
    dy = abs(answer.coords[1] - center[1])
    return dx <= cw / 2 and dy <= ch / 2


def should_refine(answer, target: str, boxes, shot: Shot, uia, grid_spec) -> bool:
    if not answer.found or shot.image is None or answer.steps:
        return False
    name = answer.target or target
    if uia and match_uia(name, uia) is not None:
        return False
    rough = answer.coords
    if rough is None and answer.cell and grid_spec is not None:
        rough = cell_center(grid_spec, answer.cell)
    if rough is None:
        return False
    if _ocr_would_snap(name, rough, boxes, shot):
        return False
    return _cell_only_coarse(answer, grid_spec)


def refine_point(
    question: str,
    shot: Shot,
    api_key: str,
    rough_xy: tuple[float, float],
    target: str | None,
) -> tuple[float, float] | None:
    if shot.image is None:
        return None
    crop, box = crop_around(shot, rough_xy[0], rough_xy[1])
    cw, ch = crop.size
    label = target or "the target"
    mini = Shot(image=crop, scale=shot.scale, origin=shot.origin, screen_size=shot.screen_size)
    prompt = (
        f"{question.strip()} — in this zoomed crop ({cw}x{ch}px), point precisely at {label}."
    )
    try:
        answer = ask(prompt, mini, api_key)
    except Exception:
        return None
    if not answer.found or answer.coords is None:
        return None
    return map_from_crop(answer.coords, box)
