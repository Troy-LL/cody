## Purpose

Defines how the six-person Cody sprint collaborates without file conflicts: ownership boundaries, additive contracts, stub-first integration, and sources of truth.

## Requirements

### Requirement: No cross-component editing
Owners SHALL edit only their assigned component folders and branches. Requests for behavior changes MUST go through contract discussion, not direct edits to another owner's files.

#### Scenario: Neighbor wants different extractor behavior
- **GIVEN** the matcher owner wants richer snippets from the extractor
- **WHEN** they need a change mid-sprint
- **THEN** they discuss an additive contract change with the group and MUST NOT edit `extractor/` themselves

### Requirement: Additive-only mid-sprint contracts
Contract fields in `spec.md` §6 SHALL remain stable mid-sprint except for optional additive fields. Consumers MUST ignore unknown fields.

#### Scenario: Optional field added
- **GIVEN** an owner needs a new optional output field
- **WHEN** they announce it to the group and add the field without renaming existing ones
- **THEN** other components continue to parse known fields and ignore the new one

### Requirement: Stub-first by thirty minutes
Each component owner SHALL land a contract-shaped stub by the 0:30 mark so orchestration can integrate against real entry points.

#### Scenario: Orchestration starts against stubs
- **GIVEN** stubs exist for indexer, extractor, nlu, matcher, reveal, and voice
- **WHEN** the 0:30 mark passes
- **THEN** orchestration MUST be able to call each entry point without importing unfinished internals

### Requirement: Only orchestration imports siblings
Non-orchestration packages MUST NOT import each other. Only `orchestration/` MAY import sibling component packages.

#### Scenario: Matcher needs extracted text
- **GIVEN** match requires `ExtractedContent`
- **WHEN** implementing the matcher
- **THEN** it MUST accept content via its function arguments and MUST NOT import `extractor`

### Requirement: OpenSpec and READMEs are sources of truth
Owners SHALL keep root README, component READMEs, and `openspec/specs/<domain>/spec.md` aligned with reviewed behavior. Product shapes remain defined in `spec.md`.

#### Scenario: Done condition changes
- **GIVEN** a reviewed task changes a component's done condition
- **WHEN** the change merges
- **THEN** the component README and domain OpenSpec MUST be updated in the same change set
