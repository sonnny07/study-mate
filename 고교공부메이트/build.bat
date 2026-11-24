@echo off
rem ===== GosuMate exe build script =====
rem Put this file and study_mate.py in the SAME folder (English path recommended, e.g. C:\study_mate)

cd /d "%~dp0"

if not exist study_mate.py (
  echo [ERROR] study_mate.py was not found in this folder.
  goto fail
)

rem --- find Python ("python" first, then "py") ---
set PY=python
%PY% --version >nul 2>nul
if errorlevel 1 (
  set PY=py
  %PY% --version >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Install it from https://www.python.org and check "Add python.exe to PATH".
    goto fail
  )
)

echo [1/3] Installing / updating PyInstaller...
%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 goto fail

echo.
echo [2/3] Building GosuMate.exe (this can take 1-2 minutes)...
%PY% -m PyInstaller --onefile --windowed --clean --noconfirm --name GosuMate study_mate.py
if errorlevel 1 goto fail

echo.
echo [3/3] Done!  Your program is: dist\GosuMate.exe
echo       (The "build" folder and GosuMate.spec can be ignored.)
explorer dist
pause
exit /b 0

:fail
echo.
echo Build failed. Take a screenshot of this window and ask for help.
pause
exit /b 1
