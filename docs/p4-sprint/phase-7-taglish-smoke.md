# Phase 7. Taglish and last_week smoke

Back to [overview.md](overview.md).

## Goal

Demo-critical path works end to end inside the matcher. Cody's share of §4 criterion 4.

## Changes

- `matcher/golden_cases.json` only if the Taglish case is missing. Prefer zero file churn.

## Data structures

None new.

## Verification

**Runtime.** Run the full golden suite live twice. Taglish Lazada case returns the receipt both times. Each `reasoning` is one presenter-readable sentence. Save one full `MatchResult` as evidence in the decision trail or run log.
