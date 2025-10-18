' DD Content Browser - Silent Launcher (HOME version)
' Launches without console window

Set WshShell = CreateObject("WScript.Shell")

' Python path
pythonPath = "C:\Users\Danki\AppData\Local\Programs\Python\Python311\python.exe"

' Script path (same directory as this VBS file)
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonScript = scriptDir & "\standalone_launcher_home.py"

' Launch Python script hidden (0 = hidden, False = don't wait)
WshShell.Run """" & pythonPath & """ """ & pythonScript & """", 0, False

' Exit VBScript
Set WshShell = Nothing
