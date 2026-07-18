# Contributor notes

Cody is a Python 3.12 PySide6 desktop app. The runnable shell is `orchestration/`; seat packages (`indexer/`, `extractor/`, `nlu/`, `matcher/`, `reveal/`, `voice/`) implement frozen contracts in `spec.md`.

## Setup

```
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
```

On Linux, Qt may need system libraries (`libegl1`, `libxcb-cursor0`, `libxkbcommon-x11-0`, etc.) for the `xcb` / `offscreen` plugins.

## Run

```
python -m orchestration.main --demo-stubs
```

Use `--demo-stubs` until live seat packages are ready.

## Test

```
set QT_QPA_PLATFORM=offscreen
python -m pytest
```

Windows is the locked demo target. Some path assertions in orchestration window tests assume Windows-style paths.
