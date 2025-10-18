' DD Content Browser - Silent Launcher (HOME version)
' Launches without console window

Set WshShell = CreateObject("WScript.Shell")

' Script path (same directory as this VBS file)
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
wrapperBat = scriptDir & "\launch_silent_wrapper.bat"

' Launch wrapper batch in hidden mode (0 = hidden, False = don't wait)
WshShell.Run """" & wrapperBat & """", 0, False

' Exit VBScript
Set WshShell = Nothing
