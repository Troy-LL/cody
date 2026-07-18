# Cody companion cursor (Tkinter)

Small Cody next to your mouse. Scan the screen, then point by voice or keys. A text bubble appears next to Cody; ElevenLabs speaks the line.

## Run

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\pip install -e ".[overlay]"
.\.venv\Scripts\python -m overlay
```

Needs [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) on PATH. Paste your ElevenLabs API key in the panel and **Save** (stored in gitignored `voice/config.local.json`).

## Voice

Say **Hey Cody, where's my ___** (also accepts “Codey”). Cody matches the list or re-OCRs the screen, flies to the best hit, shows a bubble (“Here's …”, “I think this is …”, etc.), and speaks it with ElevenLabs.

## Keys

| Control | Action |
|---------|--------|
| **Space** / **Scan** / **R** | Full-screen OCR |
| **1–9** / **z–m** | Point at finds |
| **Listen** | Restart mic |
| **Esc** | Quit |
