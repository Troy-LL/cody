# AGENTS.md

## Cursor Cloud specific instructions

Cody is a Python 3.12 PySide6 (Qt) desktop app that finds files from a natural-language (Taglish) query. The only runnable service is the GUI shell in `orchestration/`; the other top-level packages (`indexer/`, `extractor/`, `nlu/`, `matcher/`, `reveal/`, `voice/`) are per-seat components that are still `NotImplemented` and are exercised through fixture-backed stubs.

### Environment
- The project installs into `.venv` (created by the update script) as an editable package (`pip install -e .`). Activate with `.venv/bin/python` or `source .venv/bin/activate`.
- PySide6 needs system Qt libraries that are NOT pip-installed. These are preinstalled on the VM image; if a fresh VM ever lacks them, install: `libegl1 libgl1 libxkbcommon0 libxkbcommon-x11-0 libxcb-xkb1 libxcb-cursor0 libdbus-1-3 libfontconfig1` (plus the other `libxcb-*` helpers). Missing `libxkbcommon-x11.so.0` is the usual cause of "Could not load the Qt platform plugin xcb".

### Running the app
- A VNC desktop is available at `DISPLAY=:1`. Run the GUI there: `DISPLAY=:1 .venv/bin/python -m orchestration.main --demo-stubs --folder "C:/Users/troy/Desktop"`.
- Always use `--demo-stubs` until the teammate component packages are implemented; without it the live deps raise `NotImplementedError`.
- Hello-world flow: type a query (e.g. `yung resibo ko sa Lazada last week`) → click `Find` → status becomes `result` with a breadcrumb, filename, confidence, and reasoning.

### Testing
- Run tests with the offscreen Qt platform so no display is required: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`.
- Known caveat: `tests/orchestration/test_window.py::test_window_find_updates_result` fails on Linux because it asserts on `Path(windows_path).name`, and POSIX `pathlib` does not treat `\` as a separator (the sprint is "locked to a Windows demo machine"). This is a platform difference, not a setup or code regression — the other 30 tests pass.

### Lint / build
- There is no linter (no ruff/flake8/black/mypy config) and no build step beyond the editable install; `pytest` is the quality gate.
