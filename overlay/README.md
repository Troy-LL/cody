# Cody companion cursor (Tkinter)

Small Cody sits next to your mouse. Ask questions about what's on screen; Cody captures one screenshot, calls OpenAI, and can fly to UI elements with pixel-perfect OCR pointing. Replies show in a bubble and speak via ElevenLabs.

## Run

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\pip install -e ".[overlay]"
.\.venv\Scripts\python -m overlay
```

If Windows Security blocks mic, hotkeys, or capture, run elevated (UAC). Prefer the `.bat` (bypasses ExecutionPolicy):

```powershell
.\scripts\run_overlay_admin.bat
```

Built `dist\Cody.exe` also requests Administrator (`--uac-admin`).

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
- **Ctrl+Shift+Space** — hold to talk, release to send (same OpenAI path). Tray “Talk” uses a fixed-length clip.

## Pointing (voice / ask)

When Cody answers a “where is …” question, one screenshot goes to OpenAI together with a **scene card** (UIA names and bounds for the taskbar and foreground window) and a **grid legend** on an annotated copy of the image. The model returns `found`, optional cell id, and image pixels.

- **Scene + grid** — coarse layout from the grid; fine x,y when the model is confident.
- **`found=false`** — Cody speaks the reply only; the buddy does not move.
- **UIA** — named taskbar buttons and in-app controls (Settings list items, etc.) snap to accessibility bounds when the name matches; unlabeled icons still rely on vision + OCR snap.
- **Crop refine** — if the model only names a grid cell, a second zoomed vision pass may refine the point before fly.

**Manual smoke (operator):** 5 taskbar icons by name, 5 in-app controls in Settings, 3 missing targets → buddy stays put.

## Manual pointing (OCR)

| Control | Action |
|---------|--------|
| **Space** / **Scan** / **R** | Full-screen OCR — numbered finds in the panel |
| **1–9** / **z–m** | Fly Cody to that find (pixel coords from OCR boxes) |
| **Listen** | Restart mic |
| **Esc** | Quit |

Use scan + hotkeys when you want to point without asking the model.
