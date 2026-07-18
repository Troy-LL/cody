# Cody

Cody is an AI that **shows you where a file is** instead of explaining how to dig for it.

You describe a file in plain (messy, Taglish-friendly) language. Cody searches a real local folder by metadata and content, then opens the folder, selects the file, and speaks a short confirmation. The point of the product is that last moment: pointing, not instructions.

Example: *"yung resibo ko sa Lazada last week"* → Cody finds the receipt PDF, highlights it in Explorer, and says so out loud.

## What it does

1. You pick a folder and type a natural-language query (English or Taglish).
2. Cody indexes the folder, extracts text from PDF/docx/txt, and understands the query (including relative time like "last week").
3. The matcher picks a best match and explains why.
4. The app animates toward that path, reveals the file in the OS, and narrates the result (English or Tagalog).

MVP is a single happy path on a Windows demo machine. Voice **input** and cloud sync are out of scope for now.

Product truth and contracts live in [`spec.md`](spec.md).

## Requirements

- Python 3.12+
- Windows is the locked demo target (reveal uses Explorer select)
- On Linux, Qt may need system libs (`libegl1`, `libxcb-cursor0`, `libxkbcommon-x11-0`, …) for `xcb` / `offscreen`

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
```

If OneDrive `MAX_PATH` bites you on Windows, install `PySide6-Essentials` instead of full `PySide6` (see note in `pyproject.toml`).

## Run

Desktop app (stub seats until live packages are wired):

```bash
python -m orchestration.main --demo-stubs
```

Desktop companion cursor (voice + full-screen OCR pointing):

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\pip install -e ".[overlay]"
.\.venv\Scripts\python -m overlay
```

Say **Hey Cody, where's my ___** (or type + Find). Details: [`overlay/README.md`](overlay/README.md).

Browser cursor overlay demo (mock desktop + pointing animation):

```bash
python -m http.server 8765
```

Then open [http://localhost:8765/demo/cody-cursor/overlay.html](http://localhost:8765/demo/cody-cursor/overlay.html). Details: [`demo/cody-cursor/README.md`](demo/cody-cursor/README.md).

## Test

```bash
set QT_QPA_PLATFORM=offscreen
python -m pytest
```

## Contributing

- Setup and package layout: [`AGENTS.md`](AGENTS.md)
- Sprint seats and parallel build map: [`docs/team/SPRINT-MAP.md`](docs/team/SPRINT-MAP.md)
- Team process: [`docs/team/SDD-ETIQUETTE.md`](docs/team/SDD-ETIQUETTE.md)
