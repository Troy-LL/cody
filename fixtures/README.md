# Shared fixtures

Sample `FileRecord`, `ExtractedContent`, and `QueryIntent` JSON for parallel component work before live folder / matcher exist.

## Rules

- **Additive-only** during the sprint: you may add optional fields or new sample rows; do not rename, remove, or retype existing keys.
- Consumers ignore unknown fields (spec §6.9).
- Paths are demo-shaped Windows paths under `C:/Users/troy/Desktop` — not required to exist on disk for contract tests.

## Contents

| File | Shape |
|------|-------|
| `file_records.json` | `FileRecord[]` |
| `extracted_content.json` | `ExtractedContent[]` |
| `query_intents.json` | `QueryIntent[]` |

Load helpers: `fixtures/load.py`.
