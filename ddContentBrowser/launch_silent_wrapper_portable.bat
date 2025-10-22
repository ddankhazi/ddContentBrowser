@echo off
REM Silent wrapper for DD Content Browser (PORTABLE version)
REM Redirects output to nul to avoid console window

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
    set "COMMON_PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
    if exist "%COMMON_PYTHON%" set "PYTHON_CMD=%COMMON_PYTHON%"
)

REM 4. If still not found, exit silently
if "%PYTHON_CMD%"=="" (
    exit /b 1
)

REM Convert python.exe to pythonw.exe for silent execution
REM Extract directory and build pythonw.exe path
for %%F in ("%PYTHON_CMD%") do (
    set "PYTHON_DIR=%%~dpF"
    set "PYTHON_NAME=%%~nxF"
)

REM Check if pythonw.exe exists in the same directory
if exist "%PYTHON_DIR%pythonw.exe" (
    set "PYTHONW_CMD=%PYTHON_DIR%pythonw.exe"
) else (
    REM Fallback: use python.exe (will show console briefly)
    set "PYTHONW_CMD=%PYTHON_CMD%"
)

start /B "" "%PYTHONW_CMD%" "%~dp0standalone_launcher_portable.py"