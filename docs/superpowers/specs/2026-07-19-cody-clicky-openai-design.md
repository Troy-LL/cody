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
brain.py: OpenAI vision model (gpt-4o) with a point(x, y, label) tool
     |
     +--> reply text  -> bubble next to Cody + ElevenLabs speaks it
     +--> point coords -> cursor-buddy flies there, overlay highlights
```

**Pointing mechanism:** the model is given a real **tool/function**
`point(x, y, label)` rather than clicky's text-tag parsing. The model calls it
with coordinates in the downscaled image's space; Cody inverts the transform to
true virtual-desktop pixels. Pointing is optional — a text-only reply is valid.

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
| `overlay/brain.py` | The loop: screenshot + transcript -> OpenAI call w/ `point` tool -> `{reply_text, point?}` | auth, screenshot |
| `overlay/input_router.py` | Both PTT and wake word land in one `handle_query(text)` -> brain | brain, listen, hotkey |

### Retire / demote (keep on disk, stop wiring)
`find_target.py`, `query_parse.py`, `ocr_scan.py`, `ocr_targets.py`,
`icon_bounds.py` — the deterministic OCR+match brain; the LLM replaces it.

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
| Model points off-screen | Clamp to nearest on-screen pixel. |

**Cost guard:** one vision call per trigger. No background frames, no polling.

## Testing

- `screenshot.py`: self-check draws model point back onto the screenshot.
- `brain.py`: feed a saved PNG + a text question, print the parsed
  `{reply_text, point}` — no live overlay needed.
- `auth.py`: assert-based check over each source with the others absent.
- `stt.py` / `tts.py`: smoke check against a short fixture clip / phrase.

Assert-based `demo()` / `test_*.py` per non-trivial module; no framework scaffolding.

## Platform

Windows-first (Cody's existing target). System tray replaces macOS menu bar.
Multi-monitor supported via `mss` virtual-desktop capture.
