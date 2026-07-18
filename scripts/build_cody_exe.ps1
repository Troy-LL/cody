# Build dist\Cody.exe for the desktop overlay.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path .venv\Scripts\python.exe)) {
  python -m venv .venv
}
.\.venv\Scripts\pip install -U pip
.\.venv\Scripts\pip install -e ".[overlay]"

.\.venv\Scripts\pip install pyinstaller
.\.venv\Scripts\pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name Cody `
  --paths $Root `
  --hidden-import overlay `
  --hidden-import overlay.tk_lens `
  --hidden-import overlay.find_target `
  --hidden-import reveal `
  --hidden-import reveal.reveal `
  overlay\__main__.py

Write-Host "Built: $Root\dist\Cody.exe"
if (Test-Path "$Root\dist\Cody.exe") {
  Start-Process "$Root\dist\Cody.exe"
}
