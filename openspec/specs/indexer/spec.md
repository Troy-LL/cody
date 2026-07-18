## Purpose

The indexer walks a Windows demo folder at top level and emits `FileRecord` metadata for every file so downstream matching can reason over the set without reading file bytes.

## Requirements

### Requirement: Top-level folder walk
`index_folder` SHALL enumerate only immediate children of the given folder path (non-recursive for MVP) and MUST return one `FileRecord` per file.

#### Scenario: Flat demo folder
- **GIVEN** a folder containing several files and one subdirectory
- **WHEN** `index_folder` is called on that folder
- **THEN** it MUST return `FileRecord` entries for the files and MUST NOT recurse into the subdirectory

### Requirement: FileRecord shape
Each emitted record SHALL include `path`, `filename`, `extension`, `size_bytes`, `created_at`, and `modified_at` as defined in `spec.md` §6.1.

#### Scenario: PDF on Desktop
- **GIVEN** a PDF file exists in the target folder
- **WHEN** indexing completes
- **THEN** the corresponding record MUST expose absolute `path`, filename with extension, and ISO-8601 timestamps

### Requirement: Read-only indexing
The indexer MUST NOT modify, move, or delete anything inside the scanned folder.

#### Scenario: Scan completes
- **GIVEN** a writable demo folder
- **WHEN** `index_folder` finishes successfully
- **THEN** folder contents and file bytes MUST be unchanged
