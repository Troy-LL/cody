# Cody pointing accuracy — hybrid OpenAI + UIA design

**Date:** 2026-07-20  
**Status:** Approved design  
**Branch target:** `main` (follow-up to clicky OpenAI brain)

## Goal

When the user asks Cody to point at something — a **taskbar/desktop icon** or an **in-app control** — Cody either lands on the right spot or **refuses**. It must never invent a point on the taskbar or empty chrome.

This design is **accuracy-first**. Guidance polish, full screen memory, and buddy UX redesign are later tracks; this spec only keeps the multi-step `guide()` path already introduced and makes its targeting trustworthy.

## Constraints

- **OpenAI only** for models (no Anthropic Computer Use).
- **Windows-first**; reuse existing overlay stack (`float_app` / `tk_lens`, `brain`, `pointer_resolve`, `screenshot`).
- **Point, don't click** — Cody flies the buddy; the user clicks.
- **Degrade, never crash** — UIA missing → vision+OCR only.
- Baseline already shipped (uncommitted or recent): cursor-monitor capture, image dimensions in prompt, model-coords primary + OCR snap, `found=false`, multi-step `guide()`.

## Architecture

One query loop:

```
transcript
  → capture cursor monitor (mss)
  → scene card (UIA: taskbar + foreground window)
  → grid overlay on screenshot copy
  → OpenAI vision (gpt-4o) + scene card + grid legend
  → found=false | point | guide steps (image pixels / cells)
  → resolve: UIA name → OCR snap-near → model coords
  → optional crop refine (second OpenAI call) if coarse/low confidence
  → Outcome → buddy fly (no OS cursor warp)
```

## Components

| Unit | Responsibility |
|------|----------------|
| `overlay/scene.py` (new) | Collect UIA elements for taskbar + foreground window: name, control type, screen bounds. Cap ~40. Pure data for the prompt; no AI. |
| `overlay/grid.py` (new) | Draw a light row/column legend on a screenshot copy; map cell id ↔ image pixel center. |
| `overlay/brain.py` | Send image + scene card text + grid legend. Tools: `point`, `guide`, `reveal`. Require `found`. Prefer cell id + fine x,y when pointing. |
| `overlay/pointer_resolve.py` | Resolve order: (1) UIA fuzzy/exact name → bounds center (2) OCR snap within SNAP_PX of model point (3) model image coords via `to_screen`. Honor `found=false`. |
| `overlay/input_router.py` | Wire scene+grid into ask; pass UIA list into resolve; keep multi-step `Outcome.steps`. |
| `overlay/float_app.py` / `tk_lens.py` | Unchanged contract: fly tip to resolved points; sequence guide steps; no move when no points. |

### Scene card (prompt shape)

Plain text block, e.g.:

```
Scene (accessibility, may be incomplete):
- taskbar: "Chrome" Button @ (120,1040)-(180,1080)
- taskbar: "File Explorer" Button @ ...
- window "Settings": "System" ListItem @ ...
- window "Settings": "Bluetooth & devices" ...
```

Icons without UIA names still rely on vision.

### Grid

- Divisions chosen for readability (~12×8 or similar on the downscaled image).
- Prompt: "Screenshot has grid A1…; you may return cell (e.g. B7) and optional fine x,y inside the image."
- Resolver maps cell → image center, then `to_screen`.

### Optional refine pass

If the model returns only a cell (or confidence-equivalent: large uncertainty), crop that cell with padding, one second OpenAI call for fine x,y in crop space, then map back. Still OpenAI-only. Skip if first pass already has precise coords and a UIA/OCR snap succeeded.

## Resolve priority (normative)

1. If `found=false` → no point, speak reply only.  
2. Else if UIA name matches query/target (exact, then fuzzy / core-token) → center of that element's screen bounds.  
3. Else if model coords present and OCR label matches nearby (SNAP_PX) → OCR center.  
4. Else if model coords (or cell→coords) present → `to_screen` + clamp.  
5. Else → no point (speak that Cody couldn't lock a target).

Never prefer a far OCR or UIA hit over a nearby model guess without a name match.

## Error handling

| Failure | Behavior |
|---------|----------|
| UIA / uiautomation import or query fails | Empty scene card; continue |
| `found=false` | Bubble + TTS reason; buddy unmoved |
| Refine fails | Use first-pass coords, or refuse if none |
| Guide step N fails to resolve | Fly steps 1..N-1; stop; say what's missing for N |
| OpenAI error | Existing "I couldn't reach the model." path |

## Testing

- **Unit:** grid cell↔pixel; scene parsing/cap; resolve priority matrix; `found=false` short-circuit; refine crop math.  
- **Fixture:** fake scene + Answer → expected screen point.  
- **Manual:** ≥5 taskbar/desktop icons; ≥5 in-app controls in a common app (e.g. Settings); ≥3 missing-target prompts must not move the buddy.

## Non-goals

- Anthropic Computer Use or non-OpenAI vision vendors  
- Autonomous clicking / computer-use agents  
- Background screen polling or persistent world model  
- Large buddy personality / visual redesign (separate UX track)  
- Expanding multi-step coaching pedagogy beyond trustworthy `guide()` targeting  

## Success criteria

- Wrong-target "taskbar stabs" on missing items are rare (manual: 0/3 on missing prompts).  
- Taskbar/desktop icon requests hit the named icon or refuse.  
- In-app named controls prefer UIA bounds when available.  
- Still one primary vision call per trigger; refine is optional and capped at one extra call.

## Roadmap after this spec

1. **Guidance** — clearer step copy, wait-for-user-click, highlight rings.  
2. **Context** — short-lived scene cache across turns.  
3. **UX** — bubble/timing/animation polish.
