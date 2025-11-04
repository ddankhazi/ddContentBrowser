@echo off
REM DD Content Browser - Silent Standalone Launcher BAT (INTERNAL)
REM Uses company Python 3.11 installation - NO CONSOLE WINDOW

REM Set Python 3.11 path (use pythonw.exe for no console)
set PYTHON_PATH=C:\Python311\pythonw.exe

REM Check if Python exists
if not exist "%PYTHON_PATH%" (
    REM Fallback to python.exe if pythonw.exe doesn't exist
    set PYTHON_PATH=C:\Python311\python.exe
)

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Run the launcher (silent - no console window)
start "" "%PYTHON_PATH%" "%SCRIPT_DIR%ddContentBrowser_internal.pyw"
