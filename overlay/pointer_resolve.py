"""Turn a model target label into exact screen pixels via OCR; else model coords."""
from __future__ import annotations

from dataclasses import dataclass

from overlay.ocr_targets import ocr_boxes
from overlay.screenshot import Shot, to_screen


@dataclass
class OcrBox:
    text: str
    center: tuple[int, int]


def _match(target: str, boxes: list):
    want = target.strip().lower()
    if not want:
        return None
    exact = [b for b in boxes if b.text.strip().lower() == want]
    if exact:
        return exact[0]
    subs = [b for b in boxes if want in b.text.strip().lower()]
    if subs:
        return max(subs, key=lambda b: len(b.text))
    return None


def resolve(target, coords, boxes, shot: Shot):
    if target:
        box = _match(target, boxes)
        if box is not None:
            return tuple(box.center)
    if coords is not None:
        return to_screen(shot, coords[0], coords[1])
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
