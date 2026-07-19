# Cody clicky-style OpenAI companion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Cody's deterministic OCR-match brain with an OpenAI vision loop that sees the screen, answers by voice, and points at UI elements with OCR-perfect accuracy — a clicky-style companion running on Windows.

**Architecture:** A single per-trigger loop — screenshot (all monitors, downscaled) + Whisper transcript go to an OpenAI vision model holding a `point(target, x, y)` tool and a `reveal(path)` tool. `pointer_resolve.py` turns the model's `target` label into exact screen pixels via OCR boxes, falling back to the model's downscaled `x,y`. Reply text shows in a bubble and speaks via ElevenLabs. Credentials resolve pasted-key → env → Codex CLI.

**Tech Stack:** Python 3, `openai` SDK (chat + Whisper), `mss` (multi-monitor capture), `Pillow`, existing `pytesseract` OCR, existing ElevenLabs REST TTS, PyQt overlay (`float_app.py`/`cursor_window.py`), Tk config panel.

## Global Constraints

- Windows-first; must run on Windows 11. Multi-monitor via `mss` virtual desktop.
- No Cloudflare worker / hosted proxy. All API calls direct from the local process.
- Keys live only in gitignored `voice/config.local.json` or env — never committed.
- One vision call per user trigger. No background polling / autonomous frames.
- New deps: `openai>=1.40`, `mss>=9.0` added to `[project.optional-dependencies].overlay` in `pyproject.toml`.
- Follow existing patterns: config load/save mirrors `voice/config.py`; tests are assert-based `pytest`, no new frameworks.
- Degrade, never crash the overlay: every failure path returns a spoken/bubble message, cursor unmoved.

---

### Task 1: Add dependencies

**Files:**
- Modify: `pyproject.toml:22-31` (overlay extras)

- [ ] **Step 1: Add openai and mss to overlay extras**

In `pyproject.toml`, inside `overlay = [ ... ]`, add:

```toml
    "openai>=1.40",
    "mss>=9.0",
```

- [ ] **Step 2: Install**

Run: `.\.venv\Scripts\pip install -e ".[overlay]"`
Expected: openai and mss install without error.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore(overlay): add openai and mss deps for AI brain"
```

---

### Task 2: Credential resolver (`auth.py`)

**Files:**
- Create: `overlay/auth.py`
- Test: `overlay/tests/test_auth.py`

**Interfaces:**
- Produces:
  - `resolve_openai(environ: dict | None = None, config_path: Path | None = None, codex_path: Path | None = None) -> Credentials`
  - `@dataclass Credentials: api_key: str | None; source: str` where `source ∈ {"config","env","codex","none"}`.

- [ ] **Step 1: Write the failing test**

```python
# overlay/tests/test_auth.py
import json
from pathlib import Path
from overlay.auth import resolve_openai


def test_config_key_wins(tmp_path: Path):
    cfg = tmp_path / "config.local.json"
    cfg.write_text(json.dumps({"openai_api_key": "sk-cfg"}), encoding="utf-8")
    creds = resolve_openai(environ={"OPENAI_API_KEY": "sk-env"}, config_path=cfg, codex_path=tmp_path / "none.json")
    assert creds.api_key == "sk-cfg"
    assert creds.source == "config"


def test_env_when_no_config(tmp_path: Path):
    creds = resolve_openai(environ={"OPENAI_API_KEY": "sk-env"}, config_path=tmp_path / "none.json", codex_path=tmp_path / "none.json")
    assert creds.api_key == "sk-env"
    assert creds.source == "env"


def test_codex_fallback(tmp_path: Path):
    cdx = tmp_path / "auth.json"
    cdx.write_text(json.dumps({"OPENAI_API_KEY": "sk-codex"}), encoding="utf-8")
    creds = resolve_openai(environ={}, config_path=tmp_path / "none.json", codex_path=cdx)
    assert creds.api_key == "sk-codex"
    assert creds.source == "codex"


def test_none_found(tmp_path: Path):
    creds = resolve_openai(environ={}, config_path=tmp_path / "none.json", codex_path=tmp_path / "none.json")
    assert creds.api_key is None
    assert creds.source == "none"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: overlay.auth`.

- [ ] **Step 3: Write minimal implementation**

```python
# overlay/auth.py
"""Resolve OpenAI credentials: pasted config key -> env -> Codex CLI."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "voice" / "config.local.json"
DEFAULT_CODEX = Path.home() / ".codex" / "auth.json"


@dataclass
class Credentials:
    api_key: str | None
    source: str  # "config" | "env" | "codex" | "none"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _codex_key(path: Path) -> str | None:
    # ponytail: best-effort parse of ~/.codex/auth.json; format not a stable contract.
    data = _read_json(path)
    for key in ("OPENAI_API_KEY", "openai_api_key", "api_key"):
        val = str(data.get(key, "")).strip()
        if val:
            return val
    # Nested {"tokens": {"access_token": ...}} shape (ChatGPT-subscription OAuth).
    tokens = data.get("tokens")
    if isinstance(tokens, dict):
        val = str(tokens.get("access_token", "")).strip()
        if val:
            return val
    return None


def resolve_openai(
    environ: dict | None = None,
    config_path: Path | None = None,
    codex_path: Path | None = None,
) -> Credentials:
    env = environ if environ is not None else os.environ
    cfg = config_path if config_path is not None else DEFAULT_CONFIG
    cdx = codex_path if codex_path is not None else DEFAULT_CODEX

    cfg_key = str(_read_json(cfg).get("openai_api_key", "")).strip() if cfg.is_file() else ""
    if cfg_key:
        return Credentials(cfg_key, "config")

    env_key = str(env.get("OPENAI_API_KEY", "")).strip()
    if env_key:
        return Credentials(env_key, "env")

    if cdx.is_file():
        codex = _codex_key(cdx)
        if codex:
            return Credentials(codex, "codex")

    return Credentials(None, "none")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_auth.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add overlay/auth.py overlay/tests/test_auth.py
git commit -m "feat(overlay): OpenAI credential resolver with Codex fallback"
```

---

### Task 3: Screen capture + coord transform (`screenshot.py`)

**Files:**
- Create: `overlay/screenshot.py`
- Test: `overlay/tests/test_screenshot.py`

**Interfaces:**
- Produces:
  - `@dataclass Shot: image: PIL.Image.Image; scale: float; origin: tuple[int,int]` — `image` is the downscaled virtual-desktop PNG; `origin` is the virtual desktop's top-left in screen coords (can be negative with left monitors); `scale = downscaled_px / screen_px`.
  - `capture(max_width: int = 1536) -> Shot`
  - `to_screen(shot: Shot, x: float, y: float) -> tuple[int,int]` — invert a point in downscaled-image space to absolute screen pixels.

- [ ] **Step 1: Write the failing test**

```python
# overlay/tests/test_screenshot.py
from overlay.screenshot import Shot, to_screen


def test_to_screen_inverts_scale_and_origin():
    shot = Shot(image=None, scale=0.5, origin=(-1920, 0))
    # image point (100, 40) at 0.5 scale -> (200, 80) desktop px, minus origin.
    assert to_screen(shot, 100, 40) == (-1920 + 200, 0 + 80)


def test_to_screen_rounds():
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    assert to_screen(shot, 33, 33) == (66, 66)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_screenshot.py -v`
Expected: FAIL — `ModuleNotFoundError: overlay.screenshot`.

- [ ] **Step 3: Write minimal implementation**

```python
# overlay/screenshot.py
"""Capture all monitors as one downscaled image; invert model coords to screen px."""
from __future__ import annotations

from dataclasses import dataclass

import mss
from PIL import Image


@dataclass
class Shot:
    image: Image.Image | None
    scale: float           # downscaled_px / screen_px
    origin: tuple[int, int]  # virtual-desktop top-left in screen coords


def to_screen(shot: Shot, x: float, y: float) -> tuple[int, int]:
    sx = shot.origin[0] + round(x / shot.scale)
    sy = shot.origin[1] + round(y / shot.scale)
    return (sx, sy)


def capture(max_width: int = 1536) -> Shot:
    with mss.mss() as sct:
        mon = sct.monitors[0]  # [0] = full virtual desktop across all monitors
        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
    origin = (mon["left"], mon["top"])
    scale = 1.0
    if img.width > max_width:
        scale = max_width / img.width
        img = img.resize((max_width, round(img.height * scale)))
    return Shot(image=img, scale=scale, origin=origin)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_screenshot.py -v`
Expected: 2 passed.

- [ ] **Step 5: Manual coord self-check (run once, eyeball)**

Add a `if __name__ == "__main__":` block that captures, marks the image center mapped back, and saves:

```python
if __name__ == "__main__":
    shot = capture()
    print("scale", shot.scale, "origin", shot.origin, "img", shot.image.size)
    cx, cy = shot.image.width / 2, shot.image.height / 2
    print("center image ->", to_screen(shot, cx, cy))
    shot.image.save("shot_debug.png")
```

Run: `.\.venv\Scripts\python -m overlay.screenshot`
Expected: prints a screen coord near the physical center of your desktop; `shot_debug.png` shows all monitors stitched.

- [ ] **Step 6: Commit**

```bash
git add overlay/screenshot.py overlay/tests/test_screenshot.py
git commit -m "feat(overlay): multi-monitor capture with coord inversion"
```

---

### Task 4: Speech-to-text (`stt.py`)

**Files:**
- Create: `overlay/stt.py`
- Test: `overlay/tests/test_stt.py`

**Interfaces:**
- Consumes: `overlay.auth.Credentials`.
- Produces:
  - `record_clip(seconds: float, samplerate: int = 16000) -> bytes` — WAV bytes from the mic (uses `sounddevice`, already a dep).
  - `transcribe(wav_bytes: bytes, api_key: str) -> str` — Whisper text, `""` on empty/failure.

- [ ] **Step 1: Write the failing test** (parse path only — no live mic/network)

```python
# overlay/tests/test_stt.py
from overlay import stt


def test_transcribe_empty_bytes_returns_empty():
    assert stt.transcribe(b"", api_key="sk-x") == ""


def test_wav_header(monkeypatch):
    # record_clip must emit a valid RIFF/WAVE header.
    import numpy as np
    monkeypatch.setattr(stt, "_read_frames", lambda s, r: np.zeros((r, 1), dtype="int16"))
    data = stt.record_clip(0.1, samplerate=16000)
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_stt.py -v`
Expected: FAIL — `ModuleNotFoundError: overlay.stt`.

- [ ] **Step 3: Write minimal implementation**

```python
# overlay/stt.py
"""Record a mic clip and transcribe via OpenAI Whisper."""
from __future__ import annotations

import io
import logging
import wave

logger = logging.getLogger("cody.stt")


def _read_frames(seconds: float, samplerate: int):
    import sounddevice as sd
    frames = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    return frames


def record_clip(seconds: float, samplerate: int = 16000) -> bytes:
    frames = _read_frames(seconds, samplerate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(frames.tobytes())
    return buf.getvalue()


def transcribe(wav_bytes: bytes, api_key: str) -> str:
    if not wav_bytes:
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        audio = io.BytesIO(wav_bytes)
        audio.name = "clip.wav"
        resp = client.audio.transcriptions.create(model="whisper-1", file=audio)
        return (resp.text or "").strip()
    except Exception:
        logger.warning("whisper transcribe failed", exc_info=True)
        return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_stt.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add overlay/stt.py overlay/tests/test_stt.py
git commit -m "feat(overlay): mic clip recording + Whisper transcription"
```

---

### Task 5: Pointer resolver (`pointer_resolve.py`)

**Files:**
- Create: `overlay/pointer_resolve.py`
- Test: `overlay/tests/test_pointer_resolve.py`
- Reference (reuse OCR): `overlay/ocr_scan.py`, `overlay/icon_bounds.py`

**Interfaces:**
- Consumes: `overlay.screenshot.Shot`, `to_screen`; an OCR box list `list[Box]` where `Box` has `.text: str` and `.center: tuple[int,int]` in **screen** pixels (adapt to the actual return type of `ocr_scan` — inspect it first and map into this shape).
- Produces:
  - `resolve(target: str | None, coords: tuple[float,float] | None, boxes: list, shot: Shot) -> tuple[int,int] | None` — screen pixel to point at, or `None` if nothing resolvable.

- [ ] **Step 1: Write the failing test**

```python
# overlay/tests/test_pointer_resolve.py
from dataclasses import dataclass
from overlay.screenshot import Shot
from overlay.pointer_resolve import resolve


@dataclass
class FakeBox:
    text: str
    center: tuple[int, int]


def test_ocr_match_wins_over_coords():
    boxes = [FakeBox("Save", (500, 300)), FakeBox("Cancel", (600, 300))]
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    # target matches OCR -> exact box center, ignoring coords guess.
    assert resolve("save", coords=(10, 10), boxes=boxes, shot=shot) == (500, 300)


def test_coords_fallback_when_no_ocr_match():
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    # no matching box -> invert coords: (10,10)/0.5 = (20,20)
    assert resolve("nonexistent", coords=(10, 10), boxes=[], shot=shot) == (20, 20)


def test_none_when_nothing():
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve(None, coords=None, boxes=[], shot=shot) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_pointer_resolve.py -v`
Expected: FAIL — `ModuleNotFoundError: overlay.pointer_resolve`.

- [ ] **Step 3: Write minimal implementation**

```python
# overlay/pointer_resolve.py
"""Turn a model target label into exact screen pixels via OCR; else model coords."""
from __future__ import annotations

from overlay.screenshot import Shot, to_screen


def _match(target: str, boxes: list):
    want = target.strip().lower()
    if not want:
        return None
    # exact, then substring (longest text first to prefer specific labels).
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_pointer_resolve.py -v`
Expected: 3 passed.

- [ ] **Step 5: Wire real OCR boxes**

Read `overlay/ocr_scan.py` to learn its actual scan return type. Add an adapter `boxes_for(shot) -> list` in `pointer_resolve.py` that runs the existing OCR over `shot.image` (or a fresh full-res grab) and maps each result into an object with `.text` and screen-pixel `.center`. If OCR centers come back in downscaled-image space, convert with `to_screen`. Add one assert-based test with a synthetic OCR result confirming the adapter yields screen-space centers.

- [ ] **Step 6: Commit**

```bash
git add overlay/pointer_resolve.py overlay/tests/test_pointer_resolve.py
git commit -m "feat(overlay): OCR-assisted pointer resolution with coord fallback"
```

---

### Task 6: The brain (`brain.py`)

**Files:**
- Create: `overlay/brain.py`
- Test: `overlay/tests/test_brain.py`

**Interfaces:**
- Consumes: `overlay.auth.Credentials`, `overlay.screenshot.Shot`.
- Produces:
  - `@dataclass Answer: reply_text: str; target: str | None; coords: tuple[float,float] | None; reveal_path: str | None`
  - `ask(question: str, shot: Shot, api_key: str, model: str = "gpt-4o") -> Answer`
  - `parse_tool_calls(message) -> Answer` — pure function turning an OpenAI chat message into `Answer` (tested directly; no network).

- [ ] **Step 1: Write the failing test** (parse layer only)

```python
# overlay/tests/test_brain.py
import json
from types import SimpleNamespace
from overlay.brain import parse_tool_calls


def _msg(content, tools):
    calls = [SimpleNamespace(function=SimpleNamespace(name=n, arguments=json.dumps(a))) for n, a in tools]
    return SimpleNamespace(content=content, tool_calls=calls or None)


def test_parse_point_target():
    ans = parse_tool_calls(_msg("Here is Save.", [("point", {"target": "Save", "x": 12, "y": 34})]))
    assert ans.reply_text == "Here is Save."
    assert ans.target == "Save"
    assert ans.coords == (12.0, 34.0)


def test_parse_text_only():
    ans = parse_tool_calls(_msg("Just text.", []))
    assert ans.reply_text == "Just text."
    assert ans.target is None and ans.coords is None and ans.reveal_path is None


def test_parse_reveal():
    ans = parse_tool_calls(_msg("Opening it.", [("reveal", {"path": "C:/x.txt"})]))
    assert ans.reveal_path == "C:/x.txt"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_brain.py -v`
Expected: FAIL — `ModuleNotFoundError: overlay.brain`.

- [ ] **Step 3: Write minimal implementation**

```python
# overlay/brain.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_brain.py -v`
Expected: 3 passed.

- [ ] **Step 5: Live smoke (run once with a real key + saved PNG)**

With `OPENAI_API_KEY` set, add a `__main__` block that loads `shot_debug.png` into a `Shot` and asks "what app is this?"; print the `Answer`. Confirms auth + vision + parse end-to-end.

- [ ] **Step 6: Commit**

```bash
git add overlay/brain.py overlay/tests/test_brain.py
git commit -m "feat(overlay): OpenAI vision brain with point/reveal tools"
```

---

### Task 7: OpenAI key in config + panel field

**Files:**
- Modify: `voice/config.py:112-132` (extend `save_api_key` / add `save_openai_key`)
- Modify: `overlay/tk_lens.py` (the config panel — add OpenAI key field + Save)
- Test: `voice/tests/test_config.py` (add cases)

**Interfaces:**
- Produces: `voice.config.save_openai_key(api_key: str, path: Path | None = None) -> None` writing `openai_api_key` into `config.local.json`, preserving other fields. (Matches the `openai_api_key` key `auth.resolve_openai` reads.)

- [ ] **Step 1: Write the failing test**

```python
# add to voice/tests/test_config.py
import json
from pathlib import Path
from voice.config import save_openai_key


def test_save_openai_key_preserves_fields(tmp_path: Path):
    p = tmp_path / "config.local.json"
    p.write_text(json.dumps({"api_key": "eleven", "provider": "elevenlabs"}), encoding="utf-8")
    save_openai_key("sk-abc", path=p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["openai_api_key"] == "sk-abc"
    assert data["api_key"] == "eleven"  # untouched
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest voice/tests/test_config.py::test_save_openai_key_preserves_fields -v`
Expected: FAIL — `ImportError: cannot import name 'save_openai_key'`.

- [ ] **Step 3: Write minimal implementation**

```python
# voice/config.py — add near save_api_key
def save_openai_key(api_key: str, path: Path | None = None) -> None:
    """Write openai_api_key into gitignored config.local.json (keeps other fields)."""
    cfg_path = path if path is not None else CONFIG_PATH
    data: dict[str, Any] = {}
    if cfg_path.is_file():
        try:
            loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (OSError, json.JSONDecodeError):
            data = {}
    data["openai_api_key"] = str(api_key).strip()
    cfg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest voice/tests/test_config.py::test_save_openai_key_preserves_fields -v`
Expected: PASS.

- [ ] **Step 5: Add the panel field**

In `overlay/tk_lens.py`, next to the existing ElevenLabs key field, add an "OpenAI key" entry + Save button calling `save_openai_key(entry.get())`, and a status label showing `auth.resolve_openai().source` (`Using: config / env / codex / none`). Follow the existing widget style in that file.

- [ ] **Step 6: Commit**

```bash
git add voice/config.py voice/tests/test_config.py overlay/tk_lens.py
git commit -m "feat(overlay): OpenAI key config store + panel field"
```

---

### Task 8: Input router (`input_router.py`)

**Files:**
- Create: `overlay/input_router.py`
- Test: `overlay/tests/test_input_router.py`
- Reference: `overlay/hotkey.py` (PTT), `overlay/listen.py` (wake word)

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `handle_query(question: str, deps: Deps) -> Outcome` — orchestrates capture → brain → resolve; returns what the overlay should do.
  - `@dataclass Outcome: reply_text: str; point: tuple[int,int] | None; reveal_path: str | None`
  - `@dataclass Deps` bundling injectable callables: `capture`, `ask`, `boxes_for`, `resolve` (so the test injects fakes — no network/screen).

- [ ] **Step 1: Write the failing test**

```python
# overlay/tests/test_input_router.py
from overlay.input_router import handle_query, Deps
from overlay.brain import Answer
from overlay.screenshot import Shot


def _deps(answer, point):
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    return Deps(
        capture=lambda: shot,
        ask=lambda q, s: answer,
        boxes_for=lambda s: [],
        resolve=lambda target, coords, boxes, s: point,
    )


def test_query_with_point():
    out = handle_query("where is save", _deps(Answer("Here.", target="Save"), (500, 300)))
    assert out.reply_text == "Here." and out.point == (500, 300)


def test_query_text_only():
    out = handle_query("what is this", _deps(Answer("A browser."), None))
    assert out.reply_text == "A browser." and out.point is None


def test_empty_question_short_circuits():
    out = handle_query("", _deps(Answer("should not run"), (1, 1)))
    assert out.reply_text == "Didn't catch that." and out.point is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_input_router.py -v`
Expected: FAIL — `ModuleNotFoundError: overlay.input_router`.

- [ ] **Step 3: Write minimal implementation**

```python
# overlay/input_router.py
"""Single entry for PTT and wake-word queries: capture -> brain -> resolve."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


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
    answer = deps.ask(question, shot)
    point = None
    if answer.target or answer.coords:
        boxes = deps.boxes_for(shot)
        point = deps.resolve(answer.target, answer.coords, boxes, shot)
    return Outcome(answer.reply_text or "", point, answer.reveal_path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_input_router.py -v`
Expected: 3 passed.

- [ ] **Step 5: Build the real Deps factory**

Add `default_deps(api_key: str) -> Deps` wiring `screenshot.capture`, `lambda q,s: brain.ask(q, s, api_key)`, `pointer_resolve.boxes_for`, `pointer_resolve.resolve`. No test needed (pure wiring).

- [ ] **Step 6: Commit**

```bash
git add overlay/input_router.py overlay/tests/test_input_router.py
git commit -m "feat(overlay): unify PTT + wake word into one query router"
```

---

### Task 9: Wire the overlay + triggers + speech

**Files:**
- Modify: the active overlay entry (`overlay/float_app.py` or `overlay/tk_lens.py` — whichever is the running companion; confirm via `pyproject.toml` `cody-overlay` script = `overlay.tk_lens:main`).
- Reference: `overlay/hotkey.py`, `overlay/listen.py`, `overlay/cursor_window.py`, `voice/speak.py`.

**Interfaces:**
- Consumes: `input_router.handle_query`, `input_router.default_deps`, `stt.record_clip`, `stt.transcribe`, `auth.resolve_openai`, `voice.speak.speak` (existing ElevenLabs), cursor-move from `cursor_window`.

- [ ] **Step 1: Push-to-talk trigger**

Register `Ctrl+Shift+Space` via `hotkey.py`. On press: `record_clip(4.0)` → `transcribe(...)` → `handle_query(...)`. Run in a worker thread; marshal UI updates back to the main loop (follow the existing `after(0, ...)` / Qt signal pattern in the file).

- [ ] **Step 2: Wake-word trigger**

On `listen.py` wake detection, record a follow-up clip, same `handle_query` path. Both triggers call one shared `_run_query(text)`.

- [ ] **Step 3: Apply the Outcome**

`_run_query` result:
- Always show `reply_text` in the bubble and `speak(reply_text)` (ElevenLabs); skip audio silently if TTS unavailable.
- If `point` is not None: move the cursor-buddy there (`cursor_window` move) + highlight.
- If `reveal_path`: call `reveal.reveal(reveal_path)`.
- If `resolve_openai().source == "none"`: bubble "Add an OpenAI key in the panel." and skip the model call entirely (guard before capture).

- [ ] **Step 4: Manual end-to-end check**

Run: `.\.venv\Scripts\python -m overlay`
- Paste OpenAI + ElevenLabs keys in the panel, Save.
- Hold Ctrl+Shift+Space, ask "where's the address bar?" → cursor flies to it, Cody speaks.
- Ask "what am I looking at?" → text-only reply, cursor unmoved.
- Clear the key → ask again → "Add an OpenAI key in the panel," no crash.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(overlay): wire AI brain to PTT + wake word, cursor, and speech"
```

---

### Task 10: Retire dead brain wiring + docs

**Files:**
- Modify: `overlay/README.md`
- No deletion of `find_target.py` / `query_parse.py` — leave on disk, just unreferenced.

- [ ] **Step 1: Confirm nothing imports the retired modules**

Run: `grep -rn "find_target\|query_parse" overlay --include=*.py`
Expected: no imports in the live path (only their own files / old tests). If a live file still imports them, remove that import.

- [ ] **Step 2: Update README**

Rewrite `overlay/README.md`: Cody now sees the screen and answers via OpenAI; keys (OpenAI + ElevenLabs) in the panel; PTT `Ctrl+Shift+Space` + "Hey Cody"; OCR gives pixel-perfect pointing; no Cloudflare worker needed.

- [ ] **Step 3: Full test run**

Run: `.\.venv\Scripts\python -m pytest overlay/tests voice/tests -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add overlay/README.md
git commit -m "docs(overlay): document OpenAI companion; retire OCR-match brain"
```

---

## Self-Review

**Spec coverage:**
- Tray/overlay/cursor-buddy → Task 9 (reuses existing Qt overlay). ✔
- PTT + wake word → Tasks 8, 9. ✔
- Whisper STT → Task 4. ✔
- OpenAI vision brain + point/reveal tools → Task 6. ✔
- Hybrid OCR-assisted pointing → Task 5. ✔
- Auth key→env→Codex → Task 2; panel + config store → Task 7. ✔
- Multi-monitor capture + coord inversion → Task 3. ✔
- ElevenLabs TTS → Task 9 (reuses `voice/speak.py`). ✔
- Error degradation → Tasks 8 (empty/none), 9 (no-key guard, TTS skip). ✔
- No Cloudflare, one call per trigger → Global Constraints + Task 9. ✔
- Improvements (act via reveal, wake word) → Tasks 6, 9. ✔

**Placeholder scan:** Steps that touch existing UI files (Task 7 Step 5, Task 9) describe integration against files whose exact current widget code the implementer must read first — these are genuine "follow existing pattern" integrations, not logic placeholders; all pure-logic modules (auth, screenshot, stt, pointer_resolve, brain, input_router) ship complete code + tests.

**Type consistency:** `Answer(reply_text, target, coords, reveal_path)` consistent across Tasks 6/8. `Shot(image, scale, origin)` + `to_screen` consistent across Tasks 3/5/8. `resolve_openai().source` values consistent across Tasks 2/7/9. Config key `openai_api_key` consistent across Tasks 2/7. ✔
