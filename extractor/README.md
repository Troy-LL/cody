# Content Extractor

| Field | Value |
|-------|-------|
| **Owner** | Person 3 |
| **Purpose** | Given a file path, return extracted text snippet or a graceful non-extractable result. |
| **Owns** | `extractor/` package and `extract` entry point. |
| **Does not own** | Indexing, OCR/images, matching, UI. |
| **Frozen I/O** | `extract(path: str) -> ExtractedContent` per `spec.md` §6.2. |
| **Stub requirement** | Replaced by real `extract` — PDF/docx/txt + soft-fail unsupported. |
| **Test command** | `python -m pytest extractor/tests -q` (owner adds tests). |
| **Branch** | `feature/extractor` |
| **Done condition** | PDF/docx/txt snippets extract correctly; unsupported files return `extractable: false`. |
| **Integration handoff** | Orchestration imports `extractor.extract.extract`. Do not import other components. |
| **Deps** | `pypdf` for PDF text layer; docx via stdlib `zipfile` + `ElementTree` (no lxml). |

## Usage

```python
from extractor.extract import extract

result = extract(r"C:\Users\you\Desktop\receipt.pdf")
# path echoed; extractable True/False; text_snippet capped ≤1000 chars;
# extraction_method: plain_text | pdf_text_layer | docx_paragraphs | unsupported
```

Supported extensions (case-insensitive): `.txt`, `.pdf`, `.docx`. Unsupported, missing, corrupt, or empty-text files soft-fail with `extractable: false` (never raise).

**Live app:** orchestration imports `extract` when you run `python -m orchestration.main` (no `--demo-stubs`).  
**Demo path:** `--demo-stubs` uses fixture stubs, not this live extractor.

**Tests:** `python -m pytest extractor/tests -q`
