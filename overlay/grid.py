"""Screenshot grid overlay and cell ↔ pixel mapping for vision pointing."""
from __future__ import annotations

import re
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

_CELL_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


@dataclass
class GridSpec:
    cols: int
    rows: int
    img_w: int
    img_h: int


def default_grid(img_w: int, img_h: int) -> GridSpec:
    cols = max(6, min(16, round(img_w / 100)))
    rows = max(4, min(12, round(img_h / 100)))
    return GridSpec(cols=cols, rows=rows, img_w=img_w, img_h=img_h)


def _col_index(letters: str) -> int:
    idx = 0
    for ch in letters.upper():
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def _parse_cell(cell: str) -> tuple[int, int] | None:
    m = _CELL_RE.match(cell.strip())
    if not m:
        return None
    return _col_index(m.group(1)), int(m.group(2)) - 1


def cell_center(spec: GridSpec, cell: str) -> tuple[float, float] | None:
    parsed = _parse_cell(cell)
    if parsed is None:
        return None
    col, row = parsed
    if col < 0 or col >= spec.cols or row < 0 or row >= spec.rows:
        return None
    cw = spec.img_w / spec.cols
    ch = spec.img_h / spec.rows
    return (col + 0.5) * cw, (row + 0.5) * ch


def annotate(image: Image.Image, spec: GridSpec) -> Image.Image:
    out = image.copy()
    draw = ImageDraw.Draw(out)
    cw = spec.img_w / spec.cols
    ch = spec.img_h / spec.rows
    line = (200, 200, 200)
    label = (80, 80, 80)

    for c in range(1, spec.cols):
        x = round(c * cw)
        draw.line([(x, 0), (x, spec.img_h)], fill=line, width=1)
    for r in range(1, spec.rows):
        y = round(r * ch)
        draw.line([(0, y), (spec.img_w, y)], fill=line, width=1)

    try:
        font = ImageFont.load_default()
    except OSError:
        font = None

    for c in range(spec.cols):
        letters = ""
        n = c
        while True:
            n, rem = divmod(n, 26)
            letters = chr(ord("A") + rem) + letters
            if n == 0:
                break
            n -= 1
        draw.text((c * cw + 2, 2), letters, fill=label, font=font)

    for r in range(spec.rows):
        draw.text((2, r * ch + 2), str(r + 1), fill=label, font=font)

    return out


def legend_text(spec: GridSpec) -> str:
    last_col = ""
    n = spec.cols - 1
    while True:
        n, rem = divmod(n, 26)
        last_col = chr(ord("A") + rem) + last_col
        if n == 0:
            break
        n -= 1
    top = f"A1"
    bottom = f"{last_col}{spec.rows}"
    return (
        f"Screenshot has grid {top}…{bottom}; return a cell (e.g. B7) "
        f"and optional fine x,y in image pixels ({spec.img_w}×{spec.img_h})."
    )
