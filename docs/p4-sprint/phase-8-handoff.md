# Phase 8. Orchestration handoff

Back to [overview.md](overview.md).

## Goal

Orchestration can call Cody without reading matcher internals.

## Changes

- `matcher/README.md`. Entry-point signature, raise-on-failure behavior, config path and gitignore status, copy-paste fixture call example.
- Delete `matcher/smoke.py` if it still exists.

## Data structures

None new.

## Verification

**Runtime.** Execute the README example in a fresh shell. Confirm a valid `MatchResult`. Ask the orchestration owner (Person 1 / Troy) to confirm they catch raised errors as an error state. That shout-out is the kickoff open decision from the PRD.
