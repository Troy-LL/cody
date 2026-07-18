## Purpose

Orchestration is the only cross-importing package: it owns the UI shell, calls components in order, builds the baseline in-app reveal animation, and coordinates voice without owning sibling internals.

## Requirements

### Requirement: Sole importer
Only `orchestration/` MAY import `indexer`, `extractor`, `nlu`, `matcher`, `reveal`, `voice`, and optionally `overlay-stretch`. Sibling packages MUST NOT import each other through orchestration helpers.

#### Scenario: Pipeline wiring
- **GIVEN** stubs or real implementations for all primary components
- **WHEN** a user submits a query
- **THEN** orchestration MUST call index/extract/nlu, then match, then reveal and speak

### Requirement: Baseline reveal animation
Orchestration SHALL build `RevealAnimation` segments (`spec.md` §6.7) from the matched path relative to the scan root and animate them in-app timed with OS reveal.

#### Scenario: Desktop receipt path
- **GIVEN** root `C:/Users/troy/Desktop` and match path ending in `receipt_lazada.pdf`
- **WHEN** the result UI runs
- **THEN** segments MUST light up toward the file as `reveal` fires

### Requirement: Troy ownership boundary
Person 1 (Troy) owns orchestration only and MUST NOT implement reveal/voice/indexer/extractor/nlu/matcher internals on this branch beyond wiring and stubs scaffolding.

#### Scenario: Voice owned by Person 6
- **GIVEN** Person 6 owns `reveal/` and `voice/`
- **WHEN** orchestration needs spoken confirmation
- **THEN** it MUST call `speak` via the frozen interface rather than embedding TTS logic
