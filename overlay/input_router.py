"""Single entry for PTT and wake-word queries: capture -> brain -> resolve."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from overlay import brain, pointer_resolve, refine, screenshot, scene
from overlay.grid import annotate, cell_center, default_grid, legend_text
from overlay.scene import format_scene
@dataclass
class ScreenStep:
    label: str
    point: tuple[int, int]
    say: str = ""


@dataclass
class Outcome:
    reply_text: str
    point: tuple[int, int] | None
    reveal_path: str | None = None
    steps: list[ScreenStep] = field(default_factory=list)


@dataclass
class Deps:
    capture: Callable
    ask: Callable  # (question, shot) -> Answer
    boxes_for: Callable  # (shot) -> list
    resolve: Callable  # (target, coords, boxes, shot) -> (x,y)|None
    refine_point: Callable | None = None  # (question, shot, rough_xy, target) -> image xy|None


def _resolve_steps(answer, boxes, shot, resolve, *, uia=None, cell=None, grid_spec=None) -> list[ScreenStep]:
    if answer.steps:
        out: list[ScreenStep] = []
        for step in answer.steps:
            pt = resolve(
                step.label, step.coords, boxes, shot, uia=uia, cell=cell, grid_spec=grid_spec
            )
            if pt is None:
                continue
            out.append(ScreenStep(step.label, pt, step.say))
        return out
    if answer.target or answer.coords:
        pt = resolve(
            answer.target, answer.coords, boxes, shot, uia=uia, cell=cell, grid_spec=grid_spec
        )
        if pt is not None:
            return [ScreenStep(answer.target or "here", pt, "")]
    return []


def handle_query(question: str, deps: Deps) -> Outcome:
    if not question.strip():
        return Outcome("Didn't catch that.", None)
    shot = deps.capture()
    els = scene.collect_scene()
    if shot.image is not None:
        w, h = shot.image.size
        spec = default_grid(w, h)
        annotated = annotate(shot.image, spec)
    else:
        spec = default_grid(1, 1)
        annotated = None
    try:
        answer = deps.ask(
            question,
            shot,
            scene_text=format_scene(els),
            grid_legend=legend_text(spec),
            annotated_image=annotated,
        )
    except Exception:
        return Outcome("I couldn't reach the model.", None)

    if not answer.found:
        return Outcome(
            answer.reply_text or "I don't see that on this screen.",
            None,
            answer.reveal_path,
            [],
        )

    boxes = deps.boxes_for(shot) if (answer.steps or answer.target or answer.coords) else []
    if (
        deps.refine_point
        and refine.should_refine(answer, question, boxes, shot, els, spec)
    ):
        rough = answer.coords
        if rough is None and answer.cell:
            rough = cell_center(spec, answer.cell)
        if rough is not None:
            refined = deps.refine_point(question, shot, rough, answer.target)
            if refined is not None:
                answer.coords = refined

    steps: list[ScreenStep] = []
    if answer.steps or answer.target or answer.coords:
        steps = _resolve_steps(
            answer,
            boxes,
            shot,
            deps.resolve,
            uia=els,
            cell=answer.cell,
            grid_spec=spec,
        )

    point = steps[0].point if steps else None
    return Outcome(answer.reply_text or "", point, answer.reveal_path, steps)


def default_deps(api_key: str) -> Deps:
    return Deps(
        capture=screenshot.capture,
        ask=lambda q, s, **kw: brain.ask(q, s, api_key, **kw),
        boxes_for=pointer_resolve.boxes_for,
        resolve=pointer_resolve.resolve,
        refine_point=lambda q, s, xy, t: refine.refine_point(q, s, api_key, xy, t),
    )
