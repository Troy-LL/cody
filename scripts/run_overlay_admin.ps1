# Launch Cody overlay elevated (UAC).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $Root ".venv\Scripts\python.exe"

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($id)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Path $Python)) {
    Write-Error "Missing $Python - create the venv and run: .\.venv\Scripts\pip install -e `".[overlay]`""
}

if (-not (Test-IsAdmin)) {
    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $arg -WorkingDirectory $Root | Out-Null
    exit 0
}

Set-Location $Root
$env:PYTHONPATH = $Root
Write-Host "Cody overlay running as Administrator (pid $PID)"
& $Python -m overlay
exit $LASTEXITCODE
