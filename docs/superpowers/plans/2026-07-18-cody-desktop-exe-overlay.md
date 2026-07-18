# Cody desktop exe overlay — Implementation Plan

> **For agentic workers:** implement top-to-bottom; commit after each green slice. SPEED MODE → push `main`.

**Goal:** Runnable `python -m overlay` + PyInstaller `Cody.exe` that hotkeys to Notion Installer.

**Files:** `overlay/{__init__,app,cursor_window,find_target,icon_bounds,hotkey}.py`, `overlay/README.md`, `overlay/tests/test_find_target.py`, `pyproject.toml`, `scripts/build_cody_exe.ps1`

## Task 1: find_target + tests

- Glob Downloads for `Notion Installer*`; return absolute path or None.
- Pytest with tmp_path monkeypatch of downloads root.

## Task 2: cursor_window + hotkey + app

- Transparent always-on-top click-through widget; follow mouse; point animation; caption.
- Win32 `RegisterHotKey` Ctrl+Shift+C / Q; Esc via Qt.
- Wire reveal + icon_bounds soft-fail.

## Task 3: package

- Add `overlay*` to setuptools; README run/build; `scripts/build_cody_exe.ps1`; push main.
