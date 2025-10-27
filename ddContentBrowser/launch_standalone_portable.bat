@echo off
setlocal enabledelayedexpansion
REM DD Content Browser - Standalone Launcher (PORTABLE version)
REM Tries to find Python 3.11 in PATH or common locations

echo Starting DD Content Browser (Standalone - PORTABLE)...

REM Try to find python 3.11 executable
set "PYTHON_CMD="

REM 1. Check if python311 is in PATH
where python311 >nul 2>nul && set "PYTHON_CMD=python311"

REM 2. If not found, check if python is in PATH and is version 3.11
if "%PYTHON_CMD%"=="" (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        for /f "tokens=2 delims=. " %%v in ('"%%i" --version 2^>nul') do (
            if "%%v"=="3" (
                for /f "tokens=3 delims=. " %%w in ('"%%i" --version 2^>nul') do (
                    if "%%w"=="11" set "PYTHON_CMD=%%i"
                )
            )
        )
    )
)

REM 3. If still not found, check common install locations
if "%PYTHON_CMD%"=="" (
    REM Check C:\Python311 first (common system-wide install)
    if exist "C:\Python311\python.exe" set "PYTHON_CMD=C:\Python311\python.exe"
)

if "%PYTHON_CMD%"=="" (
    REM Check user AppData location
    set COMMON_PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
    if exist "!COMMON_PYTHON!" (
        echo Found Python at !COMMON_PYTHON!
        set "PYTHON_CMD=!COMMON_PYTHON!"
    ) else (
        echo Checking Python installation in user directory...
        dir "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\" 2>nul
    )
)

REM 4. If still not found, prompt user
if "%PYTHON_CMD%"=="" (
    echo ERROR: Could not find Python 3.11 in PATH or common locations.
    echo Please install Python 3.11 and ensure it is in your PATH.
    pause
    exit /b 1
)

echo Using Python: %PYTHON_CMD%

REM Check if PySide6 is installed
"%PYTHON_CMD%" -c "import PySide6" 2>nul
if errorlevel 1 (
    echo Installing PySide6...
    "%PYTHON_CMD%" -m pip install PySide6
)

echo Starting application...
"%PYTHON_CMD%" standalone_launcher_portable.py

pause