# Cody desktop app (Tkinter)

A real window you can see and click. Points at **Notion Installer** in Downloads.

## Run (dev)

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python -m overlay
```

- Button **Point → Notion Installer**
- Hotkey **Ctrl+Shift+C**
- **Quit** or close the window

## Build `.exe`

```powershell
.\scripts\build_cody_exe.ps1
```

Then double-click `dist\Cody.exe`.

## Tests

```powershell
.\.venv\Scripts\python -m pytest overlay/tests -q
```
