# Phase 6. Soft hint handling

Back to [overview.md](overview.md).

## Goal

Prove soft annotations steer the model. Tune prompt wording if distractors win.

## Changes

- `matcher/prompt.py` only if wording needs a tweak.
- `matcher/golden_cases.json`. Add cases where a keyword distractor sits outside `resolved_range`, and where `type_hint` conflicts with a tempting wrong extension.
- Shared fixtures. Only if existing rows cannot express the distractor. Append at most one `FileRecord` + matching `ExtractedContent` (and optionally one intent). Stay under the shared 10-row cap in `tests/contracts/test_fixtures.py`. Shout out before pushing fixture edits.

## Data structures

No new shapes.

## Verification

**Runtime.** New goldens pass live. Distractor loses. Reasoning cites date or type evidence in one sentence.
