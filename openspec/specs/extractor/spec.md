## Purpose

The content extractor turns a single file path into `ExtractedContent` with a bounded text snippet for PDF, docx, and txt, while failing gracefully for unsupported types.

## Requirements

### Requirement: Supported text extraction
For PDF, docx, and txt inputs, `extract` SHALL return `extractable: true` with a non-empty `text_snippet` capped around 500–1000 characters and a populated `extraction_method`.

#### Scenario: Lazada receipt PDF
- **GIVEN** a PDF with a text layer containing "Lazada"
- **WHEN** `extract` is called on that path
- **THEN** the result MUST set `extractable` true and include a snippet referencing order content

### Requirement: Unsupported files fail soft
For unsupported or binary files, `extract` MUST return `extractable: false` with `text_snippet: null` and MUST NOT raise in a way that breaks the pipeline.

#### Scenario: Image file
- **GIVEN** a `.png` path
- **WHEN** `extract` runs
- **THEN** it MUST return `extractable: false` and `text_snippet: null`

### Requirement: Path echoed
The output SHALL include the same `path` value that was requested.

#### Scenario: Path round-trip
- **GIVEN** an absolute Windows path argument
- **WHEN** extraction returns
- **THEN** `path` in the result MUST equal the input path
