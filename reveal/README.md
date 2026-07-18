# Reveal Layer

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (also owns `voice/`) |
| **Purpose** | OS-native folder open + file select/highlight on Windows. |
| **Owns** | `reveal/` package and `reveal` entry point. |
| **Does not own** | Matching, in-app baseline animation (§6.7 is orchestration), stretch overlay (§6.8). |
| **Frozen I/O** | `reveal(path: str) -> bool` per `spec.md` §6.5. |
| **Stub requirement** | Stub raises `NotImplementedError` until fixture-shaped return lands (Task 2 / 0:30). |
| **Test command** | `python -m pytest reveal/tests -q` (owner adds tests). |
| **Branch** | `feature/reveal` |
| **Done condition** | Hardcoded valid path opens Explorer and visibly selects the file on Windows. |
| **Integration handoff** | Orchestration imports `reveal.reveal.reveal`. Keep `voice/` changes on `feature/voice`. |
