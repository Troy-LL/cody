# Content Extractor

| Field | Value |
|-------|-------|
| **Owner** | Person 3 |
| **Purpose** | Given a file path, return extracted text snippet or a graceful non-extractable result. |
| **Owns** | `extractor/` package and `extract` entry point. |
| **Does not own** | Indexing, OCR/images, matching, UI. |
| **Frozen I/O** | `extract(path: str) -> ExtractedContent` per `spec.md` §6.2. |
| **Stub requirement** | Stub raises `NotImplementedError` until fixture-shaped return lands (Task 2 / 0:30). |
| **Test command** | `python -m pytest extractor/tests -q` (owner adds tests). |
| **Branch** | `feature/extractor` |
| **Done condition** | PDF/docx/txt snippets extract correctly; unsupported files return `extractable: false`. |
| **Integration handoff** | Orchestration imports `extractor.extract.extract`. Do not import other components. |
