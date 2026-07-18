# Phase 1. Fixture-shaped stub

Back to [overview.md](overview.md).

## Goal

`match` returns a valid `MatchResult` shape so orchestration can integrate against the stub. Replaces today's `NotImplementedError`.

## Changes

- `matcher/types.py` (new). Minimal TypedDict or alias wrappers for the three inputs and `MatchResult`, or re-export from `contracts.schemas` without importing sibling packages' runtime logic.
- `matcher/match.py`. Return a fixture-shaped dict with `best_match.{path,confidence,reasoning}` and `alternatives`. Path must be one of the input paths when inputs are non-empty.

## Data structures

`MatchResult = { best_match: {path, confidence, reasoning}, alternatives: [...] }` per §6.4.

## Verification

**Static.** Signature matches `contracts.interfaces.Match`. Returned keys match `MATCH_RESULT_KEYS`.

**Runtime.** Call `match` with fixture loaders. Assert JSON-serializable output and all three `best_match` fields present. `python -m pytest matcher/tests -q` once the first test file exists.
