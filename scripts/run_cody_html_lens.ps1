# Run the HTML Cody magnifying-glass lens in a transparent host window.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path .venv\Scripts\python.exe)) {
  python -m venv .venv
}
.\.venv\Scripts\pip install -q pywebview

$env:PYTHONPATH = $Root
.\.venv\Scripts\python -m overlay.html_host
