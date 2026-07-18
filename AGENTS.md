# AGENTS.md

## Cursor Cloud specific instructions

Cody is a single PySide6 (Qt) desktop app on Python 3.12, packaged as the editable `cody`
package via `pyproject.toml`. Component packages (`indexer/`, `extractor/`, `nlu/`,
`matcher/`, `reveal/`, `voice/`) are mostly stubs; only `orchestration/` and `indexer/` are
implemented. Standard commands live in `pyproject.toml` and `README.md` — prefer those.

### Environment
- The update script installs into a virtualenv at `.venv` (`.venv/bin/python`, `.venv/bin/pytest`).
- System packages required by Qt are provisioned outside the update script (via `apt`):
  `python3.12-venv`, `libegl1`, `libgl1`, `libxkbcommon0`, `libxkbcommon-x11-0`, `libdbus-1-3`,
  `libfontconfig1`, `libnss3`, and the `libxcb-*` set (notably `libxcb-cursor0` for the `xcb`
  platform plugin). They persist in the VM snapshot, so the update script stays dependency-only.

### Running the app (dev)
- A display is available at `DISPLAY=:1`. Run the fixture-backed demo (no API keys) with:
  `DISPLAY=:1 .venv/bin/python -m orchestration.main --demo-stubs`.
- Live mode (`python -m orchestration.main`, no `--demo-stubs`) calls teammate entry points that
  still raise `NotImplementedError`; use `--demo-stubs` for any end-to-end run today.
- For headless smoke checks without a display, set `QT_QPA_PLATFORM=offscreen`.

### Tests
- `pytest` (config in `pyproject.toml`) only collects `tests/`. Component suites like
  `indexer/tests` must be named explicitly, e.g. `.venv/bin/python -m pytest indexer/tests`.
- Non-Qt suites pass cleanly: `tests/contracts`, `tests/team`, `indexer/tests`.
- Two known non-blocking issues on this Linux environment (the app is Windows-targeted per
  `spec.md`), not caused by setup:
  - `tests/orchestration/test_window.py::test_window_find_updates_result` fails because
    `Path(...).name` does not split Windows backslash paths on POSIX. Demo-stub paths use forward
    slashes, so the running app displays filenames correctly.
  - `tests/orchestration/test_controller.py` can intermittently segfault at teardown due to a
    PySide6/pytest-qt `QThread` cleanup race under the headless/xcb harness (crashes at a different
    test each run). Individual controller tests pass in isolation.

### Lint
- No linter/formatter/type-checker or CI is configured in this repo.
