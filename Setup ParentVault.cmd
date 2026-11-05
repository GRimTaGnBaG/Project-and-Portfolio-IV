@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Setup complete. Double-click Start ParentVault.cmd.
pause
exit /b
:failed
echo Setup did not complete. Check that Python 3.12 is installed and internet access is available.
pause
exit /b 1
