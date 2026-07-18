# Clicky — MVP Spec (SOT)

**Status:** Draft v0.3 — scoped for a **3-hour build sprint**
**Owner:** Troy (architecture) + 5 contributors (Voice Layer ownership TBD — Section 9)
**Last updated:** 2026-07-18

---

## 1. One-liner

Clicky is an AI that shows you where something is instead of telling you how to find it. MVP proves this with one scenario: describe a file in natural, messy (Taglish-friendly) language, and Clicky finds it on a real local machine and physically points to it — no manual searching, no folder-by-folder instructions.

**Naming:** Clicky is the product. **Cody** is the name of the AI reasoning engine underneath it — the Matcher (Section 6.4), powered by the Codex API (Section 8.1). Cody's `reasoning` string is what actually gets surfaced to the user as "why it picked this file," so it's worth treating as a small in-product persona, not just a backend function.

## 2. Core insight (protect this)

Most AI assistants operate in "instruction mode" — they explain steps. Clicky's bet is that **pointing beats explaining**. The demo lives or dies on whether the final "reveal" moment feels like the AI actually walked over and put its finger on the file, not just returned a text path.

Everything in this spec is in service of making that one moment convincing.

## 3. MVP / Demo scope

**In scope:**
- One real local folder (Desktop, or a staged "messy" folder) on a real machine — live demo, not a mockup
- Natural language query in Taglish/English describing a file by content, approximate time, or vague descriptor (e.g. *"yung resibo ko sa Lazada last week"*)
- Matching against file metadata + extracted text content (PDF, docx, txt) for a demo-scale folder (dozens–low hundreds of files)
- Matching performed via LLM reasoning over an assembled context (indexer output + extracted snippets), not a full vector search / embedding pipeline
- OS-native "reveal": open the containing folder and select/highlight the resolved file
- Baseline pointing animation: Clicky's own UI visibly narrows in on the file (breadcrumb/tree lighting up path segments) timed to land as the real OS-native select fires — Section 6.7
- Cody narrates the result aloud, not just visually — a short spoken confirmation, with a language knob (English / Tagalog / auto-match the person's own mix) so it isn't only pointing, it's also telling you
- Single happy-path flow: query in → shortlist reasoned over → best match revealed (visually + aloud)

**Stretch (attempt only if the baseline above is solid and there's time left):**
- Full overlay animation drawn directly on the real OS explorer window, converging on the actual file icon via accessibility APIs — Section 6.8. Bigger "wow," real engineering risk; never load-bearing for demo success

**Explicitly out of scope for MVP:**
- Image/OCR content search
- Multi-file / ambiguous "did you mean" disambiguation UI (return best guess + say why; refinement loop is v2)
- Embedding-based semantic search infrastructure
- Voice **input** (speech-to-text query) — MVP takes typed/text queries only; voice is an output channel for now, not an input one
- Full translation of Cody's technical `reasoning` string into Tagalog — voice uses a small set of templated spoken phrases (Section 6.6), not open-ended translation
- Cross-device or cloud-synced folders
- Auth, multi-user, or persistence beyond a single session
- Filipino NLU beyond Taglish code-switching + relative time phrases (no dialect coverage beyond that for v1)

## 4. Success criteria

MVP demo is a success if, on a folder the audience hasn't seen prepped in advance:
1. A natural-language, non-filename-based query resolves to the correct file
2. The system can state *why* it picked that file (which snippet/metadata matched)
3. The reveal moment visibly happens on-screen (folder opens, file is selected) within a few seconds
4. At least one query uses Taglish / relative time phrasing and still resolves correctly
5. Cody speaks the result aloud, and does so in Tagalog when the language knob (or auto-detected input language) calls for it
6. The in-app baseline animation (Section 6.7) visibly narrows in on the file before/as the real reveal happens — the stretch overlay (Section 6.8) is a bonus, not required for this criterion

## 5. Architecture — components

Seven independently buildable pieces. Each is a function/service with a fixed input/output contract (Section 6) so people can build in parallel against mocked data before the neighboring component exists.

| # | Component | Responsibility | Depends on |
|---|-----------|-----------------|------------|
| 1 | **Indexer** | Walk target folder, emit file metadata | none |
| 2 | **Content Extractor** | Given a path, return extracted text | none |
| 3 | **Query Understanding (NLU)** | Normalize raw user text into structured intent | none |
| 4 | **Matcher / Ranker — "Cody"** | Given indexed files + extracted text + structured query, return ranked matches with reasoning | 1, 2, 3 (via contracts, not code) |
| 5 | **Reveal Layer** | Given a resolved path, perform OS-level select/highlight | none (mockable with hardcoded path) |
| 6 | **Orchestration / UI shell** | Wire 1–5 together, handle input/thinking/result states, build the baseline reveal animation (6.7) | all |
| 7 | **Voice Layer — "Cody speaks"** | Given a resolved filename + language knob, speak a short confirmation aloud | 4 (needs the resolved filename), config from 8.2 |
| 8 | **Pointing Overlay — stretch, Option A** | Locate the file icon's on-screen coordinates via OS accessibility APIs and animate a highlight directly onto the real explorer window | 5 (reveal must succeed first) — **optional, non-blocking** |

Each of 1, 2, 3, 5, 7 can be built and unit-tested in complete isolation using the fixture data in Section 7. Component 4 is the only piece that meaningfully depends on the others' *output shape* — which is why the contracts below are the first thing to lock. Component 8 is a stretch goal (Section 3) — attempted only if time allows, never required for demo success.

## 6. Data contracts

These are the shapes passed between components. Treat this section as the actual source of truth — implementation details of each component can change freely as long as these shapes hold.

### 6.1 Indexer output — `FileRecord`

```json
{
  "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
  "filename": "receipt_lazada.pdf",
  "extension": ".pdf",
  "size_bytes": 84213,
  "created_at": "2026-07-10T14:22:00Z",
  "modified_at": "2026-07-10T14:22:00Z"
}
```

Indexer emits a list of these for every file in the target folder (non-recursive for v1 unless decided otherwise).

### 6.2 Content Extractor output — `ExtractedContent`

```json
{
  "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
  "extractable": true,
  "text_snippet": "Lazada Order Confirmation... Total: PHP 1,240.00... Order date: July 9, 2026",
  "extraction_method": "pdf_text_layer"
}
```

- `extractable: false` with `text_snippet: null` for unsupported/binary files (images, etc. — out of scope for v1 but should not break the pipeline)
- Snippet length: cap around 500–1000 chars per file to keep matcher context manageable

### 6.3 Query Understanding output — `QueryIntent`

```json
{
  "raw_query": "yung resibo ko sa Lazada last week",
  "description": "a receipt from Lazada",
  "time_hint": {
    "type": "relative",
    "value": "last_week",
    "resolved_range": ["2026-07-06T00:00:00Z", "2026-07-12T23:59:59Z"]
  },
  "type_hint": null,
  "language_mix": "taglish"
}
```

- `type_hint` populated when the user implies a file type (e.g. "yung PDF ko", "yung picture")
- `time_hint.resolved_range` is computed against the current date, not left for the matcher to figure out — keeps component 3 self-contained

### 6.4 Matcher output — `MatchResult` (this is Cody's output)

```json
{
  "best_match": {
    "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
    "confidence": 0.91,
    "reasoning": "Filename and extracted content both reference Lazada; modified date (July 10) falls within the 'last week' range."
  },
  "alternatives": [
    { "path": "C:/Users/troy/Desktop/lazada_screenshot.png", "confidence": 0.34 }
  ]
}
```

- `reasoning` is shown to the user in the demo — this is what makes the "AI actually understood me" moment land, separate from the reveal itself
- Alternatives kept for possible v2 disambiguation, not used in MVP flow

### 6.5 Reveal Layer input

```json
{ "path": "C:/Users/troy/Desktop/receipt_lazada.pdf" }
```

Takes only a resolved path. Output is a side effect (folder opens, file selected), not data — but should return a simple success/failure boolean for the orchestration layer to handle errors (e.g. file moved/deleted between match and reveal).

### 6.6 Voice Layer input — `SpeechRequest`

```json
{
  "filename": "receipt_lazada.pdf",
  "language_mode": "tl"
}
```

- Voice Layer maps this to a short **templated** spoken line — e.g. English: "Found it — receipt_lazada.pdf." / Tagalog: "Nakita ko na — receipt_lazada.pdf." — rather than translating Cody's full `reasoning` string on the fly
- Keeps the language surface small and reliable for a demo: a handful of phrase templates per language, not open-ended translation
- `language_mode` normally comes from the `VoiceConfig` knob (Section 8.2); when set to `"auto"`, it should just mirror whatever `QueryIntent.language_mix` (Section 6.3) already detected, so Cody's voice matches how the person actually asked
- Output: audio played aloud (side effect) + success/failure boolean — same shape as the Reveal Layer's return value (Section 6.5)

### 6.7 Reveal Animation (baseline, in-app) — `RevealAnimation`

```json
{
  "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
  "root": "C:/Users/troy/Desktop",
  "segments": ["Desktop", "receipt_lazada.pdf"]
}
```

- Built inside Orchestration (component 6) — not a separate owner. `segments` is just the resolved path split relative to the scanned root folder
- Clicky's own UI animates each segment lighting up in sequence, timed to land right as the real OS-native select (Section 6.5) fires
- This is the **guaranteed baseline**: it never touches the real explorer window, so it can't break due to OS accessibility quirks — this is what Section 4's success criterion 6 depends on, not the stretch overlay below

### 6.8 Pointing Overlay input (stretch, Option A) — `OverlayRequest`

```json
{ "path": "C:/Users/troy/Desktop/receipt_lazada.pdf" }
```

- Same input shape as the Reveal Layer (Section 6.5) — reuses the already-resolved path, no new upstream dependency
- Behavior: query the OS accessibility tree (Windows UI Automation / macOS Accessibility API) for the file icon's on-screen bounding box inside the now-open explorer window, then draw a transparent, always-on-top overlay animating an arrow or ring onto that spot
- Must fail silently and safely — if the icon's coordinates can't be resolved (wrong view mode, window not yet rendered, timing race), fall back to the baseline (6.5 + 6.7) with nothing visibly broken
- Only attempted if a component owner finishes their primary piece early — never load-bearing for demo success

### 6.9 Change-resilience rules — how to change things without breaking anyone

These four rules are what make the contracts hold up under a fast sprint where everyone's changing code constantly. If everyone follows them, any change inside a component stays invisible to the other five people:

1. **Internals are free, contracts are not.** Anything inside your folder can change at any time, no announcement needed — rewrite it, swap libraries, restructure completely. Only the entry-point function's input/output shape (Sections 6.1–6.8) is frozen.
2. **Contract changes during the sprint are additive-only.** You may add a new *optional* field to your output. You may never rename, remove, retype, or change the meaning of an existing field mid-sprint. Adding a field requires a 30-second shout-out to the group; anything non-additive waits until after the sprint.
3. **Consumers ignore unknown fields.** Every component that reads another component's output must tolerate fields it doesn't recognize (parse what you need, ignore the rest). This is what makes rule 2 safe — additions land without coordinating with every consumer.
4. **Stubs are contracts too.** Your first commit (Section 10.4) is a stub returning fixture data in the exact contract shape. From that moment, orchestration integrates against your component — when your real implementation replaces the stub, nothing downstream should notice.

The test for any change: *"if I make this change and tell no one, does anyone else's code break?"* If yes, it's a contract change — rule 2 applies. If no, ship it.

## 7. Fixture data for parallel dev

Before component 4 exists, contributors on 1, 2, 3, and 5 should build against a shared fixture folder + 5–10 sample `FileRecord`/`ExtractedContent`/`QueryIntent` examples (checked into the repo) so nobody blocks on a live folder or a working matcher.

## 8. Tech notes / constraints

- Matching is LLM-driven, not embedding/vector-search — appropriate at demo scale (dozens–low hundreds of files fit in a single context window)
- **Model is swappable, not hardcoded.** The Matcher reads its provider/model/API key from one config point (Section 8.1) — anyone can paste in a different key or base URL to point at another OpenAI-compatible provider without touching Matcher code
- **Chosen provider for this build: OpenAI's Codex API.** Accessed via OpenAI's Responses API (not the older Chat Completions format — Codex has moved off that entirely). Current model ID is `gpt-5.3-codex`; confirm the latest ID against OpenAI's model list at build time since this updates fairly often
- Codex is tuned primarily for agentic coding tasks (writing/running/debugging code). It's still a capable general LLM and should handle the Matcher's "which file matches this description" reasoning fine, but it's worth a quick smoke test early rather than assuming parity with a general-purpose reasoning model
- No GPU dependency anywhere in the pipeline
- Reveal layer is platform-specific: Windows (`explorer /select,<path>`) and macOS (`open -R <path>`) implementations can be split between two people if needed
- **Stretch overlay risk (Section 6.8):** depends on OS accessibility APIs — Windows UI Automation, macOS Accessibility API — which behave differently across icon/list/details view and race against window-render timing. Genuinely optional engineering, not a hidden requirement
- Indexer should be non-destructive and read-only — no writes to the scanned folder

### 8.1 Model Provider Config — `ModelConfig`

One config object, read by the Matcher (and NLU too, if it ends up needing LLM assistance beyond rule-based parsing) — never hardcoded inline:

```json
{
  "provider": "openai",
  "base_url": "https://api.openai.com/v1",
  "api_key": "<pasted locally, per machine — never committed>",
  "model": "gpt-5.3-codex"
}
```

- Lives in a local, gitignored config/env file — it's a live secret pasted per person/per machine, not project data
- Because Codex speaks OpenAI's standard Responses API shape, switching providers later (or routing through a gateway) is just changing `base_url` + `api_key` + `model` — no code changes in the Matcher itself
- This is what makes "paste any API key to use any model" actually true architecturally, not just in theory

### 8.2 Voice Provider Config — `VoiceConfig` (Resolved: ElevenLabs)

Same pattern as 8.1, kept as a separate config since the TTS provider doesn't need to be the same company as the matching model. **Provider is resolved: ElevenLabs.**

```json
{
  "enabled": true,
  "language_mode": "auto",
  "provider": "elevenlabs",
  "base_url": "https://api.elevenlabs.io",
  "api_key": "<pasted locally, never committed>",
  "model_id": "eleven_flash_v2_5",
  "routing": {
    "en": { "voice_id": "<en_voice_id>" },
    "tl": { "voice_id": "<tl_voice_id>" },
    "taglish": { "voice_id": "<tl_voice_id>" }
  }
}
```

- Endpoint: `POST {base_url}/v1/text-to-speech/{voice_id}` with the templated phrase (Section 6.6) as `text` and the configured `model_id` — returns audio bytes, play them, done. One HTTP call per reveal
- **Routing is the "knob" made concrete:** the Voice Layer resolves `language_mode` → the `routing` table → a `voice_id`. `"auto"` mirrors `QueryIntent.language_mix` (Section 6.3). Adding a new language later = adding a row to `routing`, zero code changes
- Use a multilingual ElevenLabs model (`eleven_flash_v2_5` is fast and cheap, good for a live demo) — but **verify Tagalog output quality in the first 30 minutes of the sprint**; if it sounds off, try `eleven_v3` or a different voice before building anything else on top
- `en` and `tl` can even share one `voice_id` since multilingual models switch language based on the input text — separate rows kept anyway so voices can be tuned per language without touching code
- `enabled: false` must cleanly fall back to visual-only reveal — voice should never be a hard dependency for the core demo moment to work, in case the key isn't wired up yet or the API fails live

## 9. Open decisions (need answers before build starts)

- [ ] Recursive folder scan, or top-level only, for the demo? (sprint default: top-level)
- [x] ~~Which LLM/model powers the matcher~~ → **Resolved: OpenAI's Codex API** (Section 8.1). Still open: is caching worth setting up for repeated demo runs? (sprint default: no caching)
- [ ] Exact list of demo files/scenarios to stage (need at least one Taglish + relative-time case per Section 4)
- [ ] Windows vs Mac as the primary demo machine (affects who builds the reveal layer first)
- [x] ~~Which TTS provider powers the Voice Layer~~ → **Resolved: ElevenLabs** (Section 8.2). Still to verify in first 30 min: Tagalog voice quality on `eleven_flash_v2_5`
- [ ] Is voice demo-blocking, or a nice-to-have that falls back to visual-only if it's not ready in time? (sprint default: fallback — Section 8.2 already designs for this)
- [ ] Who owns the Voice Layer — a dedicated seat, or folded into an existing owner's scope (Reveal or Orchestration are the natural fits)?
- [ ] Who attempts the stretch overlay — whoever finishes their primary component first, or does someone volunteer upfront? (cutoff is fixed at the 2:00 mark — Section 10.4)

## 10. Team kickoff — ownership & alignment

### 10.1 Per-component briefs

Each owner should leave kickoff knowing exactly this — no more, no less:

**Indexer Owner**
- Build: folder walker → list of `FileRecord` (Section 6.1)
- Done when: given any folder path, returns valid `FileRecord` JSON for every file in it
- No dependencies to start — build against your own test folder immediately

**Content Extractor Owner**
- Build: path → `ExtractedContent` (Section 6.2)
- Done when: correctly extracts snippets from PDF, docx, txt; returns `extractable: false` gracefully for anything else
- No dependencies to start — build against a folder of sample files

**Query Understanding (NLU) Owner**
- Build: raw user text → `QueryIntent` (Section 6.3)
- Done when: handles Taglish code-switching and resolves relative time phrases ("last week," "kanina") against the current date
- No dependencies to start — first task is writing your own sample query list to build against

**Matcher / Ranker Owner — builds Cody**
- Build: `FileRecord[]` + `ExtractedContent[]` + `QueryIntent` → `MatchResult` (Section 6.4), calling out to the Codex API via the `ModelConfig` in Section 8.1
- Done when: given the Section 7 fixtures, returns the correct file with a legible one-sentence reasoning string
- Depends on: the *contracts* from 1–3, not their code — start immediately against fixtures
- Also owns: getting a Codex API key set up and smoke-testing that it handles the matching task well (Section 8)

**Reveal Layer Owner**
- Build: path → OS select/highlight action + success/failure boolean (Section 6.5)
- Done when: given any hardcoded valid path, opens the folder and visibly selects the file on the target OS
- No dependencies to start — build against hardcoded paths

**Orchestration / UI Owner**
- Build: the glue — input box, calls 1–3 in parallel, then 4, then 5 and 7; handles loading/result states; also builds the baseline reveal animation (Section 6.7) — Clicky's own in-app breadcrumb visibly narrowing in on the file
- Done when: the full pipeline runs end-to-end on the real demo folder, visually (with the baseline animation) and aloud
- Depends on: everyone else's contracts — can build the shell against mocked responses before real components exist

**Voice Layer Owner — TBD (dedicated seat, or folded into Reveal/Orchestration)**
- Build: `SpeechRequest` (Section 6.6) → one ElevenLabs TTS call routed via the `VoiceConfig.routing` table (Section 8.2) → play audio + success/failure boolean
- Done when: given a fixture filename, correctly speaks the templated confirmation in both English and Tagalog through the routed voice
- First 30 minutes: smoke-test Tagalog output quality on `eleven_flash_v2_5` — this is the last cheap moment to change model or voice
- No dependencies to start — build against hardcoded filenames and both language templates; wire in the real `QueryIntent.language_mix` for `"auto"` mode once component 3 exists
- Needs resolving at kickoff: dedicated builder, or does someone already on Reveal/Orchestration pick this up alongside their component?

**Stretch: Pointing Overlay Owner (Option A) — optional, not a required seat**
- Build: `OverlayRequest` (Section 6.8) → animated highlight on the real file icon + success/failure boolean
- Done when: on the target OS, the overlay correctly lands on the icon in whatever view mode the demo folder actually uses
- Attempt only after your primary component is done — this never blocks demo readiness. If it's not working reliably by the cutoff (Section 9), it gets dropped with zero impact on the guaranteed baseline (6.7)

### 10.2 Kickoff session agenda (~15 min — this is minute 0:00–0:15 of the sprint)

Goal: the group leaves aligned on scope, and the open decisions in Section 9 get resolved *together* — not handed down by one person. Timeboxed hard; anything that can't be decided in the room defaults to the spec's stated default.

1. **Read-through (3 min)** — Sections 1–4 skimmed aloud so everyone is building toward the same demo moment
2. **Contracts + change rules (5 min)** — Section 6 shapes confirmed, Section 6.9 rules stated out loud once; objections now or hold until after the sprint
3. **Resolve open decisions (5 min)** — rapid-fire through Section 9; each gets a choice and an owner. Undecided = spec default wins:
   - Recursive vs. top-level scan (default: top-level)
   - Codex API caching (default: none — demo scale doesn't need it)
   - Demo scenarios/files (owner assigns themselves, stages during the sprint)
   - Primary OS (default: whatever the demo machine runs)
   - Voice demo-blocking or fallback (default: fallback — Section 8.2 already handles it)
   - Voice Layer + stretch overlay ownership
4. **Confirm ownership (2 min)** — each person states their component out loud

### 10.3 Decision log (fill in during/after the session)

| Decision | Chosen option | Reasoning | Owner |
|---|---|---|---|
| Scan depth (recursive vs. top-level) | | | |
| Matcher model | OpenAI Codex API (`gpt-5.3-codex`, via Responses API) | Team decision — confirm smoke test results at kickoff | |
| Caching approach | | | |
| Demo scenarios/files | | | |
| Primary OS | | | |
| TTS provider | ElevenLabs (`eleven_flash_v2_5`, routing per Section 8.2) | Team decision — verify Tagalog voice quality in first 30 min | |
| Voice demo-blocking or fallback-only | | | |
| Voice Layer ownership | | | |
| Stretch overlay cutoff time | Default: 2:00 mark | Sprint schedule (Section 10.4) | |
| Stretch overlay owner (optional) | | | |

### 10.4 The 3-hour sprint schedule

| Time | What happens |
|---|---|
| **0:00–0:15** | Kickoff (Section 10.2). Contracts locked, owners confirmed |
| **0:15–0:30** | **Stub commit.** Every owner commits a stub that returns fixture data in their exact contract shape. Voice owner also smoke-tests ElevenLabs Tagalog quality now; Matcher owner smoke-tests Codex on one fixture query now — this is the last cheap moment to swap either |
| **0:30–2:00** | **Build.** Real implementations replace stubs, each in their own folder/branch. Orchestration builds the shell + baseline animation (6.7) against stubs from minute 30 — integration is continuous, not a big-bang event |
| **2:00** | **Stretch cutoff.** If the overlay (6.8) isn't visibly working, it's dropped — no discussion needed, the baseline is the demo |
| **2:00–2:30** | **Integration checkpoint.** All real implementations merged; full pipeline runs end-to-end on the real demo folder |
| **2:30–3:00** | **Rehearse + freeze.** Run the demo script 2–3 times, fix only demo-breaking bugs, freeze `main`. No new features past 2:30 under any circumstances |

Two rules that protect the schedule: anything not working at its checkpoint gets stubbed/faked/dropped rather than debugged past the timebox, and the 2:30 freeze is absolute — a rough demo that runs beats a polished one that doesn't.

## 11. Repo structure — avoiding file conflicts

The component split in Section 5 only prevents conflicts if it's mirrored in the actual folder layout. Nobody should ever have a reason to open a file inside someone else's component.

### 11.1 Proposed layout

```
clicky/
├── SPEC.md
├── contracts/
│   └── schemas.md        # Section 6 — locked after kickoff sign-off
├── fixtures/              # Section 7 — shared sample data, additive-only
├── indexer/               # Owner 1 — entry point: index_folder(path) -> FileRecord[]
├── extractor/             # Owner 2 — entry point: extract(path) -> ExtractedContent
├── nlu/                   # Owner 3 — entry point: parse_query(text) -> QueryIntent
├── matcher/               # Owner 4 — "Cody" — entry point: match(files, content, intent) -> MatchResult
├── reveal/                # Owner 5 — entry point: reveal(path) -> bool
├── voice/                 # Owner 7 (or folded in) — entry point: speak(filename, language_mode) -> bool
├── overlay-stretch/       # Optional Owner 8 — entry point: overlay(path) -> bool — only if someone picks it up
└── orchestration/         # Owner 6 — the only folder allowed to import from the others
```

Each folder is a black box to everyone except its owner: internal structure, helper files, tests — all up to that person. The only thing that has to match Section 6 exactly is the single entry-point function's input/output shape.

### 11.2 Rules that actually prevent conflicts

- **No cross-editing.** If the matcher owner (Cody) wants the extractor to behave differently, that's a conversation about the contract, not a direct edit to someone else's folder.
- **Only orchestration crosses boundaries.** It's the sole folder that imports from the other six — so it's also the one place integration conflicts can happen, which is why it's built last (Section 11.3).
- **`contracts/` is read-many, write-rarely.** Everyone builds against it, nobody edits it solo — a silent change there breaks all five other components at once. Changes go through a quick group check the same way the open decisions did in the kickoff.
- **`fixtures/` is additive-only.** People can add new sample records but shouldn't rewrite existing ones — others may already be building against them.

### 11.3 Git workflow to match

- One branch per component: `feature/indexer`, `feature/extractor`, `feature/nlu`, `feature/matcher`, `feature/reveal`, `feature/voice`, and `feature/overlay-stretch` if someone picks it up
- **Stub-first:** everyone's first commit (by the 0:30 mark — Section 10.4) is a contract-shaped stub merged straight to `main`, so orchestration integrates against real interfaces from minute 30 onward
- After that, real implementations merge to `main` whenever they pass their own "done when" — small merges beat one big-bang integration; the 2:00–2:30 window is for catching what's left, not for merging everything at once
- `feature/overlay-stretch`, if it exists, merges only if it's visibly working by the 2:00 cutoff — otherwise it's simply left out, zero impact
- A genuine need to touch `contracts/` or `fixtures/` follows Section 6.9 rule 2: additive-only, with a quick shout-out to the group — never a silent commit

This keeps the team building in parallel with near-zero file overlap until the single planned integration moment.

## 12. Deferred / future work

- Image content search (OCR)
- Embedding-based semantic search for scaling beyond context-window limits
- Disambiguation flow when confidence is low or multiple strong candidates exist
- Broader Filipino dialect/language coverage beyond Taglish
- Voice **input** (speech-to-text queries) — MVP is typed-query, spoken-response only
- Full open-ended translation of Cody's `reasoning` string into Tagalog (voice uses fixed templates for v1, not live translation)
- Multi-folder / recursive whole-drive search
- Persistence, history, multi-user support