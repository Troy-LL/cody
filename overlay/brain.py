"""OpenAI vision loop: screenshot + question -> reply text + optional point/reveal."""
from __future__ import annotations

import base64
import io
import json
import logging
from dataclasses import dataclass

from overlay.screenshot import Shot

logger = logging.getLogger("cody.brain")

SYSTEM = (
    "You are Cody, a friendly on-screen helper. You see the user's screen and hear "
    "their question. Answer briefly and conversationally in one or two sentences. "
    "When the user asks where something is, call point() with the on-screen text of "
    "the element as `target` (and your best-guess x,y in image pixels as a fallback). "
    "Call reveal() only when they clearly ask to open a file. Otherwise just reply."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "point",
            "description": "Point the cursor at an on-screen element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Visible text/label of the element"},
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                },
                "required": ["target"],
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
class Answer:
    reply_text: str
    target: str | None = None
    coords: tuple[float, float] | None = None
    reveal_path: str | None = None


def parse_tool_calls(message) -> Answer:
    ans = Answer(reply_text=(getattr(message, "content", None) or "").strip())
    for call in (getattr(message, "tool_calls", None) or []):
        name = call.function.name
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            continue
        if name == "point":
            ans.target = args.get("target")
            if "x" in args and "y" in args:
                ans.coords = (float(args["x"]), float(args["y"]))
        elif name == "reveal":
            ans.reveal_path = args.get("path")
    if not ans.reply_text and (getattr(message, "tool_calls", None) or []):
        if ans.target:
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
                    {"type": "text", "text": question},
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
