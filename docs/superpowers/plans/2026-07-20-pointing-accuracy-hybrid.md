# Pointing accuracy hybrid (OpenAI + UIA + grid) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Cody land on the right taskbar icon or in-app control — or refuse — using OpenAI vision plus a Windows UIA scene card and screenshot grid, without Anthropic Computer Use.

**Architecture:** Capture cursor monitor → build UIA scene card + grid-annotated image → gpt-4o returns `found` / `point` / `guide` → resolve with UIA name match first, then OCR snap-near, then model coords → optional one crop-refine call → buddy flies. Spec: [`docs/superpowers/specs/2026-07-20-pointing-accuracy-hybrid-design.md`](../specs/2026-07-20-pointing-accuracy-hybrid-design.md).

**Tech Stack:** Python 3.12, existing `openai` + `mss` + `Pillow` + `pytesseract`, `uiautomation` (already in overlay extras), PySide6/Tk overlay shells.

## Global Constraints

- OpenAI only for models (no Anthropic Computer Use).
- Windows-first; point don't click; degrade never crash.
- One primary vision call per trigger; optional refine capped at one extra call.
- Reuse `overlay/brain.py`, `pointer_resolve.py`, `screenshot.py`, `input_router.py`, `float_app.py`.
- Assert-based pytest; no new frameworks.
- Baseline pointing behavior (`found=false`, guide steps, cursor-monitor capture) must be committed before Task 1 if still dirty in the worktree.

---

### Task 0: Commit baseline pointing WIP (if dirty)

**Files:**
- Modify: existing uncommitted overlay pointing files (brain, pointer_resolve, screenshot, input_router, float_app, tk_lens, tests)

- [ ] **Step 1: Check git status**

Run: `git status -sb`

- [ ] **Step 2: If overlay pointing files are modified, commit them**

```bash
git add overlay/brain.py overlay/pointer_resolve.py overlay/screenshot.py overlay/input_router.py overlay/float_app.py overlay/tk_lens.py overlay/tests/test_brain.py overlay/tests/test_input_router.py overlay/tests/test_pointer_resolve.py
git commit -m "feat(overlay): refuse missing targets; multi-step guide; cursor-monitor point path"
```

If clean, skip. Do not commit `.claude/`.

---

### Task 1: Grid overlay + cell mapping (`grid.py`)

**Files:**
- Create: `overlay/grid.py`
- Test: `overlay/tests/test_grid.py`

**Interfaces:**
- Produces:
  - `@dataclass GridSpec: cols: int; rows: int; img_w: int; img_h: int`
  - `default_grid(img_w: int, img_h: int) -> GridSpec` — ~12 cols × 8 rows (clamp 6–16 / 4–12)
  - `cell_center(spec: GridSpec, cell: str) -> tuple[float, float] | None` — e.g. `"B7"` → image pixel center; case-insensitive
  - `annotate(image: PIL.Image.Image, spec: GridSpec) -> PIL.Image.Image` — copy with light grid + axis labels (does not mutate input)
  - `legend_text(spec: GridSpec) -> str` — one-line prompt help

- [ ] **Step 1: Write failing tests**

```python
# overlay/tests/test_grid.py
from overlay.grid import cell_center, default_grid


def test_cell_center_a1_is_top_left_bucket():
    spec = default_grid(1200, 800)
    pt = cell_center(spec, "A1")
    assert pt is not None
    assert 0 <= pt[0] < 1200 / spec.cols
    assert 0 <= pt[1] < 800 / spec.rows


def test_cell_center_rejects_bad():
    spec = default_grid(1200, 800)
    assert cell_center(spec, "ZZ9") is None
    assert cell_center(spec, "") is None
```

- [ ] **Step 2: Run to verify fail**

Run: `.\.venv\Scripts\python -m pytest overlay/tests/test_grid.py -v`  
Expected: FAIL — `ModuleNotFoundError: overlay.grid`

- [ ] **Step 3: Implement `overlay/grid.py`**

Minimal: letter columns A…, 1-based rows; draw with `ImageDraw` in pale color; `cell_center` = mid of cell rect.

- [ ] **Step 4: Tests pass + commit**

```bash
git add overlay/grid.py overlay/tests/test_grid.py
git commit -m "feat(overlay): screenshot grid overlay for pointing cells"
```

---

### Task 2: UIA scene card (`scene.py`)

**Files:**
- Create: `overlay/scene.py`
- Test: `overlay/tests/test_scene.py`
- Reference: `overlay/icon_bounds.py` (uiautomation import pattern)

**Interfaces:**
- Produces:
  - `@dataclass SceneEl: name: str; kind: str; bounds: tuple[int,int,int,int]` — bounds = left, top, right, bottom in **screen physical px**
  - `collect_scene(max_els: int = 40) -> list[SceneEl]` — taskbar-ish + foreground window; empty list on any failure
  - `format_scene(els: list[SceneEl]) -> str` — prompt block from the spec
  - `match_uia(target: str, els: list[SceneEl]) -> SceneEl | None` — exact casefold name, then substring / `_query_core`-style core token; prefer longer names

- [ ] **Step 1: Failing tests for format + match (no live UIA)**

```python
# overlay/tests/test_scene.py
from overlay.scene import SceneEl, format_scene, match_uia


def test_format_scene_lists_names():
    els = [SceneEl("Chrome", "Button", (10, 1000, 60, 1060))]
    text = format_scene(els)
    assert "Chrome" in text and "Button" in text


def test_match_uia_exact_and_core():
    els = [
        SceneEl("Google Chrome", "Button", (10, 1000, 60, 1060)),
        SceneEl("Settings", "ListItem", (100, 200, 400, 240)),
    ]
    hit = match_uia("Chrome icon", els)
    assert hit is not None and hit.name == "Google Chrome"
```

- [ ] **Step 2: Run fail → implement → pass**

`collect_scene` uses `uiautomation`; walk shallow (depth cap); skip empty names; swallow all errors → `[]`.

- [ ] **Step 3: Commit**

```bash
git add overlay/scene.py overlay/tests/test_scene.py
git commit -m "feat(overlay): UIA scene card for pointing context"
```

---

### Task 3: Resolve priority — UIA first

**Files:**
- Modify: `overlay/pointer_resolve.py`
- Modify: `overlay/tests/test_pointer_resolve.py`
- Modify: `overlay/input_router.py` (pass scene els into resolve)

**Interfaces:**
- Change `resolve(...)` to:
  - `resolve(target, coords, boxes, shot, *, uia: list | None = None, cell: str | None = None, grid_spec=None) -> tuple[int,int] | None`
- Priority per spec: UIA match → OCR snap-near → cell_center → model coords → None
- `handle_query` collects scene once; passes `uia` into resolve for each step

- [ ] **Step 1: Failing test — UIA wins over far model coords**

```python
from overlay.scene import SceneEl

def test_uia_name_wins_over_far_coords():
    uia = [SceneEl("Chrome", "Button", (100, 1000, 160, 1060))]
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    # model points at (10,10); UIA chrome is far — name match still wins
    pt = resolve("Chrome", coords=(10, 10), boxes=[], shot=shot, uia=uia)
    assert pt == (130, 1030)  # center of bounds
```

- [ ] **Step 2: Implement + update call sites + tests green**

- [ ] **Step 3: Commit**

```bash
git add overlay/pointer_resolve.py overlay/input_router.py overlay/tests/test_pointer_resolve.py overlay/tests/test_input_router.py
git commit -m "feat(overlay): prefer UIA name match when resolving points"
```

---

### Task 4: Brain — scene + grid in the ask path

**Files:**
- Modify: `overlay/brain.py`
- Modify: `overlay/tests/test_brain.py`
- Modify: `overlay/input_router.py` (`default_deps` / `handle_query` wiring)

**Interfaces:**
- `ask(question, shot, api_key, *, scene_text: str = "", grid_legend: str = "", annotated_image=None, model="gpt-4o") -> Answer`
- Extend `Answer` with `cell: str | None = None` (optional); `parse_tool_calls` reads `cell` from point/guide step args
- Point/guide tool schemas add optional `cell` string
- SYSTEM blurb: use scene list when names match; use grid cell when helpful; still `found=false` if not visible
- `handle_query`: `els = scene.collect_scene()`; `spec = default_grid(...)`; `annotated = annotate(shot.image, spec)`; ask with annotated image + `format_scene(els)` + `legend_text(spec)`; resolve with `uia=els`, `cell=...`, `grid_spec=spec`

- [ ] **Step 1: Test parse accepts cell**

```python
def test_parse_point_cell():
    ans = parse_tool_calls(_msg("Here.", [("point", {"found": True, "target": "Chrome", "cell": "B7", "x": 100, "y": 200})]))
    assert ans.cell == "B7"
    assert ans.coords == (100.0, 200.0)
```

- [ ] **Step 2: Implement wiring (keep unit tests offline — no live OpenAI)**

- [ ] **Step 3: Commit**

```bash
git add overlay/brain.py overlay/input_router.py overlay/tests/test_brain.py overlay/tests/test_input_router.py
git commit -m "feat(overlay): send UIA scene + grid image to vision brain"
```

---

### Task 5: Optional crop refine

**Files:**
- Create: `overlay/refine.py` (or functions in `brain.py` if smaller — prefer `refine.py`)
- Test: `overlay/tests/test_refine.py`
- Modify: `overlay/input_router.py` — call refine only when `found` and coords/cell coarse (define: no UIA hit AND no OCR snap AND only `cell` without fine x,y, OR flag from parse)

**Interfaces:**
- `crop_around(shot: Shot, x: float, y: float, pad: float = 0.15) -> tuple[Image, tuple[int,int,int,int]]` — image crop box in image pixels
- `refine_point(question, shot, api_key, rough_xy, target) -> tuple[float,float] | None` — second ask on crop; map back to full image coords; `None` on failure

- [ ] **Step 1: Unit-test crop math only (no network)**

```python
def test_crop_around_maps_back():
    # synthetic 200x200 image, point at center, pad 0.1 → crop origin known
    ...
```

- [ ] **Step 2: Wire into router behind a clear condition; on failure keep first-pass coords**

- [ ] **Step 3: Commit**

```bash
git add overlay/refine.py overlay/tests/test_refine.py overlay/input_router.py
git commit -m "feat(overlay): optional crop refine for coarse vision points"
```

---

### Task 6: Manual checklist + README note

**Files:**
- Modify: `overlay/README.md` — short "Pointing" subsection: scene+grid, found=false, UIA helps named controls

- [ ] **Step 1: Update README**

- [ ] **Step 2: Full tests**

Run: `.\.venv\Scripts\python -m pytest overlay/tests voice/tests -q`  
Expected: all pass

- [ ] **Step 3: Manual smoke (operator)**

- 5 taskbar icons by name  
- 5 in-app controls in Settings  
- 3 missing targets → buddy unmoved  

- [ ] **Step 4: Commit**

```bash
git add overlay/README.md
git commit -m "docs(overlay): document hybrid pointing accuracy path"
```

---

## Self-Review

**Spec coverage:** scene, grid, brain wiring, resolve priority, refine, found=false, tests/manual, non-goals → Tasks 1–6. ✔  
**Baseline WIP:** Task 0. ✔  
**Type consistency:** `SceneEl`, `GridSpec`, `Answer.cell`, resolve kwargs used across Tasks 2–5. ✔  
**Placeholders:** None — refine trigger condition stated (no UIA, no OCR snap, cell-only or coarse). ✔
