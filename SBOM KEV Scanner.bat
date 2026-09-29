@echo off
REM Double-click launcher for the SBOM KEV Scanner (Windows).
REM Runs the GUI from this folder using your installed Python.

setlocal
cd /d "%~dp0"

REM Prefer pythonw (no console window) for the GUI; fall back to python.
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0run.py"
    goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0run.py"
    if errorlevel 1 (
        echo.
        echo The application exited with an error. See the message above.
        pause
    )
    goto :eof
)

echo Python was not found on your PATH.
echo Install Python 3.10+ from https://www.python.org/downloads/ and try again.
pause
endlocal
