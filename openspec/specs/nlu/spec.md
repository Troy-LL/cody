## Purpose

Query understanding normalizes messy Taglish/English user text into a structured `QueryIntent` with description, optional type hint, language mix, and resolved relative time ranges.

## Requirements

### Requirement: Structured QueryIntent
`parse_query` SHALL return `raw_query`, `description`, `time_hint`, `type_hint`, and `language_mix` per `spec.md` §6.3.

#### Scenario: Taglish Lazada query
- **GIVEN** the query "yung resibo ko sa Lazada last week"
- **WHEN** `parse_query` runs
- **THEN** `description` MUST capture a Lazada receipt intent and `language_mix` MUST be `taglish`

### Requirement: Relative time resolution
When the query contains relative time phrases, `time_hint.resolved_range` MUST be computed against the current date inside NLU (not deferred to the matcher).

#### Scenario: Last week phrase
- **GIVEN** a query containing "last week" on a known current date
- **WHEN** parsing completes
- **THEN** `time_hint.type` MUST be `relative` and `resolved_range` MUST be a concrete start/end pair

### Requirement: Optional type hint
`type_hint` SHALL be set when the user implies a file type and MUST be `null` otherwise.

#### Scenario: Explicit PDF mention
- **GIVEN** a query like "yung PDF ko"
- **WHEN** `parse_query` runs
- **THEN** `type_hint` MUST indicate a PDF-related type
