# P4 matcher (Cody) implementation plan

Single plan for component 4 of Cody, sized for the 3-hour sprint (spec 10.4). Companion to `docs/p4-matcher-prd.md`. Spec references are to `/workspace/spec.md`.

## Context

Cody takes indexed files, extracted text, and a structured query, and returns the best match with a reasoning sentence. Entry point is `match(files, content, intent) -> MatchResult` (6.4, 11.1). All work lands in `matcher/` plus additive fixture data (Section 7, 11.2). Orchestration is the only consumer (11.2).

## Scope

In. The `match` entry point, a fixture corpus with golden cases, a `ModelConfig` loader (8.1), prompt assembly, one Responses API call with strict parsing, soft handling of `time_hint` and `type_hint`, a Taglish smoke test, and handoff notes for orchestration.

Out. Embeddings, voice, reveal, overlay, orchestration UI, disambiguation flows, caching, and any edit outside `matcher/` and `fixtures/` (Sections 3, 5, 9, 11.2, 12).

## Constraints

- Contracts 6.1 through 6.4 are frozen. Changes are additive-only with a group shout-out (6.9 rule 2).
- Stub commit to `main` by 0:30, real implementation by the 2:00 to 2:30 integration window (10.4).
- Model access only through `ModelConfig`, OpenAI Responses API, model `gpt-5.3-codex` confirmed at build time, key gitignored and never committed (Section 8, 8.1).
- Demo-scale input, dozens to low hundreds of files in one context window (Sections 3 and 8).
- One legible reasoning sentence per match (10.1).

The language inside `matcher/` is the owner's call under 6.9 rule 1. This plan defaults to Python for sketches and phase file names (`matcher/*.py`). Swap the extension if the owner picks another language; the phase goals stay the same.

## Alternatives for the model call

Option A. One Responses call. All candidates go in one prompt with the intent, and the model returns `MatchResult` JSON directly. Code annotates each candidate with whether it fits the time range and type hint, but removes nothing.

Option B. Two calls. The first shortlists candidates, the second picks a winner and writes the reasoning. Doubles latency and failure surface. Buys context headroom the demo scale does not need (Section 8).

Option C. Hard code-side filters. Drop candidates outside `resolved_range` or mismatching `type_hint`, then one call over survivors. Smallest prompt, but a noisy upstream hint silently eliminates the right file with no recovery, which kills demo criterion 1 (Section 4).

Chosen. Option A. The whole folder fits one window at demo scale (Section 8), one call keeps the reveal inside its few-second budget (Section 4, criterion 3), and soft annotations let the model weigh a hint against content evidence instead of being overruled by it. The parse step validates that the returned path exists in the input and rejects anything else. This choice is decided, not yet demonstrated. Phase 3 smoke plus Phase 6 distractor goldens are the proof.

## Phases

Each phase is small, touches at most three files, and ends in a check before the next starts. Phases 1 through 3 must complete by the 0:30 stub checkpoint (10.4).

### Phase 1. Folder, types, stub

Goal. `matcher/` exists and `match` returns a fixture-shaped `MatchResult`. This commit merges straight to `main` (11.3).
Files. `matcher/match.py`, `matcher/types.py`.
Shapes. `match(files: list[FileRecord], content: list[ExtractedContent], intent: QueryIntent) -> MatchResult` per 6.1 to 6.4. `MatchResult` carries `best_match {path, confidence, reasoning}` and `alternatives`.
Verification. Static, the signature and returned keys match 6.4 field for field. Runtime, call the stub with any input and assert the output parses as valid `MatchResult` JSON with all three `best_match` fields present.

### Phase 2. Fixture corpus and golden cases

Goal. Test data exists before any logic. 5 to 10 `FileRecord`, `ExtractedContent`, and `QueryIntent` samples per Section 7, plus golden cases pairing an intent with its expected path. Include the Lazada receipt Taglish case from 6.3 and at least one distractor file that matches on keyword but not date.
Files. `fixtures/` (additive-only, 11.2), `matcher/golden_cases.json`, `matcher/run_golden.py`.
Shapes. Golden case is `{intent, expected_path, note}`.
Verification. Runtime, `run_golden.py` loads every fixture, calls the stub, and asserts each output is shape-valid. Golden path assertions stay recorded but disabled until phase 5.

### Phase 3. ModelConfig loader and live smoke

Goal. Config comes from a gitignored file, and one raw Responses call proves the key and model work. This doubles as the 0:30 Codex smoke test (10.4), the last cheap moment to swap models.
Files. `matcher/config.py`, `.gitignore` entry for the config file, `matcher/smoke.py` (throwaway).
Shapes. `load_config() -> ModelConfig` with `provider`, `base_url`, `api_key`, `model` per 8.1.
Verification. Static, `git check-ignore` confirms the config file cannot be committed. Runtime, a missing file raises a clear error, and one live Responses call on the Lazada Taglish golden fixture returns that fixture's expected path (not a vague "sensible" pick). If the path is wrong, escalate the model choice now, not at 2:00.

### Phase 4. Prompt assembly

Goal. A pure function builds the prompt from the three inputs. No API call in this phase.
Files. `matcher/prompt.py`.
Shapes. `build_prompt(files, content, intent) -> str`. One line per candidate joining 6.1 metadata to its 6.2 snippet, an intent block quoting `description`, `resolved_range`, and `type_hint`, per-candidate in-range and type-match annotations, and an instruction to answer as 6.4 JSON with a one-sentence reasoning naming the matched evidence. Unknown input fields are ignored (6.9 rule 3), and `extractable: false` files appear with metadata only (6.2).
Verification. Static, unit asserts that the prompt for the Lazada golden case contains the fixture filename, the snippet text, and the resolved range. Runtime, print the assembled prompt for the largest fixture set and confirm the length is nowhere near the window.

### Phase 5. Responses call and strict parse

Goal. The stub internals become real. One API call, parsed into `MatchResult`, shape-identical to the stub so orchestration notices nothing (6.9 rule 4).
Files. `matcher/match.py`.
Shapes. `parse_result(raw: str, valid_paths: set[str]) -> MatchResult`. Rejects unparseable JSON and any `best_match.path` not in the input, raising a clear error for orchestration to catch. Exactly one Responses call per query. Zero retries. Protects the latency budget (Section 4, criterion 3).
Verification. Runtime, enable the golden path assertions in `run_golden.py` and run live. Every case must return its expected path. Feed the parser a fabricated path by hand and confirm it raises instead of passing it through.

### Phase 6. Soft hint handling

Goal. Confirm the in-prompt annotations from phase 4 actually steer the model, and tune wording if not. Hints stay soft, no candidate is removed in code.
Files. `matcher/prompt.py`, `matcher/golden_cases.json`.
Shapes. No new shapes. Golden cases gain one where the keyword distractor sits outside `resolved_range` and one with a `type_hint` conflict.
Verification. Runtime, the new golden cases pass live. The distractor loses to the in-range file, and the reasoning sentence cites the date or type evidence.

### Phase 7. Taglish and last_week smoke

Goal. The demo-critical path works end to end inside the matcher. This is Cody's share of Section 4 criterion 4.
Files. `matcher/golden_cases.json` if a case is missing, otherwise none.
Shapes. None new. The 6.3 example intent, `language_mix: "taglish"` with a resolved `last_week` range, is the input.
Verification. Runtime, run the full golden suite live twice. The Taglish case returns the receipt both times, and each reasoning string is one sentence a presenter can read aloud (10.1). Record one full `MatchResult` output in the run log as evidence.

### Phase 8. Orchestration handoff

Goal. The orchestration owner can call Cody without reading matcher internals.
Files. `matcher/README.md`.
Shapes. None new. The README states the entry-point signature, the error behavior from phase 5, the config file location and its gitignored status, and a copy-paste call example against fixtures.
Verification. Runtime, execute the README's example exactly as written in a fresh shell and confirm it returns a valid `MatchResult`. Ask the orchestration owner to confirm they catch raised errors and display them as an error state (kickoff shout-out from the PRD open decisions). Then delete `matcher/smoke.py`, it was throwaway.

## Implementation guidance

- Contracts are frozen. Any output addition is optional-field-only with a shout-out (6.9 rule 2).
- Never edit another owner's folder. Upstream problems are contract conversations, not cross-folder patches (11.2).
- Stub merges to `main` first, real work continues on `feature/matcher`, small merges when green (11.3).
- Fixtures are additive-only. Add records, never rewrite existing ones (11.2).
- If the real matcher is broken at a checkpoint, keep the stub and move on rather than debugging past the timebox (10.4).
- Run `/deslop` before each commit.

## Non-goals

No embeddings or vector search (Sections 3, 12). No voice (component 7). No reveal (component 5). No overlay (component 8). No orchestration or UI work (component 6). No disambiguation UI, no caching, no recursive scan handling beyond whatever the kickoff decides (Sections 3, 9).
