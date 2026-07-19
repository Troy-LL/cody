"""Windows UIA scene card for pointing context."""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from overlay.pointer_resolve import _query_core

logger = logging.getLogger(__name__)

_MAX_DEPTH = 5


@dataclass
class SceneEl:
    name: str
    kind: str
    bounds: tuple[int, int, int, int]


def format_scene(els: list[SceneEl]) -> str:
    lines = ["Scene (accessibility, may be incomplete):"]
    for el in els:
        left, top, right, bottom = el.bounds
        lines.append(f'- "{el.name}" {el.kind} @ ({left},{top})-({right},{bottom})')
    return "\n".join(lines)


def match_uia(target: str, els: list[SceneEl]) -> SceneEl | None:
    want = _query_core(target or "")
    if not want:
        return None

    exact = [el for el in els if el.name.casefold() == want]
    if exact:
        return max(exact, key=lambda el: len(el.name))

    subs: list[SceneEl] = []
    for el in els:
        label = el.name.casefold()
        if len(label) < 2:
            continue
        if want in label or label in want:
            subs.append(el)
    if not subs:
        return None
    return max(subs, key=lambda el: len(el.name))


def collect_scene(max_els: int = 40) -> list[SceneEl]:
    if sys.platform != "win32":
        return []
    try:
        import uiautomation as auto
    except ImportError:
        logger.info("uiautomation not installed — skip scene card")
        return []

    els: list[SceneEl] = []
    try:
        root = auto.GetRootControl()
        for win in root.GetChildren():
            try:
                if win.ClassName == "Shell_TrayWnd":
                    _walk_collect(win, els, max_els, depth=0)
                    break
            except Exception:
                continue

        if len(els) < max_els:
            fg = auto.GetForegroundControl()
            if fg is not None:
                _walk_collect(fg, els, max_els, depth=0)
    except Exception:
        logger.warning("UIA scene collect failed", exc_info=True)
        return []
    return els[:max_els]


def _walk_collect(control, out: list[SceneEl], max_els: int, depth: int) -> None:
    if len(out) >= max_els or depth > _MAX_DEPTH:
        return
    try:
        name = (control.Name or "").strip()
        if name:
            kind = control.ControlTypeName or ""
            rect = control.BoundingRectangle
            left, top, right, bottom = int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
            if right > left and bottom > top:
                out.append(SceneEl(name=name, kind=kind, bounds=(left, top, right, bottom)))
    except Exception:
        pass

    if len(out) >= max_els or depth >= _MAX_DEPTH:
        return
    try:
        children = control.GetChildren()
    except Exception:
        return
    for child in children:
        _walk_collect(child, out, max_els, depth + 1)
        if len(out) >= max_els:
            return
