# Indexer

| Field | Value |
|-------|-------|
| **Owner** | Person 2 |
| **Purpose** | Walk a target folder and emit file metadata for every top-level file. |
| **Owns** | `indexer/` package and `index_folder` entry point. |
| **Does not own** | Content extraction, matching, UI, recursive deep walks (MVP is top-level). |
| **Frozen I/O** | `index_folder(path: str) -> list[FileRecord]` per `spec.md` §6.1. |
| **Stub requirement** | Real top-level walker landed; returns `FileRecord` dicts (extension `""` when none). |
| **Test command** | `python -m pytest indexer/tests -q` (owner adds tests). |
| **Branch** | `feature/indexer` |
| **Done condition** | Any folder path returns valid `FileRecord` JSON for every top-level file. |
| **Integration handoff** | Orchestration imports `indexer.index_folder.index_folder`. Do not import other components. |
