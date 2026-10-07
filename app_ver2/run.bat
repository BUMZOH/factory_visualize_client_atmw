@echo off   

REM Change to the folder containing run.bat
cd /d "%~dp0"

REM Use the virtual environment in the parent folder
set "PYTHON=..\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ERROR: Python not found.
    echo Please create .venv in the parent folder.
    pause
    exit /b 1
)

REM Start the application
"%PYTHON%" app.py

pause