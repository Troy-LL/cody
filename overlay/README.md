# Cody companion cursor (Tkinter)

Small Cody sits next to your mouse. Ask questions about what's on screen; Cody captures one screenshot, calls OpenAI, and can fly to UI elements with pixel-perfect OCR pointing. Replies show in a bubble and speak via ElevenLabs.

## Run

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\pip install -e ".[overlay]"
.\.venv\Scripts\python -m overlay
```

Needs [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) on PATH for screen scanning and pointing.

## API keys

Paste keys in the panel and **Save**. Both are stored in gitignored `voice/config.local.json` (or set `OPENAI_API_KEY` / ElevenLabs env vars).

| Key | Purpose |
|-----|---------|
| **OpenAI** | Vision + chat — Cody sees your screen and answers |
| **ElevenLabs** | Text-to-speech for replies |

All API calls go direct from your machine. No Cloudflare worker or hosted proxy.

## Voice

- **Hey Cody, where's my ___** — wake phrase (also accepts “Codey”). Cody records your question, sends one screenshot to OpenAI, speaks the reply, and points if the model names a target.
- **Hey Cody** alone — Cody listens for your follow-up question.
- **Ctrl+Shift+Space** — push-to-talk (same OpenAI path; works when the panel is not focused in a text field).

## Manual pointing (OCR)

| Control | Action |
|---------|--------|
| **Space** / **Scan** / **R** | Full-screen OCR — numbered finds in the panel |
| **1–9** / **z–m** | Fly Cody to that find (pixel coords from OCR boxes) |
| **Listen** | Restart mic |
| **Esc** | Quit |

Use scan + hotkeys when you want to point without asking the model.
