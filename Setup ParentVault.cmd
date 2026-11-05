@echo off
@rem Keep environment changes local to this launcher run.
setlocal
@rem Switch to the drive and directory containing the project.
cd /d "%~dp0"
@rem Create the isolated Python 3.12 environment beside the app.
py -3.12 -m venv .venv
@rem Show the setup failure message if the previous step failed.
if errorlevel 1 goto failed
@rem Install dependencies using the new environment's interpreter.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
@rem Show the setup failure message if the previous step failed.
if errorlevel 1 goto failed
echo Setup complete. Double-click Start ParentVault.cmd.
@rem Keep the message visible until the user presses a key.
pause
exit /b
:failed
echo Setup did not complete. Check that Python 3.12 is installed and internet access is available.
@rem Keep the message visible until the user presses a key.
pause
exit /b 1
