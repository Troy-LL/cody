# Cody — team map

**Product context:** [`spec.md`](spec.md) is the product source of truth (contracts, fixtures, demo scope).

**Sprint seats (6 people + stretch):** build in parallel against frozen contracts. OpenSpec domain specs live under [`openspec/specs/`](openspec/specs/). Team process: [`docs/team/SDD-ETIQUETTE.md`](docs/team/SDD-ETIQUETTE.md).

**Git (enforced):** never push to `main`/`master` — feature branches + PR only (PM merge gate). Use **granular commits** (one concern each); auto-commit and push each slice on your branch.

| Seat | Owner | Folders | Branch(es) | OpenSpec domain | Contract (`spec.md`) | Done when |
|------|-------|---------|------------|-----------------|----------------------|-----------|
| Person 1 | Troy | [`orchestration/`](orchestration/README.md) | `feature/orchestration` | [`orchestration`](openspec/specs/orchestration/spec.md) | §6.7 + pipeline glue | Full pipeline runs E2E with baseline animation + voice call |
| Person 2 | TBD | [`indexer/`](indexer/README.md) | `feature/indexer` | [`indexer`](openspec/specs/indexer/spec.md) | §6.1 `FileRecord` | Folder path → valid `FileRecord` list (top-level) |
| Person 3 | TBD | [`extractor/`](extractor/README.md) | `feature/extractor` | [`extractor`](openspec/specs/extractor/spec.md) | §6.2 `ExtractedContent` | PDF/docx/txt snippets; graceful `extractable: false` |
| Person 4 | TBD | [`nlu/`](nlu/README.md) | `feature/nlu` | [`nlu`](openspec/specs/nlu/spec.md) | §6.3 `QueryIntent` | Taglish + relative time → structured intent |
| Person 5 | TBD | [`matcher/`](matcher/README.md) | `feature/matcher` | [`matcher`](openspec/specs/matcher/spec.md) | §6.4 `MatchResult` (Cody) | Fixtures → correct best match + reasoning |
| Person 6 | TBD | [`reveal/`](reveal/README.md), [`voice/`](voice/README.md) | `feature/reveal`, `feature/voice` | [`reveal`](openspec/specs/reveal/spec.md), [`voice`](openspec/specs/voice/spec.md) | §6.5 + §6.6 | OS select works; templated TTS speaks EN/TL |
| Stretch | Unassigned | [`overlay-stretch/`](overlay-stretch/README.md) | `feature/overlay-stretch` | [`overlay-stretch`](openspec/specs/overlay-stretch/spec.md) | §6.8 | Overlay lands on icon by 2:00 or drop |

**Locked for this sprint:** Windows demo machine · top-level folder scan · Person 6 owns reveal + voice · Troy owns orchestration only · Contracts/fixtures + PySide shell: `pyproject.toml`, `contracts/`, `fixtures/`, `python -m orchestration.main --demo-stubs`.

**Team workflow OpenSpec:** [`openspec/specs/team-workflow/spec.md`](openspec/specs/team-workflow/spec.md).
protection-smoke 2026-07-18T14:03:54.9822737+08:00
