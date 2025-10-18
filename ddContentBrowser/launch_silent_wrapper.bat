@echo off
REM Silent wrapper for DD Content Browser
REM Redirects output to nul to avoid console window

start /B "" "C:\Users\Danki\AppData\Local\Programs\Python\Python311\pythonw.exe" "%~dp0standalone_launcher_home.py"
