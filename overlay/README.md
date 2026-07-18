# Cody Cursor Overlay (core MVP)

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (with `reveal/` + `voice/`) for this redirected scope |
| **Purpose** | Clicky-style desktop AI cursor: follow, then point at the real Explorer file icon. |
| **Owns** | `overlay/` package: `start_follow`, `point_at`, `stop` |
| **Does not own** | Matcher/NLU, PySide query shell (orchestration wires when ready) |
| **Contract** | See `docs/superpowers/specs/2026-07-18-cody-clicky-overlay-scope-design.md` |
| **Test command** | `python -m pytest overlay/tests -q` |
| **Branch** | `feature/voice` (Person 6 seat carrying voice + cursor + reveal) |

## API

```python
from overlay import start_follow, point_at, stop

start_follow()
ok = point_at(r"C:\path\to\file.pdf")  # animate toward icon / soft fallback
stop()
```

Optional: `pip install uiautomation` for real Explorer icon bounds. Without it, `point_at` soft-falls back to a mouse-relative nudge after `reveal`.
