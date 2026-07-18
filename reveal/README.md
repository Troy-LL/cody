# Reveal Layer

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (also owns `voice/`, `overlay/`) |
| **Purpose** | OS-native folder open + file select/highlight on Windows. |
| **Owns** | `reveal/` package and `reveal` entry point. |
| **Does not own** | Matcher; AI cursor geometry lives in `overlay/`. |
| **Frozen I/O** | `reveal(path: str) -> bool` per `spec.md` §6.5. |
| **Test command** | `python -m pytest reveal/tests -q` |
| **Branch** | `feature/voice` (Person 6 redirected scope) |

## Behavior

- `Path.expanduser().resolve()` then `is_file()`
- Windows: `explorer /select,{abs}` via `subprocess` (`shell=False`); ignore exit code
- Non-Windows / missing file → `false`
