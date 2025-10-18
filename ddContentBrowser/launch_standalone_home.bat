@echo off
REM DD Content Browser - Standalone Launcher (HOME version)
REM Uses Python 3.11 from user's local installation

echo Starting DD Content Browser (Standalone - HOME)...

REM Set Python 3.11 path (your home installation)
set PYTHON_311=C:\Users\Danki\AppData\Local\Programs\Python\Python311\python.exe

REM Check if Python 3.11 exists
if not exist "%PYTHON_311%" (
    echo ERROR: Python 3.11 not found at %PYTHON_311%
    echo Please update the path in launch_standalone_home.bat
    pause
    exit /b 1
)

REM Launch with Python 3.11
"%PYTHON_311%" standalone_launcher_home.py

pause
