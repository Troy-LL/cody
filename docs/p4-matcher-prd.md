# P4 matcher (Cody) product requirements

Owner scope is component 4 of Cody — the Matcher / Ranker (Section 5). This PRD covers only what P4 must build and prove. Spec references are to `/workspace/spec.md`.

## Problem and product bet

People can describe a file they cannot name. "Yung resibo ko sa Lazada last week" is a real query, and no filename search answers it. Cody's bet is that pointing beats explaining (Section 2). Instead of instructions, the demo ends with the actual file selected on a real machine.

Cody is the reasoning engine that makes the pointing possible (Section 1). It takes indexed metadata, extracted text, and a structured query, and decides which file the person means.

Cody's `reasoning` string is not debug output. The spec shows it to the user as "why it picked this file" (Sections 1 and 6.4), and success criterion 2 requires the system to state why it chose the file (Section 4). The voice layer speaks only templated phrases (Sections 3 and 6.6), so the displayed `reasoning` sentence is the single place the user sees that the AI understood them. It must read as one legible sentence naming the evidence, per the 10.1 done-when.

## In scope for P4

- The entry point `match(files, content, intent) -> MatchResult` in the `matcher/` folder (Sections 6.4 and 11.1).
- Consuming `FileRecord[]` (6.1), `ExtractedContent[]` (6.2), and `QueryIntent` (6.3) as inputs.
- LLM-driven matching over an assembled context, at demo scale of dozens to low hundreds of files (Sections 3 and 8).
- Reading model access from `ModelConfig` (8.1), never hardcoded.
- Getting a Codex API key set up and smoke-testing that `gpt-5.3-codex` handles the matching task (Sections 8 and 10.1).
- Building against the Section 7 fixtures before any live upstream component exists.

## Out of scope for P4

- Embedding or vector search infrastructure (Sections 3 and 12).
- Voice output, component 7 (Section 5). Cody hands a resolved filename downstream and nothing more.
- Reveal, component 5, and the stretch overlay, component 8 (Section 5).
- Orchestration and UI, component 6, including the baseline animation (6.7).
- Query parsing. Time phrases arrive already resolved in `time_hint.resolved_range` (6.3). Cody must not re-derive dates from `raw_query`.
- Disambiguation UI. Return best guess plus reasoning; refinement loops are v2 (Section 3).
- Caching of model calls. Sprint default is none (Section 9).
- Editing any other owner's folder (11.2).

## Users of the matcher

Orchestration (component 6) is the only caller. It is the sole folder allowed to import from `matcher/` (11.2). No other component reads `MatchResult`. The end user never calls Cody directly; they see the `reasoning` string that orchestration displays.

## Functional requirements

- FR1. Expose one entry point, `match(files, content, intent) -> MatchResult`, matching the `matcher/` layout in 11.1.
- FR2. Accept a list of `FileRecord` objects with the 6.1 fields (`path`, `filename`, `extension`, `size_bytes`, `created_at`, `modified_at`).
- FR3. Accept a list of `ExtractedContent` objects per 6.2 (`path`, `extractable`, `text_snippet`, `extraction_method`). Files with `extractable: false` and `text_snippet: null` must not break matching; they remain candidates on metadata alone. `extraction_method` may be ignored under FR10.
- FR4. Accept a `QueryIntent` per 6.3 and use `description`, `time_hint.resolved_range`, `type_hint`, and `language_mix` as evidence. The resolved range is authoritative for time. Cody does not compute dates, and does not re-interpret `time_hint.type`, `time_hint.value`, or `raw_query`.
- FR5. Return a `MatchResult` per 6.4 with `best_match.path`, `best_match.confidence`, and `best_match.reasoning`, plus an `alternatives` list. `best_match.path` must be one of the input file paths.
- FR6. `reasoning` is one legible sentence naming which snippet or metadata matched (6.4 and 10.1).
- FR7. Populate `alternatives` with lower-confidence candidates. MVP flow does not consume them (6.4), but the shape is frozen.
- FR8. Matching runs as LLM reasoning over an assembled context in a single context window, not embeddings (Sections 3 and 8).
- FR9. Read provider, base URL, key, and model from `ModelConfig` only (8.1). Call OpenAI's Responses API, not Chat Completions (Section 8).
- FR10. Tolerate unknown fields on all inputs (6.9 rule 3). Parse what is needed, ignore the rest.
- FR11. On model failure or unparseable output, fail in a way orchestration can catch and show as an error state (Section 5, component 6 handles result states). Never return a fabricated path.
- FR12. Complete fast enough that the reveal lands within a few seconds of the query (Section 4, criterion 3). Exactly one model call per query. Zero retries.

## Contracts and change rules

Sections 6.1 through 6.4 are frozen at kickoff (10.2). The 6.9 rules bind P4 both ways.

- Internals of `matcher/` are free to change at any time (rule 1).
- Any change to the `MatchResult` shape mid-sprint is additive-only, a new optional field with a shout-out to the group. No renames, removals, or retypes (rule 2).
- As a consumer of 6.1 through 6.3, Cody ignores unknown fields (rule 3).
- The stub is a contract (rule 4). Once the stub merges, orchestration integrates against it, and the real implementation must be shape-identical when it lands.

## Model provider requirements

Per 8.1, one config object, read at call time and never hardcoded:

- Fields are `provider`, `base_url`, `api_key`, `model`.
- Provider for this build is OpenAI's Codex API via the Responses API. Spec current model ID is `gpt-5.3-codex`. Confirm the live ID at build time before the 0:30 smoke (Section 8). Until that smoke passes, treat the ID as provisional.
- The key lives in a local, gitignored config or env file, pasted per machine. It is never committed (8.1).
- Swapping providers is a config change only. `base_url`, `api_key`, and `model` change; matcher code does not (8.1).

## Acceptance criteria

Mapped to Section 4. Cody owns criteria 1, 2, and the matching half of 4. It feeds 3 and 5 but does not implement them.

- AC1. Given the Section 7 fixtures, a natural-language, non-filename query returns the correct file as `best_match` (criterion 1).
- AC2. The returned `reasoning` states which snippet or metadata matched, in one sentence a presenter can read aloud (criterion 2).
- AC3. A Taglish query with a relative time phrase, arriving as a 6.3 intent with `resolved_range` populated, resolves to the correct file (criterion 4). Cody's share is using the resolved fields correctly, not parsing Taglish.
- AC4. `best_match.path` is always a real input path, so the reveal layer (criterion 3) and voice layer (criterion 5) receive something actionable.
- AC5. A single match call completes within the few-second reveal budget on a demo-scale folder (criterion 3).

## Done when

From the 10.1 matcher brief. Given the Section 7 fixtures, `match` returns the correct file with a legible one-sentence reasoning string. The owner has a working Codex key and has smoke-tested that the model handles the matching task (Section 8).

## Fixture-first development

Section 7 supplies 5 to 10 sample `FileRecord`, `ExtractedContent`, and `QueryIntent` examples checked into `fixtures/`. P4 starts against these immediately and never blocks on live Indexer, Extractor, or NLU code (10.1). Additions to `fixtures/` are additive-only (11.2). Golden query cases, meaning an intent paired with its expected path, live inside `matcher/` as owner-internal test data.

## Sprint checkpoints

From 10.4. The sprint is three hours.

- 0:00 to 0:15. Kickoff. Contracts locked, P4 ownership confirmed.
- By 0:30. Stub commit to `main` returning fixture-shaped `MatchResult`. Codex smoke test on one fixture query happens in this window; it is the last cheap moment to swap the model.
- 0:30 to 2:00. Real implementation replaces the stub on `feature/matcher`, merged to `main` when green (11.3).
- 2:00 to 2:30. Integration checkpoint. The full pipeline runs on the real demo folder with the real matcher.
- 2:30. Freeze. Only demo-breaking fixes after this.

If the real matcher is not working at its checkpoint, the stub stays in and gets faked rather than debugged past the timebox (10.4).

## Open decisions affecting P4

From Section 9.

- Caching for repeated demo runs. Sprint default is none; P4 plans for no cache.
- Model ID confirmation. `gpt-5.3-codex` is current per the spec; confirm at build time (Section 8).
- Recursive vs top-level scan. Default is top-level. Recursive would grow the candidate set and context size.
- Demo file list. The staged scenarios define which golden cases matter most; P4 needs at least one Taglish plus relative-time case (Section 4).
- Failure shape. 6.4 defines no error field. Sprint approach is to raise a clear error for orchestration to catch. P4 must shout this out at kickoff (10.2) so orchestration handles the same shape. Adding an optional error field later is additive under 6.9 rule 2.

## Risks

- Codex is tuned for coding tasks. Matching quality is plausible but unproven (Section 8). Mitigation is the 0:30 smoke test, the last cheap moment to swap models.
- Context size. Snippets are capped at 500 to 1000 chars upstream (6.2), but a larger-than-expected folder could crowd the window. Mitigation is trimming snippets or shortlisting candidates before the call.
- Stub-to-real swap breaking orchestration. Mitigation is 6.9 rule 4, the real output stays shape-identical to the stub.
- Malformed model output. The model may return JSON that does not parse or a path not in the input. Mitigation is a parse guard that rejects fabricated paths (FR11).
- Latency. A slow model call breaks criterion 3. Mitigation is exactly one call per query and zero retries.
- Key setup on the demo machine. The gitignored config must be pasted on the actual demo machine before rehearsal (8.1).
