# Phase 2. Owner goldens and runner

Back to [overview.md](overview.md).

## Goal

Test data exists before real matching logic. Golden cases live inside `matcher/` so shared `fixtures/` stays mostly untouched.

## Changes

- `matcher/golden_cases.json` (new). Cases shaped `{intent_id or intent, expected_path, note}`. Include the Lazada Taglish case from fixtures. Record path assertions as data even if the runner skips live path checks until Phase 5.
- `matcher/run_golden.py` (new). Loads fixtures via `fixtures.load`, calls `match`, asserts shape validity. Path equality gated behind a flag until Phase 5.
- Prefer zero edits to `fixtures/*.json` in this phase. Shared fixtures already cover Taglish Lazada and a Lazada screenshot distractor on keyword (both dates currently fall inside `last_week`). Document that Phase 6 may need one additive out-of-range distractor row.

## Data structures

Golden case `{intent, expected_path, note}`.

## Verification

**Static.** Golden JSON parses. Every `expected_path` appears in `fixtures/file_records.json`.

**Runtime.** `python matcher/run_golden.py --shape-only` passes against the Phase 1 stub.
