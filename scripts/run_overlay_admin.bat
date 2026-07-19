@echo off
setlocal
REM Elevate + run Cody overlay. Self-contained (no .ps1) so ExecutionPolicy cannot block it.
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "PY=%ROOT%\.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo Missing "%PY%"
  echo Create the venv and run: .\.venv\Scripts\pip install -e ".[overlay]"
  pause
  exit /b 1
)

REM Already admin? run directly.
net session >nul 2>&1
if %errorlevel%==0 goto :run

REM Re-launch this bat elevated (UAC).
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%ROOT%'"
exit /b 0

:run
cd /d "%ROOT%"
set "PYTHONPATH=%ROOT%"
echo Cody overlay running as Administrator
"%PY%" -m overlay
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" pause
exit /b %EC%
