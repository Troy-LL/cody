## Purpose

The reveal layer performs the Windows OS-native "show this file" action: open the containing folder and select/highlight the resolved path, returning success or failure to orchestration.

## Requirements

### Requirement: Path-only input
`reveal` SHALL accept a resolved absolute path (and only that path) as defined in `spec.md` §6.5.

#### Scenario: Hardcoded valid path
- **GIVEN** an existing file path on the demo Windows machine
- **WHEN** `reveal` is called
- **THEN** Explorer MUST open the containing folder with the file selected and the function MUST return `true`

### Requirement: Failure boolean
If the file is missing or the OS action fails, `reveal` MUST return `false` rather than crashing the pipeline.

#### Scenario: File deleted between match and reveal
- **GIVEN** a path that no longer exists
- **WHEN** `reveal` runs
- **THEN** it MUST return `false` and MUST NOT raise an unhandled exception to orchestration

### Requirement: Windows demo target
MVP reveal SHALL target Windows (`explorer /select,<path>` or equivalent) as the primary demo OS.

#### Scenario: Windows select
- **GIVEN** the locked Windows demo machine
- **WHEN** reveal succeeds
- **THEN** the selected file MUST be visibly highlighted in Explorer
