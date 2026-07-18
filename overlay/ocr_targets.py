"""Screenshot a window + OCR into up to 9 point targets (screen coords)."""

from __future__ import annotations

import logging
import random
import re
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PointTarget:
    label: str
    x: int
    y: int


PROMPT = "I think this is _____."


def fill_prompt(label: str) -> str:
    blank = (label or "…").strip() or "…"
    return PROMPT.replace("_____", blank)


def enable_dpi_awareness() -> None:
    """Must run before Tk() so OCR coords match window placement."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        # PER_MONITOR_AWARE_V2 = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def window_rect_at(x: int, y: int) -> tuple[int, int, int, int] | None:
    """Visible window bounds under the cursor (no DWM shadow padding)."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        dwmapi = ctypes.windll.dwmapi
        pt = wintypes.POINT(int(x), int(y))
        hwnd = user32.WindowFromPoint(pt)
        if not hwnd:
            return None
        root = user32.GetAncestor(hwnd, 2)
        if root:
            hwnd = root

        rect = wintypes.RECT()
        # DWMWA_EXTENDED_FRAME_BOUNDS = 9 — visible frame, not shadow
        hr = dwmapi.DwmGetWindowAttribute(
            hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)
        )
        if hr != 0:
            user32.GetWindowRect(hwnd, ctypes.byref(rect))

        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w < 40 or h < 40:
            return None
        if w * h > 4_000_000:
            cx, cy = (rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2
            return cx - 500, cy - 400, cx + 500, cy + 400
        return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
    except Exception:
        logger.warning("window_rect_at failed", exc_info=True)
        return None


def grab_bbox(left: int, top: int, right: int, bottom: int):
    from PIL import ImageGrab

    # Same coordinate space as GetCursorPos / Dwm bounds when DPI-aware
    return ImageGrab.grab(bbox=(left, top, right, bottom))


def _configure_tesseract() -> None:
    import os
    from pathlib import Path

    import pytesseract

    cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "") or ""
    if cmd and Path(cmd).is_file():
        return
    for path in (
        os.environ.get("TESSERACT_CMD"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if path and Path(path).is_file():
            pytesseract.pytesseract.tesseract_cmd = path
            return


def group_word_boxes(
    words: list[tuple[str, int, int, int, int]],
    *,
    max_gap_ratio: float = 0.7,
    max_label: int = 72,
) -> list[tuple[str, int, int, int, int]]:
    """Merge neighboring words on the same line into phrases.

    Example: separate boxes "New" + "folder" → one "New folder" target.
    """
    if not words:
        return []

    # Sort top-to-bottom, then left-to-right
    ordered = sorted(words, key=lambda b: (b[2], b[1]))
    # Cluster into lines by vertical overlap / similar tops
    lines: list[list[tuple[str, int, int, int, int]]] = []
    for box in ordered:
        text, x, y, w, h = box
        placed = False
        for line in lines:
            _, _, ly, _, lh = line[0]
            # same line if vertical centers are close
            cy = y + h / 2
            lcy = ly + lh / 2
            if abs(cy - lcy) <= max(h, lh) * 0.55:
                line.append(box)
                placed = True
                break
        if not placed:
            lines.append([box])

    phrases: list[tuple[str, int, int, int, int]] = []
    for line in lines:
        line.sort(key=lambda b: b[1])
        run_text = line[0][0]
        rx, ry, rw, rh = line[0][1], line[0][2], line[0][3], line[0][4]
        for text, x, y, w, h in line[1:]:
            gap = x - (rx + rw)
            # Allow a bit more than a space (and slight OCR overlap); break on big gaps
            max_gap = max(10, int(max(rh, h) * max_gap_ratio))
            if gap <= max_gap and gap >= -max(rh, h):
                # join with space (or none after hyphen)
                if run_text.endswith("-"):
                    run_text = run_text + text
                else:
                    run_text = f"{run_text} {text}"
                # expand bounding box
                right = max(rx + rw, x + w)
                bottom = max(ry + rh, y + h)
                rx = min(rx, x)
                ry = min(ry, y)
                rw = right - rx
                rh = bottom - ry
            else:
                phrases.append((run_text[:max_label], rx, ry, rw, rh))
                run_text, rx, ry, rw, rh = text, x, y, w, h
        phrases.append((run_text[:max_label], rx, ry, rw, rh))
    return phrases


def ocr_boxes(img) -> list[tuple[str, int, int, int, int]]:
    """Word-level OCR, then group into line phrases."""
    try:
        import pytesseract
    except ImportError:
        return []

    _configure_tesseract()
    try:
        # PSM 11 = sparse text (toolbars / icons with labels)
        data = pytesseract.image_to_data(
            img, output_type=pytesseract.Output.DICT, config="--psm 11"
        )
    except Exception as exc:
        logger.info("OCR failed: %s", exc)
        return []

    words: list[tuple[str, int, int, int, int]] = []
    n = len(data.get("text", []))
    for i in range(n):
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1
        text = (data["text"][i] or "").strip()
        if conf < 40 or len(text) < 2:
            continue
        if not re.search(r"[A-Za-z0-9]", text):
            continue
        x = int(data["left"][i])
        y = int(data["top"][i])
        w = int(data["width"][i])
        h = int(data["height"][i])
        if w < 4 or h < 4:
            continue
        words.append((text, x, y, w, h))
    return group_word_boxes(words)


def boxes_to_targets(
    boxes: list[tuple[str, int, int, int, int]],
    origin: tuple[int, int],
    scale: tuple[float, float],
) -> list[PointTarget]:
    ox, oy = origin
    sx, sy = scale
    screen: list[PointTarget] = []
    seen: set[str] = set()
    for label, x, y, w, h in boxes:
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        cx = ox + int((x + w / 2) * sx)
        cy = oy + int((y + h / 2) * sy)
        screen.append(PointTarget(label=label, x=cx, y=cy))
    return screen


def pick_targets(
    boxes: list[tuple[str, int, int, int, int]],
    origin: tuple[int, int],
    scale: tuple[float, float],
    k: int = 9,
) -> list[PointTarget]:
    screen = boxes_to_targets(boxes, origin, scale)
    # Prefer multi-word phrases over lone fragments when sampling
    screen.sort(key=lambda t: (-t.label.count(" "), -len(t.label), t.label.casefold()))
    if len(screen) <= k:
        return screen
    # Keep the strongest phrases first, then fill with a light shuffle of the rest
    head = screen[: max(1, k // 2)]
    rest = screen[len(head) :]
    random.shuffle(rest)
    return (head + rest)[:k]


def rank_targets_for_query(targets: list[PointTarget], query: str, k: int = 9) -> list[PointTarget]:
    """Score OCR labels against 'where's my ____' terms; best first."""
    from overlay.query_parse import query_terms

    terms = query_terms(query)
    if not terms:
        return targets[:k]

    scored: list[tuple[int, int, PointTarget]] = []
    for t in targets:
        low = t.label.casefold()
        score = 0
        for term in terms:
            if low == term:
                score += 100
            elif low.startswith(term) or term.startswith(low):
                score += 60
            elif term in low:
                score += 40
            # fuzzy-ish: shared prefix
            elif len(term) >= 3 and low[:3] == term[:3]:
                score += 10
        if score > 0:
            scored.append((score, -len(t.label), t))
    scored.sort(reverse=True)
    if scored:
        return [t for _, __, t in scored[:k]]
    # No lexical hit — return empty so voice path can say so
    return []


def primary_screen_rect() -> tuple[int, int, int, int]:
    if sys.platform == "win32":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            # Primary monitor (matches ImageGrab.grab() default)
            w = int(user32.GetSystemMetrics(0))
            h = int(user32.GetSystemMetrics(1))
            return 0, 0, w, h
        except Exception:
            pass
    return 0, 0, 1920, 1080


def _scan_rect(
    left: int,
    top: int,
    right: int,
    bottom: int,
    *,
    query: str | None = None,
    k: int = 9,
) -> list[PointTarget]:
    img = grab_bbox(left, top, right, bottom)
    boxes = ocr_boxes(img)
    sx = (right - left) / max(img.width, 1)
    sy = (bottom - top) / max(img.height, 1)
    if abs(sx - 1.0) > 0.02 or abs(sy - 1.0) > 0.02:
        logger.warning(
            "DPI/grab scale mismatch: rect=%sx%s img=%sx%s scale=%.3f,%.3f",
            right - left,
            bottom - top,
            img.width,
            img.height,
            sx,
            sy,
        )
    all_targets = boxes_to_targets(boxes, (left, top), (sx, sy))
    if query:
        ranked = rank_targets_for_query(all_targets, query, k=k)
        logger.info("full OCR %s hits, query %r → %s", len(all_targets), query, [t.label for t in ranked])
        return ranked
    targets = pick_targets(boxes, (left, top), (sx, sy), k=k)
    logger.info("scan → %s targets (of %s)", len(targets), len(all_targets))
    return targets


def scan_full_screen(query: str | None = None, k: int = 9) -> list[PointTarget]:
    """OCR the whole primary screen; optionally rank by voice query."""
    left, top, right, bottom = primary_screen_rect()
    return _scan_rect(left, top, right, bottom, query=query, k=k)


def scan_window_behind(
    cursor_x: int,
    cursor_y: int,
    query: str | None = None,
    k: int = 9,
) -> list[PointTarget]:
    rect = window_rect_at(cursor_x, cursor_y)
    if rect is None:
        rect = (cursor_x - 400, cursor_y - 300, cursor_x + 400, cursor_y + 300)
    left, top, right, bottom = rect
    return _scan_rect(left, top, right, bottom, query=query, k=k)
