@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
  start "ParentVault" ".venv\Scripts\pythonw.exe" "app.py"
  exit /b
)
if exist "%USERPROFILE%\Documents\Codex\pv-env\Scripts\pythonw.exe" (
  start "ParentVault" "%USERPROFILE%\Documents\Codex\pv-env\Scripts\pythonw.exe" "app.py"
  exit /b
)
echo Python dependencies are not configured. Run Setup ParentVault.cmd first.
pause
