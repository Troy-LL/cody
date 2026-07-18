# Query Understanding (NLU)

| Field | Value |
|-------|-------|
| **Owner** | Person 4 |
| **Purpose** | Normalize messy Taglish/English queries into structured `QueryIntent`. |
| **Owns** | `nlu/` package and `parse_query` entry point. |
| **Does not own** | Matching, TTS, indexing, UI. |
| **Frozen I/O** | `parse_query(text: str) -> QueryIntent` per `spec.md` §6.3. |
| **Stub requirement** | Stub raises `NotImplementedError` until fixture-shaped return lands (Task 2 / 0:30). |
| **Test command** | `python -m pytest nlu/tests -q` (owner adds tests). |
| **Branch** | `feature/nlu` |
| **Done condition** | Taglish code-switching and relative time phrases resolve against current date. |
| **Integration handoff** | Orchestration imports `nlu.parse_query.parse_query`. Do not import other components. |
