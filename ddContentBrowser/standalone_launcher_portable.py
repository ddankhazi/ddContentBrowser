"""
DD Content Browser - Standalone Launcher (PORTABLE version)
Launch the content browser without Maya - portable, works if any Python 3.11 is available

Usage:
    python standalone_launcher_portable.py
"""

import sys
from pathlib import Path

# Get script directory
script_dir = Path(__file__).parent

# Add parent directory to path (so we can import ddContentBrowser as a package)
parent_dir = script_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Add external_libs to path if exists
external_libs = script_dir / "external_libs"
if external_libs.exists() and str(external_libs) not in sys.path:
    sys.path.insert(0, str(external_libs))

# Import Qt
try:
    from PySide6 import QtWidgets, QtCore
    from PySide6.QtCore import Qt
    print("Using PySide6")
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
        from PySide2.QtCore import Qt
        print("Using PySide2")
    except ImportError:
        print("Error: PySide2 or PySide6 required!")
        print("\nTo install PySide6, run:")
        print("    pip install PySide6")
        print("\nOr for PySide2:")
        print("    pip install PySide2")
        sys.exit(1)

# Import browser as package
try:
    from ddContentBrowser.browser import DDContentBrowser
except ImportError as e:
    print(f"Error importing browser: {e}")
    print(f"\nPython path:")
    for p in sys.path:
        print(f"  {p}")
    sys.exit(1)

def main():
    """Launch standalone content browser (PORTABLE version)"""
    print("=" * 60)
    print("DD Content Browser - Standalone (PORTABLE)")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Script dir: {script_dir}")
    print("=" * 60)
    
    # Create QApplication if it doesn't exist
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle('Fusion')  # Modern dark theme
        # Windows: Set AppUserModelID for proper taskbar icon
        try:
            import ctypes
            myappid = 'ddankhazi.DDContentBrowser.Portable.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    # Set dark palette and stylesheet (Maya-like theme)
    try:
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt
        palette = app.palette()
        palette.setColor(QPalette.Window, QColor(68, 68, 68))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
        palette.setColor(QPalette.ToolTipBase, QColor(58, 58, 58))
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(60, 60, 60))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        app.setPalette(palette)
        app.setStyleSheet("""
            QMainWindow { background-color: #444444; }
            QWidget { background-color: #444444; color: #e0e0e0; }
            QMenuBar { background-color: #3c3c3c; color: #e0e0e0; border-bottom: 1px solid #2a2a2a; }
            QMenuBar::item:selected { background-color: #0078d4; }
            QMenu { background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #555; }
            QMenu::item:selected { background-color: #0078d4; }
            QPushButton { background-color: #3c3c3c; color: #e0e0e0; border: 1px solid #555; padding: 5px; border-radius: 2px; }
            QPushButton:hover { background-color: #4a4a4a; border: 1px solid #0078d4; }
            QPushButton:pressed { background-color: #0078d4; }
            QPushButton:checked { background-color: #0078d4; border: 1px solid #0078d4; }
            QLineEdit, QTextEdit, QPlainTextEdit { background-color: #2a2a2a; color: #e0e0e0; border: 1px solid #555; padding: 3px; border-radius: 2px; }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border: 1px solid #0078d4; }
            QComboBox { background-color: #3c3c3c; color: #e0e0e0; border: 1px solid #555; padding: 3px; border-radius: 2px; }
            QComboBox:hover { border: 1px solid #0078d4; }
            QComboBox::drop-down { border: none; background-color: #3c3c3c; }
            QComboBox QAbstractItemView { background-color: #3a3a3a; color: #e0e0e0; selection-background-color: #0078d4; border: 1px solid #555; }
            QListView, QTreeView, QTableView { background-color: #2a2a2a; color: #e0e0e0; border: 1px solid #555; selection-background-color: #0078d4; selection-color: white; alternate-background-color: #323232; }
            QListView::item:hover, QTreeView::item:hover, QTableView::item:hover { background-color: #3a3a3a; }
            QScrollBar:vertical { background-color: #2a2a2a; width: 14px; border: none; }
            QScrollBar::handle:vertical { background-color: #555; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background-color: #666; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar:horizontal { background-color: #2a2a2a; height: 14px; border: none; }
            QScrollBar::handle:horizontal { background-color: #555; border-radius: 3px; min-width: 20px; }
            QScrollBar::handle:horizontal:hover { background-color: #666; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
            QSplitter::handle { background-color: #555; }
            QSplitter::handle:hover { background-color: #0078d4; }
            QStatusBar { background-color: #3c3c3c; color: #e0e0e0; border-top: 1px solid #2a2a2a; }
            QToolBar { background-color: #3c3c3c; border: none; spacing: 3px; padding: 3px; }
            QGroupBox { background-color: #3c3c3c; border: 1px solid #555; border-radius: 3px; margin-top: 1ex; padding-top: 10px; color: #e0e0e0; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #e0e0e0; }
            QCheckBox, QRadioButton { color: #e0e0e0; spacing: 5px; }
            QCheckBox::indicator, QRadioButton::indicator { width: 13px; height: 13px; background-color: #2a2a2a; border: 1px solid #555; border-radius: 2px; }
            QCheckBox::indicator:hover, QRadioButton::indicator:hover { border: 1px solid #0078d4; }
            QCheckBox::indicator:checked, QRadioButton::indicator:checked { background-color: #0078d4; border: 1px solid #0078d4; }
            QTabWidget::pane { background-color: #444444; border: 1px solid #555; }
            QTabBar::tab { background-color: #3c3c3c; color: #e0e0e0; border: 1px solid #555; padding: 5px 10px; border-bottom: none; }
            QTabBar::tab:selected { background-color: #444444; border-bottom: 2px solid #0078d4; }
            QTabBar::tab:hover { background-color: #4a4a4a; }
        """)
    except Exception as e:
        print(f"Warning: Could not apply dark theme: {e}")
        pass
    # Set application icon
    try:
        from PySide6.QtGui import QIcon
        icon_path = script_dir.parent / "icons" / "ddContentBrowser.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            print(f"Icon loaded: {icon_path}")
        else:
            print(f"Icon not found: {icon_path}")
    except Exception as e:
        print(f"Could not load icon: {e}")
    # Create and show browser (parent=None for standalone)
    browser = DDContentBrowser(parent=None)
    browser.setWindowTitle("DD Content Browser (Standalone - PORTABLE)")
    # Set window icon for browser window too
    try:
        from PySide6.QtGui import QIcon
        icon_path = script_dir.parent / "icons" / "ddContentBrowser.png"
        if icon_path.exists():
            browser.setWindowIcon(QIcon(str(icon_path)))
    except:
        pass
    browser.show()
    browser.raise_()
    browser.activateWindow()
    print("\nBrowser window opened!")
    print("Close the window to exit.")
    # Run event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
