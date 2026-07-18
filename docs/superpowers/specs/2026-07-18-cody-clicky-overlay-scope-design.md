# Cody = Clicky with a desktop-following cursor — scope redesign

**Date:** 2026-07-18  
**Status:** Draft — awaiting user review before `spec.md` / OpenSpec updates  
**Decision locked in brainstorm:** Approach **A** (transparent always-on-top overlay) + product option **1** (behavior like Clicky; Codex-powered matcher; PySide shell)

## 1. Goal

Ship a Windows desktop demo where Cody feels like Clicky: the user asks in natural / Taglish language, Cody finds the file, then a **branded cursor on the real desktop** follows near the user’s pointer and **moves to point at the actual Explorer file icon** — not merely a path string or an in-app breadcrumb.

Cody remains the product/persona name. Matching still uses the Codex API. The missing piece that makes it Clicky is the **OS-level pointing cursor**, not more seat scaffolding.

## 2. Demo story (success path)

1. User runs Cody (PySide shell) and picks a messy folder (Desktop or staged demo folder).
2. User types a non-filename query (e.g. Taglish + relative time).
3. Pipeline indexes / extracts / understands / matches (Codex) → best path.
4. **Cody cursor** appears on a full-screen, click-through overlay, initially tracking near the real mouse.
5. Reveal opens Explorer and selects the file (`explorer /select,...`).
6. Overlay resolves the file icon’s screen bounds (UI Automation), then **animates the Cody cursor from the user’s pointer to that icon**.
7. Optional: short spoken confirmation (voice remains soft-fail / non-blocking).

If step 6 fails (a11y race, wrong view mode), demo still has Explorer select; cursor may soft-fail — but **MVP treats a working overlay point as the primary “wow,”** so we invest here first, not as stretch.

## 3. In scope (MVP)

| Area | Keep / change |
|------|----------------|
| Query → match → path | Keep contracts §6.1–6.4; Codex matcher |
| OS reveal | Keep §6.5 Windows `explorer /select` |
| **Desktop Cody cursor** | **Promote** former §6.8 overlay to **core MVP** |
| Cursor follow | Overlay tracks real mouse until “point” starts |
| Point animation | Smooth move from mouse position → icon center (or icon rect) |
| Assets | **Required in repo** under `assets/cody-cursor/` (see §6) |
| PySide shell | Keep orchestration window for query + status |
| Voice | Optional soft-fail (already designed) |
| Fixtures | Keep for matcher/tests without live folder |

## 4. Out of scope / deprioritize

- In-app breadcrumb as the *primary* pointing story (may remain as secondary polish; must not block overlay work)
- Multi-file disambiguation UI, OCR/images, embeddings, cloud sync, auth
- Moving the real system cursor (Approach B) or a separate game-engine compositor (Approach C)
- Vendoring unrelated agent skill packs / SpecStory dumps / Cursor Cloud noise
- Expanding seat docs (P4 phase novels, grill ADRs) over shipping the overlay + assets

## 5. Architecture (Approach A)

```
[PySide main window]  query + status
        │
        ▼
[pipeline] indexer → extract → nlu → matcher(Codex) → path
        │
        ├─► reveal(path)           # Explorer /select
        └─► cody_cursor overlay    # NEW core module (rename of overlay-stretch)
              ├─ mouse follow (global position)
              ├─ icon bounds (UI Automation)
              └─ animate sprite to target
```

### 5.1 Module ownership

- **`overlay/` (or keep `overlay-stretch/` renamed to `overlay/`):** fullscreen transparent, click-through `Qt` widget; sprite paint; animation timer; a11y lookup.
- **`orchestration/`:** after match + reveal kickoff, starts cursor follow → point sequence; never blocks reveal on overlay failure.
- **`reveal/`:** unchanged contract `reveal(path) -> bool`.
- Seat packages indexer/extractor/nlu/matcher: unchanged contracts; stop treating them as the product surface.

### 5.2 Proposed overlay contract (additive)

```text
start_follow() -> None          # show sprite; track cursor
point_at(path: str) -> bool     # resolve icon; animate; True if pointed
stop() -> None                  # hide overlay
```

- `point_at` MUST be callable with the same path reveal used.
- Failure → `false`, log warning, leave Explorer select as fallback.

### 5.3 Windows constraints

- Primary demo OS: **Windows** (already locked).
- DPI-aware geometry; click-through (`WS_EX_TRANSPARENT` / Qt equivalent).
- Icon lookup: UI Automation after Explorer is foreground; retry briefly (e.g. 200–500ms × N) then soft-fail.
- Prefer Details/List view staging notes in demo checklist so icons are findable.

## 6. Assets (blocker — not in repo today)

Create and commit:

```
assets/cody-cursor/
  README.md                 # sizes, hotspot, license
  cursor-default.png        # resting / follow (hotspot documented)
  cursor-point.png          # optional “pointing” frame
  cursor-sheet.png          # optional short anim strip
  sfx-point.wav             # optional, soft-fail if missing
```

Rules:

- Hotspot (tip of pointer) documented in `assets/cody-cursor/README.md`.
- No secrets; binary assets are required for demo authenticity.
- Until assets land, overlay may use a temporary simple geometric pointer **only in `--demo-stubs`**, never as the shipped look.

**Owner action:** drop final Cody/Clicky cursor art into that folder (or approve generating a minimal placeholder set).

## 7. What changes in product docs (after this design is approved)

1. `spec.md` §3: overlay cursor follow + point = **in scope**; breadcrumb §6.7 becomes secondary.
2. `spec.md` §6.8: rewrite as **core** Cody Cursor Overlay (not stretch).
3. `openspec/specs/overlay-stretch/spec.md` → rename/retarget to `overlay` with follow + point requirements.
4. `README.md` team map: overlay seat is load-bearing; Person 1 orchestration wires it; assign explicit overlay owner if not Troy.
5. Landing copy “How it works” step 3 = desktop cursor point (not only OS select + voice).

## 8. Success criteria (replaces “stretch optional”)

Demo succeeds if:

1. Natural-language query resolves to the correct file (existing).
2. Explorer opens with the file selected (existing).
3. **Cody cursor is visible on the desktop, tracks near the user pointer, then moves to the file icon.**
4. At least one Taglish / relative-time query works (existing).
5. Voice optional; overlay failure is rare enough that the live run shows the point at least once.

## 9. Implementation order (for later plan — not started yet)

1. Land `assets/cody-cursor/` (or approved placeholders).
2. Overlay skeleton: fullscreen click-through + mouse follow.
3. Hook reveal → a11y icon rect → animate to target.
4. Wire orchestration happy path; stub mode for CI without Explorer.
5. Trim / freeze non-essential seat polish.

## 10. Non-goals for this redesign doc

- Rewriting all six seats’ implementations in one PR
- Changing Codex → another matcher provider
- macOS overlay parity
