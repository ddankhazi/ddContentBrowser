@echo off
REM DD Content Browser - Standalone Launcher (Windows)
REM Uses Python 3.11 with company PySide6 libraries

echo Starting DD Content Browser (Standalone)...

REM Set Python 3.11 path
set PYTHON_311=C:\Python311\python.exe

REM Check if Python 3.11 exists
if not exist "%PYTHON_311%" (
    echo ERROR: Python 3.11 not found at %PYTHON_311%
    echo Please update the path in launch_standalone.bat
    pause
    exit /b 1
)

REM Launch with Python 3.11
"%PYTHON_311%" standalone_launcher.py

pause
