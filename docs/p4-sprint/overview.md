# P4 matcher sprint plan

Companion to [`docs/p4-matcher-prd.md`](../p4-matcher-prd.md) and [`docs/p4-matcher-plan.md`](../p4-matcher-plan.md). This directory is the poteto-mode execution plan for Person 5 (Cody). Product shapes stay in `spec.md`.

## Context

Cody ranks files against a structured query and returns a `MatchResult` with a one-sentence `reasoning` string the presenter can read aloud. The entry point is `match(files, content, intent) -> MatchResult` (`spec.md` §6.4, §11.1).

**Current state (2026-07-18).** `matcher/match.py` still raises `NotImplementedError`. No `types.py`, `config.py`, `prompt.py`, golden runner, or `matcher/tests`. Shared fixtures already hold 8 files, 8 content rows, and 7 intents, including the Taglish Lazada `last_week` case. All P4 work for this seat lands on `rohart-branch` (tracks `origin/rohart-branch`). Never write matcher changes on `main`.

## Scope

**In.** Everything under `matcher/`. Owner-internal goldens. Additive fixture rows only when a golden truly needs a new shared sample. `ModelConfig` loader from a gitignored local file. One Responses API call. Parse guards. README handoff for orchestration.

**Out.** Embeddings. Voice. Reveal. Overlay. Orchestration UI. NLU parsing. Sibling packages. Contract renames. Caching. Raising the shared `tests/contracts/test_fixtures.py` 10-row cap unless the group agrees.

## Constraints

- Branch `rohart-branch` only. Never commit or push to `main` (`docs/team/SDD-ETIQUETTE.md`). The team map still lists `feature/matcher` as the Person 5 seat name; this seat's actual git branch is `rohart-branch`.
- Edit circle is `matcher/**`. Shared surfaces (`fixtures/`, `contracts/`, `spec.md`, `openspec/specs/matcher/spec.md`, root `pyproject.toml`) are additive-only with a group shout-out.
- Consumers ignore unknown fields (§6.9 rule 3). Matcher must not import sibling packages. Only `orchestration/` imports `matcher`.
- Stub returns fixture-shaped `MatchResult` by the 0:30 checkpoint. Real matcher by the 2:00–2:30 integration window. Freeze at 2:30.
- Secrets never land in git. `.env` is already ignored. Phase 3 must also ignore the matcher config path.
- `pyproject.toml` has no OpenAI client today. Prefer a thin stdlib HTTP call to the Responses API so P4 does not fight other seats over root deps. If an `openai` package is still required, shout it out before editing `pyproject.toml`.

## Alternatives (model call)

Already decided in [`docs/p4-matcher-plan.md`](../p4-matcher-plan.md). Restated here so implementers do not reopen it without evidence.

| Option | Idea | Verdict |
|--------|------|---------|
| A | One Responses call over all candidates with soft in-prompt annotations | **Chosen.** Demo scale fits one window. One call protects latency. |
| B | Two calls (shortlist then pick) | Rejected. Doubles latency and failure surface. |
| C | Hard-drop candidates outside time/type hints, then one call | Rejected. A noisy hint can delete the right file. |

Phase 3 smoke plus Phase 6 distractor goldens are the proof for A.

## Applicable skills

- poteto-mode Feature playbook for each phase implementation
- `how` before touching unfamiliar Responses API wiring
- `unslop` on every prose surface (README, plan edits, PR body)
- `/deslop` before each commit
- Keep the PR merge-ready after it opens
- `show-me-your-work` if the parent cloud loop runs unattended across phases
- Repo agents `.codex/agents/p4-matcher-planner.md` and `p4-matcher-prd.md` when revising plan or PRD

## Phases

1. [phase-1-stub.md](phase-1-stub.md). Fixture-shaped stub.
2. [phase-2-goldens.md](phase-2-goldens.md). Owner goldens + runner.
3. [phase-3-config-smoke.md](phase-3-config-smoke.md). `ModelConfig` + live Codex smoke.
4. [phase-4-prompt.md](phase-4-prompt.md). Pure prompt assembly.
5. [phase-5-call-parse.md](phase-5-call-parse.md). Responses call + strict parse.
6. [phase-6-soft-hints.md](phase-6-soft-hints.md). Distractor / type-hint goldens.
7. [phase-7-taglish-smoke.md](phase-7-taglish-smoke.md). Demo-critical Taglish path.
8. [phase-8-handoff.md](phase-8-handoff.md). README handoff + delete throwaway smoke.

Agent orchestration for the parent cloud loop lives in [agent-loop.md](agent-loop.md). Project verification commands live in [testing.md](testing.md).

## Verification

See [testing.md](testing.md). Every phase ends in static + runtime checks before the next phase starts.

## Implementation guidance

Implementer non-negotiables from poteto-mode:

- Run the `how` skill over the matcher subsystem before changing call or parse paths.
- Run `interrogate` only if someone contests Option A or the failure-raise shape.
- `/deslop` every diff before commit. `unslop` every prose surface.
- Keep a short decision trail via `show-me-your-work` when the cloud parent runs multi-phase unattended.
- After opening the PR, keep it merge-ready until the gate lands it.
- Granular commits on `rohart-branch`. One concern each. Push after each green slice (team SDD rule). Never secrets.

Conflict discipline for this seat:

- Default all new files under `matcher/`.
- Prefer goldens that reuse existing fixture rows.
- If a distractor row is required, append at most one or two rows per fixtures JSON file (headroom under the shared 10-row cap). Shout out before push.
- Do not edit `tests/contracts/`, `orchestration/`, or other owners' folders to "win" a merge.
