@echo off
rem ============================================================
rem  Plan B (local backup) for Windows.  Double-click to start.
rem  Optional: run from Command Prompt with  run_dashboard.bat --server.address 0.0.0.0
rem  to let other computers on the same network open it.
rem  NOTE: written carefully but NOT yet tested on a real Windows machine.
rem ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python was not found. Install Python 3.10 or newer from python.org and tick "Add python.exe to PATH".
  pause
  exit /b 1
)
%PY% --version

if not exist ".venv\Scripts\python.exe" (
  echo Creating local environment .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create .venv
    pause
    exit /b 1
  )
)

if not exist ".venv\.installed" (
  echo Installing libraries - internet is needed the first time only ...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements-tested.txt
  if errorlevel 1 (
    echo Exact versions failed, trying flexible versions ...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
      echo [ERROR] Installation failed. Check the internet connection and try again.
      pause
      exit /b 1
    )
  )
  echo done> ".venv\.installed"
)

".venv\Scripts\python.exe" preflight.py
if errorlevel 1 (
  echo [ERROR] Pre-flight check failed. Read the FAIL lines above.
  pause
  exit /b 1
)

echo.
echo Open http://localhost:8501 in your browser. Press Ctrl+C in this window to stop.
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 %*
pause
