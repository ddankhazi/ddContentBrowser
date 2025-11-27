@echo off
REM DD Content Browser - Standalone Launcher BAT
REM Uses company Python 3.11 installation

REM Set Python 3.11 path
set PYTHON_PATH=C:\Python311\python.exe

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Get version from __init__.py by parsing the file
for /f "tokens=2 delims='" %%i in ('findstr /C:"__version__ = " "%SCRIPT_DIR%__init__.py"') do set VERSION=%%i
if not defined VERSION set VERSION=Unknown

echo ============================================================
echo DD Content Browser v%VERSION% (Standalone)
echo ============================================================

REM Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo ERROR: Python 3.11 not found at: %PYTHON_PATH%
    echo.
    echo Please check the Python installation path.
    pause
    exit /b 1
)

echo Using Python: %PYTHON_PATH%
echo.

REM Run the launcher
"%PYTHON_PATH%" "%SCRIPT_DIR%standalone_launcher.py"

REM If window closes immediately, keep console open
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Browser failed to start!
    echo ============================================================
    pause
)
