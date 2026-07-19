"""Turn a model target label into exact screen pixels via OCR; else model coords."""
from __future__ import annotations

import re
from dataclasses import dataclass

from overlay.ocr_targets import ocr_boxes
from overlay.screenshot import Shot, clamp_screen, to_screen

_WORD = re.compile(r"[a-z0-9]+")
# Below this best score we'd rather point nowhere (fall back to model coords)
# than land on a loose substring hit — e.g. "gmail" inside an unrelated line.
_MIN_SCORE = 0.45


@dataclass
class OcrBox:
    text: str
    center: tuple[int, int]


def _norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _tokens(s: str) -> list[str]:
    return _WORD.findall(s.lower())


def _score(want: str, want_tokens: list[str], text: str) -> float:
    """Rank how well an OCR line matches the target label. 0 = no match.

    Rewards whole-word matches over substrings so "troy" hits the "Troy-LL"
    tab, not "troylazaro09" — the old code did the opposite (longest substring).
    """
    t = _norm(text)
    if not t:
        return 0.0
    if t == want:
        return 1.0
    toks = set(_tokens(text))
    # Every wanted token present as a whole word — the strong case. Bonus for
    # coverage so a tight label ("Cursor Settings") beats a line that merely
    # contains it ("Here's Cursor Settings.").
    if want_tokens and all(w in toks for w in want_tokens):
        cov = min(len(want) / max(len(t), 1), 1.0)
        return 0.75 + 0.2 * cov
    # A wanted token is the prefix of some word (e.g. "sett" → "settings").
    if any(tok.startswith(w) for w in want_tokens for tok in _tokens(text)):
        return 0.5
    # Loose substring — last resort; shorter lines are closer to the label.
    if want in t:
        return 0.3 * (len(want) / len(t))
    return 0.0


def _match(target: str, boxes: list):
    want = _norm(target)
    if not want:
        return None
    want_tokens = _tokens(target)
    best = None
    best_score = 0.0
    for b in boxes:
        s = _score(want, want_tokens, b.text)
        # Tie-break: prefer the shorter line (tighter around the actual label).
        if s > best_score or (
            s == best_score and s > 0 and best is not None and len(b.text) < len(best.text)
        ):
            best, best_score = b, s
    if best is None or best_score < _MIN_SCORE:
        return None
    return best


def resolve(target, coords, boxes, shot: Shot):
    if target:
        box = _match(target, boxes)
        if box is not None:
            return clamp_screen(*box.center)
    if coords is not None:
        return clamp_screen(*to_screen(shot, coords[0], coords[1]))
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
