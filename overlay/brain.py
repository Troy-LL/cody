"""OpenAI vision loop: screenshot + question -> reply text + optional point/reveal."""
from __future__ import annotations

import base64
import io
import json
import logging
from dataclasses import dataclass, field

from overlay.screenshot import Shot

logger = logging.getLogger("cody.brain")

SYSTEM = (
    "You are Cody, a friendly on-screen helper. You see ONE screenshot of the user's "
    "current monitor and hear their question. Answer briefly in one or two sentences.\n"
    "\n"
    "POINTING RULES (critical):\n"
    "- Only point at something you can CLEARLY see in the screenshot.\n"
    "- If it is missing, hidden, or you are unsure: set found=false. Do NOT invent "
    "coordinates. Do NOT point at the taskbar, empty space, or a random control. "
    "Say you don't see it and tell the user what to open or where to look first.\n"
    "- x,y are screenshot image pixels (top-left origin) when found=true.\n"
    "- target names the element: visible text, or icon identity by appearance "
    "(logos/shapes/colors) when there is no text.\n"
    "\n"
    "MULTI-STEP:\n"
    "- If getting there needs more than one click (e.g. open a menu, then pick an "
    "item), call guide() with found=true and ordered steps. Each step has x,y,"
    "target, and a short say instruction (what to click).\n"
    "- Use point() for a single clear target. Use guide() for 2+ clicks.\n"
    "\n"
    "Call reveal() only when they clearly ask to open a file. Otherwise just reply."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "point",
            "description": (
                "Point at one visible UI element. Set found=false if it is not "
                "clearly on screen — never guess coordinates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "found": {
                        "type": "boolean",
                        "description": "true only if the target is clearly visible",
                    },
                    "target": {
                        "type": "string",
                        "description": "Visible text, or icon identity",
                    },
                    "x": {"type": "number", "description": "X in screenshot image pixels"},
                    "y": {"type": "number", "description": "Y in screenshot image pixels"},
                },
                "required": ["found"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "guide",
            "description": (
                "Multi-step click path. Use when the user must click A, then B "
                "(and optionally more). Set found=false if the first needed "
                "control is not visible."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "found": {
                        "type": "boolean",
                        "description": "true only if every step target is visible",
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target": {"type": "string"},
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "say": {
                                    "type": "string",
                                    "description": "Short spoken tip for this click",
                                },
                            },
                            "required": ["target", "x", "y"],
                        },
                    },
                },
                "required": ["found"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reveal",
            "description": "Open or reveal a file path in the OS.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
]


@dataclass
class GuideStep:
    label: str
    coords: tuple[float, float]
    say: str = ""


@dataclass
class Answer:
    reply_text: str
    target: str | None = None
    coords: tuple[float, float] | None = None
    reveal_path: str | None = None
    found: bool = True
    steps: list[GuideStep] = field(default_factory=list)


def _truthy_found(value) -> bool:
    if value is False:
        return False
    if isinstance(value, str) and value.strip().lower() in {"false", "0", "no", "none"}:
        return False
    return bool(value) if value is not None else True


def parse_tool_calls(message) -> Answer:
    ans = Answer(reply_text=(getattr(message, "content", None) or "").strip())
    for call in (getattr(message, "tool_calls", None) or []):
        name = call.function.name
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            continue
        if name == "point":
            if not _truthy_found(args.get("found", True)):
                ans.found = False
                ans.target = None
                ans.coords = None
                continue
            ans.found = True
            ans.target = args.get("target")
            if "x" in args and "y" in args:
                ans.coords = (float(args["x"]), float(args["y"]))
            else:
                # found=true without coords → treat as not found (no hallucinated move)
                ans.found = False
                ans.target = None
                ans.coords = None
        elif name == "guide":
            if not _truthy_found(args.get("found", True)):
                ans.found = False
                ans.steps = []
                ans.target = None
                ans.coords = None
                continue
            steps: list[GuideStep] = []
            for raw in args.get("steps") or []:
                if not isinstance(raw, dict) or "x" not in raw or "y" not in raw:
                    continue
                steps.append(
                    GuideStep(
                        label=str(raw.get("target") or "here"),
                        coords=(float(raw["x"]), float(raw["y"])),
                        say=str(raw.get("say") or "").strip(),
                    )
                )
            if not steps:
                ans.found = False
                continue
            ans.found = True
            ans.steps = steps
            ans.target = steps[0].label
            ans.coords = steps[0].coords
        elif name == "reveal":
            ans.reveal_path = args.get("path")
    if not ans.reply_text and (getattr(message, "tool_calls", None) or []):
        if not ans.found:
            ans.reply_text = "I don't see that on this screen."
        elif ans.steps:
            ans.reply_text = ans.steps[0].say or f"Start with {ans.steps[0].label}."
        elif ans.target:
            ans.reply_text = f"Here's {ans.target}."
        elif ans.reveal_path:
            ans.reply_text = f"Opening {ans.reveal_path}."
        else:
            ans.reply_text = "Okay."
    return ans


def _data_url(shot: Shot) -> str:
    buf = io.BytesIO()
    shot.image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _user_text(question: str, shot: Shot) -> str:
    if shot.image is None:
        return question
    w, h = shot.image.size
    return (
        f"{question.strip()}\n\n"
        f"Screenshot size: {w}x{h} pixels (top-left origin). "
        f"If found=true, x must be 0..{w - 1} and y must be 0..{h - 1} in THIS image. "
        f"If the thing is not clearly visible, found=false — do not guess."
    )


def ask(question: str, shot: Shot, api_key: str, model: str = "gpt-4o") -> Answer:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        tools=TOOLS,
        messages=[
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _user_text(question, shot)},
                    {"type": "image_url", "image_url": {"url": _data_url(shot)}},
                ],
            },
        ],
    )
    return parse_tool_calls(resp.choices[0].message)


if __name__ == "__main__":
    import os
    from pathlib import Path

    from PIL import Image

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY not set; skipping live smoke")
    else:
        png = Path("shot_debug.png")
        if not png.exists():
            print(f"{png} not found; run overlay.screenshot first")
        else:
            shot = Shot(image=Image.open(png), scale=1.0, origin=(0, 0))
            print(ask("what app is this?", shot, key))
