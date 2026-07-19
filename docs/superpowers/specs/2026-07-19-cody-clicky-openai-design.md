# Cody as a clicky-style AI companion, on OpenAI, on Windows

**Date:** 2026-07-19
**Branch:** `feat/clicky-openai-brain`
**Status:** Approved design

## Goal

Turn Cody from a deterministic OCR-match helper into a clicky-style AI learning
companion ([farzaa/clicky](https://github.com/farzaa/clicky)): an assistant that
lives next to the cursor, sees the screen, listens, replies out loud, and points
at UI elements — but powered by **OpenAI** instead of Anthropic, running on
**Windows**, with **no Cloudflare worker**.

The core change is one substitution: replace the rule-based OCR+string-match
brain with an LLM vision loop. Cody already has the overlay, cursor window, mic,
TTS, tray, and hotkey plumbing; this rewires them around an AI brain.

## Non-goals

- No Cloudflare worker / hosted proxy. Cody is a local personal dev tool; the
  user's own key stays in a gitignored local config. A proxy only matters when
  distributing to strangers who must not see the key — not now.
- No autonomous/background screen polling. One vision call per user trigger.
- No deletion of the old OCR brain in this work — demote and stop wiring it,
  keep on disk during migration.

## User-facing behavior

1. Cody sits in the **Windows system tray** (clicky's macOS menu bar equivalent)
   and as a small Qt cursor-buddy next to the mouse.
2. User triggers a query two ways (both supported):
   - **Push-to-talk:** hold `Ctrl+Shift+Space`, speak, release.
   - **"Hey Cody" wake word:** existing always-listening path.
3. Cody grabs a screenshot of all monitors + the transcribed question.
4. OpenAI vision model replies with text and, optionally, a screen point.
5. The cursor-buddy flies to the point, the pointer overlay highlights it, a
   text bubble appears next to Cody, and ElevenLabs speaks the reply.

## Architecture — the loop

```
[Tray icon] — always available, no window required
     |
Trigger (either):
  - Push-to-talk: hold Ctrl+Shift+Space -> record clip -> Whisper -> text
  - "Hey Cody" wake word: listen.py -> record segment -> Whisper -> text
     |
     v
screenshot.py: grab all monitors -> one image, downscale, keep scale/offset map
     |
     v
brain.py: OpenAI vision model (gpt-4o) with a point(target, x, y) tool
     |
     +--> reply text  -> bubble next to Cody + ElevenLabs speaks it
     +--> target/coords -> pointer_resolve.py: OCR box for target (exact),
          else invert model x,y -> cursor-buddy flies there, overlay highlights
```

**Pointing mechanism — hybrid, OCR-assisted (Cody's edge over clicky):**
clicky asks the LLM to guess pixel coordinates off a downscaled screenshot —
imprecise (often tens of px off) and it re-pays vision tokens for spatial
reasoning the model is weak at. Cody already produces exact word/element
bounding boxes via OCR, so it points better and cheaper:

1. The model is given a tool `point(target, x, y)` where `target` is the
   **on-screen text/label** it wants to indicate (e.g. "Save", "API key field").
   `x, y` are an optional fallback guess in downscaled-image space.
2. Cody resolves the point in this order:
   - **OCR match:** look up `target` in the OCR box list -> exact pixel box.
     Pixel-perfect, deterministic, free.
   - **Model coords fallback:** if OCR finds no text match (icons, images,
     ambiguous), invert the model's `x, y` from image space to screen pixels.
3. Pointing is optional — a text-only reply is valid.

## Components

### Reuse (already built)
| File | Role |
|------|------|
| `overlay/float_app.py` / `overlay/cursor_window.py` | Qt cursor-buddy + transparent pointer overlay |
| `overlay/listen.py` | Wake-word mic path ("Hey Cody") |
| `overlay/hotkey.py` | Global hotkey registration (reused for push-to-talk) |
| `reveal/` | Open/reveal a file if the model requests it |
| voice config panel + `voice/config.local.json` | Gitignored key store (add OpenAI key field) |

### New — the AI brain (small, single-purpose files)
| File | Purpose | Depends on |
|------|---------|-----------|
| `overlay/auth.py` | Resolve credentials (pasted key -> env -> Codex CLI), return ready OpenAI client + source label | — |
| `overlay/screenshot.py` | All-monitors grab via `mss`, downscale, keep transform to invert model coords -> screen pixels | mss |
| `overlay/stt.py` | Record clip (PTT hold or wake segment) -> Whisper -> text | OpenAI key |
| `overlay/tts.py` | Text -> ElevenLabs audio -> play (may partly exist in `voice/`) | ElevenLabs key |
| `overlay/pointer_resolve.py` | Resolve a model `target` label to exact screen pixels via OCR boxes; fall back to model `x,y` | ocr_scan, icon_bounds, screenshot |
| `overlay/brain.py` | The loop: screenshot + transcript -> OpenAI call w/ `point(target,x,y)` tool -> `{reply_text, target?, coords?}` | auth, screenshot |
| `overlay/input_router.py` | Both PTT and wake word land in one `handle_query(text)` -> brain -> pointer_resolve | brain, pointer_resolve, listen, hotkey |

### Repurpose (Cody's original code, kept alive)
- `ocr_scan.py`, `ocr_targets.py`, `icon_bounds.py` — **no longer the brain**;
  demoted to the **pointing precision layer** behind `pointer_resolve.py`. This
  is Cody's edge over clicky (pixel-perfect, free pointing).
- `reveal/` — lets Cody *act* (open/reveal a file), not just point. clicky lacks
  this. Exposed to the model as an optional `reveal(path)` tool.
- `listen.py` wake word — hands-free mode clicky does not have.

### Retire (keep on disk, stop wiring)
`find_target.py`, `query_parse.py` — the hardcoded query parser + Notion-demo
target resolver; the LLM replaces this layer.

## Auth — key primary, Codex fallback

`auth.py` resolves in order and reports which source won (shown in the panel):

1. **Pasted OpenAI key** — panel field, saved to gitignored
   `voice/config.local.json`. Load-bearing.
2. **`OPENAI_API_KEY` env var** — standard dev-tool convention. Load-bearing.
3. **Codex CLI fallback** — read `~/.codex/auth.json`. Plain key -> use directly;
   ChatGPT-subscription OAuth token -> use best-effort.

**Honesty flag:** the Codex path is fragile. Codex's file layout / token format
is not a stable public contract and may drift between versions. Key and env are
the reliable paths; Codex is best-effort convenience. The implementation plan
must verify the current `~/.codex/auth.json` shape before committing to a parser.
Panel shows: "Using: pasted key / env / Codex CLI / none".

## Improvements over clicky (from Cody's original code)

- **Pixel-perfect, cheaper pointing** via OCR box resolution instead of the
  model guessing coordinates (see hybrid pointing above).
- **Cody can act**, not just point — `reveal(path)` tool opens/reveals files.
- **Hands-free wake word** in addition to push-to-talk.

## Coordinate mapping

- `screenshot.py` stitches all monitors into one image via `mss`, recording each
  monitor's pixel offset and the downscale factor.
- Model receives the downscaled image, calls `point(x, y)` in image space.
- Cody inverts: image coords -> full-res virtual-desktop coords -> move the real
  cursor to the correct monitor.
- Multi-monitor is where bugs hide: `screenshot.py` gets a runnable self-check
  that draws the returned point back onto the screenshot to eyeball accuracy.

## Error handling — degrade, never crash the overlay

| Failure | Behavior |
|---------|----------|
| No credentials | Bubble: "Add an OpenAI key in the panel." No calls. |
| OpenAI call fails / times out | Bubble + spoken: "I couldn't reach the model." Cursor unmoved. |
| Whisper returns empty | "Didn't catch that." No model call. |
| Model replies, no `point` | Show/speak text only — pointing is optional. |
| ElevenLabs fails | Show text bubble, skip audio. Never block on TTS. |
| OCR finds no match for `target` | Fall back to model `x,y`; if none, speak text only. |
| Model points off-screen | Clamp to nearest on-screen pixel. |

**Cost guard:** one vision call per trigger. No background frames, no polling.

## Testing

- `screenshot.py`: self-check draws model point back onto the screenshot.
- `brain.py`: feed a saved PNG + a text question, print the parsed
  `{reply_text, target, coords}` — no live overlay needed.
- `pointer_resolve.py`: given a target label + a fixture OCR box list, assert it
  returns the right box; assert model-coord fallback fires when no OCR match.
- `auth.py`: assert-based check over each source with the others absent.
- `stt.py` / `tts.py`: smoke check against a short fixture clip / phrase.

Assert-based `demo()` / `test_*.py` per non-trivial module; no framework scaffolding.

## Platform

Windows-first (Cody's existing target). System tray replaces macOS menu bar.
Multi-monitor supported via `mss` virtual-desktop capture.
