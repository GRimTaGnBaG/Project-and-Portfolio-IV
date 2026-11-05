@echo off
@rem Keep environment changes local to this launcher run.
setlocal
@rem Switch to the drive and directory containing the project.
cd /d "%~dp0"
@rem Use the environment installed inside the project folder when available.
if exist ".venv\Scripts\pythonw.exe" (
  @rem Launch the desktop app with the selected interpreter.
  start "ParentVault" ".venv\Scripts\pythonw.exe" "app.py"
  exit /b
)
@rem Try the existing development environment if the project has none.
if exist "%USERPROFILE%\Documents\Codex\pv-env\Scripts\pythonw.exe" (
  @rem Launch the desktop app with the selected interpreter.
  start "ParentVault" "%USERPROFILE%\Documents\Codex\pv-env\Scripts\pythonw.exe" "app.py"
  exit /b
)
echo Python dependencies are not configured. Run Setup ParentVault.cmd first.
@rem Keep the message visible until the user presses a key.
pause
