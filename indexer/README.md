# Indexer

| Field | Value |
|-------|-------|
| **Owner** | Person 2 (Vincent) |
| **Purpose** | Walk a target folder and emit file metadata for every top-level file. |
| **Owns** | `indexer/` package and `index_folder` entry point. |
| **Does not own** | Content extraction, matching, UI, recursive deep walks (MVP is top-level). |
| **Frozen I/O** | `index_folder(path: str) -> list[FileRecord]` per `spec.md` §6.1. |
| **Behavior** | Top-level files only; metadata via `stat` (no content reads); ISO-8601 UTC timestamps; extension `""` when none. |
| **Test command** | `python -m pytest indexer/tests -q` |
| **Branch** | `vincent` |
| **Done condition** | Any folder path returns valid `FileRecord` JSON for every top-level file. |
| **Integration handoff** | Orchestration imports `indexer.index_folder.index_folder`. Do not import other components. |
