# DD Content Browser - Standalone Mode

## Overview

The DD Content Browser can run **without Maya** as a standalone file browser with preview capabilities.

In standalone mode:
- ✅ **File browsing** - Full navigation, search, filtering
- ✅ **Preview panel** - Images, HDR/EXR, PDFs, text files
- ✅ **Batch rename** - All rename operations work
- ✅ **Favorites & Recent** - Folder bookmarks and history
- ✅ **Settings** - Full settings system
- ❌ **Maya import/reference** - Disabled (requires Maya)
- ❌ **Middle-drag import** - Disabled (requires Maya)

## Requirements

- **Python 3.11** - `C:\Python311`
- **PySide6** - Company libraries: `C:\dApps\extensions\python\python_libraries\3.11\win64`

All dependencies are pre-configured. No installation needed!

## Launch Methods

### Method 1: Batch File (Windows) - RECOMMENDED
Double-click `launch_standalone.bat`

This automatically uses:
- Python: `C:\Python311\python.exe`
- Libraries: `C:\dApps\extensions\python\python_libraries\3.11\win64`

### Method 2: Python Script
```bash
C:\Python311\python.exe standalone_launcher.py
```

### Method 3: Direct Import
```python
import sys
sys.path.insert(0, r'C:\dApps\extensions\python\python_libraries\3.11\win64')
sys.path.insert(0, r'C:\Users\dankhazid\Documents\maya\2026\scripts\ddContentBrowser')

from browser import DDContentBrowser
from PySide6 import QtWidgets

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
browser = DDContentBrowser(parent=None)
browser.setWindowTitle("DD Content Browser (Standalone)")
browser.show()
app.exec_()
```

## Use Cases

### 1. **File Organization**
Browse and organize project files without opening Maya

### 2. **Asset Preview**
Quick preview of HDR/EXR files with exposure control

### 3. **Batch Operations**
Rename hundreds of files with multi-rule system

### 4. **Cross-Platform File Browser**
Use on any system with Python + PySide (Windows/Mac/Linux)

## Limitations in Standalone Mode

- **No Maya Import**: Cannot import .ma/.mb files
- **No Maya Commands**: cmds/mel functions unavailable
- **No Scene Integration**: Cannot create file nodes or references

These features automatically become available when running inside Maya.

## Notes

- All settings are shared between Maya and standalone mode
- Thumbnail cache is shared (same cache folder)
- External libraries (OpenCV, PyMuPDF, NumPy) are included
- Dark theme automatically applied in standalone mode

---

**Author:** DankHazid  
**Version:** 2.4.1  
**License:** MIT
