# P4 verification

Back to [overview.md](overview.md).

## Project commands

```bash
# Component tests (owner adds under matcher/tests)
python -m pytest matcher/tests -q

# Shared contract fixtures still must pass after any additive fixture row
python -m pytest tests/contracts -q

# Shape-only goldens (Phase 2+)
python matcher/run_golden.py --shape-only

# Live path goldens (Phase 5+, needs local ModelConfig)
python matcher/run_golden.py

# Config ignore check (Phase 3+)
git check-ignore -v matcher/local_model.json

# Secret scan before every commit
git status
git diff --cached
```

## Surface note

Matcher is a library entry point, not a CLI product surface. There is no `control-cli` / `control-ui` skill target for Cody itself. Runtime proof is the golden runner plus one live Responses smoke. Orchestration E2E is Person 1's surface at the 2:00 checkpoint. P4 only proves `match` against fixtures.

## Per-phase gate

Do not start phase N+1 until phase N's static and runtime lines in its phase file both pass. QA owns that gate in the [agent loop](agent-loop.md).
