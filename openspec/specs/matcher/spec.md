## Purpose

Cody (the matcher) ranks indexed files plus extracted snippets against a `QueryIntent` via the Codex API and returns a `MatchResult` with best match, confidence, reasoning, and alternatives.

## Requirements

### Requirement: MatchResult shape
`match` SHALL return `best_match` with `path`, `confidence`, and `reasoning`, plus an `alternatives` list per `spec.md` §6.4.

#### Scenario: Fixture Lazada receipt
- **GIVEN** Section 7 fixtures for files, content, and a Lazada receipt intent
- **WHEN** `match` runs
- **THEN** `best_match.path` MUST be the receipt file and `reasoning` MUST be a non-empty one-sentence explanation

### Requirement: Model config is external
The matcher MUST read provider, base URL, API key, and model from `ModelConfig` (`spec.md` §8.1) and MUST NOT hardcode secrets in source.

#### Scenario: Local API key
- **GIVEN** a machine-local gitignored config with a Codex-compatible key
- **WHEN** matching executes
- **THEN** the matcher MUST load credentials from that config path/env and MUST NOT commit the key

### Requirement: Consumers of contracts only
The matcher SHALL accept `FileRecord[]`, `ExtractedContent[]`, and `QueryIntent` as arguments and MUST NOT import indexer, extractor, or nlu packages.

#### Scenario: Parallel build against fixtures
- **GIVEN** fixture-shaped inputs without live sibling packages
- **WHEN** the matcher is unit-tested
- **THEN** tests MUST succeed using only contract-shaped dicts
