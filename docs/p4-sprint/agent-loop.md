# P4 agent loop

Back to [overview.md](overview.md).

Parent model is Grok 4.5 High. Subagents use Claude Sonnet 5 (`claude-sonnet-5-thinking-medium`).

## Topology

One parent cloud agent owns the loop. Three local subagents rotate per phase. They never edit outside the P4 circle.

```
Parent (cloud, Grok 4.5 High)
  ├─ Planner   (read-only)   → next phase checklist from docs/p4-sprint/
  ├─ Developer (write)       → implement exactly one phase under matcher/
  └─ QA        (verify)      → run that phase's static + runtime checks
```

Loop per phase:

1. Parent picks the next incomplete phase file.
2. Planner returns a one-page checklist. Files allowed. Files forbidden. Verification commands. Conflict risks.
3. Developer implements only the checklist. Stops when tests for that phase are green.
4. QA re-runs verification from the phase file and [testing.md](testing.md). Reports pass/fail with command output pointers, not vibes.
5. Parent commits and pushes on `rohart-branch` if QA is green (team SDD cadence). Then advances.

If QA fails, Planner diagnoses from evidence. Developer gets a fix checklist. Same phase until green. Do not start the next phase.

## Role rules

### Planner

- `subagent_type`: `p4-matcher-planner` when revising phase order or plan docs. Otherwise `poteto-agent` read-only.
- May read `spec.md`, PRD, plan, fixtures, contracts, matcher.
- Must not edit code.
- Must name the data shape before any suggested logic.
- Must flag shared-surface edits (fixtures, pyproject, contracts) as shout-out required.

### Developer

- `subagent_type`: `poteto-agent`.
- Writes only under `matcher/` unless Planner explicitly approved an additive fixtures append with shout-out text.
- Follows TDD for behavior changes. Failing test or golden first, then impl.
- One phase per invocation. No "while I'm here" work on Phase N+1.
- Never opens `orchestration/`, `nlu/`, `indexer/`, `extractor/`, `reveal/`, `voice/`, or `overlay-stretch/`.

### QA

- `subagent_type`: `poteto-agent`.
- Runs commands. Reads diffs. Does not "fix" by rewriting product code unless Parent assigns a tiny verify-script fix inside `matcher/`.
- Proves against the real artifact (`pytest`, golden runner, live smoke). Compiles-is-green is not enough.
- On shared CI failures outside `matcher/`, stop and escalate to Parent. Do not patch a teammate's folder.

## Conflict firewall

| Surface | Who may touch | Rule |
|---------|---------------|------|
| `matcher/**` | Developer | Free. Internals are free (§6.9 rule 1). |
| `fixtures/*.json` | Developer only after Planner + shout-out | Append rows only. Cap 10. Prefer matcher goldens first. |
| `contracts/**` | Nobody in this loop by default | Additive optional fields need group shout-out. |
| `spec.md` / OpenSpec | Nobody mid-phase | PRD/plan docs under `docs/p4-*` are P4-owned docs. |
| `pyproject.toml` | Avoid | Prefer stdlib HTTP. Shout out if a dep is unavoidable. |
| Other component folders | Never | Talk contracts only. |

## Parent checklist before each cloud turn

1. Confirm branch is `rohart-branch` and tracking is set (`origin/rohart-branch`).
2. Confirm working tree has no accidental edits outside `matcher/` and approved fixture appends.
3. Name the single phase in progress.
4. Spawn Planner → Developer → QA in that order. Do not parallelize Developer and QA on the same phase.
5. After green QA, granular commit + push. Message states why the slice exists.

## Autonomy

Reversible work proceeds without asking. Force-push, deleting teammate files, and pasting secrets into the repo stay blocked. If the real matcher is broken at a sprint checkpoint, keep the stub and stop debugging past the timebox (§10.4).
