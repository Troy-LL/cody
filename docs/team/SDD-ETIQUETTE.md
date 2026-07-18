# SDD etiquette (Cody sprint)

Follow this for the whole 6-person sprint. Product contracts live in [`spec.md`](../../spec.md). Process requirements live in [`openspec/specs/team-workflow/spec.md`](../../openspec/specs/team-workflow/spec.md).

## No cross-editing

- Edit only your component folder(s) and your branch.
- Want a neighbor to change behavior? Talk about the **contract**, do not open their files.
- Shared surfaces (`spec.md` contracts, fixtures, OpenSpec domain specs, root README) change only with a group shout-out and additive-only edits (below).

## Contracts are additive-only

- Mid-sprint you MAY add an **optional** output field; you MUST NOT rename, remove, retype, or redefine an existing field.
- Consumers MUST ignore unknown fields.
- Announce additive contract edits to the group; non-additive waits until after the sprint.

## Stub-first by 0:30

- By the 0:30 mark, each owner commits a stub that returns (or documents) the exact contract shape for their entry point.
- Orchestration integrates against stubs from minute 30 — real code replaces stubs later without changing the interface.

## Only orchestration imports others

- `indexer/`, `extractor/`, `nlu/`, `matcher/`, `reveal/`, `voice/`, and `overlay-stretch/` MUST NOT import each other.
- Only `orchestration/` may import sibling component packages.

## Sources of truth

- Product behavior and data shapes: `spec.md`.
- Domain requirements: `openspec/specs/<domain>/spec.md`.
- Ownership and handoff: root `README.md` + each component `README.md`.
- If code and docs disagree for this session, the owner updates the owning doc in the same change.

## SDD with Grok 4.5

- Each task: implement with Grok 4.5 subagents per the SDD workflow, then run a review pass before merging.
- Keep OpenSpec specs and component READMEs updated when behavior or contracts change.

## Git: SPEED MODE (direct `main`)

- **Commit and push on `main`.** No feature branches or PRs for this sprint — maximize speed.
- **Granular commits required.** One concern per commit — stub, failing tests, implementation slice, docs note, etc.
- After each logical slice (tests green for that slice), **commit immediately**, then **push immediately** (`git push origin main`).
- Stage only owned/relevant files; never commit secrets (`.env`, keys, API tokens).
- **Do not delete remote branches** unless the branch owner explicitly asks.
- On merge conflicts: `git pull --rebase origin main`, resolve **only files you own**, re-test, push. If the conflict is inside a teammate's folder, stop and escalate via the contract.

## Team Codex rule pack

- Sprint agent pack lives under [`.codex/`](../../.codex/) (OpenSpec skills/commands, agents, team rule).
- Always-on rule: [`.codex/rules/team-sdd-memory.mdc`](../../.codex/rules/team-sdd-memory.mdc) (tracked). Mirror: [`team-sdd-memory.mdc`](team-sdd-memory.mdc).
- Do **not** gitignore `.codex/`.

## Team rule evolution

- The always-on rule may gain **Learned** bullets only after reviewed work lands.
- New bullets must be durable, verified, team-wide conventions; cite source + date; replace stale lines; no secrets or guesses; max 10 learned bullets; must appear in the task diff.
