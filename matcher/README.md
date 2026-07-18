# Matcher / Ranker (Cody)

| Field | Value |
|-------|-------|
| **Owner** | Person 5 |
| **Purpose** | Rank files against structured intent using Codex; emit best match + reasoning. |
| **Owns** | `matcher/` package, `match` entry point, and `ModelConfig` usage (`spec.md` §8.1). |
| **Does not own** | Indexing, extraction, NLU implementation, reveal/voice, UI shell. |
| **Frozen I/O** | `match(files, content, intent) -> MatchResult` per `spec.md` §6.4. |
| **Stub requirement** | Stub raises `NotImplementedError` until fixture-shaped return lands (Task 2 / 0:30). |
| **Test command** | `python -m pytest matcher/tests -q` (owner adds tests). |
| **Branch** | `feature/matcher` |
| **Done condition** | Section 7 fixtures yield the correct file with a one-sentence `reasoning` string. |
| **Integration handoff** | Orchestration imports `matcher.match.match`. Consume contracts only — do not import sibling packages. |
