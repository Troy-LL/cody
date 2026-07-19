"""Single entry for PTT and wake-word queries: capture -> brain -> resolve."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from overlay import brain, pointer_resolve, screenshot


@dataclass
class Outcome:
    reply_text: str
    point: tuple[int, int] | None
    reveal_path: str | None = None


@dataclass
class Deps:
    capture: Callable
    ask: Callable        # (question, shot) -> Answer
    boxes_for: Callable  # (shot) -> list
    resolve: Callable    # (target, coords, boxes, shot) -> (x,y)|None


def handle_query(question: str, deps: Deps) -> Outcome:
    if not question.strip():
        return Outcome("Didn't catch that.", None)
    shot = deps.capture()
    try:
        answer = deps.ask(question, shot)
    except Exception:
        return Outcome("I couldn't reach the model.", None)
    point = None
    if answer.target or answer.coords:
        boxes = deps.boxes_for(shot)
        point = deps.resolve(answer.target, answer.coords, boxes, shot)
    return Outcome(answer.reply_text or "", point, answer.reveal_path)


def default_deps(api_key: str) -> Deps:
    return Deps(
        capture=screenshot.capture,
        ask=lambda q, s: brain.ask(q, s, api_key),
        boxes_for=pointer_resolve.boxes_for,
        resolve=pointer_resolve.resolve,
    )
