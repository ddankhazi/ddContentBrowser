"""
DD Content Browser - Standalone Launcher
Launch the content browser without Maya

Usage:
    python standalone_launcher.py
"""

import sys
from pathlib import Path

# Get script directory
script_dir = Path(__file__).parent

# Add parent directory to path (so we can import ddContentBrowser as a package)
parent_dir = script_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Add company Python libraries to path (Python 3.11 - PySide6 included)
company_lib = Path(r"C:\dApps\extensions\python\python_libraries\3.11\win64")
if company_lib.exists() and str(company_lib) not in sys.path:
    sys.path.insert(0, str(company_lib))

# Add external_libs to path
external_libs = script_dir / "external_libs"
if external_libs.exists() and str(external_libs) not in sys.path:
    sys.path.insert(0, str(external_libs))

# Import Qt
try:
    from PySide6 import QtWidgets, QtCore
    from PySide6.QtCore import Qt
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
        from PySide2.QtCore import Qt
    except ImportError:
        print("Error: PySide2 or PySide6 required!")
        print("Check company libraries at: C:\\dApps\\extensions\\python\\python_libraries\\3.11\\win64")
        sys.exit(1)

# Import browser as package
from ddContentBrowser.browser import DDContentBrowser


def main():
    """Launch standalone content browser"""
    # Create QApplication if it doesn't exist
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle('Fusion')  # Modern dark theme
    
    # Set dark palette (compatible with both PySide2 and PySide6)
    try:
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt
        
        palette = app.palette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)
    except:
        # Fallback - simpler palette setup
        pass
    
    # Create and show browser (parent=None for standalone)
    browser = DDContentBrowser(parent=None)
    browser.setWindowTitle("DD Content Browser (Standalone)")
    browser.show()
    browser.raise_()
    browser.activateWindow()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
