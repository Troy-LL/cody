# Phase 5. Responses call and strict parse

Back to [overview.md](overview.md).

## Goal

Stub internals become real. Shape stays identical so orchestration notices nothing (§6.9 rule 4).

## Changes

- `matcher/match.py`. Load config, build prompt, one Responses call, parse into `MatchResult`.
- `parse_result(raw, valid_paths) -> MatchResult`. Reject unparseable JSON and any `best_match.path` not in the input set. Raise a clear error for orchestration. Never fabricate a path.
- Exactly one model call per query. Zero retries.
- Prefer stdlib HTTP against the Responses endpoint to avoid a contested `pyproject.toml` dependency edit. Document the request shape in a short comment only if the why is non-obvious.

## Data structures

Same `MatchResult`. Internal parse error is an exception, not an additive contract field, unless the group shouted an optional error field at kickoff.

## Verification

**Static.** `python -m pytest matcher/tests -q`.

**Runtime.** Enable path assertions in `run_golden.py` and run live. Feed the parser a fabricated path and confirm it raises. Record one full `MatchResult` in the run log.
