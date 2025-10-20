# ddContentBrowser
Content Browser for Maya by Denes Dankhazi

launcher starter script (python): 

import maya.cmds as cmds

exec(open(cmds.internalVar(userScriptDir=True) + 'launch_browser_full_reload.py').read())
