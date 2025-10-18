"""
DD Content Browser - UI Widgets
Breadcrumb navigation, filter panel, preview panel, and custom list view

Author: DankHazid
License: MIT
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# UI Font - Default value (can be overridden by browser at runtime)
# Set to Segoe UI to match Windows/Maya default
UI_FONT = "Segoe UI"

# Add external_libs to path for OpenEXR
import sys
_external_libs = os.path.join(os.path.dirname(__file__), "external_libs")
if os.path.exists(_external_libs) and _external_libs not in sys.path:
    sys.path.insert(0, _external_libs)

# NumPy is built into Maya 2026+
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("NumPy not available")

# Try to import OpenEXR for proper HDR/EXR support
try:
    import OpenEXR
    import Imath
    OPENEXR_AVAILABLE = True
    # print(f"OpenEXR loaded - Full EXR support enabled")  # Commented to avoid duplicate messages
except ImportError:
    OPENEXR_AVAILABLE = False
    # print("OpenEXR not available - EXR preview will be limited")

# Try to import OpenCV for Radiance HDR (.hdr) support
try:
    import cv2
    OPENCV_AVAILABLE = True
    # print(f"OpenCV loaded - Full HDR support enabled")
except ImportError:
    OPENCV_AVAILABLE = False
    # print("OpenCV not available - HDR preview will be limited")

# Try to import PyMuPDF (fitz) for PDF support
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    # print(f"PyMuPDF loaded - PDF support enabled")
except ImportError:
    PYMUPDF_AVAILABLE = False
    # print("PyMuPDF not available - PDF preview will be limited")

try:
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                                    QLineEdit, QScrollArea, QFrame, QGroupBox, QCheckBox, 
                                    QSpinBox, QFormLayout, QDateEdit, QDialog, QGraphicsView,
                                    QApplication, QListView, QListWidget, QCompleter)
    from PySide6.QtCore import Signal, Qt, QEvent, QPoint, QSize, QDate, QRect
    from PySide6.QtGui import QPixmap, QColor, QPainter, QImageReader, QImage, QCursor, QFont
    from PySide6 import QtCore, QtGui, QtWidgets
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                    QLineEdit, QScrollArea, QFrame, QGroupBox, QCheckBox,
                                    QSpinBox, QFormLayout, QDateEdit, QDialog, QGraphicsView,
                                    QApplication, QListView, QListWidget, QCompleter)
    from PySide2.QtCore import Signal, Qt, QEvent, QPoint, QSize, QDate, QRect
    from PySide2.QtGui import QPixmap, QColor, QPainter, QImageReader, QImage, QCursor, QFont
    from PySide2 import QtCore, QtGui, QtWidgets
    PYSIDE_VERSION = 2

# Maya API for HDR/EXR loading (optional - only needed for Maya-specific operations)
try:
    import maya.api.OpenMaya as om
    MAYA_API_AVAILABLE = True
except ImportError:
    om = None
    MAYA_API_AVAILABLE = False

# Maya availability check
try:
    import maya.cmds as cmds
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


class ClickableWidget(QWidget):
    """Widget that emits a signal when clicked on empty space"""
    clicked = Signal()
    
    def mousePressEvent(self, event):
        """Emit clicked signal when widget is clicked"""
        self.clicked.emit()
        super().mousePressEvent(event)


class FlowLayout(QtWidgets.QLayout):
    """Flow layout that wraps widgets horizontally like tag chips (Qt example-based)"""
    
    def __init__(self, parent=None, margin=0, hSpacing=-1, vSpacing=-1):
        super().__init__(parent)
        self.itemList = []
        self.m_hSpace = hSpacing
        self.m_vSpace = vSpacing
        
        self.setContentsMargins(margin, margin, margin, margin)
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item):
        self.itemList.append(item)
    
    def addWidget(self, widget):
        """Add widget to the flow layout"""
        self.addItem(QtWidgets.QWidgetItem(widget))
    
    def horizontalSpacing(self):
        if self.m_hSpace >= 0:
            return self.m_hSpace
        else:
            return self.smartSpacing(QtWidgets.QStyle.PM_LayoutHorizontalSpacing)
    
    def verticalSpacing(self):
        if self.m_vSpace >= 0:
            return self.m_vSpace
        else:
            return self.smartSpacing(QtWidgets.QStyle.PM_LayoutVerticalSpacing)
    
    def count(self):
        return len(self.itemList)
    
    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size
    
    def doLayout(self, rect, testOnly):
        left, top, right, bottom = self.getContentsMargins()
        effectiveRect = rect.adjusted(+left, +top, -right, -bottom)
        x = effectiveRect.x()
        y = effectiveRect.y()
        lineHeight = 0
        
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.horizontalSpacing()
            if spaceX == -1:
                spaceX = wid.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton,
                    QtWidgets.QSizePolicy.PushButton,
                    Qt.Horizontal
                )
            spaceY = self.verticalSpacing()
            if spaceY == -1:
                spaceY = wid.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton,
                    QtWidgets.QSizePolicy.PushButton,
                    Qt.Vertical
                )
            
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > effectiveRect.right() and lineHeight > 0:
                x = effectiveRect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        
        return y + lineHeight - rect.y() + bottom
    
    def smartSpacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()
    
    def clear(self):
        """Remove all widgets from layout"""
        while self.count():
            item = self.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class BreadcrumbWidget(QWidget):
    """Breadcrumb navigation widget with clickable path segments"""
    
    path_clicked = Signal(str)  # Emitted when a breadcrumb is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.setFixedHeight(32)  # Fixed widget height
        
        # Dark background for better visibility
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(60, 60, 60))  # Dark gray background
        self.setPalette(palette)
        
        # Main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)  # Even margins
        self.layout.setSpacing(0)
        
        # Scroll area for breadcrumbs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(28)  # Fixed height, no max/min
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Dark background for scroll area too
        scroll_palette = self.scroll_area.palette()
        scroll_palette.setColor(self.scroll_area.backgroundRole(), QColor(60, 60, 60))
        self.scroll_area.setPalette(scroll_palette)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #3c3c3c; border: none; }")
        
        # Container for breadcrumb buttons (custom widget to catch clicks)
        self.breadcrumb_container = ClickableWidget()
        self.breadcrumb_container.clicked.connect(self.enter_edit_mode)  # Click on empty space = edit mode
        self.breadcrumb_container.setStyleSheet("QWidget { background-color: #3c3c3c; }")
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_container)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(2)
        self.breadcrumb_layout.addStretch()
        
        self.scroll_area.setWidget(self.breadcrumb_container)
        self.layout.addWidget(self.scroll_area, 1, Qt.AlignVCenter)  # Explicit vertical center alignment
        
        # Hidden line edit for manual path entry (activated by clicking on empty breadcrumb area)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Enter path and press Enter (or Escape to cancel)...")
        self.path_edit.setStyleSheet(f"""
            QLineEdit {{
                font-size: 12px;
                font-family: {UI_FONT};
                padding: 2px 4px;
                border: 1px solid #555;
                background-color: #3c3c3c;
            }}
        """)
        self.path_edit.setFixedHeight(28)  # Exact height match
        self.path_edit.hide()
        self.path_edit.returnPressed.connect(self.exit_edit_mode)
        # Install event filter to catch Escape key
        self.path_edit.installEventFilter(self)
        self.layout.addWidget(self.path_edit, 1, Qt.AlignVCenter)  # Explicit vertical center alignment, stretch
    
    def eventFilter(self, obj, event):
        """Event filter to catch Escape key and focus loss in path edit"""
        if obj == self.path_edit:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    # Cancel edit mode without changing path
                    self.path_edit.hide()
                    self.scroll_area.show()
                    return True
            elif event.type() == QEvent.FocusOut:
                # Exit edit mode when focus is lost (clicked elsewhere)
                # Use a short timer to avoid conflicts with returnPressed
                QtCore.QTimer.singleShot(100, self.cancel_edit_mode)
                return False  # Let the event propagate
        return super().eventFilter(obj, event)
    
    def sizeHint(self):
        """Override to return consistent size"""
        return QSize(self.width(), 32)
    
    def minimumSizeHint(self):
        """Override to return consistent minimum size"""
        return QSize(100, 32)
        
    def set_path(self, path):
        """Set the current path and update breadcrumbs"""
        self.current_path = str(path)
        self.update_breadcrumbs()
    
    def update_breadcrumbs(self):
        """Update breadcrumb buttons based on current path"""
        # Clear existing buttons
        while self.breadcrumb_layout.count() > 1:  # Keep the stretch
            item = self.breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_path:
            return
        
        # Split path into segments
        path_obj = Path(self.current_path)
        parts = path_obj.parts
        
        # Create button for each segment
        for i, part in enumerate(parts):
            # Create breadcrumb button
            btn = QPushButton(part)
            btn.setFlat(True)
            btn.setMaximumHeight(24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    padding: 2px 6px;
                    background: transparent;
                    text-align: left;
                    font-size: 12px;
                    font-family: {UI_FONT};
                    color: #e0e0e0;
                }}
                QPushButton:hover {{
                    background: rgba(100, 150, 255, 80);
                    border-radius: 2px;
                    color: #ffffff;
                }}
                QPushButton:pressed {{
                    background: rgba(100, 150, 255, 120);
                }}
            """)
            
            # Build path up to this segment
            segment_path = str(Path(*parts[:i+1]))
            # Use lambda with explicit checked parameter (even though we don't use it)
            btn.clicked.connect(lambda checked=False, p=segment_path: self.path_clicked.emit(p))
            
            # Insert button at the END (before stretch)
            self.breadcrumb_layout.insertWidget(self.breadcrumb_layout.count() - 1, btn)
            
            # Add separator (except for last item)
            if i < len(parts) - 1:
                separator = QLabel("›")
                separator.setStyleSheet(f"color: #999999; padding: 0 2px; font-size: 12px; font-family: {UI_FONT};")
                # Insert separator at the END (before stretch)
                self.breadcrumb_layout.insertWidget(self.breadcrumb_layout.count() - 1, separator)
    
    def enter_edit_mode(self):
        """Switch to manual path edit mode"""
        self.scroll_area.hide()
        self.path_edit.setText(self.current_path)
        self.path_edit.show()
        self.path_edit.setFocus()
        self.path_edit.selectAll()
        # Force layout update
        self.updateGeometry()
        self.layout.update()
    
    def exit_edit_mode(self):
        """Exit manual edit mode and emit path if valid"""
        new_path = self.path_edit.text().strip()
        
        # Switch back to breadcrumb mode
        self.path_edit.hide()
        self.scroll_area.show()
        
        # Force layout update
        self.updateGeometry()
        self.layout.update()
        
        # Only emit path if valid and different
        if new_path and Path(new_path).exists() and new_path != self.current_path:
            self.path_clicked.emit(new_path)
    
    def cancel_edit_mode(self):
        """Cancel edit mode without applying changes"""
        # Only cancel if path_edit is still visible (not already processed by returnPressed)
        if self.path_edit.isVisible():
            self.path_edit.hide()
            self.scroll_area.show()
            # Force layout update
            self.updateGeometry()
            self.layout.update()
    
    def set_collection_mode(self, collection_name):
        """Set breadcrumb to collection mode - shows collection name instead of path"""
        # Clear existing buttons
        while self.breadcrumb_layout.count() > 1:  # Keep the stretch
            item = self.breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create collection icon + name button (using gray triangle icon)
        collection_btn = QPushButton(f"▸ {collection_name}")
        collection_btn.setFlat(True)
        collection_btn.setMaximumHeight(24)
        collection_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                padding: 2px 8px;
                background: transparent;
                text-align: left;
                font-size: 12px;
                font-family: {UI_FONT};
                color: #b0b0b0;
                font-weight: bold;
            }}
        """)
        collection_btn.setEnabled(False)  # Not clickable
        
        # Insert at the END (before stretch)
        self.breadcrumb_layout.insertWidget(self.breadcrumb_layout.count() - 1, collection_btn)
        
        # Apply blue background style
        self.breadcrumb_container.setStyleSheet("""
            QWidget {
                background-color: #2a4a6a;
                border-radius: 3px;
            }
        """)
    
    def clear_collection_mode(self):
        """Clear collection mode and restore normal path breadcrumb"""
        # Reset background style
        self.breadcrumb_container.setStyleSheet("QWidget { background-color: #3c3c3c; }")
        
        # Restore normal breadcrumbs
        self.update_breadcrumbs()


class EnhancedSearchBar(QWidget):
    """Enhanced search bar with case-sensitive and regex toggles"""
    
    textChanged = Signal(str)  # Emitted when search text changes
    optionsChanged = Signal()  # Emitted when case/regex toggles change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.match_count = 0
        self.total_count = 0
        self.setup_ui()
    
    def setup_ui(self):
        """Setup search bar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(5)
        
        # Search icon label
        icon_label = QLabel("🔍")
        icon_label.setStyleSheet(f"font-size: 16px; font-family: {UI_FONT};")
        layout.addWidget(icon_label)
        
        # Search input field
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search files... (Ctrl+F)")
        self.search_input.setMinimumWidth(300)
        self.search_input.setStyleSheet(f"font-size: 12px; font-family: {UI_FONT}; padding: 4px;")
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input)
        
        # Case-sensitive toggle button
        self.case_btn = QPushButton("Aa")
        self.case_btn.setCheckable(True)
        self.case_btn.setToolTip("Case Sensitive Search")
        self.case_btn.setMaximumWidth(35)
        self.case_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                background-color: #2a2a2a;
            }
            QPushButton:checked {
                background-color: #4b7daa;
                border-color: #5a8db8;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        self.case_btn.clicked.connect(self._on_options_changed)
        layout.addWidget(self.case_btn)
        
        # Regex toggle button
        self.regex_btn = QPushButton(".*")
        self.regex_btn.setCheckable(True)
        self.regex_btn.setToolTip("Regular Expression Search")
        self.regex_btn.setMaximumWidth(35)
        self.regex_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                background-color: #2a2a2a;
                font-family: 'Courier New', monospace;
            }
            QPushButton:checked {
                background-color: #4b7daa;
                border-color: #5a8db8;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        self.regex_btn.clicked.connect(self._on_options_changed)
        layout.addWidget(self.regex_btn)
        
        # Clear button (only visible when text present)
        self.clear_btn = QPushButton("❌")
        self.clear_btn.setMaximumWidth(30)
        self.clear_btn.setToolTip("Clear Search")
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.setVisible(False)
        layout.addWidget(self.clear_btn)
        
        # Match count label
        self.match_label = QLabel("")
        self.match_label.setStyleSheet(f"color: #888; font-size: 12px; font-family: {UI_FONT}; font-weight: bold;")
        self.match_label.setMinimumWidth(90)
        layout.addWidget(self.match_label)
        
        layout.addStretch()
    
    def _on_text_changed(self, text):
        """Handle text change"""
        self.clear_btn.setVisible(bool(text))
        self.textChanged.emit(text)
    
    def _on_options_changed(self):
        """Handle case/regex toggle change"""
        self.optionsChanged.emit()
    
    def clear_search(self):
        """Clear search text"""
        self.search_input.clear()
    
    def set_match_count(self, matches, total):
        """Update match count display"""
        self.match_count = matches
        self.total_count = total
        if matches > 0:
            self.match_label.setText(f"{matches} match{'es' if matches != 1 else ''}")
            self.match_label.setStyleSheet(f"color: #5dade2; font-size: 12px; font-family: {UI_FONT}; font-weight: bold;")  # Maya cyan
        elif self.search_input.text():
            self.match_label.setText("No matches")
            self.match_label.setStyleSheet(f"color: #e74c3c; font-size: 12px; font-family: {UI_FONT}; font-weight: bold;")  # Brighter red
        else:
            self.match_label.setText("")
    
    def is_case_sensitive(self):
        """Check if case-sensitive search is enabled"""
        return self.case_btn.isChecked()
    
    def is_regex_enabled(self):
        """Check if regex search is enabled"""
        return self.regex_btn.isChecked()
    
    def get_text(self):
        """Get current search text"""
        return self.search_input.text()
    
    def set_case_sensitive(self, enabled):
        """Set case-sensitive mode"""
        self.case_btn.setChecked(enabled)
    
    def set_regex_enabled(self, enabled):
        """Set regex mode"""
        self.regex_btn.setChecked(enabled)


class FilterPanel(QWidget):
    """Advanced filter panel widget"""
    
    filtersChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup filter panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Header with toggle button
        header_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("▼ Filters")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setMaximumWidth(100)
        header_layout.addWidget(self.toggle_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setMaximumWidth(80)
        header_layout.addWidget(self.clear_btn)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Filter content (collapsible) - COMPACT HORIZONTAL LAYOUT
        self.filter_content = QWidget()
        self.filter_content.setMaximumHeight(120)  # Taller for 3 rows
        content_layout = QHBoxLayout(self.filter_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        
        # === COLUMN 1: File Types (Compact 2-row grid) ===
        type_group = QGroupBox("File Types")
        type_grid = QtWidgets.QGridLayout(type_group)
        type_grid.setSpacing(3)
        type_grid.setContentsMargins(5, 8, 5, 5)
        
        self.type_checkboxes = {}
        
        # Get file types from central registry
        from .utils import get_simple_filter_types
        file_types = get_simple_filter_types()
        
        # Calculate grid layout (3 columns, auto rows)
        cols = 3
        for idx, (ext, label) in enumerate(file_types):
            row = idx // cols
            col = idx % cols
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.stateChanged.connect(self.on_filter_changed)
            self.type_checkboxes[ext] = cb
            type_grid.addWidget(cb, row, col)
        
        type_group.setMaximumWidth(220)  # Wider for more items
        type_group.setMaximumHeight(140)  # Taller for more rows
        content_layout.addWidget(type_group)
        
        # === COLUMN 2: Size Filter (Compact) ===
        size_group = QGroupBox("File Size")
        size_layout = QFormLayout(size_group)
        size_layout.setSpacing(2)
        size_layout.setContentsMargins(5, 8, 5, 5)
        
        self.size_min_spin = QSpinBox()
        self.size_min_spin.setRange(0, 10000)
        self.size_min_spin.setSuffix(" MB")
        self.size_min_spin.setMaximumWidth(80)
        self.size_min_spin.valueChanged.connect(self.on_filter_changed)
        
        self.size_max_spin = QSpinBox()
        self.size_max_spin.setRange(0, 10000)
        self.size_max_spin.setSuffix(" MB")
        self.size_max_spin.setMaximumWidth(80)
        self.size_max_spin.valueChanged.connect(self.on_filter_changed)
        
        size_layout.addRow("Min:", self.size_min_spin)
        size_layout.addRow("Max:", self.size_max_spin)
        
        size_group.setMaximumWidth(150)
        size_group.setMaximumHeight(90)
        content_layout.addWidget(size_group)
        
        # === COLUMN 3: Date Filter (Compact) ===
        date_group = QGroupBox("Modified Date")
        date_layout = QHBoxLayout(date_group)
        date_layout.setSpacing(3)
        date_layout.setContentsMargins(5, 8, 5, 5)
        
        # Quick filter buttons
        self.date_today_btn = QPushButton("Today")
        self.date_week_btn = QPushButton("Week")
        self.date_month_btn = QPushButton("Month")
        self.date_today_btn.setMaximumWidth(55)
        self.date_week_btn.setMaximumWidth(50)
        self.date_month_btn.setMaximumWidth(55)
        
        self.date_today_btn.clicked.connect(lambda: self.set_date_range("today"))
        self.date_week_btn.clicked.connect(lambda: self.set_date_range("week"))
        self.date_month_btn.clicked.connect(lambda: self.set_date_range("month"))
        
        date_layout.addWidget(self.date_today_btn)
        date_layout.addWidget(self.date_week_btn)
        date_layout.addWidget(self.date_month_btn)
        
        # Custom range button (opens date picker dialog)
        self.date_custom_btn = QPushButton("...")
        self.date_custom_btn.setMaximumWidth(30)
        self.date_custom_btn.setToolTip("Custom Date Range")
        self.date_custom_btn.clicked.connect(self.open_custom_date_dialog)
        date_layout.addWidget(self.date_custom_btn)
        
        # Clear date filter button
        self.date_clear_btn = QPushButton("✕")
        self.date_clear_btn.setMaximumWidth(25)
        self.date_clear_btn.setToolTip("Clear Date Filter")
        self.date_clear_btn.clicked.connect(self.clear_date_filter)
        date_layout.addWidget(self.date_clear_btn)
        
        # Store date range internally
        self.date_from = None
        self.date_to = None
        
        date_group.setMaximumWidth(250)
        date_group.setMaximumHeight(90)
        content_layout.addWidget(date_group)
        
        # === COLUMN 4: Options (Compact) ===
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(2)
        options_layout.setContentsMargins(5, 8, 5, 5)
        
        self.show_folders_check = QCheckBox("Show Folders")
        self.show_folders_check.setChecked(True)
        self.show_folders_check.stateChanged.connect(self.on_filter_changed)
        options_layout.addWidget(self.show_folders_check)
        
        self.show_images_check = QCheckBox("Show Images")
        self.show_images_check.setChecked(True)
        self.show_images_check.setToolTip("Show image files (TIF, JPG, PNG, HDR, EXR, TGA)")
        self.show_images_check.stateChanged.connect(self.on_filter_changed)
        options_layout.addWidget(self.show_images_check)
        
        self.show_scripts_check = QCheckBox("Show Scripts")
        self.show_scripts_check.setChecked(True)
        self.show_scripts_check.setToolTip("Show script files (MEL, Python)")
        self.show_scripts_check.stateChanged.connect(self.on_filter_changed)
        options_layout.addWidget(self.show_scripts_check)
        
        options_group.setMaximumWidth(120)
        options_group.setMaximumHeight(120)
        content_layout.addWidget(options_group)
        
        content_layout.addStretch()
        
        layout.addWidget(self.filter_content)
        self.filter_content.hide()  # Initially collapsed
        
        # Connections
        self.toggle_btn.toggled.connect(self.toggle_filters)
        self.clear_btn.clicked.connect(self.clear_all_filters)
    
    def toggle_filters(self, checked):
        """Toggle filter panel visibility"""
        if checked:
            self.toggle_btn.setText("▲ Filters")
            self.filter_content.show()
        else:
            self.toggle_btn.setText("▼ Filters")
            self.filter_content.hide()
    
    def on_filter_changed(self):
        """Emit signal when any filter changes"""
        self.filtersChanged.emit()
    
    def open_custom_date_dialog(self):
        """Open dialog to select custom date range"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Custom Date Range")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # From date
        from_label = QLabel("From Date:")
        from_edit = QDateEdit()
        from_edit.setCalendarPopup(True)
        from_edit.setDisplayFormat("yyyy-MM-dd")
        from_edit.setDate(QDate.currentDate().addDays(-7))
        
        layout.addWidget(from_label)
        layout.addWidget(from_edit)
        
        # To date
        to_label = QLabel("To Date:")
        to_edit = QDateEdit()
        to_edit.setCalendarPopup(True)
        to_edit.setDisplayFormat("yyyy-MM-dd")
        to_edit.setDate(QDate.currentDate())
        
        layout.addWidget(to_label)
        layout.addWidget(to_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            # Convert QDate to datetime
            from_qdate = from_edit.date()
            to_qdate = to_edit.date()
            
            self.date_from = datetime(from_qdate.year(), from_qdate.month(), from_qdate.day())
            self.date_to = datetime(to_qdate.year(), to_qdate.month(), to_qdate.day(), 23, 59, 59)
            
            self.on_filter_changed()
    
    def clear_date_filter(self):
        """Clear date filter"""
        self.date_from = None
        self.date_to = None
        self.on_filter_changed()
    
    def set_date_range(self, range_type):
        """Set date range filter"""
        now = datetime.now()
        
        if range_type == "today":
            self.date_from = now.replace(hour=0, minute=0, second=0)
            self.date_to = now
        elif range_type == "week":
            self.date_from = now - timedelta(days=7)
            self.date_to = now
        elif range_type == "month":
            self.date_from = now - timedelta(days=30)
            self.date_to = now
        
        self.on_filter_changed()
    
    def get_selected_file_types(self):
        """Get list of selected file type extensions"""
        selected = []
        for ext, cb in self.type_checkboxes.items():
            if cb.isChecked():
                selected.append(ext)
        return selected
    
    def get_size_range(self):
        """Get size range in bytes (returns min, max)"""
        min_mb = self.size_min_spin.value()
        max_mb = self.size_max_spin.value()
        
        min_bytes = min_mb * 1024 * 1024 if min_mb > 0 else 0
        max_bytes = max_mb * 1024 * 1024 if max_mb > 0 else 0
        
        return min_bytes, max_bytes
    
    def get_date_range(self):
        """Get date range (returns from, to)"""
        # Return current date range if set
        return self.date_from, self.date_to
    
    def get_show_folders(self):
        """Get show folders option"""
        return self.show_folders_check.isChecked()
    
    def get_show_images(self):
        """Get show images option"""
        return self.show_images_check.isChecked()
    
    def get_show_scripts(self):
        """Get show scripts option"""
        return self.show_scripts_check.isChecked()
    
    def clear_all_filters(self):
        """Clear all filters to default state"""
        # Reset all file type checkboxes
        for cb in self.type_checkboxes.values():
            cb.setChecked(True)
        
        # Reset size filters
        self.size_min_spin.setValue(0)
        self.size_max_spin.setValue(0)
        
        # Reset date filter
        self.date_from = None
        self.date_to = None
        
        # Reset options
        self.show_folders_check.setChecked(True)
        self.show_images_check.setChecked(True)
        self.show_scripts_check.setChecked(True)
        
        self.on_filter_changed()


def load_hdr_exr_raw(file_path, max_size=2048):
    """
    Load raw HDR/EXR float data (NO tone mapping) for fast exposure adjustment
    
    Args:
        file_path: Path to HDR/EXR file
        max_size: Maximum width/height for preview (default 2048)
        
    Returns:
        tuple: (rgb_float_array, width, height, resolution_str) or (None, None, None, None) on failure
    """
    file_path_str = str(file_path)
    file_ext = file_path_str.lower()
    
    # Use OpenCV for .hdr (Radiance RGBE) files if available (best option!)
    if file_ext.endswith('.hdr') and OPENCV_AVAILABLE and NUMPY_AVAILABLE:
        try:
            # print(f"🔍 Attempting to load HDR with OpenCV: {file_path_str}")
            # Read HDR with OpenCV (cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR for float32)
            rgb = cv2.imread(file_path_str, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR)
            
            if rgb is None:
                raise Exception("OpenCV returned None - file may be corrupted or unsupported")
            
            # OpenCV loads as BGR, convert to RGB
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            
            # print(f"✅ OpenCV loaded HDR: shape={rgb.shape}, dtype={rgb.dtype}, min={rgb.min():.3f}, max={rgb.max():.3f}")
            
            height, width = rgb.shape[:2]
            resolution_str = f"{width} x {height}"
            
            # Scale if needed
            if width > max_size or height > max_size:
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # Use OpenCV resize (high quality)
                rgb = cv2.resize(rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                width, height = new_width, new_height
            
            # print(f"✅ HDR ready for tone mapping: {width}x{height}")
            # Return RAW float data (no tone mapping!)
            return rgb, width, height, resolution_str
            
        except Exception as e:
            print(f"❌ OpenCV HDR loading failed: {e}")
            import traceback
            print(f"❌ OpenCV HDR loading failed: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None, None
    
    # Use OpenEXR for .exr files if available
    if file_ext.endswith('.exr') and OPENEXR_AVAILABLE and NUMPY_AVAILABLE:
        try:
            # Open EXR file
            with OpenEXR.File(file_path_str) as exr_file:
                # Get header info
                header = exr_file.header()
                dw = header['dataWindow']
                width = dw[1][0] - dw[0][0] + 1
                height = dw[1][1] - dw[0][1] + 1
                resolution_str = f"{width} x {height}"
                
                # Read RGB channels
                channels = exr_file.channels()
                rgb = None
                
                # Try standard interleaved RGB or RGBA
                if "RGB" in channels:
                    rgb = np.array(channels["RGB"].pixels, dtype=np.float32).reshape(height, width, 3)
                elif "RGBA" in channels:
                    rgba = np.array(channels["RGBA"].pixels, dtype=np.float32).reshape(height, width, 4)
                    rgb = rgba[:, :, :3]  # Drop alpha
                elif all(c in channels for c in ["R", "G", "B"]):
                    r = np.array(channels["R"].pixels, dtype=np.float32).reshape(height, width)
                    g = np.array(channels["G"].pixels, dtype=np.float32).reshape(height, width)
                    b = np.array(channels["B"].pixels, dtype=np.float32).reshape(height, width)
                    rgb = np.stack([r, g, b], axis=2)
                
                if rgb is None:
                    return None, None, None, None
                
                # Scale if needed
                if width > max_size or height > max_size:
                    scale = min(max_size / width, max_size / height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    
                    # Simple nearest-neighbor resize (fast)
                    indices_h = np.linspace(0, height-1, new_height, dtype=int)
                    indices_w = np.linspace(0, width-1, new_width, dtype=int)
                    rgb = rgb[np.ix_(indices_h, indices_w)]
                    
                    width, height = new_width, new_height
                
                # Return RAW float data (no tone mapping!)
                return rgb, width, height, resolution_str
                
        except Exception as e:
            print(f"OpenEXR raw loading failed: {e}")
            return None, None, None, None
    
    # If neither imageio nor OpenEXR available
    return None, None, None, None


def load_hdr_exr_image(file_path, max_size=2048, exposure=0.0, return_raw=False):
    """
    Load HDR/EXR image with proper float HDR handling
    
    Args:
        file_path: Path to HDR/EXR file
        max_size: Maximum width/height for preview (default 2048 for high quality)
        exposure: Exposure compensation in stops (0.0 = neutral, +1.0 = 2x brighter, -1.0 = half)
                 Like Arnold/Maya lighting exposure
        return_raw: If True, also return raw float RGB array (for caching)
        
    Returns:
        If return_raw=False: tuple (QPixmap, resolution_string) or (None, None) on failure
        If return_raw=True: tuple (QPixmap, resolution_string, rgb_raw_array) or (None, None, None) on failure
    """
    file_path_str = str(file_path)
    file_ext = file_path_str.lower()
    
    # Use OpenCV for .hdr (Radiance RGBE) files if available
    if file_ext.endswith('.hdr') and OPENCV_AVAILABLE and NUMPY_AVAILABLE:
        try:
            # Read HDR with OpenCV
            rgb = cv2.imread(file_path_str, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR)
            
            if rgb is None:
                raise Exception("OpenCV returned None")
            
            # OpenCV loads as BGR, convert to RGB
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            
            if rgb.ndim == 2:
                # Grayscale - convert to RGB
                rgb = np.stack([rgb, rgb, rgb], axis=2)
            elif rgb.shape[2] == 4:
                # RGBA - drop alpha
                rgb = rgb[:, :, :3]
            
            height, width = rgb.shape[:2]
            resolution_str = f"{width} x {height}"
            
            # Scale if needed
            if width > max_size or height > max_size:
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # Use OpenCV resize
                rgb = cv2.resize(rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                width, height = new_width, new_height
            
            # Apply exposure compensation in stops (like Arnold/Maya)
            # Each stop = 2x or 0.5x brightness: multiplier = 2^exposure
            exposure_multiplier = pow(2.0, exposure)
            rgb = rgb * exposure_multiplier
            
            # ACES Filmic tone mapping (Stephen Hill's fit)
            # Used in Unreal Engine, Unity, and many film pipelines
            # Works great with ACEScg workflow
            a = 2.51
            b = 0.03
            c = 2.43
            d = 0.59
            e = 0.14
            rgb_tonemapped = np.clip((rgb * (a * rgb + b)) / (rgb * (c * rgb + d) + e), 0, 1)
            
            # Gamma correction (2.2 for sRGB)
            gamma = 1.0 / 2.2
            rgb_tonemapped = np.power(rgb_tonemapped, gamma)
            
            # Convert to 8-bit
            rgb_8bit = (rgb_tonemapped * 255).astype(np.uint8)
            
            # Create QImage
            bytes_per_line = width * 3
            q_image = QImage(rgb_8bit.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
            q_image = q_image.copy()
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            return pixmap, resolution_str
            
        except Exception as e:
            print(f"OpenCV HDR loading failed: {e}")
            import traceback
            traceback.print_exc()
            # Fall through to Maya MImage fallback
    
    # Use OpenEXR for .exr files if available
    if file_ext.endswith('.exr') and OPENEXR_AVAILABLE and NUMPY_AVAILABLE:
        try:
            # Open EXR file
            with OpenEXR.File(file_path_str) as exr_file:
                # Get header info
                header = exr_file.header()
                dw = header['dataWindow']
                width = dw[1][0] - dw[0][0] + 1
                height = dw[1][1] - dw[0][1] + 1
                resolution_str = f"{width} x {height}"
                
                # Read RGB channels as interleaved array
                channels = exr_file.channels()
                
                # Get RGB data (returns numpy array directly!)
                # Try multiple naming conventions for RGB channels
                rgb = None
                
                # 1. Try standard interleaved RGB or RGBA
                if "RGB" in channels:
                    rgb_data = channels["RGB"].pixels  # Shape: (height, width, 3)
                    if rgb_data is not None:
                        rgb = rgb_data
                elif "RGBA" in channels:
                    rgba_data = channels["RGBA"].pixels  # Shape: (height, width, 4)
                    if rgba_data is not None:
                        rgb = rgba_data[:, :, :3]  # Drop alpha, keep RGB only
                
                # 2. Try separate R, G, B channels
                elif all(c in channels for c in ["R", "G", "B"]):
                    r = channels["R"].pixels
                    g = channels["G"].pixels
                    b = channels["B"].pixels
                    if r is not None and g is not None and b is not None:
                        rgb = np.stack([r, g, b], axis=2)  # Shape: (height, width, 3)
                
                # 3. Try Beauty pass (common in render layers)
                elif all(c in channels for c in ["Beauty.R", "Beauty.G", "Beauty.B"]):
                    r = channels["Beauty.R"].pixels
                    g = channels["Beauty.G"].pixels
                    b = channels["Beauty.B"].pixels
                    if r is not None and g is not None and b is not None:
                        rgb = np.stack([r, g, b], axis=2)
                
                # 4. Try first layer with .R .G .B (generic multi-layer)
                else:
                    # Find first layer that has RGB channels
                    channel_names = list(channels.keys())
                    layer_prefixes = set()
                    for name in channel_names:
                        if '.' in name:
                            prefix = name.rsplit('.', 1)[0]
                            layer_prefixes.add(prefix)
                    
                    # Try each layer prefix
                    for prefix in sorted(layer_prefixes):
                        r_name = f"{prefix}.R"
                        g_name = f"{prefix}.G"
                        b_name = f"{prefix}.B"
                        if all(c in channels for c in [r_name, g_name, b_name]):
                            r = channels[r_name].pixels
                            g = channels[g_name].pixels
                            b = channels[b_name].pixels
                            if r is not None and g is not None and b is not None:
                                rgb = np.stack([r, g, b], axis=2)
                                break
                
                # 5. If still no RGB, try single channel (grayscale)
                if rgb is None:
                    # Try common single-channel names first
                    single_channels = ["Y", "Z", "depth", "A", "alpha", "luminance"]
                    for ch_name in single_channels:
                        if ch_name in channels:
                            gray = channels[ch_name].pixels
                            if gray is not None:
                                # Convert to RGB by repeating channel
                                if gray.ndim == 2:
                                    rgb = np.stack([gray, gray, gray], axis=2)
                                else:
                                    # Already 3D, just use it
                                    rgb = gray
                                break
                
                # 6. Last resort: use ANY available channel as grayscale
                if rgb is None and len(channels) > 0:
                    # Take the first available channel
                    first_channel_name = list(channels.keys())[0]
                    gray = channels[first_channel_name].pixels
                    
                    if gray is not None:
                        # Convert to RGB by repeating channel
                        if gray.ndim == 2:
                            rgb = np.stack([gray, gray, gray], axis=2)
                        elif gray.ndim == 3 and gray.shape[2] == 1:
                            # Single channel as 3D array
                            rgb = np.concatenate([gray, gray, gray], axis=2)
                        else:
                            rgb = gray
                
                # If still nothing, list available channels and give up
                if rgb is None:
                    available = ", ".join(sorted(channels.keys())[:10])  # Show first 10
                    raise Exception(f"No usable channels found. Available: {available}")
                
                # Final safety check: verify rgb is valid numpy array with data
                if rgb is None or not isinstance(rgb, np.ndarray) or rgb.size == 0:
                    raise Exception(f"RGB data is invalid or empty after channel processing")
                
                # Check if dtype is numeric (not object or other non-numeric types)
                # Deep EXR channels can return object arrays which we can't process
                if rgb.dtype == np.object_ or not np.issubdtype(rgb.dtype, np.number):
                    raise Exception(f"RGB data has non-numeric dtype: {rgb.dtype} (deep/volumetric EXR not supported)")
                
                # Scale if needed
                if width > max_size or height > max_size:
                    scale = min(max_size / width, max_size / height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    
                    # Simple nearest-neighbor resize (fast)
                    indices_h = np.linspace(0, height-1, new_height, dtype=int)
                    indices_w = np.linspace(0, width-1, new_width, dtype=int)
                    rgb = rgb[np.ix_(indices_h, indices_w)]
                    
                    width, height = new_width, new_height
                
                # Apply exposure compensation in stops (like Arnold/Maya)
                # Each stop = 2x or 0.5x brightness: multiplier = 2^exposure
                exposure_multiplier = pow(2.0, exposure)
                rgb = rgb * exposure_multiplier
                
                # ACES Filmic tone mapping (Stephen Hill's fit)
                # Used in Unreal Engine, Unity, and many film pipelines
                # Works great with ACEScg workflow
                a = 2.51
                b = 0.03
                c = 2.43
                d = 0.59
                e = 0.14
                
                # Suppress numpy warnings for HDR tonemapping (overflow/divide by zero are expected)
                with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
                    rgb_tonemapped = np.clip((rgb * (a * rgb + b)) / (rgb * (c * rgb + d) + e), 0, 1)
                
                # Gamma correction (2.2 for sRGB)
                gamma = 1.0 / 2.2
                rgb_tonemapped = np.power(rgb_tonemapped, gamma)
                
                # Convert to 8-bit
                with np.errstate(invalid='ignore'):
                    rgb_8bit = (rgb_tonemapped * 255).astype(np.uint8)
                
                # Create QImage
                bytes_per_line = width * 3
                q_image = QImage(rgb_8bit.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                q_image = q_image.copy()
                
                # Convert to QPixmap
                pixmap = QPixmap.fromImage(q_image)
                return pixmap, resolution_str
                
        except Exception as e:
            print(f"OpenEXR loading failed: {e}")
            # Fall through to Maya MImage fallback
    
    # Fallback: Use Maya MImage for HDR or if OpenEXR not available
    # Only available if Maya API is present
    if not MAYA_API_AVAILABLE or om is None:
        # No Maya API - return error
        return None, -1, f"HDR/EXR loading requires Maya API (not available in standalone mode)"
    
    try:
        # Use Maya's MImage to read HDR/EXR
        m_image = om.MImage()
        m_image.readFromFile(str(file_path))
        
        # Get image dimensions using getSize()
        size = m_image.getSize()
        width = size[0]
        height = size[1]
        resolution_str = f"{width} x {height}"
        
        # Calculate scaled size if needed
        if width > max_size or height > max_size:
            if width > height:
                scaled_width = max_size
                scaled_height = int(max_size * height / width)
            else:
                scaled_height = max_size
                scaled_width = int(max_size * width / height)
            
            # Resize the MImage
            m_image.resize(scaled_width, scaled_height, True)
            
            # Update dimensions after resize
            size = m_image.getSize()
            width = size[0]
            height = size[1]
        
        # Try to get HDR pixels if numpy is available
        if NUMPY_AVAILABLE:
            try:
                # Maya MImage doesn't reliably expose float pixels via API
                # Better approach: write to temp file in HDR format, then read with proper library
                
                # Try IFF format (Maya native, preserves more data than PNG)
                import tempfile
                import os
                
                # Write as IFF (Maya's format, better than PNG for HDR)
                temp_path = tempfile.mktemp(suffix='.iff')
                m_image.writeToFile(temp_path, 'iff')
                
                # Read back with Maya and get pixels
                m_image2 = om.MImage()
                m_image2.readFromFile(temp_path)
                m_image2.setRGBA(True)
                
                # Get 8-bit pixels (but from IFF which preserves more range)
                pixel_ptr = m_image2.pixels()
                
                if pixel_ptr:
                    import ctypes
                    pixel_count = width * height * 4  # RGBA bytes
                    
                    # Create numpy array from 8-bit pixel data
                    ByteArray = ctypes.POINTER(ctypes.c_ubyte * pixel_count)
                    byte_array = ctypes.cast(pixel_ptr, ByteArray).contents
                    pixel_array = np.frombuffer(byte_array, dtype=np.uint8).copy()
                    pixel_array = pixel_array.reshape((height, width, 4))
                    
                    # Extract RGB
                    rgb = pixel_array[:, :, :3].astype(np.float32) / 255.0
                    
                    # Apply exposure compensation in stops (even on 8-bit, it helps)
                    exposure_multiplier = pow(2.0, exposure)
                    rgb = np.clip(rgb * exposure_multiplier, 0, 1)
                    
                    # Gamma correction
                    gamma = 1.0 / 2.2
                    rgb = np.power(rgb, gamma)
                    
                    # Convert back to 8-bit
                    rgb_8bit = (rgb * 255).astype(np.uint8)
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    
                    # Create QImage
                    bytes_per_line = width * 3
                    q_image = QImage(rgb_8bit.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                    q_image = q_image.copy()
                    
                    # Convert to QPixmap
                    pixmap = QPixmap.fromImage(q_image)
                    return pixmap, resolution_str
                
                # Clean up if we got here
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
            except Exception as numpy_error:
                print(f"NumPy HDR processing failed: {numpy_error}")
                import traceback
                traceback.print_exc()
                # Fall through to PNG fallback
        
        # Fallback: PNG export + simple exposure (no proper tone mapping)
            import tempfile
            import os
        # Fallback: PNG export + simple exposure (no proper tone mapping)
        print("Using PNG fallback for HDR (NumPy not available - install for better quality)")
        import tempfile
        import os
        
        temp_path = tempfile.mktemp(suffix='.png')
        m_image.writeToFile(temp_path, 'png')
        q_image = QImage(temp_path)
        
        try:
            os.remove(temp_path)
        except:
            pass
        
        if q_image.isNull():
            return None, None
        
        q_image = q_image.convertToFormat(QImage.Format_RGB888)
        
        # Simple 8-bit exposure (not proper HDR)
        bits = q_image.bits()
        bytes_per_line = q_image.bytesPerLine()
        
        if PYSIDE_VERSION == 6:
            pixel_data = bits.tobytes()
        else:
            bits.setsize(q_image.height() * bytes_per_line)
            pixel_data = bytes(bits)
        
        pixel_array = bytearray(pixel_data)
        # Apply exposure in stops (2^exposure)
        exposure_multiplier = pow(2.0, exposure)
        for i in range(0, len(pixel_array), 3):
            pixel_array[i] = min(int(pixel_array[i] * exposure_multiplier), 255)
            pixel_array[i+1] = min(int(pixel_array[i+1] * exposure_multiplier), 255)
            pixel_array[i+2] = min(int(pixel_array[i+2] * exposure_multiplier), 255)
        
        q_image = QImage(bytes(pixel_array), q_image.width(), q_image.height(), bytes_per_line, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(q_image)
        return pixmap, resolution_str
        
    except Exception as e:
        print(f"Error loading HDR/EXR: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def load_pdf_page(file_path, page_number=0, max_size=1024):
    """
    Load PDF page as QPixmap for preview
    
    Args:
        file_path: Path to PDF file
        page_number: Page number to load (0-indexed)
        max_size: Maximum width/height for preview (default 1024)
        
    Returns:
        tuple: (QPixmap, page_count, resolution_str) or (None, 0, None) on failure
               Returns (None, -1, "encrypted") if PDF is password protected
    """
    if not PYMUPDF_AVAILABLE:
        print("PyMuPDF not available - cannot load PDF")
        return None, 0, None
    
    try:
        # Open PDF document
        doc = fitz.open(str(file_path))
        
        # Check if document is encrypted
        if doc.is_encrypted:
            print(f"PDF is password protected: {file_path}")
            doc.close()
            return None, -1, "encrypted"  # Special return value for encrypted PDFs
        
        page_count = len(doc)
        
        # Validate page number
        if page_number < 0 or page_number >= page_count:
            page_number = 0
        
        # Get page
        try:
            page = doc[page_number]
        except (ValueError, RuntimeError) as e:
            print(f"Error accessing PDF page {page_number}: {e}")
            doc.close()
            return None, 0, None
        
        # Get page dimensions
        rect = page.rect
        width = int(rect.width)
        height = int(rect.height)
        resolution_str = f"{width} x {height}"
        
        # Calculate zoom to fit max_size
        zoom = min(max_size / width, max_size / height, 2.0)  # Max 2x zoom for quality
        mat = fitz.Matrix(zoom, zoom)
        
        # Render page to pixmap
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert to QImage
        img_format = QImage.Format_RGB888 if pix.n == 3 else QImage.Format_RGBA8888
        q_image = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        q_image = q_image.copy()  # Make a deep copy
        
        # Convert to QPixmap
        pixmap = QPixmap.fromImage(q_image)
        
        # Close document
        doc.close()
        
        return pixmap, page_count, resolution_str
        
    except Exception as e:
        print(f"Error loading PDF: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, None


class PreviewPanel(QWidget):
    """Preview panel showing file preview and metadata"""
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_assets = []
        self.current_pixmap = None  # Store scaled preview pixmap
        self.full_res_pixmap = None  # Store full resolution pixmap for zoom
        self.preview_cache = {}  # Cache: file_path -> (pixmap, resolution)
        self.cache_max_size = 50  # Max 50 previews in cache
        self.current_image_path = None  # Track current image path
        self.zoom_mode = False  # Track if in zoom mode
        self.zoom_level = 1.0  # Current zoom level
        self.pan_offset = QPoint(0, 0)  # Pan offset
        self.last_mouse_pos = None  # For dragging
        self.hdr_exposure = 0.0  # Default HDR exposure in stops (0 = neutral, like Arnold)
        self.current_hdr_path = None  # Track current HDR file for re-loading with new exposure
        self.hdr_raw_cache = {}  # Cache raw HDR float data: file_path -> (numpy_array, width, height, resolution_str)
        self.hdr_cache_max_size = 5  # Only cache last 5 HDR raw data (they're big!)
        self.max_preview_size = 1024  # Default preview resolution (can be changed by settings)
        self.max_hdr_cache_size = 5  # Maximum HDR cache items (for settings compatibility)
        
        # Text preview mode flag
        self.is_showing_text = False
        
        # PDF preview state
        self.is_showing_pdf = False
        self.current_pdf_path = None
        self.current_pdf_page = 0
        self.current_pdf_page_count = 0
        
        # Exposure adjustment debounce timer for smooth slider
        self.exposure_timer = QtCore.QTimer()
        self.exposure_timer.setSingleShot(True)
        self.exposure_timer.setInterval(20)  # 50ms delay (smooth but responsive)
        self.exposure_timer.timeout.connect(self.apply_exposure_change)
        self.pending_exposure_value = None
        
        self.setMinimumWidth(250)  # Minimum width when visible
        self.setup_ui()
    
    def setup_ui(self):
        """Setup preview panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title label with zoom info
        title_layout = QHBoxLayout()
        self.title_label = QLabel("Preview")
        self.title_label.setStyleSheet(f"font-weight: bold; font-size: 12px; font-family: {UI_FONT}; padding: 5px;")
        title_layout.addWidget(self.title_label)
        
        self.zoom_label = QLabel("")
        self.zoom_label.setStyleSheet(f"font-size: 10px; font-family: {UI_FONT}; color: #888; padding: 5px;")
        title_layout.addWidget(self.zoom_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Create splitter between preview and info tabs
        self.preview_splitter = QtWidgets.QSplitter(Qt.Vertical)
        self.preview_splitter.setHandleWidth(3)
        self.preview_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555;
            }
            QSplitter::handle:hover {
                background-color: #777;
            }
        """)
        
        # Top part: Preview area + controls in a container
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(5)
        
        # Preview image area using QGraphicsView (allows free positioning, no forced centering!)
        self.graphics_view = QGraphicsView()
        self.graphics_view.setMinimumHeight(200)
        self.graphics_view.setStyleSheet("QGraphicsView { background-color: #2a2a2a; border: 1px solid #555; }")
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setDragMode(QGraphicsView.NoDrag)
        
        # NO transformation anchor - we'll do it manually!
        self.graphics_view.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.graphics_view.setResizeAnchor(QGraphicsView.NoAnchor)
        
        # Disable keyboard focus - preview panel should NOT steal focus from browser
        # This was causing Space key (Quick View) to open Maya hotbox instead
        self.graphics_view.setFocusPolicy(Qt.NoFocus)
        
        # Create scene
        self.graphics_scene = QtWidgets.QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.pixmap_item = None
        
        # Install event filter instead of overriding methods directly
        self.graphics_view.viewport().installEventFilter(self)
        self.graphics_view.installEventFilter(self)
        self.graphics_view.setMouseTracking(True)
        
        preview_layout.addWidget(self.graphics_view)
        
        # Zoom controls toolbar (only visible in zoom mode)
        self.zoom_controls = QWidget()
        zoom_controls_layout = QHBoxLayout(self.zoom_controls)
        zoom_controls_layout.setContentsMargins(5, 2, 5, 2)
        zoom_controls_layout.setSpacing(5)
        
        zoom_controls_layout.addWidget(QLabel("Zoom:"))
        
        # Zoom out button
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setMaximumWidth(30)
        self.zoom_out_btn.setToolTip("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_controls_layout.addWidget(self.zoom_out_btn)
        
        # Zoom in button
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setMaximumWidth(30)
        self.zoom_in_btn.setToolTip("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_controls_layout.addWidget(self.zoom_in_btn)
        
        # 100% button
        self.zoom_100_btn = QPushButton("100%")
        self.zoom_100_btn.setMaximumWidth(50)
        self.zoom_100_btn.setToolTip("Actual Size (1:1)")
        self.zoom_100_btn.clicked.connect(self.zoom_100)
        zoom_controls_layout.addWidget(self.zoom_100_btn)
        
        # Fit button
        self.zoom_fit_btn = QPushButton("Fit")
        self.zoom_fit_btn.setMaximumWidth(50)
        self.zoom_fit_btn.setToolTip("Fit to View")
        self.zoom_fit_btn.clicked.connect(self.zoom_fit)
        zoom_controls_layout.addWidget(self.zoom_fit_btn)
        
        zoom_controls_layout.addStretch()
        
        # Exit zoom mode button
        self.zoom_exit_btn = QPushButton("Exit Zoom")
        self.zoom_exit_btn.setToolTip("Exit Zoom Mode (or double-click)")
        self.zoom_exit_btn.clicked.connect(self.exit_zoom_mode)
        zoom_controls_layout.addWidget(self.zoom_exit_btn)
        
        preview_layout.addWidget(self.zoom_controls)
        self.zoom_controls.hide()  # Hidden by default
        
        # HDR/EXR Exposure control (always visible for HDR/EXR files)
        self.exposure_controls = QWidget()
        exposure_layout = QHBoxLayout(self.exposure_controls)
        exposure_layout.setContentsMargins(5, 2, 5, 2)
        exposure_layout.setSpacing(5)
        
        exposure_layout.addWidget(QLabel("Exposure:"))
        
        # Exposure slider (-5.0 to +5.0 stops, default 0.0, like Arnold/Maya)
        self.exposure_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.exposure_slider.setMinimum(-50)  # -5.0 stops
        self.exposure_slider.setMaximum(50)   # +5.0 stops
        self.exposure_slider.setValue(0)      # 0.0 (neutral, default)
        self.exposure_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.exposure_slider.setTickInterval(10)  # Tick every 1.0 stop
        self.exposure_slider.valueChanged.connect(self.on_exposure_changed)
        exposure_layout.addWidget(self.exposure_slider, 1)
        
        # Exposure value label
        self.exposure_label = QLabel("0.0")
        self.exposure_label.setMinimumWidth(40)
        self.exposure_label.setStyleSheet("color: #aaa;")
        exposure_layout.addWidget(self.exposure_label)
        
        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setMaximumWidth(50)
        reset_btn.setToolTip("Reset to neutral (0.0)")
        reset_btn.clicked.connect(lambda: self.exposure_slider.setValue(0))
        exposure_layout.addWidget(reset_btn)
        
        preview_layout.addWidget(self.exposure_controls)
        self.exposure_controls.hide()  # Hidden by default, shown only for HDR/EXR
        
        # Text file preview controls (only visible for text files)
        self.text_controls = QWidget()
        text_controls_layout = QHBoxLayout(self.text_controls)
        text_controls_layout.setContentsMargins(5, 2, 5, 2)
        text_controls_layout.setSpacing(5)
        
        # Line wrap toggle
        self.line_wrap_checkbox = QCheckBox("Wrap Lines")
        self.line_wrap_checkbox.setChecked(True)  # Default: wrap on
        self.line_wrap_checkbox.toggled.connect(self.on_line_wrap_changed)
        text_controls_layout.addWidget(self.line_wrap_checkbox)
        
        text_controls_layout.addWidget(QLabel("Font Size:"))
        
        # Font size slider (6-20pt)
        self.font_size_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(6)
        self.font_size_slider.setMaximum(20)
        self.font_size_slider.setValue(9)  # Default 9pt
        self.font_size_slider.setMaximumWidth(100)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        text_controls_layout.addWidget(self.font_size_slider)
        
        # Font size label
        self.font_size_label = QLabel("9")
        self.font_size_label.setMinimumWidth(20)
        self.font_size_label.setStyleSheet("color: #aaa;")
        text_controls_layout.addWidget(self.font_size_label)
        
        text_controls_layout.addStretch()
        
        # Load Full File button (toggle)
        self.load_full_btn = QPushButton("📄 Load Full")
        self.load_full_btn.setMaximumWidth(90)
        self.load_full_btn.setCheckable(True)
        self.load_full_btn.setToolTip("Load full file content (may be slow for large files)")
        self.load_full_btn.clicked.connect(self.toggle_load_full_file)
        text_controls_layout.addWidget(self.load_full_btn)
        
        # Copy to clipboard button
        self.copy_text_btn = QPushButton("📋 Copy")
        self.copy_text_btn.setMaximumWidth(70)
        self.copy_text_btn.setToolTip("Copy text to clipboard")
        self.copy_text_btn.clicked.connect(self.copy_text_to_clipboard)
        text_controls_layout.addWidget(self.copy_text_btn)
        
        preview_layout.addWidget(self.text_controls)
        self.text_controls.hide()  # Hidden by default, shown only for text files
        
        # Store current text content for controls
        self.current_text_content = None
        self.current_text_item = None
        self.current_text_asset = None  # Store current asset for reload
        self.is_full_text_loaded = False  # Track if full file is loaded
        
        # Add preview container to splitter
        self.preview_splitter.addWidget(preview_container)
        
        # === PDF Navigation Overlay (modern, floating controls) ===
        # Previous page button (left overlay)
        self.pdf_prev_overlay = QPushButton("◀")
        self.pdf_prev_overlay.setParent(self.graphics_view)
        self.pdf_prev_overlay.setFixedSize(50, 80)
        self.pdf_prev_overlay.setToolTip("Previous Page (Left Arrow)")
        self.pdf_prev_overlay.setCursor(Qt.PointingHandCursor)
        self.pdf_prev_overlay.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 120);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                color: white;
                font-size: 24px;
                font-family: {UI_FONT};
            }}
            QPushButton:hover {{
                background-color: rgba(0, 120, 215, 180);
                border-color: rgba(255, 255, 255, 120);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 120, 215, 220);
            }}
            QPushButton:disabled {{
                background-color: rgba(0, 0, 0, 60);
                color: rgba(255, 255, 255, 80);
            }}
        """)
        self.pdf_prev_overlay.clicked.connect(self.pdf_previous_page)
        self.pdf_prev_overlay.hide()
        
        # Next page button (right overlay)
        self.pdf_next_overlay = QPushButton("▶")
        self.pdf_next_overlay.setParent(self.graphics_view)
        self.pdf_next_overlay.setFixedSize(50, 80)
        self.pdf_next_overlay.setToolTip("Next Page (Right Arrow)")
        self.pdf_next_overlay.setCursor(Qt.PointingHandCursor)
        self.pdf_next_overlay.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 120);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                color: white;
                font-size: 24px;
                font-family: {UI_FONT};
            }}
            QPushButton:hover {{
                background-color: rgba(0, 120, 215, 180);
                border-color: rgba(255, 255, 255, 120);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 120, 215, 220);
            }}
            QPushButton:disabled {{
                background-color: rgba(0, 0, 0, 60);
                color: rgba(255, 255, 255, 80);
            }}
        """)
        self.pdf_next_overlay.clicked.connect(self.pdf_next_page)
        self.pdf_next_overlay.hide()
        
        # Page indicator overlay (bottom center)
        self.pdf_page_overlay = QLabel("1 / 1")
        self.pdf_page_overlay.setParent(self.graphics_view)
        self.pdf_page_overlay.setAlignment(Qt.AlignCenter)
        self.pdf_page_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 150);
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 12px;
                color: white;
                font-size: 13px;
                font-family: {UI_FONT};
                font-weight: bold;
                padding: 6px 16px;
            }}
        """)
        self.pdf_page_overlay.hide()
        
        # Tab widget for Metadata and Tags (same style as other tabs in the app)
        self.info_tabs = QtWidgets.QTabWidget()
        self.info_tabs.setMovable(True)  # Enable drag & drop tab reordering like other tabs
        
        # Metadata tab
        metadata_tab = QWidget()
        metadata_tab_layout = QVBoxLayout(metadata_tab)
        metadata_tab_layout.setContentsMargins(0, 0, 0, 0)
        metadata_tab_layout.setSpacing(0)
        
        metadata_scroll = QScrollArea()
        metadata_scroll.setWidgetResizable(True)
        metadata_scroll.setMinimumHeight(80)  # Reduced from 250 to 80 for compact view
        metadata_scroll.setMaximumHeight(400)
        metadata_scroll.setStyleSheet("QScrollArea { border: none; background-color: #2a2a2a; }")
        
        metadata_widget = QWidget()
        self.metadata_layout = QVBoxLayout(metadata_widget)
        self.metadata_layout.setAlignment(Qt.AlignTop)
        self.metadata_layout.setSpacing(3)  # Reduced from 8 to 3
        self.metadata_layout.setContentsMargins(5, 5, 5, 5)
        metadata_scroll.setWidget(metadata_widget)
        
        metadata_tab_layout.addWidget(metadata_scroll)
        self.info_tabs.addTab(metadata_tab, "Metadata")
        
        # Tags tab
        tags_tab = QWidget()
        tags_tab_layout = QVBoxLayout(tags_tab)
        tags_tab_layout.setContentsMargins(5, 5, 5, 5)
        tags_tab_layout.setSpacing(5)
        
        # Tag input area
        tag_input_layout = QHBoxLayout()
        tag_input_layout.setSpacing(5)
        
        self.tag_input = QtWidgets.QLineEdit()
        self.tag_input.setPlaceholderText("Add tag...")
        self.tag_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
                font-family: {UI_FONT};
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: #4b7daa;
            }}
        """)
        self.tag_input.returnPressed.connect(self.add_tag)
        tag_input_layout.addWidget(self.tag_input)
        
        # Setup autocomplete for tag input
        self.setup_tag_autocomplete()
        
        self.add_tag_btn = QPushButton("+ Add")
        self.add_tag_btn.setMaximumWidth(60)
        self.add_tag_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #4b7daa;
                border: none;
                border-radius: 3px;
                padding: 5px;
                color: white;
                font-family: {UI_FONT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #5a8db8;
            }}
            QPushButton:pressed {{
                background-color: #3a6d9a;
            }}
        """)
        self.add_tag_btn.clicked.connect(self.add_tag)
        tag_input_layout.addWidget(self.add_tag_btn)
        
        # Browse Tags button
        self.browse_tags_btn = QPushButton("📚 Browse")
        self.browse_tags_btn.setMaximumWidth(80)
        self.browse_tags_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #cccccc;
                font-family: {UI_FONT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #4a4a4a;
                border-color: #666;
            }}
            QPushButton:pressed {{
                background-color: #2a2a2a;
            }}
        """)
        self.browse_tags_btn.clicked.connect(self.show_browse_tags_dialog)
        self.browse_tags_btn.setToolTip("Browse all available tags by category")
        tag_input_layout.addWidget(self.browse_tags_btn)
        
        # Clear All Tags button
        self.clear_all_tags_btn = QPushButton("🗑️ Clear All")
        self.clear_all_tags_btn.setMaximumWidth(80)
        self.clear_all_tags_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #cccccc;
                font-family: {UI_FONT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #8B0000;
                border-color: #A00000;
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #6B0000;
            }}
        """)
        self.clear_all_tags_btn.clicked.connect(self.clear_all_tags_from_selection)
        self.clear_all_tags_btn.setToolTip("Remove all tags from selected file(s)")
        tag_input_layout.addWidget(self.clear_all_tags_btn)
        
        tags_tab_layout.addLayout(tag_input_layout)
        
        # Tags display area (scrollable)
        tags_scroll = QScrollArea()
        tags_scroll.setWidgetResizable(True)
        tags_scroll.setStyleSheet("QScrollArea { border: none; background-color: #2a2a2a; }")
        
        self.tags_container = QWidget()  # Store as instance variable for later access
        self.tags_layout = FlowLayout()  # Flow layout for tag chips
        self.tags_layout.setSpacing(5)
        self.tags_layout.setContentsMargins(0, 5, 0, 5)
        self.tags_container.setLayout(self.tags_layout)
        tags_scroll.setWidget(self.tags_container)
        
        tags_tab_layout.addWidget(tags_scroll)
        
        # Tag info label
        self.tag_info_label = QLabel("No tags yet. Add tags to organize your assets.")
        self.tag_info_label.setStyleSheet(f"color: #888; font-size: 10px; font-family: {UI_FONT}; padding: 5px;")
        self.tag_info_label.setAlignment(Qt.AlignCenter)
        self.tag_info_label.setWordWrap(True)
        tags_tab_layout.addWidget(self.tag_info_label)
        
        self.info_tabs.addTab(tags_tab, "Tags")
        
        # Set minimum height for info tabs (similar to Collections/Advanced Filters tabs)
        self.info_tabs.setMinimumHeight(120)
        
        # Add info tabs to splitter
        self.preview_splitter.addWidget(self.info_tabs)
        
        # Restore splitter position from config or set default
        if self.config and "preview_splitter_position" in self.config.config:
            try:
                from base64 import b64decode
                state_str = self.config.config["preview_splitter_position"]
                state_bytes = QtCore.QByteArray.fromBase64(state_str.encode())
                self.preview_splitter.restoreState(state_bytes)
            except:
                # If restore fails, use default sizes
                self.preview_splitter.setSizes([600, 400])
        else:
            # Set initial splitter sizes (60% preview, 40% info)
            self.preview_splitter.setSizes([600, 400])
        
        # Connect signal to save position when moved
        if self.config:
            self.preview_splitter.splitterMoved.connect(self.on_preview_splitter_moved)
        
        # Add splitter to main layout
        layout.addWidget(self.preview_splitter)
        
        # Show empty state
        self.show_empty_state()
    
    def resizeEvent(self, event):
        """Handle resize - refit image to new panel width and reposition PDF overlays"""
        super().resizeEvent(event)
        
        # Only resize if NOT in zoom mode
        if not self.zoom_mode and self.current_pixmap and not self.current_pixmap.isNull():
            self.fit_pixmap_to_label()
        
        # Update PDF overlay positions
        self.update_pdf_overlay_positions()
        
        # Update text wrap width on resize
        if self.current_text_item and self.line_wrap_checkbox.isChecked():
            try:
                viewport_width = self.graphics_view.viewport().width() - 20
                self.current_text_item.setTextWidth(viewport_width)
                
                # Update scene rect to fit new text bounds (without processEvents)
                text_rect = self.current_text_item.boundingRect()
                padded_rect = text_rect.adjusted(-10, -10, 10, 100)
                self.graphics_scene.setSceneRect(padded_rect)
            except RuntimeError:
                # Object was already deleted, reset reference
                self.current_text_item = None
    
    def fit_pixmap_to_label(self):
        """Fit current pixmap to view"""
        if not self.current_pixmap or self.current_pixmap.isNull() or self.zoom_mode:
            return
        
        self.set_preview_pixmap(self.current_pixmap)
        self.fit_preview_to_view()
    
    def update_pdf_overlay_positions(self):
        """Update PDF overlay button positions (called on resize)"""
        if not self.is_showing_pdf:
            return
        
        view_width = self.graphics_view.width()
        view_height = self.graphics_view.height()
        
        # Previous button - left side, vertically centered
        self.pdf_prev_overlay.move(10, (view_height - self.pdf_prev_overlay.height()) // 2)
        
        # Next button - right side, vertically centered
        self.pdf_next_overlay.move(
            view_width - self.pdf_next_overlay.width() - 10,
            (view_height - self.pdf_next_overlay.height()) // 2
        )
        
        # Page indicator - bottom center
        self.pdf_page_overlay.adjustSize()  # Adjust to text size
        self.pdf_page_overlay.move(
            (view_width - self.pdf_page_overlay.width()) // 2,
            view_height - self.pdf_page_overlay.height() - 15
        )
    
    def show_empty_state(self):
        """Show empty state when no file is selected"""
        self.title_label.setText("Preview")
        self.set_preview_pixmap(None)
        self.current_image_path = None
        self.current_hdr_path = None
        self.exit_zoom_mode()  # Exit zoom mode when deselecting
        self.clear_metadata()
        self.exposure_controls.hide()  # Hide exposure controls
        self.text_controls.hide()  # Hide text controls
        
        # Hide PDF overlay controls
        self.pdf_prev_overlay.hide()
        self.pdf_next_overlay.hide()
        self.pdf_page_overlay.hide()
        
        self.is_showing_text = False  # Reset text mode flag
        self.is_showing_pdf = False  # Reset PDF mode flag
        self.graphics_view.viewport().setCursor(Qt.ArrowCursor)  # Reset cursor
        
        # Reset text preview state
        self.is_full_text_loaded = False
        if hasattr(self, 'load_full_btn'):
            self.load_full_btn.setChecked(False)
            self.load_full_btn.setText("📄 Load Full")
    
    def on_exposure_changed(self, value):
        """Handle exposure slider change - debounced for smooth dragging"""
        exposure_stops = value / 10.0  # Slider -50 to +50 -> -5.0 to +5.0 stops
        
        # Format label with +/- sign (like Arnold) - update immediately
        if exposure_stops >= 0:
            self.exposure_label.setText(f"+{exposure_stops:.1f}")
        else:
            self.exposure_label.setText(f"{exposure_stops:.1f}")
        
        # Store pending value and restart timer (debounce)
        self.pending_exposure_value = exposure_stops
        self.exposure_timer.stop()
        self.exposure_timer.start()
    
    def apply_exposure_change(self):
        """Actually apply the exposure change (called after debounce timer)"""
        if self.pending_exposure_value is None:
            return
        
        exposure_stops = self.pending_exposure_value
        self.hdr_exposure = exposure_stops
        
        # Fast re-tone map from cached raw data if available
        if self.current_hdr_path and self.current_hdr_path in self.hdr_raw_cache:
            # print(f"🚀 FAST PATH: Using cached raw data for exposure adjustment")
            rgb_raw, width, height, resolution_str = self.hdr_raw_cache[self.current_hdr_path]
            
            # Apply tone mapping with new exposure (FAST - no disk I/O!)
            pixmap = self.apply_hdr_tone_mapping(rgb_raw, width, height, exposure_stops)
            
            if pixmap:
                self.current_pixmap = pixmap
                # Update preview cache too
                self.add_to_cache(self.current_hdr_path, pixmap, resolution_str)
                self.fit_pixmap_to_label()
        elif self.current_hdr_path:
            # print(f"⚠️ SLOW PATH: Raw data not cached, reloading from disk...")
            # Fallback: raw data not cached - reload from disk (slower)
            # Remove from preview cache to force reload
            if self.current_hdr_path in self.preview_cache:
                del self.preview_cache[self.current_hdr_path]
            
            # Reload with new exposure (use max_preview_size setting)
            pixmap, resolution_str = load_hdr_exr_image(self.current_hdr_path, max_size=self.max_preview_size, exposure=exposure_stops)
            
            if pixmap:
                self.current_pixmap = pixmap
                self.add_to_cache(self.current_hdr_path, pixmap, resolution_str)
                self.fit_pixmap_to_label()
    
    def apply_hdr_tone_mapping(self, rgb_raw, width, height, exposure_stops):
        """Apply tone mapping to raw HDR data - FAST (no disk I/O)"""
        if not NUMPY_AVAILABLE:
            return None
        
        try:
            # Apply exposure compensation in stops
            exposure_multiplier = pow(2.0, exposure_stops)
            rgb = rgb_raw * exposure_multiplier
            
            # ACES Filmic tone mapping
            a = 2.51
            b = 0.03
            c = 2.43
            d = 0.59
            e = 0.14
            rgb_tonemapped = np.clip((rgb * (a * rgb + b)) / (rgb * (c * rgb + d) + e), 0, 1)
            
            # Gamma correction (2.2 for sRGB)
            gamma = 1.0 / 2.2
            rgb_tonemapped = np.power(rgb_tonemapped, gamma)
            
            # Convert to 8-bit
            rgb_8bit = (rgb_tonemapped * 255).astype(np.uint8)
            
            # Create QImage
            bytes_per_line = width * 3
            q_image = QImage(rgb_8bit.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
            q_image = q_image.copy()
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            return pixmap
            
        except Exception as e:
            print(f"Tone mapping error: {e}")
            return None
    
    def add_to_hdr_raw_cache(self, file_path, rgb_raw, width, height, resolution_str):
        """Add raw HDR float data to cache with LRU eviction"""
        # If cache is full, remove oldest entry
        if len(self.hdr_raw_cache) >= self.hdr_cache_max_size:
            first_key = next(iter(self.hdr_raw_cache))
            del self.hdr_raw_cache[first_key]
        
        # Add new entry (store a COPY to prevent modification)
        self.hdr_raw_cache[file_path] = (rgb_raw.copy(), width, height, resolution_str)
    
    def show_hdr_placeholder(self, filename):
        """Show placeholder for HDR/EXR files that couldn't be loaded"""
        # Create a simple placeholder pixmap
        placeholder = QPixmap(400, 300)
        placeholder.fill(QColor(60, 60, 60))
        
        # Draw icon and text
        painter = QPainter(placeholder)
        painter.setPen(QColor(180, 180, 180))
        
        # Draw large icon
        font = QFont(UI_FONT, 48)
        painter.setFont(font)
        painter.drawText(placeholder.rect(), Qt.AlignCenter, "🌅")
        
        # Draw filename below
        font = QFont(UI_FONT, 10)
        painter.setFont(font)
        text_rect = placeholder.rect().adjusted(0, 100, 0, 0)
        painter.drawText(text_rect, Qt.AlignCenter, f"HDR/EXR Preview\n\n{filename}\n\nCould not load file")
        
        painter.end()
        
        self.current_pixmap = placeholder
        self.fit_pixmap_to_label()
        
        # Add metadata note
        self.add_metadata_row("⚠️", "Error", "Failed to load HDR/EXR")
        self.add_metadata_row("💡", "Tip", "Check if file is corrupted")
    
    def eventFilter(self, obj, event):
        """Event filter for graphics view - handles mouse events for zoom/pan and PDF navigation"""
        # Only filter events from graphics_view or its viewport
        if obj not in (self.graphics_view, self.graphics_view.viewport()):
            return super().eventFilter(obj, event)
        
        event_type = event.type()
        
        # === PDF Navigation with Arrow Keys === DISABLED
        # PDF has its own navigation buttons in the preview panel
        # Arrow keys should be used for file navigation in the browser, not PDF page navigation
        # This was causing conflicts with Quick View activation and file navigation
        # if self.is_showing_pdf and event_type == QEvent.KeyPress:
        #     key = event.key()
        #     if key == Qt.Key_Left:
        #         # Left arrow - previous page
        #         if self.current_pdf_page > 0:
        #             self.pdf_previous_page()
        #         return True
        #     elif key == Qt.Key_Right:
        #         # Right arrow - next page
        #         if self.current_pdf_page < self.current_pdf_page_count - 1:
        #             self.pdf_next_page()
        #         return True
        
        # Handle Ctrl+Wheel for font size adjustment in text mode
        if self.is_showing_text and event_type == QEvent.Wheel:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                # Ctrl+Scroll to change font size
                delta = event.angleDelta().y()
                current_size = self.font_size_slider.value()
                
                # Increase or decrease by 1
                if delta > 0:
                    new_size = min(current_size + 1, 20)  # Max 20
                else:
                    new_size = max(current_size - 1, 6)   # Min 6
                
                if new_size != current_size:
                    self.font_size_slider.setValue(new_size)
                
                return True  # Event handled, don't scroll
        
        # In text mode (without Ctrl), let all events pass through for text selection
        if self.is_showing_text:
            return False  # Don't filter, let the default handler work
        
        # Handle image-specific events (zoom mode)
        
        # Double-click - enter/exit zoom mode
        if event_type == QEvent.MouseButtonDblClick:
            if self.current_image_path and Path(self.current_image_path).exists():
                if not self.zoom_mode:
                    self.enter_zoom_mode()
                else:
                    self.exit_zoom_mode()
                return True  # Event handled
        
        # Mouse wheel - zoom in zoom mode
        if event_type == QEvent.Wheel and self.zoom_mode and self.pixmap_item:
            # Get mouse position in scene coordinates BEFORE zoom
            old_pos = self.graphics_view.mapToScene(event.position().toPoint())
            
            # Calculate zoom factor
            delta = event.angleDelta().y()
            zoom_factor = 1.15 if delta > 0 else 1.0 / 1.15
            
            # Update zoom level
            old_zoom = self.zoom_level
            if delta > 0:
                self.zoom_level = min(self.zoom_level * zoom_factor, 10.0)
            else:
                self.zoom_level = max(self.zoom_level * zoom_factor, 0.1)
            
            # Snap to 100%
            if 0.95 <= self.zoom_level <= 1.05:
                self.zoom_level = 1.0
            
            # Calculate actual zoom factor applied
            actual_factor = self.zoom_level / old_zoom
            
            # Apply zoom using view transform
            self.graphics_view.scale(actual_factor, actual_factor)
            
            # Get mouse position in scene coordinates AFTER zoom
            new_pos = self.graphics_view.mapToScene(event.position().toPoint())
            
            # Calculate offset to keep point under cursor
            delta_pos = new_pos - old_pos
            
            # Translate view to compensate
            self.graphics_view.translate(delta_pos.x(), delta_pos.y())
            
            # Update zoom label
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
            
            return True  # Event handled
        
        # Mouse press - start panning in zoom mode
        if event_type == QEvent.MouseButtonPress and self.zoom_mode and event.button() == Qt.LeftButton:
            try:
                self.last_mouse_pos = event.globalPosition().toPoint()
            except AttributeError:
                self.last_mouse_pos = event.globalPos()
            
            self.graphics_view.setCursor(Qt.ClosedHandCursor)
            return True  # Event handled
        
        # Mouse move - pan in zoom mode
        if event_type == QEvent.MouseMove and self.zoom_mode and self.last_mouse_pos is not None:
            try:
                current_pos = event.globalPosition().toPoint()
            except AttributeError:
                current_pos = event.globalPos()
            
            delta = current_pos - self.last_mouse_pos
            self.last_mouse_pos = current_pos
            
            # Scroll the graphics view
            h_bar = self.graphics_view.horizontalScrollBar()
            v_bar = self.graphics_view.verticalScrollBar()
            
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            
            return True  # Event handled
        
        # Mouse release - stop panning
        if event_type == QEvent.MouseButtonRelease and self.zoom_mode and event.button() == Qt.LeftButton:
            self.last_mouse_pos = None
            self.graphics_view.setCursor(Qt.OpenHandCursor)
            return True  # Event handled
        
        # Don't filter other events
        return False
    
    def enter_zoom_mode(self):
        """Enter zoom mode - load full resolution image or PDF"""
        if not self.current_image_path:
            return
        
        try:
            file_path_str = str(self.current_image_path)
            file_ext = file_path_str.lower()
            
            # === PDF ZOOM ===
            if file_ext.endswith('.pdf') and PYMUPDF_AVAILABLE:
                # Load current PDF page at FULL resolution (max 4096 for quality)
                pixmap, page_count, resolution = load_pdf_page(
                    self.current_pdf_path,
                    self.current_pdf_page,
                    max_size=4096  # High quality zoom
                )
                
                if pixmap and not pixmap.isNull():
                    self.full_res_pixmap = pixmap
                else:
                    print("Failed to load high-res PDF page")
                    return
            
            # === TIFF with OpenCV ===
            elif (file_ext.endswith('.tif') or file_ext.endswith('.tiff')) and OPENCV_AVAILABLE and NUMPY_AVAILABLE:
                try:
                    import cv2
                    import numpy as np
                    
                    # Read FULL resolution image with OpenCV
                    img = cv2.imread(file_path_str, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
                    
                    if img is not None:
                        # Convert to RGB if needed (same logic as preview)
                        if len(img.shape) == 2:
                            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                        elif img.shape[2] == 4:
                            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                        elif img.shape[2] == 3:
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        
                        # Normalize to 0-255 range (same logic as preview)
                        if img.dtype == np.uint16:
                            img = (img / 256).astype(np.uint8)
                        elif img.dtype == np.float32 or img.dtype == np.float64:
                            img = np.clip(img, 0, 1)
                            img = (img * 255).astype(np.uint8)
                        
                        # Convert to QPixmap
                        height, width, channels = img.shape
                        bytes_per_line = width * channels
                        q_image = QImage(img.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                        self.full_res_pixmap = QPixmap.fromImage(q_image.copy())
                    else:
                        raise Exception("OpenCV could not load TIFF")
                        
                except Exception as e:
                    # Fallback to standard QPixmap loading
                    self.full_res_pixmap = QPixmap(file_path_str)
            
            # === Standard images (JPG, PNG, etc.) ===
            else:
                # Standard image formats - use QPixmap directly
                self.full_res_pixmap = QPixmap(file_path_str)
            
            if self.full_res_pixmap.isNull():
                return
            
            self.zoom_mode = True
            self.pan_offset = QPoint(0, 0)
            
            # Keep PDF overlay controls visible in zoom mode for easy page navigation
            # (They stay visible so you can navigate pages while zoomed)
            
            # Set pixmap at original size
            self.set_preview_pixmap(self.full_res_pixmap)
            
            # Reset view transform and fit to window initially
            self.graphics_view.resetTransform()
            self.graphics_view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            
            # Calculate the zoom level from fitInView
            # This gives us the current fit zoom level
            rect = self.pixmap_item.boundingRect()
            view_rect = self.graphics_view.viewport().rect()
            x_ratio = view_rect.width() / rect.width()
            y_ratio = view_rect.height() / rect.height()
            self.zoom_level = min(x_ratio, y_ratio)
            
            # Update title
            self.title_label.setText(f"🔍 Zoom Mode")
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
            
            # Show zoom controls
            self.zoom_controls.show()
            
            # Change cursor
            self.graphics_view.setCursor(Qt.OpenHandCursor)
            
        except Exception as e:
            print(f"Error loading full resolution: {e}")
    
    def exit_zoom_mode(self):
        """Exit zoom mode - return to preview"""
        if self.zoom_mode:
            self.zoom_mode = False
            self.full_res_pixmap = None
            self.zoom_level = 1.0
            self.pan_offset = QPoint(0, 0)
            self.zoom_label.setText("")
            
            # Hide zoom controls
            self.zoom_controls.hide()
            
            # Restore PDF overlay controls if we were viewing a PDF
            if self.is_showing_pdf:
                self.pdf_prev_overlay.show()
                self.pdf_next_overlay.show()
                self.pdf_page_overlay.show()
                self.update_pdf_overlay_positions()
            
            # Restore preview
            if self.current_pixmap:
                self.fit_pixmap_to_label()
            
            # Reset cursor
            self.graphics_view.setCursor(Qt.ArrowCursor)
            
            # Restore title
            if self.current_image_path:
                self.title_label.setText(f"Preview: {Path(self.current_image_path).name}")
    
    def set_preview_pixmap(self, pixmap):
        """Set pixmap in graphics view"""
        self.graphics_scene.clear()
        self.current_text_item = None  # Clear text item reference when showing images
        self.is_showing_text = False  # Reset text mode flag when showing images
        if pixmap:
            self.pixmap_item = self.graphics_scene.addPixmap(pixmap)
            self.graphics_scene.setSceneRect(self.pixmap_item.boundingRect())
            # Reset cursor to arrow for images
            self.graphics_view.viewport().setCursor(Qt.ArrowCursor)
        else:
            self.pixmap_item = None
            # Reset cursor to arrow
            self.graphics_view.viewport().setCursor(Qt.ArrowCursor)
    
    def show_placeholder_with_text(self, text):
        """Show a placeholder text message in the preview area"""
        self.graphics_scene.clear()
        self.pixmap_item = None
        self.current_text_item = None
        self.is_showing_text = False
        
        # Create a text item for the error message
        text_item = self.graphics_scene.addText(text)
        text_item.setDefaultTextColor(QColor("#888888"))
        
        # Center the text in the view
        text_rect = text_item.boundingRect()
        view_rect = self.graphics_view.viewport().rect()
        x = (view_rect.width() - text_rect.width()) / 2
        y = (view_rect.height() - text_rect.height()) / 2
        text_item.setPos(x, y)
        
        # Set scene rect to view size
        self.graphics_scene.setSceneRect(0, 0, view_rect.width(), view_rect.height())
    
    def fit_preview_to_view(self):
        """Fit the entire preview image in view"""
        if self.pixmap_item:
            self.graphics_view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
    
    def update_zoom_display(self):
        """Update display with current zoom level"""
        if not self.full_res_pixmap or not self.zoom_mode:
            return
        
        # Set the original full-res pixmap (without scaling)
        self.set_preview_pixmap(self.full_res_pixmap)
        
        # Reset transform and apply zoom via transform
        self.graphics_view.resetTransform()
        self.graphics_view.scale(self.zoom_level, self.zoom_level)
        
        # Update zoom label
        self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")

    
    def zoom_in(self):
        """Zoom in button - centered on current view"""
        if self.zoom_mode and self.pixmap_item:
            # Get the center of the current viewport in scene coordinates BEFORE zoom
            viewport_rect = self.graphics_view.viewport().rect()
            center_point = self.graphics_view.mapToScene(viewport_rect.center())
            
            # Calculate zoom factor
            old_zoom = self.zoom_level
            self.zoom_level *= 1.25
            self.zoom_level = min(self.zoom_level, 10.0)
            zoom_factor = self.zoom_level / old_zoom
            
            # Apply zoom using view transform
            self.graphics_view.scale(zoom_factor, zoom_factor)
            
            # Get the center point in scene coordinates AFTER zoom
            new_center = self.graphics_view.mapToScene(viewport_rect.center())
            
            # Calculate offset to keep the center point in place
            delta_pos = new_center - center_point
            
            # Translate view to compensate
            self.graphics_view.translate(delta_pos.x(), delta_pos.y())
            
            # Update zoom label
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
    
    def zoom_out(self):
        """Zoom out button - centered on current view"""
        if self.zoom_mode and self.pixmap_item:
            # Get the center of the current viewport in scene coordinates BEFORE zoom
            viewport_rect = self.graphics_view.viewport().rect()
            center_point = self.graphics_view.mapToScene(viewport_rect.center())
            
            # Calculate zoom factor
            old_zoom = self.zoom_level
            self.zoom_level /= 1.25
            self.zoom_level = max(self.zoom_level, 0.1)
            zoom_factor = self.zoom_level / old_zoom
            
            # Apply zoom using view transform
            self.graphics_view.scale(zoom_factor, zoom_factor)
            
            # Get the center point in scene coordinates AFTER zoom
            new_center = self.graphics_view.mapToScene(viewport_rect.center())
            
            # Calculate offset to keep the center point in place
            delta_pos = new_center - center_point
            
            # Translate view to compensate
            self.graphics_view.translate(delta_pos.x(), delta_pos.y())
            
            # Update zoom label
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")

    
    def zoom_100(self):
        """Zoom to 100% (actual size - 1:1 pixel ratio) centered on current view"""
        if self.zoom_mode and self.full_res_pixmap and self.pixmap_item:
            # Get the center of the current viewport in scene coordinates BEFORE zoom
            viewport_rect = self.graphics_view.viewport().rect()
            center_point = self.graphics_view.mapToScene(viewport_rect.center())
            
            # Calculate zoom factor from current zoom to 1.0
            old_zoom = self.zoom_level
            self.zoom_level = 1.0
            zoom_factor = self.zoom_level / old_zoom
            
            # Apply zoom using view transform
            self.graphics_view.scale(zoom_factor, zoom_factor)
            
            # Get the center point in scene coordinates AFTER zoom
            new_center = self.graphics_view.mapToScene(viewport_rect.center())
            
            # Calculate offset to keep the center point in place
            delta_pos = new_center - center_point
            
            # Translate view to compensate
            self.graphics_view.translate(delta_pos.x(), delta_pos.y())
            
            # Update zoom label
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
    
    def zoom_fit(self):
        """Fit image to viewport"""
        if self.zoom_mode and self.full_res_pixmap:
            self.update_zoom_display()
            self.fit_preview_to_view()
    
    def clear_metadata(self):
        """Clear metadata labels"""
        while self.metadata_layout.count():
            item = self.metadata_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_metadata_row(self, icon, label, value):
        """Add a metadata row with icon, label, and value"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 1, 0, 1)
        row_layout.setSpacing(6)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(20)
        icon_label.setStyleSheet(f"font-size: 13px; font-family: {UI_FONT};")
        row_layout.addWidget(icon_label)
        
        # Label
        label_widget = QLabel(f"<b>{label}:</b>")
        label_widget.setMinimumWidth(75)
        label_widget.setStyleSheet(f"font-size: 11px; font-family: {UI_FONT};")
        row_layout.addWidget(label_widget)
        
        # Value
        value_widget = QLabel(str(value))
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet(f"color: #b0b0b0; font-size: 11px; font-family: {UI_FONT};")
        row_layout.addWidget(value_widget, 1)
        
        # Add the row widget to metadata layout
        self.metadata_layout.addWidget(row_widget)
    
    def add_metadata_tags_display(self, assets):
        """Add read-only tags display in metadata tab with Edit button"""
        # Create row widget similar to other metadata rows
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 1, 0, 1)
        row_layout.setSpacing(6)
        
        # Icon
        icon_label = QLabel("🏷️")
        icon_label.setFixedWidth(20)
        icon_label.setStyleSheet(f"font-size: 13px; font-family: {UI_FONT};")
        row_layout.addWidget(icon_label)
        
        # Label
        label_widget = QLabel(f"<b>Tags:</b>")
        label_widget.setMinimumWidth(75)
        label_widget.setStyleSheet(f"font-size: 11px; font-family: {UI_FONT};")
        row_layout.addWidget(label_widget)
        
        # Get tags from metadata database
        try:
            from .metadata import get_metadata_manager
            metadata = get_metadata_manager()
        except ImportError:
            metadata = None
        
        if not metadata:
            row_layout.addWidget(QLabel("(no tags)"), 1)
            self.metadata_layout.addWidget(row_widget)
            return
        
        # Collect all tags from selected files
        all_file_tags = {}  # {file_path: [{'id': int, 'name': str, 'category': str, 'color': str}, ...]}
        total_files = len(assets)
        
        for asset in assets:
            file_path = str(asset.file_path)
            file_meta = metadata.get_file_metadata(file_path)
            if file_meta and file_meta.get('tags'):
                all_file_tags[file_path] = file_meta['tags']
        
        if not all_file_tags:
            # No tags on any files
            no_tags_label = QLabel("(no tags)")
            no_tags_label.setStyleSheet(f"color: #b0b0b0; font-size: 11px; font-family: {UI_FONT};")
            row_layout.addWidget(no_tags_label, 1)
        else:
            # Count tag occurrences
            tag_counts = {}  # {tag_id: {'tag': dict, 'count': int}}
            for file_tags in all_file_tags.values():
                for tag_dict in file_tags:
                    tag_id = tag_dict['id']
                    if tag_id not in tag_counts:
                        tag_counts[tag_id] = {'tag': tag_dict, 'count': 0}
                    tag_counts[tag_id]['count'] += 1
            
            # Separate common and partial tags
            common_tags = []  # Tags in ALL files
            partial_tags = []  # Tags in SOME files
            
            for tag_id, data in tag_counts.items():
                if data['count'] == total_files:
                    common_tags.append(data['tag'])
                else:
                    partial_tags.append((data['tag'], data['count']))
            
            # Sort tags
            common_tags.sort(key=lambda x: x['name'])  # Sort by tag name
            partial_tags.sort(key=lambda x: x[0]['name'])  # Sort by tag name
            
            # Create tags text display
            tags_text_parts = []
            
            # Common tags (bold)
            for tag_dict in common_tags:
                tag_text = tag_dict['name']
                tags_text_parts.append(f"<b>{tag_text}</b>")
            
            # Partial tags (normal with count)
            for tag_dict, count in partial_tags:
                tag_text = tag_dict['name']
                tags_text_parts.append(f"{tag_text} ({count}/{total_files})")
            
            # Create tags display label
            if tags_text_parts:
                tags_display = QLabel(", ".join(tags_text_parts))
                tags_display.setWordWrap(True)
                tags_display.setStyleSheet(f"color: #b0b0b0; font-size: 11px; font-family: {UI_FONT};")
                tags_display.setToolTip("Bold tags are in all selected files.\nTags with counts are in some files.\nClick 'Edit Tags' button to modify.")
                row_layout.addWidget(tags_display, 1)
            else:
                no_tags_label = QLabel("(no tags)")
                no_tags_label.setStyleSheet(f"color: #b0b0b0; font-size: 11px; font-family: {UI_FONT};")
                row_layout.addWidget(no_tags_label, 1)
        
        # Add "Edit Tags" button
        edit_button = QtWidgets.QPushButton("Edit Tags")
        edit_button.setFixedWidth(80)
        edit_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                color: #cccccc;
                padding: 2px 8px;
                font-size: 10px;
                font-family: {UI_FONT};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: #4a4a4a;
                border-color: #666;
            }}
            QPushButton:pressed {{
                background-color: #2a2a2a;
            }}
        """)
        edit_button.clicked.connect(lambda: self.info_tabs.setCurrentIndex(1))  # Switch to Tags tab (index 1)
        edit_button.setToolTip("Switch to Tags tab to edit tags")
        row_layout.addWidget(edit_button)
        
        # Add the row widget to metadata layout
        self.metadata_layout.addWidget(row_widget)
    
    def update_preview(self, assets):
        """Update preview panel with selected assets"""
        self.current_assets = assets
        
        # Refresh browse dialog colors if open (selection changed)
        if hasattr(self, '_active_browse_dialog') and self._active_browse_dialog:
            try:
                dialog = self._active_browse_dialog
                if hasattr(dialog, '_tag_buttons') and hasattr(dialog, '_mm'):
                    self._refresh_browse_dialog_buttons(dialog, dialog._tag_buttons, dialog._mm)
            except:
                pass  # Dialog might be closed
        
        if not assets:
            self.show_empty_state()
            return
        
        if len(assets) == 1:
            # Single file - show full preview and metadata
            self.show_single_file(assets[0])
        else:
            # Multiple files - show first file + summary
            self.show_multiple_files(assets)
    
    def show_single_file(self, asset):
        """Show preview and metadata for single file"""
        # Exit zoom mode when switching files
        self.exit_zoom_mode()
        
        # Clear previous pixmap to avoid showing wrong image on load failure
        self.current_pixmap = None
        self.graphics_scene.clear()
        self.current_text_item = None
        
        # Reset mode flags
        self.is_showing_text = False
        self.is_showing_pdf = False
        
        # Hide all control panels initially
        self.exposure_controls.hide()
        self.text_controls.hide()
        
        # Hide PDF overlay controls
        self.pdf_prev_overlay.hide()
        self.pdf_next_overlay.hide()
        self.pdf_page_overlay.hide()
        
        self.title_label.setText(f"Preview: {asset.name}")
        self.clear_metadata()
        
        # Store current image path for zoom viewer
        if asset.is_image_file:
            self.current_image_path = asset.file_path
        else:
            self.current_image_path = None
        
        # Load preview image (with cache!)
        pixmap = None
        resolution_str = None
        self.current_pixmap = None
        
        file_path_str = str(asset.file_path)
        
        if asset.is_image_file:
            # Check if HDR/EXR format first (before cache check)
            file_ext = file_path_str.lower()
            is_hdr_exr = file_ext.endswith('.hdr') or file_ext.endswith('.exr')
            
            # Set up exposure controls for HDR/EXR only
            if is_hdr_exr:
                self.current_hdr_path = file_path_str
                self.exposure_controls.show()
                # Reset exposure to neutral (0.0) when opening new HDR/EXR/HDR-TIFF
                self.exposure_slider.setValue(0)
                self.hdr_exposure = 0.0
            else:
                self.current_hdr_path = None
                # exposure_controls already hidden above
            
            # Check cache (skip cache for HDR formats that need exposure control)
            if not is_hdr_exr and file_path_str in self.preview_cache:
                # Cache hit! Instant load (only for non-HDR images)
                pixmap, resolution_str = self.preview_cache[file_path_str]
                self.current_pixmap = pixmap
                self.fit_pixmap_to_label()
            else:
                # Cache miss - show loading indicator
                self.graphics_scene.clear()
                self.current_text_item = None
                QApplication.processEvents()  # Update UI immediately
                
                # Load and cache
                try:
                    if is_hdr_exr:
                        # Use imageio (HDR) or OpenEXR (EXR) with exposure control
                        # Higher quality preview: adjustable via settings
                        
                        # First, try to load raw float data for fast exposure adjustment
                        # Use max_preview_size setting (default 1024px for speed)
                        rgb_raw, width, height, resolution_str = load_hdr_exr_raw(file_path_str, max_size=self.max_preview_size)
                        
                        if rgb_raw is not None:
                            # Cache raw data for fast exposure adjustments!
                            self.add_to_hdr_raw_cache(file_path_str, rgb_raw, width, height, resolution_str)
                            
                            # Apply tone mapping with current exposure
                            pixmap = self.apply_hdr_tone_mapping(rgb_raw, width, height, self.hdr_exposure)
                        else:
                            # Fallback: old method (slower, no caching)
                            pixmap, resolution_str = load_hdr_exr_image(file_path_str, max_size=self.max_preview_size, exposure=self.hdr_exposure)
                        
                        if pixmap:
                            self.current_pixmap = pixmap
                            self.add_to_cache(file_path_str, pixmap, resolution_str)
                            self.fit_pixmap_to_label()
                        else:
                            self.graphics_scene.clear()
                            self.current_text_item = None
                            self.show_hdr_placeholder(asset.name)
                    else:
                        # Standard image formats (PNG, JPG, TIF, etc.) - NO exposure control
                        self.current_hdr_path = None
                        self.exposure_controls.hide()  # Hide exposure slider for non-HDR
                        
                        # Special handling for 16-bit/32-bit TIFF files - use OpenCV for better support
                        file_ext = file_path_str.lower()
                        if (file_ext.endswith('.tif') or file_ext.endswith('.tiff')) and OPENCV_AVAILABLE and NUMPY_AVAILABLE:
                            try:
                                import cv2
                                import numpy as np
                                
                                # Read image with OpenCV (supports 16-bit and 32-bit TIFF)
                                img = cv2.imread(file_path_str, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
                                
                                if img is not None:
                                    # Get original size for resolution metadata
                                    height, width = img.shape[:2]
                                    resolution_str = f"{width} x {height}"
                                    
                                    # Convert to RGB if needed
                                    if len(img.shape) == 2:
                                        # Grayscale - convert to RGB
                                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                                    elif img.shape[2] == 4:
                                        # RGBA - convert to RGB
                                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                                    elif img.shape[2] == 3:
                                        # BGR - convert to RGB
                                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                    
                                    # Simple normalization to 0-255 range for display (like in thumbnail)
                                    if img.dtype == np.uint16:
                                        # 16-bit image - normalize to 8-bit
                                        img = (img / 256).astype(np.uint8)
                                    elif img.dtype == np.float32 or img.dtype == np.float64:
                                        # 32-bit float - simple clipping and normalization
                                        img = np.clip(img, 0, 1)  # Clip to 0-1 range
                                        img = (img * 255).astype(np.uint8)
                                    
                                    # Resize for preview if too large
                                    max_preview = 1024  # Higher quality for preview vs thumbnail
                                    if width > max_preview or height > max_preview:
                                        scale = min(max_preview / width, max_preview / height)
                                        new_width = int(width * scale)
                                        new_height = int(height * scale)
                                        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                                    
                                    # Convert numpy array to QPixmap
                                    height, width, channels = img.shape
                                    bytes_per_line = width * channels
                                    q_image = QImage(img.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                                    pixmap = QPixmap.fromImage(q_image.copy())
                                    
                                    if not pixmap.isNull():
                                        self.current_pixmap = pixmap
                                        self.add_to_cache(file_path_str, pixmap, resolution_str)
                                        self.fit_pixmap_to_label()
                                    else:
                                        raise Exception("Failed to convert to QPixmap")
                                else:
                                    raise Exception("OpenCV could not load the TIFF image")
                                    
                            except Exception as e:
                                print(f"TIFF OpenCV loading failed: {e}, trying QImageReader fallback...")
                                # Fall back to QImageReader for standard TIFF handling
                                image_reader = QImageReader(file_path_str)
                                original_size = image_reader.size()
                                if original_size.isValid():
                                    resolution_str = f"{original_size.width()} x {original_size.height()}"
                                
                                if original_size.width() > 1024 or original_size.height() > 1024:
                                    if original_size.width() > original_size.height():
                                        scaled_size = QSize(1024, int(1024 * original_size.height() / original_size.width()))
                                    else:
                                        scaled_size = QSize(int(1024 * original_size.width() / original_size.height()), 1024)
                                    image_reader.setScaledSize(scaled_size)
                                
                                image = image_reader.read()
                                if not image.isNull():
                                    pixmap = QPixmap.fromImage(image)
                                    self.current_pixmap = pixmap
                                    self.add_to_cache(file_path_str, pixmap, resolution_str)
                                    self.fit_pixmap_to_label()
                                else:
                                    self.graphics_scene.clear()
                                    self.current_text_item = None
                        else:
                            # Standard 8-bit image formats (PNG, JPG, etc.) - use QImageReader
                            image_reader = QImageReader(file_path_str)
                            
                            # Check original size (for resolution metadata)
                            original_size = image_reader.size()
                            if original_size.isValid():
                                resolution_str = f"{original_size.width()} x {original_size.height()}"
                            
                            # If image is larger than 1024px, scale it down during load
                            if original_size.width() > 1024 or original_size.height() > 1024:
                                if original_size.width() > original_size.height():
                                    scaled_size = QSize(1024, int(1024 * original_size.height() / original_size.width()))
                                else:
                                    scaled_size = QSize(int(1024 * original_size.width() / original_size.height()), 1024)
                                image_reader.setScaledSize(scaled_size)
                            
                            # Read the (scaled) image
                            image = image_reader.read()
                            
                            if not image.isNull():
                                pixmap = QPixmap.fromImage(image)
                                self.current_pixmap = pixmap
                                
                                # Add to cache
                                self.add_to_cache(file_path_str, pixmap, resolution_str)
                                
                                # Fit to current panel size
                                self.fit_pixmap_to_label()
                            else:
                                self.graphics_scene.clear()
                                self.current_text_item = None
                            
                except Exception as e:
                    print(f"Preview load error: {e}")
                    self.graphics_scene.clear()
                    self.current_text_item = None
                    self.add_metadata_row("⚠️", "Error", f"Load error: {str(e)}")
        elif asset.is_pdf_file:
            # PDF file - show preview with page navigation
            self.show_pdf_preview(asset)
        elif self.is_text_file(asset):
            # Text file - show text preview
            self.show_text_preview(asset)
        else:
            # Non-image file - check if it's a text file
            if self.is_text_file(asset):
                self.show_text_preview(asset)
            else:
                # Other non-image, non-text files - show icon/placeholder
                self.graphics_scene.clear()
        
        # Add metadata
        self.add_metadata_row("📄", "Name", asset.name)
        
        # File type with special handling for PDF
        if asset.is_pdf_file:
            file_type = "PDF Document"
        else:
            file_type = asset.extension.upper() + " file"
        self.add_metadata_row("🗂️", "Type", file_type)
        
        self.add_metadata_row("💾", "Size", self.format_file_size(asset.size))
        
        # Image resolution (use cached value if available)
        if asset.is_image_file and resolution_str:
            self.add_metadata_row("📐", "Resolution", resolution_str)
        
        # Modified date
        try:
            mod_time = datetime.fromtimestamp(asset.file_path.stat().st_mtime)
            date_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
            self.add_metadata_row("📅", "Modified", date_str)
        except:
            pass
        
        # Path (shortened)
        path_str = str(asset.file_path)
        if len(path_str) > 50:
            path_str = "..." + path_str[-47:]
        self.add_metadata_row("📂", "Path", path_str)
        
        # Add tags display in metadata (read-only)
        self.add_metadata_tags_display([asset])
        
        # Load tags for this asset (in Tags tab)
        self.load_tags(asset)
        
        # Force tags container to update and show
        if hasattr(self, 'tags_container') and self.tags_container:
            self.tags_container.update()
            self.tags_container.updateGeometry()
            if hasattr(self, 'tags_layout'):
                self.tags_layout.update()
                self.tags_layout.activate()
    
    def add_to_cache(self, file_path, pixmap, resolution):
        """Add preview to cache with LRU eviction"""
        # If cache is full, remove oldest entry
        if len(self.preview_cache) >= self.cache_max_size:
            # Remove first (oldest) item
            first_key = next(iter(self.preview_cache))
            del self.preview_cache[first_key]
        
        # Add new entry
        self.preview_cache[file_path] = (pixmap, resolution)
    
    def show_multiple_files(self, assets):
        """Show preview and summary for multiple files"""
        count = len(assets)
        self.title_label.setText(f"🖼️ {count} files selected")
        self.clear_metadata()
        
        self.current_pixmap = None
        self.current_image_path = None  # Clear for multi-select
        self.exit_zoom_mode()  # Exit zoom mode when multi-selecting
        self.is_showing_text = False  # Reset text mode flag
        
        # Show first file preview ONLY if already in cache (instant!)
        first_asset = assets[0]
        file_path_str = str(first_asset.file_path)
        
        if first_asset.is_image_file and file_path_str in self.preview_cache:
            # Cache hit - show instantly
            pixmap, _ = self.preview_cache[file_path_str]
            self.current_pixmap = pixmap
            self.fit_pixmap_to_label()
        else:
            # No cache - show placeholder (don't load!)
            self.graphics_scene.clear()
            self.current_text_item = None
        
        # First file info
        self.add_metadata_row("📄", "First", first_asset.name)
        self.add_metadata_row("💾", "Size", self.format_file_size(first_asset.size))
        
        # Summary for remaining files
        if count > 1:
            self.metadata_layout.addSpacing(10)
            separator = QLabel("─" * 30)
            separator.setStyleSheet("color: #555;")
            self.metadata_layout.addWidget(separator)
            
            # Quick summary (no file I/O!)
            total_size = sum(a.size for a in assets)  # Size already in memory
            
            self.add_metadata_row("📊", "Total files", str(count))
            self.add_metadata_row("💾", "Total size", self.format_file_size(total_size))
            
            # Count file types (quick, no I/O)
            type_counts = {}
            for asset in assets:
                ext = asset.extension.upper()
                type_counts[ext] = type_counts.get(ext, 0) + 1
            
            types_str = ", ".join([f"{count} {ext}" for ext, count in sorted(type_counts.items())])
            self.add_metadata_row("🗂️", "Types", types_str)
        
        # Add tags display in metadata (read-only)
        self.add_metadata_tags_display(assets)
        
        # Load common tags (tags that ALL selected files share) in Tags tab
        self.load_common_tags(assets)
        
        # Force tags container to update and show
        if hasattr(self, 'tags_container') and self.tags_container:
            self.tags_container.update()
            self.tags_container.updateGeometry()
            if hasattr(self, 'tags_layout'):
                self.tags_layout.update()
                self.tags_layout.activate()
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def is_text_file(self, asset):
        """Check if file is a text file"""
        text_extensions = [
            '.txt', '.log', '.md', '.json', '.xml', '.yaml', '.yml',
            '.py', '.mel', '.js', '.html', '.css', '.sh', '.bat',
            '.ini', '.cfg', '.conf', '.csv', '.tsv'
        ]
        return asset.extension.lower() in text_extensions
    
    def show_text_preview(self, asset):
        """Show text file preview in graphics view"""
        try:
            # Show text controls, hide exposure controls
            self.text_controls.show()
            self.exposure_controls.hide()
            
            # Set text mode flag
            self.is_showing_text = True
            
            # Reset load full state for NEW file (different asset)
            if not hasattr(self, 'current_text_asset') or self.current_text_asset != asset:
                self.is_full_text_loaded = False
                if hasattr(self, 'load_full_btn'):
                    self.load_full_btn.setChecked(False)
                    self.load_full_btn.setText("📄 Load Full")
            
            # Store current asset for reload
            self.current_text_asset = asset
            
            # Clear scene and reset text item reference
            self.graphics_scene.clear()
            self.current_text_item = None
            
            # Read file content (with encoding detection)
            file_path_str = str(asset.file_path)
            
            # Determine read limit based on load_full mode
            if self.is_full_text_loaded:
                read_limit = None  # Read entire file
                line_limit = None  # Show all lines
            else:
                read_limit = 50000  # Read first 50KB
                line_limit = 500    # Show first 500 lines
            
            # Try UTF-8 first, fallback to latin-1
            try:
                with open(file_path_str, 'r', encoding='utf-8') as f:
                    if read_limit:
                        content = f.read(read_limit)
                    else:
                        content = f.read()
            except UnicodeDecodeError:
                with open(file_path_str, 'r', encoding='latin-1') as f:
                    if read_limit:
                        content = f.read(read_limit)
                    else:
                        content = f.read()
            
            # Store full content for clipboard
            self.current_text_content = content
            
            # Limit preview lines if needed
            lines = content.split('\n')
            total_lines = len(lines)
            
            if line_limit is not None and total_lines > line_limit:
                # Partial mode: show only first N lines
                lines = lines[:line_limit]
                lines.append(f'\n... (showing first {line_limit} lines of {total_lines}, click "Load Full" to see all) ...')
            
            preview_text = '\n'.join(lines)
            
            # Create text item with monospace font
            text_item = self.graphics_scene.addText(preview_text)
            self.current_text_item = text_item
            
            # Make text selectable and copyable
            text_item.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            
            # Apply font settings
            font = QFont("Consolas", self.font_size_slider.value())
            if not font.exactMatch():
                font = QFont("Courier New", self.font_size_slider.value())
            text_item.setFont(font)
            text_item.setDefaultTextColor(QColor(220, 220, 220))  # Light gray text
            
            # Apply line wrap setting - ALWAYS set text width to viewport
            viewport_width = self.graphics_view.viewport().width() - 20
            if self.line_wrap_checkbox.isChecked():
                text_item.setTextWidth(viewport_width)
            else:
                text_item.setTextWidth(-1)  # No wrap
            
            # Force Qt to process layout updates to ensure text is fully rendered
            QApplication.processEvents()
            
            # Force document layout to recalculate (critical for accurate bounding rect!)
            doc_layout = text_item.document().documentLayout()
            doc_layout.documentSizeChanged.emit(text_item.document().size())
            
            # Process events again after layout update
            QApplication.processEvents()
            
            # NOW get the bounding rect (should be accurate)
            text_rect = text_item.boundingRect()
            
            # Set scene rect to text bounds with extra padding at bottom
            # Add padding: 10px on sides, 100px at bottom to ensure last lines visible
            padded_rect = text_rect.adjusted(-10, -10, 10, 100)
            self.graphics_scene.setSceneRect(padded_rect)
            
            # Don't use fitInView - just reset view to show top-left
            self.graphics_view.resetTransform()
            self.graphics_view.ensureVisible(0, 0, 10, 10)
            
            # Set cursor to I-beam (text selection cursor)
            self.graphics_view.viewport().setCursor(Qt.IBeamCursor)
            
        except Exception as e:
            print(f"Text preview error: {e}")
            self.graphics_scene.clear()
            self.current_text_content = None
            self.current_text_item = None
            error_text = f"Error loading text preview:\n{str(e)}"
            text_item = self.graphics_scene.addText(error_text)
            text_item.setDefaultTextColor(QColor(255, 100, 100))  # Red for errors
    
    def on_line_wrap_changed(self, checked):
        """Handle line wrap toggle"""
        if self.current_text_item:
            try:
                viewport_width = self.graphics_view.viewport().width() - 20
                if checked:
                    # Enable wrap
                    self.current_text_item.setTextWidth(viewport_width)
                else:
                    # Disable wrap
                    self.current_text_item.setTextWidth(-1)
                
                # Force layout update
                QApplication.processEvents()
                doc_layout = self.current_text_item.document().documentLayout()
                doc_layout.documentSizeChanged.emit(self.current_text_item.document().size())
                QApplication.processEvents()
                
                # Update scene rect with padding
                text_rect = self.current_text_item.boundingRect()
                padded_rect = text_rect.adjusted(-10, -10, 10, 100)
                self.graphics_scene.setSceneRect(padded_rect)
                
                # Reset view to top
                self.graphics_view.resetTransform()
                self.graphics_view.ensureVisible(0, 0, 10, 10)
            except RuntimeError:
                # Object was already deleted, reset reference
                self.current_text_item = None
    
    def on_font_size_changed(self, value):
        """Handle font size change"""
        self.font_size_label.setText(str(value))
        
        if self.current_text_item:
            try:
                # Store scroll position
                scroll_y = self.graphics_view.verticalScrollBar().value()
                
                # Update font size
                font = QFont("Consolas", value)
                if not font.exactMatch():
                    font = QFont("Courier New", value)
                self.current_text_item.setFont(font)
                
                # Re-apply text width if wrap is enabled
                if self.line_wrap_checkbox.isChecked():
                    viewport_width = self.graphics_view.viewport().width() - 20
                    self.current_text_item.setTextWidth(viewport_width)
                
                # Force layout update
                QApplication.processEvents()
                doc_layout = self.current_text_item.document().documentLayout()
                doc_layout.documentSizeChanged.emit(self.current_text_item.document().size())
                QApplication.processEvents()
                
                # Update scene rect with padding
                text_rect = self.current_text_item.boundingRect()
                padded_rect = text_rect.adjusted(-10, -10, 10, 100)
                self.graphics_scene.setSceneRect(padded_rect)
            except RuntimeError:
                # Object was already deleted, reset reference
                self.current_text_item = None
                return
            
            # Restore scroll position
            self.graphics_view.verticalScrollBar().setValue(scroll_y)
    
    def copy_text_to_clipboard(self):
        """Copy text content to clipboard"""
        if self.current_text_content:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_text_content)
            
            # Show confirmation in button
            original_text = self.copy_text_btn.text()
            self.copy_text_btn.setText("✓ Copied!")
            QtCore.QTimer.singleShot(1500, lambda: self.copy_text_btn.setText(original_text))
    
    def pdf_previous_page(self):
        """Navigate to previous PDF page"""
        if self.current_pdf_page > 0:
            self.current_pdf_page -= 1
            self.reload_pdf_page()
    
    def pdf_next_page(self):
        """Navigate to next PDF page"""
        if self.current_pdf_page < self.current_pdf_page_count - 1:
            self.current_pdf_page += 1
            self.reload_pdf_page()
    
    def reload_pdf_page(self):
        """Reload current PDF page after navigation"""
        if not self.current_pdf_path:
            return
        
        # Use high resolution if in zoom mode, otherwise preview size
        target_size = 4096 if self.zoom_mode else self.max_preview_size
        
        # Load page at appropriate resolution
        pixmap, page_count, resolution = load_pdf_page(
            self.current_pdf_path, 
            self.current_pdf_page, 
            target_size
        )
        
        if pixmap:
            self.current_pixmap = pixmap
            self.set_preview_pixmap(pixmap)
            
            if self.zoom_mode:
                # In zoom mode, show full resolution at 100%
                self.graphics_scene.setSceneRect(pixmap.rect())
            else:
                # In preview mode, fit to view
                self.fit_preview_to_view()
            
            # Update overlay page indicator
            self.pdf_page_overlay.setText(f"{self.current_pdf_page + 1} / {page_count}")
            
            # Enable/disable overlay buttons
            self.pdf_prev_overlay.setEnabled(self.current_pdf_page > 0)
            self.pdf_next_overlay.setEnabled(self.current_pdf_page < page_count - 1)
            
            # Reposition overlays after content change
            self.update_pdf_overlay_positions()
        else:
            # Check if PDF is password protected
            if page_count == -1 and resolution == "encrypted":
                self.show_placeholder_with_text(f"🔒 Password Protected PDF\n\nPage {self.current_pdf_page + 1}")
            else:
                # Show error if page failed to load
                self.show_placeholder_with_text(f"Failed to load PDF page {self.current_pdf_page + 1}")
            
            self.pdf_prev_overlay.hide()
            self.pdf_next_overlay.hide()
            self.pdf_page_overlay.hide()
    
    def show_pdf_preview(self, asset):
        """Show PDF file preview with floating overlay navigation"""
        self.is_showing_pdf = True
        self.is_showing_text = False
        self.text_controls.hide()
        
        # Load first page
        self.current_pdf_path = asset.file_path
        self.current_pdf_page = 0
        
        pixmap, page_count, resolution = load_pdf_page(
            asset.file_path, 
            0, 
            self.max_preview_size
        )
        
        if pixmap:
            self.current_pdf_page_count = page_count
            self.current_pixmap = pixmap
            self.current_image_path = asset.file_path  # Enable zoom for PDF
            self.set_preview_pixmap(pixmap)
            self.fit_preview_to_view()
            
            # Show and update PDF overlay controls
            self.pdf_page_overlay.setText(f"1 / {page_count}")
            self.pdf_prev_overlay.setEnabled(False)
            self.pdf_next_overlay.setEnabled(page_count > 1)
            
            # Show overlays
            self.pdf_prev_overlay.show()
            self.pdf_next_overlay.show()
            self.pdf_page_overlay.show()
            
            # Position overlays
            self.update_pdf_overlay_positions()
            
            # Don't steal focus from file_list - Quick View needs Space key to work
            # (Previously set focus here for PDF keyboard navigation, but that's now disabled)
            
            # Update title
            self.title_label.setText(f"Preview: {asset.name}")
        else:
            # Check if PDF is password protected
            if page_count == -1 and resolution == "encrypted":
                self.show_placeholder_with_text(f"🔒 Password Protected PDF\n\n{asset.name}")
            else:
                # Show error placeholder for other errors
                self.show_placeholder_with_text(f"Failed to load PDF:\n{asset.name}")
            
            self.pdf_prev_overlay.hide()
            self.pdf_next_overlay.hide()
            self.pdf_page_overlay.hide()
    
    def toggle_load_full_file(self):
        """Toggle between partial and full file loading"""
        if not self.current_text_asset:
            return
        
        # Toggle the flag
        self.is_full_text_loaded = self.load_full_btn.isChecked()
        
        # Update button text
        if self.is_full_text_loaded:
            self.load_full_btn.setText("📄 Partial")
            self.load_full_btn.setToolTip("Click to show preview only (faster)")
        else:
            self.load_full_btn.setText("📄 Load Full")
            self.load_full_btn.setToolTip("Load full file content (may be slow for large files)")
        
        # Reload the text preview with new mode
        self.show_text_preview(self.current_text_asset)
    
    def _is_high_bit_tiff(self, file_path):
        """
        Check if TIFF file is 16-bit or 32-bit (needs HDR treatment)
        
        Args:
            file_path: Path to TIFF file
            
        Returns:
            bool: True if 16/32-bit TIFF, False otherwise
        """
        file_ext = file_path.lower()
        if not (file_ext.endswith('.tif') or file_ext.endswith('.tiff')):
            return False
        
        # Try to detect bit depth using OpenCV if available
        if OPENCV_AVAILABLE:
            try:
                import cv2
                import numpy as np
                # Just read image info without loading full data
                img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH)
                if img is not None:
                    # Check data type - 16-bit or 32-bit float indicates HDR TIFF
                    is_hdr = img.dtype in [np.uint16, np.float32, np.float64]
                    return is_hdr
            except Exception as e:
                pass
                pass
        
        # Fallback: Use QImageReader to check format
        try:
            reader = QImageReader(file_path)
            if reader.canRead():
                # Read just one pixel to check format
                reader.setScaledSize(QSize(1, 1))  # Minimal read
                image = reader.read()
                if not image.isNull():
                    # If depth is more than 8 bits per channel, treat as HDR
                    return image.depth() > 24  # 24 = 8 bits * 3 channels (RGB)
        except:
            pass
        
        return False
    
    def _load_tiff_as_hdr_raw(self, file_path):
        """
        Load TIFF as raw HDR float data for exposure control
        
        Args:
            file_path: Path to TIFF file
            
        Returns:
            tuple: (rgb_float_array, width, height, resolution_str) or (None, None, None, None)
        """
        if not OPENCV_AVAILABLE or not NUMPY_AVAILABLE:
            return None, None, None, None
        
        try:
            import cv2
            import numpy as np
            
            # Read image with OpenCV (preserving original bit depth)
            img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
            
            if img is None:
                return None, None, None, None
            
            # Get dimensions
            if len(img.shape) == 2:
                height, width = img.shape
                channels = 1
            else:
                height, width, channels = img.shape
            
            resolution_str = f"{width} x {height}"
            
            # Convert to RGB if needed
            if len(img.shape) == 2:
                # Grayscale - convert to RGB
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                # RGBA - convert to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            elif img.shape[2] == 3:
                # BGR - convert to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Convert to float32 for HDR processing
            if img.dtype == np.uint8:
                # 8-bit - normalize to 0-1 range
                img_float = img.astype(np.float32) / 255.0
            elif img.dtype == np.uint16:
                # 16-bit - normalize to 0-1 range
                img_float = img.astype(np.float32) / 65535.0
            elif img.dtype in [np.float32, np.float64]:
                # 32-bit float - intelligent normalization for TIFF HDR data
                img_float = img.astype(np.float32)
                
                # Get image statistics for better normalization
                min_val = img_float.min()
                max_val = img_float.max()
                mean_val = img_float.mean()
                
                # Different normalization strategies based on data range
                if max_val <= 1.0 and min_val >= 0.0:
                    # Already in 0-1 range - use as is
                    pass
                elif max_val > 100.0:
                    # Very high values - use percentile-based normalization to preserve details
                    percentile_99 = np.percentile(img_float, 99)
                    percentile_95 = np.percentile(img_float, 95)
                    percentile_90 = np.percentile(img_float, 90)
                    
                    # Use 90th percentile for normalization to preserve most of the image
                    # but allow highlights to be clipped for better overall exposure
                    if percentile_90 > 0.1:  # Avoid division by very small numbers
                        normalization_value = percentile_90 * 2.0  # Give some headroom
                        img_float = img_float / normalization_value
                        img_float = np.clip(img_float, 0, 10.0)  # Allow significant headroom for exposure
                    else:
                        # Fallback to 99th percentile if 90th is too small
                        img_float = img_float / percentile_99
                        img_float = np.clip(img_float, 0, 5.0)
                elif max_val > 10.0:
                    # Moderate values - apply intelligent scaling
                    # Use 95th percentile to avoid outliers
                    percentile_95 = np.percentile(img_float, 95)
                    if percentile_95 > 1.0:
                        img_float = img_float / percentile_95
                        img_float = np.clip(img_float, 0, 2.0)  # Allow some headroom for exposure
                elif min_val < 0.0:
                    # Has negative values - shift and normalize
                    img_float = img_float - min_val  # Shift to start at 0
                    img_float = img_float / img_float.max()  # Normalize to 0-1
                else:
                    # Values between 1-10 - might be in linear space, use moderate normalization
                    img_float = img_float / max(max_val, 2.0)
            else:
                # Unknown format
                return None, None, None, None
            
            # Resize if too large (for performance)
            max_size = self.max_preview_size if hasattr(self, 'max_preview_size') else 1024
            if width > max_size or height > max_size:
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img_float = cv2.resize(img_float, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                width, height = new_width, new_height
                resolution_str = f"{width} x {height} (scaled)"
            
            return img_float, width, height, resolution_str
            
        except Exception as e:
            print(f"TIFF HDR raw loading failed: {e}")
            return None, None, None, None
    
    def _load_tiff_fallback(self, file_path):
        """
        Fallback TIFF loading using the original OpenCV method
        
        Args:
            file_path: Path to TIFF file
            
        Returns:
            QPixmap or None
        """
        if not OPENCV_AVAILABLE or not NUMPY_AVAILABLE:
            return None
        
        try:
            import cv2
            import numpy as np
            
            # Read image with OpenCV
            img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
            
            if img is None:
                return None
            
            # Convert to RGB if needed
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            elif img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Normalize to 0-255 range
            if img.dtype == np.uint16:
                img = (img / 256).astype(np.uint8)
            elif img.dtype == np.float32 or img.dtype == np.float64:
                img = np.clip(img, 0, 1)
                img = (img * 255).astype(np.uint8)
            
            # Convert to QPixmap
            height, width, channels = img.shape
            bytes_per_line = width * channels
            q_image = QImage(img.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image.copy())
            
            return pixmap if not pixmap.isNull() else None
            
        except Exception as e:
            print(f"TIFF fallback loading failed: {e}")
            return None
    
    # Tag Management Methods
    
    def setup_tag_autocomplete(self):
        """Setup autocomplete for tag input"""
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            # Get all tag names
            all_tags = mm.get_all_tags()
            tag_names = [tag['name'] for tag in all_tags]
            
            # Create completer
            completer = QCompleter(tag_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            
            # Apply to input
            self.tag_input.setCompleter(completer)
            
            print(f"Autocomplete loaded with {len(tag_names)} tags")
        except Exception as e:
            print(f"Error setting up tag autocomplete: {e}")
    
    def show_browse_tags_dialog(self):
        """Show dialog with all available tags grouped by category"""
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            # Get tags grouped by category
            tags_by_category = mm.get_tags_by_category()
            
            if not tags_by_category:
                QtWidgets.QMessageBox.information(
                    self, 
                    "No Tags", 
                    "No tags are available yet. Tags will be created automatically when you add them."
                )
                return
            
            # Create dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Browse Available Tags")
            dialog.setMinimumWidth(700)
            dialog.setMinimumHeight(550)
            dialog.setModal(False)  # Non-modal - can interact with main window
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: #2a2a2a;
                }}
                QLabel {{
                    color: #ffffff;
                    font-family: {UI_FONT};
                }}
                QCheckBox {{
                    color: #ffffff;
                    font-family: {UI_FONT};
                    font-size: 11px;
                    spacing: 5px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid #555;
                    border-radius: 3px;
                    background-color: #3a3a3a;
                }}
                QCheckBox::indicator:checked {{
                    background-color: #4b7daa;
                    border-color: #5a8db8;
                }}
                QGroupBox {{
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                    font-family: {UI_FONT};
                    font-size: 12px;
                    font-weight: bold;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    color: #4b7daa;
                }}
                QPushButton {{
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 8px 16px;
                    color: #ffffff;
                    font-family: {UI_FONT};
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: #4a4a4a;
                    border-color: #666;
                }}
                QPushButton:pressed {{
                    background-color: #2a2a2a;
                }}
                QPushButton#addButton {{
                    background-color: #4b7daa;
                    border-color: #5a8db8;
                }}
                QPushButton#addButton:hover {{
                    background-color: #5a8db8;
                }}
                QPushButton#addButton:pressed {{
                    background-color: #3a6d9a;
                }}
            """)
            
            # Main layout
            main_layout = QVBoxLayout(dialog)
            
            # Info label (will update dynamically)
            info_label = QLabel()
            def update_info_label():
                count = len(self.current_assets) if self.current_assets else 0
                if count == 0:
                    info_label.setText("No files selected. Select file(s) to add tags.")
                elif count == 1:
                    info_label.setText(f"Select tags to add to: {self.current_assets[0].name}")
                else:
                    info_label.setText(f"Select tags to add to {count} selected file(s)")
            
            update_info_label()
            info_label.setStyleSheet(f"font-size: 12px; padding: 5px; color: #cccccc; font-family: {UI_FONT};")
            main_layout.addWidget(info_label)
            
            # Store update function for later use
            dialog.update_info_label = update_info_label
            
            # Search/filter input
            search_input = QtWidgets.QLineEdit()
            search_input.setPlaceholderText("🔍 Search tags...")
            search_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 6px;
                    color: #ffffff;
                    font-family: {UI_FONT};
                    font-size: 11px;
                }}
                QLineEdit:focus {{
                    border-color: #4b7daa;
                }}
            """)
            main_layout.addWidget(search_input)
            
            # Edit Mode toggle button
            edit_mode_layout = QHBoxLayout()
            edit_mode_layout.addStretch()
            
            edit_mode_btn = QPushButton("📝 Edit Mode")
            edit_mode_btn.setCheckable(True)
            edit_mode_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 6px 12px;
                    color: #cccccc;
                    font-family: {UI_FONT};
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: #4a4a4a;
                    border-color: #666;
                }}
                QPushButton:checked {{
                    background-color: #4b7daa;
                    border-color: #5a8db8;
                    color: white;
                    font-weight: bold;
                }}
                QPushButton:checked:hover {{
                    background-color: #5a8db8;
                }}
            """)
            edit_mode_layout.addWidget(edit_mode_btn)
            main_layout.addLayout(edit_mode_layout)
            
            # Store edit mode button reference on dialog
            dialog._edit_mode_btn = edit_mode_btn
            
            # Scroll area for categories
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(8)
            scroll_layout.setContentsMargins(8, 8, 8, 8)
            
            # Store tag chip buttons and category widgets for filtering
            tag_buttons = {}
            category_widgets = {}  # {category_name: {'label': QLabel, 'container': QWidget, 'separator': QLabel}}
            
            # Create collapsible group for each category
            for category in sorted(tags_by_category.keys()):
                tags = tags_by_category[category]
                
                # Category header
                category_label = QLabel(f"▼ {category}")
                category_label.setStyleSheet(f"""
                    font-size: 11px;
                    font-weight: bold;
                    color: #cccccc;
                    padding: 3px 0px 2px 0px;
                    font-family: {UI_FONT};
                """)
                scroll_layout.addWidget(category_label)
                
                # Container for tag chips with flow layout
                chips_container = QWidget()
                chips_layout = FlowLayout()
                chips_layout.setSpacing(5)
                chips_layout.setContentsMargins(0, 3, 0, 3)
                
                # Get current file tags for visualization
                current_file_tags = {}  # {tag_id: count}
                if self.current_assets:
                    for asset in self.current_assets:
                        file_path = str(asset.file_path)
                        file_meta = mm.get_file_metadata(file_path)
                        if file_meta and file_meta.get('tags'):
                            for tag_dict in file_meta['tags']:
                                tag_id = tag_dict['id']
                                current_file_tags[tag_id] = current_file_tags.get(tag_id, 0) + 1
                
                total_files = len(self.current_assets) if self.current_assets else 0
                
                # Create chip-style toggle button for each tag
                for tag in sorted(tags, key=lambda x: x['name']):
                    tag_id = tag['id']
                    tag_name = tag['name']
                    
                    # Check if this tag exists on selected files
                    tag_count = current_file_tags.get(tag_id, 0)
                    
                    # Determine button text and styling
                    if tag_count == 0:
                        # No files have this tag - normal (no X button)
                        btn_text = tag_name
                        bg_color = "#4a4a4a"
                        text_color = "white"
                        has_remove_btn = False
                    elif tag_count == total_files:
                        # ALL files have this tag - green tint (with X button)
                        btn_text = f"✓ {tag_name}"
                        bg_color = "#2a5a2a"  # Dark green
                        text_color = "#90EE90"  # Light green
                        has_remove_btn = True
                    else:
                        # SOME files have this tag - show count (with X button)
                        btn_text = f"{tag_name} ({tag_count}/{total_files})"
                        bg_color = "#4a4a2a"  # Yellowish tint
                        text_color = "#FFD700"  # Gold
                        has_remove_btn = True
                    
                    # Create container widget for button + remove button
                    chip_widget = QWidget()
                    chip_layout = QHBoxLayout(chip_widget)
                    chip_layout.setContentsMargins(0, 0, 0, 0)
                    chip_layout.setSpacing(0)
                    
                    chip_btn = QtWidgets.QPushButton(btn_text)
                    chip_btn.setCheckable(True)
                    chip_btn.setProperty('tag_data', tag)
                    chip_btn.setProperty('tag_count', tag_count)
                    chip_btn.setProperty('total_files', total_files)
                    chip_btn.setFixedHeight(26)
                    chip_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {bg_color};
                            border: 1px solid #555;
                            border-radius: 3px;
                            padding: 4px 10px;
                            color: {text_color};
                            font-family: {UI_FONT};
                            font-size: 11px;
                            text-align: left;
                        }}
                        QPushButton:hover {{
                            background-color: #5a5a5a;
                            border-color: #666;
                        }}
                        QPushButton:checked {{
                            background-color: #4b7daa;
                            border-color: #5a8db8;
                            color: #ffffff;
                            font-weight: bold;
                        }}
                        QPushButton:checked:hover {{
                            background-color: #5a8db8;
                        }}
                    """)
                    
                    chip_layout.addWidget(chip_btn)
                    
                    # Always create remove button, but hide if not needed
                    remove_btn = QtWidgets.QPushButton("×")
                    remove_btn.setFixedSize(20, 26)
                    remove_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {bg_color};
                            border: 1px solid #555;
                            border-left: none;
                            border-radius: 0px 3px 3px 0px;
                            color: {text_color};
                            font-family: {UI_FONT};
                            font-size: 14px;
                            font-weight: bold;
                            padding: 0px;
                        }}
                        QPushButton:hover {{
                            background-color: #8B0000;
                            color: white;
                        }}
                        QPushButton:pressed {{
                            background-color: #6B0000;
                        }}
                    """)
                    remove_btn.clicked.connect(
                        lambda checked=False, td=tag, dlg=dialog, btns=tag_buttons: self._remove_tag_from_selection(td, dlg, btns)
                    )
                    remove_btn.setToolTip(f"Remove '{tag_name}' from selection")
                    chip_layout.addWidget(remove_btn)
                    
                    # Show/hide based on tag count
                    if has_remove_btn:
                        remove_btn.show()
                        # Adjust main button border radius (no right radius)
                        chip_btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {bg_color};
                                border: 1px solid #555;
                                border-radius: 3px 0px 0px 3px;
                                padding: 4px 10px;
                                color: {text_color};
                                font-family: {UI_FONT};
                                font-size: 11px;
                                text-align: left;
                            }}
                            QPushButton:hover {{
                                background-color: #5a5a5a;
                                border-color: #666;
                            }}
                            QPushButton:checked {{
                                background-color: #4b7daa;
                                border-color: #5a8db8;
                                color: #ffffff;
                                font-weight: bold;
                            }}
                            QPushButton:checked:hover {{
                                background-color: #5a8db8;
                            }}
                        """)
                    else:
                        remove_btn.hide()
                    
                    # Store reference to main button
                    chip_widget._main_button = chip_btn
                    chip_widget._tag_data = tag
                    
                    tag_buttons[tag['id']] = chip_widget
                    chips_layout.addWidget(chip_widget)
                
                chips_container.setLayout(chips_layout)
                scroll_layout.addWidget(chips_container)
                
                # Add thin separator line
                separator = QLabel()
                separator.setFixedHeight(1)
                separator.setStyleSheet("background-color: #3a3a3a; margin: 2px 0px;")
                scroll_layout.addWidget(separator)
                
                # Store category widgets for filtering
                category_widgets[category] = {
                    'label': category_label,
                    'container': chips_container,
                    'separator': separator
                }
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            main_layout.addWidget(scroll)
            
            # Connect search input to filter function
            def filter_tags():
                search_text = search_input.text().strip().lower()
                
                for category, widgets in category_widgets.items():
                    category_label = widgets['label']
                    chips_container = widgets['container']
                    separator = widgets['separator']
                    
                    # Get all tag buttons in this category
                    visible_count = 0
                    chips_layout = chips_container.layout()
                    
                    for i in range(chips_layout.count()):
                        item = chips_layout.itemAt(i)
                        if item and item.widget():
                            chip_widget = item.widget()
                            
                            # Get main button from chip widget
                            if hasattr(chip_widget, '_main_button'):
                                tag_btn = chip_widget._main_button
                                tag_name = tag_btn.text().lower()
                                
                                # Show/hide based on search
                                if not search_text or search_text in tag_name:
                                    chip_widget.show()
                                    visible_count += 1
                                else:
                                    chip_widget.hide()
                    
                    # Show/hide category if no tags match
                    if visible_count > 0:
                        category_label.show()
                        chips_container.show()
                        separator.show()
                    else:
                        category_label.hide()
                        chips_container.hide()
                        separator.hide()
            
            # Note: search filter connected later after dialog setup
            
            # Button layout
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # Select All / Deselect All buttons
            select_all_btn = QPushButton("Select All")
            select_all_btn.clicked.connect(lambda: self._toggle_all_tag_buttons(tag_buttons, True))
            button_layout.addWidget(select_all_btn)
            
            deselect_all_btn = QPushButton("Deselect All")
            deselect_all_btn.clicked.connect(lambda: self._toggle_all_tag_buttons(tag_buttons, False))
            button_layout.addWidget(deselect_all_btn)
            
            button_layout.addStretch()
            
            # Clear All Tags button
            clear_all_btn = QPushButton("🗑️ Clear All Tags")
            clear_all_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 8px 16px;
                    color: #cccccc;
                    font-family: {UI_FONT};
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: #8B0000;
                    border-color: #A00000;
                    color: white;
                }}
                QPushButton:pressed {{
                    background-color: #6B0000;
                }}
            """)
            clear_all_btn.clicked.connect(self.clear_all_tags_from_selection)
            clear_all_btn.setToolTip("Remove all tags from selected file(s)")
            button_layout.addWidget(clear_all_btn)
            
            button_layout.addStretch()
            
            # Add Selected button
            add_btn = QPushButton("Add Selected Tags")
            add_btn.setObjectName("addButton")
            add_btn.clicked.connect(lambda: self._add_selected_tags(dialog, tag_buttons))
            button_layout.addWidget(add_btn)
            
            # Cancel button
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            main_layout.addLayout(button_layout)
            
            # Store dialog and buttons for later refresh
            dialog._tag_buttons = tag_buttons
            dialog._mm = mm
            dialog._edit_mode = False
            dialog._category_widgets = category_widgets
            dialog._add_btn = add_btn
            dialog._clear_all_btn = clear_all_btn
            dialog._info_label = info_label
            dialog._search_input = search_input
            
            # Connect search filter
            search_input.textChanged.connect(lambda: self._filter_browse_tags(dialog))
            
            # Connect edit mode toggle
            def toggle_edit_mode(checked):
                dialog._edit_mode = checked
                if checked:
                    edit_mode_btn.setText("✅ Edit Mode")
                    # Hide add/clear buttons in edit mode
                    add_btn.hide()
                    clear_all_btn.hide()
                    # Update info label
                    info_label.setText("📝 Edit Mode: Manage categories and tags")
                    # Switch to edit view
                    self._switch_to_edit_mode(dialog, tag_buttons, category_widgets, scroll_layout, mm)
                else:
                    edit_mode_btn.setText("📝 Edit Mode")
                    # Show add/clear buttons
                    add_btn.show()
                    clear_all_btn.show()
                    # Restore info label
                    update_info_label()
                    # Switch back to normal view
                    self._switch_to_normal_mode(dialog, tag_buttons, category_widgets)
            
            edit_mode_btn.toggled.connect(toggle_edit_mode)
            
            # Store active browse dialog reference in main window
            self._active_browse_dialog = dialog
            
            # Clear reference when dialog is destroyed
            dialog.destroyed.connect(lambda: setattr(self, '_active_browse_dialog', None))
            
            # Show dialog (modeless - non-blocking)
            dialog.show()
            
        except Exception as e:
            print(f"Error showing browse tags dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def _toggle_all_tag_buttons(self, tag_buttons, checked):
        """Toggle all tag chip buttons in the browse tags dialog"""
        for chip_widget in tag_buttons.values():
            if hasattr(chip_widget, '_main_button'):
                chip_widget._main_button.setChecked(checked)
    
    def _filter_browse_tags(self, dialog):
        """Filter tags in browse dialog based on search input"""
        if not hasattr(dialog, '_search_input') or not hasattr(dialog, '_category_widgets'):
            return
        
        search_text = dialog._search_input.text().strip().lower()
        category_widgets = dialog._category_widgets
        
        # Check if we're in edit mode
        is_edit_mode = hasattr(dialog, '_edit_mode_btn') and dialog._edit_mode_btn.isChecked()
        
        for category, widgets in category_widgets.items():
            category_label = widgets['label']
            chips_container = widgets['container']
            separator = widgets['separator']
            
            # In edit mode, use edit_label and tag_list instead
            if is_edit_mode:
                category_display = widgets.get('edit_label', category_label)
                tags_display = widgets.get('tag_list', chips_container)
            else:
                category_display = category_label
                tags_display = chips_container
            
            # Get all tag buttons in this category
            visible_count = 0
            
            if is_edit_mode and 'tag_list' in widgets:
                # In edit mode, check tag_list items
                tag_list = widgets['tag_list']
                tag_list_layout = tag_list.layout()
                
                if tag_list_layout:
                    for i in range(tag_list_layout.count()):
                        item = tag_list_layout.itemAt(i)
                        if item and item.widget():
                            tag_row = item.widget()
                            # Get tag name from the row (first label in the layout)
                            if hasattr(tag_row, 'layout') and tag_row.layout():
                                row_layout = tag_row.layout()
                                if row_layout.count() > 0:
                                    first_item = row_layout.itemAt(0)
                                    if first_item and isinstance(first_item.widget(), QLabel):
                                        tag_label = first_item.widget()
                                        # Remove bullet point "• " from tag name
                                        tag_text = tag_label.text()
                                        tag_name = tag_text.replace("• ", "").lower()
                                        
                                        if not search_text or search_text in tag_name:
                                            tag_row.show()
                                            visible_count += 1
                                        else:
                                            tag_row.hide()
            else:
                # Normal mode - check chip widgets
                chips_layout = chips_container.layout()
                
                if chips_layout is None:
                    continue
                
                for i in range(chips_layout.count()):
                    item = chips_layout.itemAt(i)
                    if item and item.widget():
                        chip_widget = item.widget()
                        
                        # Get main button from chip widget
                        if hasattr(chip_widget, '_main_button'):
                            tag_btn = chip_widget._main_button
                            tag_name = tag_btn.text().lower()
                            
                            # Show/hide based on search
                            if not search_text or search_text in tag_name:
                                chip_widget.show()
                                visible_count += 1
                            else:
                                chip_widget.hide()
            
            # Show/hide category if no tags match
            if visible_count > 0:
                category_display.show()
                tags_display.show()
                separator.show()
            else:
                category_display.hide()
                tags_display.hide()
                separator.hide()
    
    def _switch_to_edit_mode(self, dialog, tag_buttons, category_widgets, scroll_layout, mm):
        """Switch Browse Tags dialog to edit mode"""
        # Hide tag chip buttons (normal mode)
        for chip_widget in tag_buttons.values():
            chip_widget.hide()
        
        # Show edit widgets for each category
        for category_name, widgets in category_widgets.items():
            label = widgets['label']
            container = widgets['container']
            
            # Remove existing edit widgets if they exist
            if 'edit_label' in widgets and widgets['edit_label']:
                old_edit_label = widgets['edit_label']
                old_edit_label.setParent(None)
                old_edit_label.deleteLater()
                widgets['edit_label'] = None
            
            if 'tag_list' in widgets and widgets['tag_list']:
                old_tag_list = widgets['tag_list']
                old_tag_list.setParent(None)
                old_tag_list.deleteLater()
                widgets['tag_list'] = None
            
            # Update category label with edit buttons
            edit_label = QWidget()
            edit_layout = QHBoxLayout(edit_label)
            edit_layout.setContentsMargins(0, 0, 0, 0)
            edit_layout.setSpacing(8)
            
            cat_text = QLabel(f"▼ {category_name}")
            cat_text.setStyleSheet(f"font-size: 11px; font-weight: bold; color: #cccccc; font-family: {UI_FONT};")
            edit_layout.addWidget(cat_text)
            
            # Edit category button
            edit_cat_btn = QPushButton("Rename")
            edit_cat_btn.setFixedHeight(24)
            edit_cat_btn.setMinimumWidth(60)
            edit_cat_btn.setToolTip("Rename category")
            edit_cat_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    color: #cccccc;
                    font-size: 10px;
                    font-family: {UI_FONT};
                    padding: 2px 10px;
                }}
                QPushButton:hover {{
                    background-color: #4b7daa;
                    color: white;
                }}
            """)
            edit_cat_btn.clicked.connect(lambda checked=False, cat=category_name: self._edit_category_name(dialog, cat, mm))
            edit_layout.addWidget(edit_cat_btn)
            
            # Delete category button
            del_cat_btn = QPushButton("Delete")
            del_cat_btn.setFixedHeight(24)
            del_cat_btn.setMinimumWidth(60)
            del_cat_btn.setToolTip("Delete category")
            del_cat_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    color: #cccccc;
                    font-size: 10px;
                    font-family: {UI_FONT};
                    padding: 2px 10px;
                }}
                QPushButton:hover {{
                    background-color: #8B0000;
                    color: white;
                }}
            """)
            del_cat_btn.clicked.connect(lambda checked=False, cat=category_name: self._delete_category(dialog, cat, mm))
            edit_layout.addWidget(del_cat_btn)
            
            edit_layout.addStretch()
            
            # Replace label
            label.hide()
            scroll_layout.insertWidget(scroll_layout.indexOf(label), edit_label)
            widgets['edit_label'] = edit_label
            
            # Create tag list for this category
            tags = mm.get_tags_by_category().get(category_name, [])
            tag_list_widget = QWidget()
            tag_list_layout = QVBoxLayout(tag_list_widget)
            tag_list_layout.setContentsMargins(20, 5, 5, 5)
            tag_list_layout.setSpacing(3)
            
            for tag in tags:
                tag_row = QWidget()
                tag_row_layout = QHBoxLayout(tag_row)
                tag_row_layout.setContentsMargins(0, 0, 0, 0)
                tag_row_layout.setSpacing(8)
                
                # Tag name bullet
                tag_label = QLabel(f"• {tag['name']}")
                tag_label.setStyleSheet(f"color: #cccccc; font-family: {UI_FONT}; font-size: 11px;")
                tag_row_layout.addWidget(tag_label)
                tag_row_layout.addStretch()
                
                # Move to category button
                move_tag_btn = QPushButton("Move to...")
                move_tag_btn.setFixedHeight(22)
                move_tag_btn.setMinimumWidth(70)
                move_tag_btn.setToolTip("Move tag to another category")
                move_tag_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #3a3a3a;
                        border: 1px solid #555;
                        border-radius: 3px;
                        color: #cccccc;
                        font-size: 10px;
                        font-family: {UI_FONT};
                        padding: 2px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: #2a5a2a;
                        color: #90EE90;
                    }}
                """)
                move_tag_btn.clicked.connect(lambda checked=False, t=tag: self._move_tag_to_category(dialog, t, mm))
                tag_row_layout.addWidget(move_tag_btn)
                
                # Edit tag button
                edit_tag_btn = QPushButton("Rename")
                edit_tag_btn.setFixedHeight(22)
                edit_tag_btn.setMinimumWidth(55)
                edit_tag_btn.setToolTip("Rename tag")
                edit_tag_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #3a3a3a;
                        border: 1px solid #555;
                        border-radius: 3px;
                        color: #cccccc;
                        font-size: 10px;
                        font-family: {UI_FONT};
                        padding: 2px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: #4b7daa;
                        color: white;
                    }}
                """)
                edit_tag_btn.clicked.connect(lambda checked=False, t=tag: self._edit_tag_name(dialog, t, mm))
                tag_row_layout.addWidget(edit_tag_btn)
                
                # Delete tag button
                del_tag_btn = QPushButton("Delete")
                del_tag_btn.setFixedHeight(22)
                del_tag_btn.setMinimumWidth(55)
                del_tag_btn.setToolTip("Delete tag")
                del_tag_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #3a3a3a;
                        border: 1px solid #555;
                        border-radius: 3px;
                        color: #cccccc;
                        font-size: 10px;
                        font-family: {UI_FONT};
                        padding: 2px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: #8B0000;
                        color: white;
                    }}
                """)
                del_tag_btn.clicked.connect(lambda checked=False, t=tag: self._delete_tag(dialog, t, mm))
                tag_row_layout.addWidget(del_tag_btn)
                
                tag_list_layout.addWidget(tag_row)
            
            # Add tag button
            add_tag_btn = QPushButton("➕ Add Tag")
            add_tag_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2a5a2a;
                    border: 1px solid #3a7a3a;
                    border-radius: 3px;
                    padding: 4px 8px;
                    color: #90EE90;
                    font-family: {UI_FONT};
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    background-color: #3a7a3a;
                    color: white;
                }}
            """)
            add_tag_btn.clicked.connect(lambda checked=False, cat=category_name: self._add_tag_to_category(dialog, cat, mm))
            tag_list_layout.addWidget(add_tag_btn)
            
            # Hide chip container, show tag list
            container.hide()
            scroll_layout.insertWidget(scroll_layout.indexOf(container), tag_list_widget)
            widgets['tag_list'] = tag_list_widget
        
        # Add "Add Category" button at bottom
        add_cat_widget = QWidget()
        add_cat_layout = QHBoxLayout(add_cat_widget)
        add_cat_layout.setContentsMargins(0, 10, 0, 0)
        
        add_cat_btn = QPushButton("➕ Add Category")
        add_cat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a5a2a;
                border: 1px solid #3a7a3a;
                border-radius: 3px;
                padding: 8px 16px;
                color: #90EE90;
                font-family: {UI_FONT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #3a7a3a;
                color: white;
            }}
        """)
        add_cat_btn.clicked.connect(lambda: self._add_category(dialog, mm))
        add_cat_layout.addWidget(add_cat_btn)
        add_cat_layout.addStretch()
        
        scroll_layout.addWidget(add_cat_widget)
        dialog._add_cat_widget = add_cat_widget
    
    def _switch_to_normal_mode(self, dialog, tag_buttons, category_widgets):
        """Switch Browse Tags dialog back to normal mode"""
        # Show tag chip buttons
        for chip_widget in tag_buttons.values():
            if chip_widget:
                try:
                    chip_widget.show()
                except (RuntimeError, AttributeError):
                    pass  # Already deleted
        
        # Remove edit widgets and restore original labels
        for category_name, widgets in list(category_widgets.items()):
            # Safely remove edit_label
            if 'edit_label' in widgets and widgets['edit_label']:
                try:
                    widgets['edit_label'].setParent(None)
                    widgets['edit_label'].deleteLater()
                except (RuntimeError, AttributeError):
                    pass  # Already deleted
                widgets['edit_label'] = None
                
                if 'label' in widgets and widgets['label']:
                    try:
                        widgets['label'].show()
                    except (RuntimeError, AttributeError):
                        pass
            
            # Safely remove tag_list
            if 'tag_list' in widgets and widgets['tag_list']:
                try:
                    widgets['tag_list'].setParent(None)
                    widgets['tag_list'].deleteLater()
                except (RuntimeError, AttributeError):
                    pass  # Already deleted
                widgets['tag_list'] = None
                
                if 'container' in widgets and widgets['container']:
                    try:
                        widgets['container'].show()
                    except (RuntimeError, AttributeError):
                        pass
        
        # Remove add category button
        if hasattr(dialog, '_add_cat_widget') and dialog._add_cat_widget:
            try:
                dialog._add_cat_widget.setParent(None)
                dialog._add_cat_widget.deleteLater()
            except (RuntimeError, AttributeError):
                pass  # Already deleted
            dialog._add_cat_widget = None
    
    def _edit_category_name(self, dialog, category_name, mm):
        """Edit category name"""
        # Check if category has any tags
        tags_by_category = mm.get_tags_by_category()
        if category_name not in tags_by_category or len(tags_by_category[category_name]) == 0:
            QtWidgets.QMessageBox.warning(
                dialog,
                "Cannot Rename",
                f"Category '{category_name}' has no tags.\n\n"
                "Add tags to this category first, or delete it."
            )
            return
        
        new_name, ok = QtWidgets.QInputDialog.getText(
            dialog,
            "Rename Category",
            f"Rename category '{category_name}' to:",
            QtWidgets.QLineEdit.Normal,
            category_name
        )
        
        if ok and new_name and new_name != category_name:
            if mm.update_category_name(category_name, new_name):
                # Refresh edit mode view
                self._refresh_edit_mode(dialog, mm)
            else:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Error",
                    "Failed to rename category"
                )
    
    def _delete_category(self, dialog, category_name, mm):
        """Delete category"""
        reply = QtWidgets.QMessageBox.warning(
            dialog,
            "Delete Category",
            f"Delete category '{category_name}' and all its tags?\n\nThis will also remove all file associations!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if mm.delete_category(category_name):
                # Refresh edit mode view
                self._refresh_edit_mode(dialog, mm)
            else:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Error",
                    "Failed to delete category"
                )
    
    def _edit_tag_name(self, dialog, tag, mm):
        """Edit tag name"""
        new_name, ok = QtWidgets.QInputDialog.getText(
            dialog,
            "Rename Tag",
            f"Rename tag '{tag['name']}' to:",
            QtWidgets.QLineEdit.Normal,
            tag['name']
        )
        
        if ok and new_name and new_name != tag['name']:
            if mm.update_tag_name(tag['id'], new_name):
                # Refresh edit mode view
                self._refresh_edit_mode(dialog, mm)
            else:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Error",
                    f"Failed to rename tag. Tag '{new_name}' may already exist."
                )
    
    def _move_tag_to_category(self, dialog, tag, mm):
        """Move tag to another category"""
        # Get all categories
        tags_by_category = mm.get_tags_by_category()
        categories = sorted(tags_by_category.keys())
        
        # Remove current category from list
        current_category = tag.get('category') or 'Uncategorized'
        if current_category in categories:
            categories.remove(current_category)
        
        if not categories:
            QtWidgets.QMessageBox.information(
                dialog,
                "No Categories",
                "No other categories available. Create a new category first."
            )
            return
        
        # Show selection dialog
        category, ok = QtWidgets.QInputDialog.getItem(
            dialog,
            "Move Tag",
            f"Move tag '{tag['name']}' to category:",
            categories,
            0,
            False
        )
        
        if ok and category:
            if mm.move_tag_to_category(tag['id'], category):
                # Refresh edit mode view
                self._refresh_edit_mode(dialog, mm)
            else:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Error",
                    "Failed to move tag"
                )
    
    def _delete_tag(self, dialog, tag, mm):
        """Delete tag"""
        reply = QtWidgets.QMessageBox.warning(
            dialog,
            "Delete Tag",
            f"Delete tag '{tag['name']}'?\n\nThis will remove it from all files!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if mm.delete_tag(tag['id']):
                # Refresh edit mode view
                self._refresh_edit_mode(dialog, mm)
            else:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Error",
                    "Failed to delete tag"
                )
    
    def _add_tag_to_category(self, dialog, category_name, mm):
        """Add new tag to category"""
        tag_name, ok = QtWidgets.QInputDialog.getText(
            dialog,
            "Add Tag",
            f"Enter new tag name for category '{category_name}':",
            QtWidgets.QLineEdit.Normal,
            ""
        )
        
        if ok and tag_name:
            tag_id = mm.add_tag(tag_name, category=category_name)
            if tag_id:
                # Refresh edit mode view
                self._refresh_edit_mode(dialog, mm)
            else:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Error",
                    f"Failed to add tag. Tag '{tag_name}' may already exist."
                )
    
    def _add_category(self, dialog, mm):
        """Add new category"""
        category_name, ok = QtWidgets.QInputDialog.getText(
            dialog,
            "Add Category",
            "Enter new category name:",
            QtWidgets.QLineEdit.Normal,
            ""
        )
        
        if ok and category_name:
            # Check if category already exists
            tags_by_category = mm.get_tags_by_category()
            if category_name in tags_by_category:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Category Exists",
                    f"Category '{category_name}' already exists!"
                )
                return
            
            # Get uncategorized tags
            uncategorized_tags = tags_by_category.get('Uncategorized', [])
            
            if uncategorized_tags:
                # Show dialog to choose existing uncategorized tag or create new
                tag_names = [tag['name'] for tag in uncategorized_tags]
                tag_names.insert(0, "➕ Create New Tag...")
                
                choice, ok2 = QtWidgets.QInputDialog.getItem(
                    dialog,
                    "Add Tag to Category",
                    f"Select an uncategorized tag to move to '{category_name}',\nor create a new one:",
                    tag_names,
                    0,
                    False
                )
                
                if ok2:
                    if choice == "➕ Create New Tag...":
                        # Create new tag
                        new_tag_name, ok3 = QtWidgets.QInputDialog.getText(
                            dialog,
                            "Create New Tag",
                            f"Enter new tag name for '{category_name}':",
                            QtWidgets.QLineEdit.Normal,
                            ""
                        )
                        
                        if ok3 and new_tag_name:
                            tag_id = mm.add_tag(new_tag_name, category=category_name)
                            if tag_id:
                                self._refresh_edit_mode(dialog, mm)
                            else:
                                QtWidgets.QMessageBox.warning(
                                    dialog,
                                    "Error",
                                    f"Failed to add tag. Tag '{new_tag_name}' may already exist."
                                )
                    else:
                        # Move existing tag to new category
                        selected_tag = next((t for t in uncategorized_tags if t['name'] == choice), None)
                        if selected_tag:
                            if mm.move_tag_to_category(selected_tag['id'], category_name):
                                self._refresh_edit_mode(dialog, mm)
                            else:
                                QtWidgets.QMessageBox.warning(
                                    dialog,
                                    "Error",
                                    "Failed to move tag"
                                )
            else:
                # No uncategorized tags, create new tag
                tag_name, ok2 = QtWidgets.QInputDialog.getText(
                    dialog,
                    "Add First Tag",
                    f"Add first tag for category '{category_name}':\n(No uncategorized tags available)",
                    QtWidgets.QLineEdit.Normal,
                    ""
                )
                
                if ok2 and tag_name:
                    tag_id = mm.add_tag(tag_name, category=category_name)
                    if tag_id:
                        self._refresh_edit_mode(dialog, mm)
                    else:
                        QtWidgets.QMessageBox.warning(
                            dialog,
                            "Error",
                            f"Failed to add tag. Tag '{tag_name}' may already exist."
                        )
    
    def _refresh_edit_mode(self, dialog, mm):
        """Refresh edit mode view after changes"""
        # Get references
        tag_buttons = dialog._tag_buttons
        category_widgets = dialog._category_widgets
        
        # Find scroll area and save position
        scroll_area = dialog.findChild(QScrollArea)
        scroll_widget = scroll_area.widget()
        scroll_layout = scroll_widget.layout()
        
        # Save scroll position
        scroll_position = scroll_area.verticalScrollBar().value()
        
        # Switch to normal mode (cleans up edit widgets)
        self._switch_to_normal_mode(dialog, tag_buttons, category_widgets)
        
        # Remove "Add Category" button if exists
        if hasattr(dialog, '_add_cat_widget') and dialog._add_cat_widget:
            dialog._add_cat_widget.setParent(None)
            dialog._add_cat_widget.deleteLater()
            dialog._add_cat_widget = None
        
        # Rebuild tag buttons from database
        tags_by_category = mm.get_tags_by_category()
        
        # Clear old category widgets
        dialog._category_widgets = {}
        
        # Remove all widgets from scroll layout
        while scroll_layout.count():
            item = scroll_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        
        # Recreate category structure (similar to show_browse_tags_dialog)
        category_widgets = {}
        new_tag_buttons = {}
        
        for category in sorted(tags_by_category.keys()):
            tags = tags_by_category[category]
            
            # Category header
            category_label = QLabel(f"▼ {category}")
            category_label.setStyleSheet(f"""
                font-size: 11px;
                font-weight: bold;
                color: #cccccc;
                padding: 3px 0px 2px 0px;
                font-family: {UI_FONT};
            """)
            scroll_layout.addWidget(category_label)
            
            # Container for tag chips
            chips_container = QWidget()
            chips_layout = FlowLayout()
            
            for tag in tags:
                # Create chip widget (simplified - just for structure, will be hidden in edit mode)
                chip_widget = QWidget()
                chip_layout = QHBoxLayout(chip_widget)
                chip_layout.setContentsMargins(0, 0, 0, 0)
                chip_layout.setSpacing(0)
                
                chip_btn = QPushButton(tag['name'])
                chip_btn.setCheckable(True)
                chip_btn.setProperty('tag_data', tag)
                chip_layout.addWidget(chip_btn)
                
                chip_widget._main_button = chip_btn
                chip_widget._tag_data = tag
                
                new_tag_buttons[tag['id']] = chip_widget
                chips_layout.addWidget(chip_widget)
            
            chips_container.setLayout(chips_layout)
            scroll_layout.addWidget(chips_container)
            
            # Separator
            separator = QLabel()
            separator.setFixedHeight(1)
            separator.setStyleSheet("background-color: #555; margin: 8px 0px;")
            scroll_layout.addWidget(separator)
            
            # Store references
            category_widgets[category] = {
                'label': category_label,
                'container': chips_container,
                'separator': separator
            }
        
        # Update dialog references
        dialog._tag_buttons = new_tag_buttons
        dialog._category_widgets = category_widgets
        
        # Switch back to edit mode
        self._switch_to_edit_mode(dialog, new_tag_buttons, category_widgets, scroll_layout, mm)
        
        # Restore scroll position after a short delay (widgets need to be rendered)
        try:
            from PySide6.QtCore import QTimer
        except ImportError:
            from PySide2.QtCore import QTimer
        
        QTimer.singleShot(50, lambda: scroll_area.verticalScrollBar().setValue(scroll_position))
    
    def _show_tag_context_menu(self, pos, button, dialog, tag_buttons):
        """Show context menu for tag button in browse dialog"""
        tag_data = button.property('tag_data')
        tag_count = button.property('tag_count')
        
        if tag_count == 0:
            # No files have this tag - no context menu needed
            return
        
        menu = QtWidgets.QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #2a2a2a;
                border: 1px solid #555;
                color: white;
                font-family: {UI_FONT};
                font-size: 11px;
            }}
            QMenu::item:selected {{
                background-color: #4b7daa;
            }}
        """)
        
        remove_action = menu.addAction(f"🗑️ Remove '{tag_data['name']}' from selection")
        
        action = menu.exec_(button.mapToGlobal(pos))
        
        if action == remove_action:
            self._remove_tag_from_selection(tag_data, dialog, tag_buttons)
    
    def _remove_tag_from_selection(self, tag_data, dialog, tag_buttons):
        """Remove specific tag from all selected files"""
        if not self.current_assets:
            return
        
        try:
            mm = dialog._mm if hasattr(dialog, '_mm') else None
            if not mm:
                from .metadata import get_metadata_manager
                mm = get_metadata_manager()
            
            tag_id = tag_data['id']
            tag_name = tag_data['name']
            
            # Remove from all selected files
            removed_count = 0
            for asset in self.current_assets:
                file_path = str(asset.file_path)
                mm.remove_tag_from_file(file_path, tag_id)
                removed_count += 1
            
            # Reload displays
            if len(self.current_assets) == 1:
                self.load_tags(self.current_assets[0])
            else:
                self.load_common_tags(self.current_assets)
            
            self.update_preview(self.current_assets)
            
            # Refresh browse dialog buttons
            self._refresh_browse_dialog_buttons(dialog, tag_buttons, mm)
            
            print(f"✓ Removed '{tag_name}' from {removed_count} file(s)")
            
        except Exception as e:
            print(f"Error removing tag: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_browse_dialog_buttons(self, dialog, tag_buttons, mm):
        """Refresh button colors/text in browse dialog based on current selection"""
        # If no selection, treat as 0 files (all tags grey)
        if not self.current_assets:
            current_file_tags = {}
            total_files = 0
        else:
            # Recalculate current file tags
            current_file_tags = {}
            for asset in self.current_assets:
                file_path = str(asset.file_path)
                file_meta = mm.get_file_metadata(file_path)
                if file_meta and file_meta.get('tags'):
                    for tag_dict in file_meta['tags']:
                        tag_id = tag_dict['id']
                        current_file_tags[tag_id] = current_file_tags.get(tag_id, 0) + 1
            
            total_files = len(self.current_assets)
        
        # Update each chip widget
        for tag_id, chip_widget in tag_buttons.items():
            if not hasattr(chip_widget, '_main_button') or not hasattr(chip_widget, '_tag_data'):
                continue
            
            button = chip_widget._main_button
            tag_data = chip_widget._tag_data
            tag_name = tag_data['name']
            tag_count = current_file_tags.get(tag_id, 0)
            
            # Update stored properties
            button.setProperty('tag_count', tag_count)
            button.setProperty('total_files', total_files)
            
            # Determine new text and colors
            if tag_count == 0:
                btn_text = tag_name
                bg_color = "#4a4a4a"
                text_color = "white"
                has_remove = False
            elif tag_count == total_files:
                btn_text = f"✓ {tag_name}"
                bg_color = "#2a5a2a"
                text_color = "#90EE90"
                has_remove = True
            else:
                btn_text = f"{tag_name} ({tag_count}/{total_files})"
                bg_color = "#4a4a2a"
                text_color = "#FFD700"
                has_remove = True
            
            # Update button text
            button.setText(btn_text)
            is_checked = button.isChecked()
            
            # Update button style
            border_radius = "3px" if not has_remove else "3px 0px 0px 3px"
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 1px solid #555;
                    border-radius: {border_radius};
                    padding: 4px 10px;
                    color: {text_color};
                    font-family: {UI_FONT};
                    font-size: 11px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: #5a5a5a;
                    border-color: #666;
                }}
                QPushButton:checked {{
                    background-color: #4b7daa;
                    border-color: #5a8db8;
                    color: #ffffff;
                    font-weight: bold;
                }}
                QPushButton:checked:hover {{
                    background-color: #5a8db8;
                }}
            """)
            
            # Show/hide remove button
            layout = chip_widget.layout()
            if layout and layout.count() > 1:
                remove_btn = layout.itemAt(1).widget()
                if remove_btn:
                    if has_remove:
                        remove_btn.show()
                        remove_btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {bg_color};
                                border: 1px solid #555;
                                border-left: none;
                                border-radius: 0px 3px 3px 0px;
                                color: {text_color};
                                font-family: {UI_FONT};
                                font-size: 14px;
                                font-weight: bold;
                                padding: 0px;
                            }}
                            QPushButton:hover {{
                                background-color: #8B0000;
                                color: white;
                            }}
                            QPushButton:pressed {{
                                background-color: #6B0000;
                            }}
                        """)
                    else:
                        remove_btn.hide()
    
    def _reset_tag_database(self):
        """Reset entire tag database - WARNING: destructive operation!"""
        reply = QtWidgets.QMessageBox.warning(
            self,
            "⚠️ Reset Tag Database",
            "This will DELETE ALL TAGS and file associations!\n\n"
            "This cannot be undone!\n\n"
            "Are you absolutely sure?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply != QtWidgets.QMessageBox.Yes:
            return
        
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            mm.reset_database()
            
            # Clear current display
            self.clear_tags()
            self.clear_metadata()
            
            # Reload autocomplete (now empty)
            self.setup_tag_autocomplete()
            
            QtWidgets.QMessageBox.information(
                self,
                "Database Reset",
                "Tag database has been reset.\n\nAll tags and associations have been deleted."
            )
            
            print("⚠️ Tag database reset complete")
            
        except Exception as e:
            print(f"Error resetting database: {e}")
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to reset database:\n{e}"
            )
    
    def _add_selected_tags(self, dialog, tag_buttons):
        """Add selected tags from browse dialog to current file(s)"""
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            # Get selected tags
            selected_tags = []
            for tag_id, chip_widget in tag_buttons.items():
                if hasattr(chip_widget, '_main_button'):
                    button = chip_widget._main_button
                    if button.isChecked():
                        tag_data = button.property('tag_data')
                        selected_tags.append(tag_data)
            
            if not selected_tags:
                QtWidgets.QMessageBox.information(
                    dialog,
                    "No Tags Selected",
                    "Please select at least one tag to add."
                )
                return
            
            # Add tags to all selected files
            if not self.current_assets:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "No Files Selected",
                    "Please select file(s) to add tags to."
                )
                return
            
            # Add each selected tag
            for tag_data in selected_tags:
                tag_name = tag_data['name']
                tag_id = tag_data['id']  # Get the ID from tag_data!
                
                # Add to all selected files
                for asset in self.current_assets:
                    file_path = str(asset.file_path)
                    
                    # Check if tag already exists
                    existing_metadata = mm.get_file_metadata(file_path)
                    if existing_metadata and existing_metadata.get('tags'):
                        existing_tag_ids = [t['id'] for t in existing_metadata['tags']]
                        if tag_id in existing_tag_ids:
                            continue  # Skip if already has this tag
                    
                    # Add tag (with ID, not name!)
                    mm.add_tag_to_file(file_path, tag_id)
            
            # Reload tags display (both Tags tab and Metadata tab)
            if len(self.current_assets) == 1:
                self.load_tags(self.current_assets[0])
            else:
                self.load_common_tags(self.current_assets)
            
            # Force update of tags container
            if hasattr(self, 'tags_container') and self.tags_container:
                self.tags_container.update()
                self.tags_container.updateGeometry()
            
            # Update metadata tab as well
            self.update_preview(self.current_assets)
            
            # Don't close dialog - let user continue adding tags
            # dialog.accept()  # Commented out - dialog stays open
            
            # Deselect all tags after adding (ready for next batch)
            for chip_widget in tag_buttons.values():
                if hasattr(chip_widget, '_main_button'):
                    chip_widget._main_button.setChecked(False)
            
            # Update info label to reflect current selection
            if hasattr(dialog, 'update_info_label'):
                dialog.update_info_label()
            
            # Refresh browse dialog button colors
            self._refresh_browse_dialog_buttons(dialog, tag_buttons, mm)
            
            # Show confirmation
            tag_names = ", ".join([t['name'] for t in selected_tags[:5]])
            if len(selected_tags) > 5:
                tag_names += f"... (+{len(selected_tags) - 5} more)"
            
            print(f"✓ Added {len(selected_tags)} tag(s) to {len(self.current_assets)} file(s): {tag_names}")
            
        except Exception as e:
            print(f"Error adding selected tags: {e}")
            import traceback
            traceback.print_exc()
    
    def add_tag(self):
        """Add a new tag from input field (supports bulk tagging for multiple files)"""
        tag_text = self.tag_input.text().strip()
        if not tag_text:
            return
        
        # Get ALL selected files (bulk tagging support!)
        if not self.current_assets or len(self.current_assets) == 0:
            print("No asset selected to tag")
            return
        
        # Check if tag already displayed (prevent duplicates in UI)
        for i in range(self.tags_layout.count()):
            item = self.tags_layout.itemAt(i)
            if item and item.widget():
                existing_tag = item.widget().property('tag_text')
                if existing_tag and existing_tag.lower() == tag_text.lower():
                    print(f"Tag '{tag_text}' already added to selection")
                    self.tag_input.clear()
                    return
        
        # Save to database
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            # Add tag to database (or get existing)
            tag_id = mm.add_tag(tag_text)
            
            # Link tag to ALL selected files (bulk operation!)
            # Note: Database will handle duplicates (INSERT OR IGNORE)
            tagged_count = 0
            for asset in self.current_assets:
                current_file = str(asset.file_path)
                mm.add_tag_to_file(current_file, tag_id)
                tagged_count += 1
            
            if tagged_count == 1:
                print(f"Tag added: {tag_text} -> {self.current_assets[0].name}")
            else:
                print(f"Tag added: {tag_text} -> {tagged_count} files")
        except Exception as e:
            print(f"Error saving tag: {e}")
        
        # Create tag chip (only once for display)
        self.create_tag_chip(tag_text, tag_id)
        
        # Clear input
        self.tag_input.clear()
        
        # Hide info label if tags exist
        if self.tags_layout.count() > 0:
            self.tag_info_label.hide()
    
    def create_tag_chip(self, tag_text, tag_id=None, is_common=True, count=None, total=None):
        """Create a visual tag chip widget
        
        Args:
            tag_text: Tag name
            tag_id: Tag ID from database
            is_common: True if tag is in ALL files, False if partial
            count: Number of files with this tag (for partial tags)
            total: Total number of selected files (for partial tags)
        """
        # CRITICAL: Check if chip already exists (prevent duplicates)
        for i in range(self.tags_layout.count()):
            item = self.tags_layout.itemAt(i)
            if item and item.widget():
                existing_widget = item.widget()
                existing_id = existing_widget.property('tag_id')
                existing_text = existing_widget.property('tag_text')
                if existing_id == tag_id and existing_text == tag_text:
                    # Chip already exists, skip creation
                    return
        
        tag_chip = QWidget(self.tags_container)  # PARENT to tags_container!
        tag_chip.setProperty('tag_id', tag_id)  # Store tag_id for later removal
        tag_chip.setProperty('tag_text', tag_text)  # Store tag_text
        
        # Set fixed height and auto width (increased from 24 to 26)
        tag_chip.setFixedHeight(26)
        tag_chip.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        
        # Different styling for common vs partial tags
        if is_common:
            # Common tags: solid grey background
            bg_color = "#4a4a4a"
            border_style = "1px solid #555"
        else:
            # Partial tags: darker background, dashed border
            bg_color = "#2a2a2a"
            border_style = "1px dashed #555"
        
        tag_chip.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: {border_style};
                border-radius: 3px;
                padding: 0px;
            }}
        """)
        
        chip_layout = QHBoxLayout(tag_chip)
        chip_layout.setContentsMargins(8, 4, 8, 4)
        chip_layout.setSpacing(5)
        
        # Tag label with count for partial tags
        if is_common:
            display_text = tag_text
            tooltip = f"{tag_text} - in all files"
        else:
            display_text = f"{tag_text} ({count}/{total})"
            tooltip = f"{tag_text} - in {count} of {total} files"
        
        tag_label = QLabel(display_text)
        tag_label.setStyleSheet(f"""
            QLabel {{
                color: {"white" if is_common else "#aaa"};
                font-family: {UI_FONT};
                font-size: 11px;
                background: transparent;
                border: none;
            }}
        """)
        tag_label.setToolTip(tooltip)
        chip_layout.addWidget(tag_label)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #555;
                border: 1px solid #666;
                border-radius: 2px;
                color: #aaa;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #666;
                color: #fff;
                border-color: #777;
            }}
            QPushButton:pressed {{
                background-color: #777;
                border-color: #888;
            }}
        """)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self.remove_tag_chip(tag_chip, tag_text))
        chip_layout.addWidget(remove_btn)
        
        # Add to layout
        self.tags_layout.addWidget(tag_chip)
        
        # CRITICAL: Explicitly show the chip widget
        tag_chip.show()
        tag_chip.setVisible(True)
        
        # Force layout update
        self.tags_layout.update()
        self.tags_layout.activate()  # Force layout recalculation
        
        if hasattr(self, 'tags_container') and self.tags_container:
            self.tags_container.updateGeometry()
            self.tags_container.show()
    
    def remove_tag_chip(self, chip_widget, tag_text):
        """Remove a tag chip (supports bulk removal from multiple files)"""
        # Get ALL selected files (bulk removal support!)
        if self.current_assets and len(self.current_assets) > 0:
            tag_id = chip_widget.property('tag_id')
            
            # Remove from database for ALL selected files
            if tag_id:
                try:
                    from .metadata import get_metadata_manager
                    mm = get_metadata_manager()
                    
                    removed_count = 0
                    for asset in self.current_assets:
                        current_file = str(asset.file_path)
                        mm.remove_tag_from_file(current_file, tag_id)
                        removed_count += 1
                    
                    if removed_count == 1:
                        print(f"Tag removed: {tag_text} -> {self.current_assets[0].name}")
                    else:
                        print(f"Tag removed: {tag_text} -> {removed_count} files")
                except Exception as e:
                    print(f"Error removing tag: {e}")
        
        # Remove from layout
        self.tags_layout.removeWidget(chip_widget)
        chip_widget.deleteLater()
        
        # Show info label if no tags remain
        if self.tags_layout.count() == 0:
            self.tag_info_label.show()
    
    def clear_tags(self):
        """Clear all tag chips"""
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.tag_info_label.show()
    
    def clear_all_tags_from_selection(self):
        """Remove ALL tags from selected file(s) with confirmation"""
        if not self.current_assets:
            QtWidgets.QMessageBox.information(
                self,
                "No Files Selected",
                "Please select file(s) to clear tags from."
            )
            return
        
        # Count total tags across all files
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            total_tags = 0
            for asset in self.current_assets:
                file_path = str(asset.file_path)
                metadata = mm.get_file_metadata(file_path)
                if metadata and metadata.get('tags'):
                    total_tags += len(metadata['tags'])
            
            if total_tags == 0:
                QtWidgets.QMessageBox.information(
                    self,
                    "No Tags",
                    "Selected file(s) have no tags to remove."
                )
                return
            
            # Confirmation dialog
            file_count = len(self.current_assets)
            file_text = f"{file_count} file(s)" if file_count > 1 else self.current_assets[0].name
            
            reply = QtWidgets.QMessageBox.question(
                self,
                "Clear All Tags",
                f"Remove ALL tags from {file_text}?\n\nThis will remove {total_tags} tag(s).",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply != QtWidgets.QMessageBox.Yes:
                return
            
            # Remove all tags from all selected files
            removed_count = 0
            for asset in self.current_assets:
                file_path = str(asset.file_path)
                metadata = mm.get_file_metadata(file_path)
                if metadata and metadata.get('tags'):
                    for tag in metadata['tags']:
                        mm.remove_tag_from_file(file_path, tag['id'])
                        removed_count += 1
            
            # Reload display
            if len(self.current_assets) == 1:
                self.load_tags(self.current_assets[0])
            else:
                self.load_common_tags(self.current_assets)
            
            # Update metadata tab
            self.update_preview(self.current_assets)
            
            # Refresh browse dialog if open
            if hasattr(self, '_active_browse_dialog') and self._active_browse_dialog:
                try:
                    dialog = self._active_browse_dialog
                    if hasattr(dialog, '_tag_buttons') and hasattr(dialog, '_mm'):
                        self._refresh_browse_dialog_buttons(dialog, dialog._tag_buttons, dialog._mm)
                except:
                    pass  # Dialog might be closed
            
            print(f"✓ Cleared {removed_count} tag(s) from {file_count} file(s)")
            
        except Exception as e:
            print(f"Error clearing tags: {e}")
            import traceback
            traceback.print_exc()
    
    def load_tags(self, asset):
        """Load tags for an asset from metadata system"""
        # Clear existing tags
        self.clear_tags()
        
        if not asset:
            return
        
        # Load tags from database
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            file_path = str(asset.file_path)
            metadata = mm.get_file_metadata(file_path)
            
            if metadata and metadata.get('tags'):
                for tag in metadata['tags']:
                    self.create_tag_chip(tag['name'], tag['id'])
                
                # Hide info label if we have tags
                if len(metadata['tags']) > 0:
                    self.tag_info_label.hide()
                    
                # Debug: print(f"Loaded {len(metadata['tags'])} tags for {asset.name}")
        except Exception as e:
            print(f"Error loading tags: {e}")
    
    def load_common_tags(self, assets):
        """Load tags for multiple files - shows common and partial tags in separate sections"""
        # Clear existing tags
        self.clear_tags()
        
        # CRITICAL: Process pending events so deleteLater() completes before adding new tags
        if PYSIDE_VERSION == 6:
            from PySide6.QtCore import QCoreApplication
        else:
            from PySide2.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        if not assets:
            return
        
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            # Get tags for all files
            all_file_tags = {}
            for asset in assets:
                file_path = str(asset.file_path)
                metadata = mm.get_file_metadata(file_path)
                if metadata and metadata.get('tags'):
                    # Store tags by tag_id for easy comparison
                    all_file_tags[file_path] = {tag['id']: tag for tag in metadata['tags']}
            
            if not all_file_tags:
                return  # No files have tags
            
            # Collect all unique tags and count occurrences
            tag_counts = {}  # {tag_id: {'tag': tag_dict, 'count': int}}
            for file_tags in all_file_tags.values():
                for tag_id, tag in file_tags.items():
                    if tag_id not in tag_counts:
                        tag_counts[tag_id] = {'tag': tag, 'count': 0}
                    tag_counts[tag_id]['count'] += 1
            
            total_files = len(assets)
            common_tags = {}  # Tags in ALL files
            partial_tags = {}  # Tags in SOME files
            
            for tag_id, data in tag_counts.items():
                if data['count'] == total_files:
                    common_tags[tag_id] = data['tag']
                else:
                    partial_tags[tag_id] = (data['tag'], data['count'])
            
            # Display tags (common first, then partial)
            if common_tags or partial_tags:
                # Add common tag chips
                for tag in common_tags.values():
                    self.create_tag_chip(tag['name'], tag['id'], is_common=True)
                
                # Add partial tag chips (with count)
                for tag, count in partial_tags.values():
                    self.create_tag_chip(tag['name'], tag['id'], is_common=False, count=count, total=total_files)
                
                self.tag_info_label.hide()
            
            # Summary message (debug)
            # if common_tags or partial_tags:
            #     print(f"Loaded {len(common_tags)} common and {len(partial_tags)} partial tags for {total_files} files")
            
        except Exception as e:
            import traceback
            print(f"Error loading common tags: {e}")
            traceback.print_exc()
    
    def on_preview_splitter_moved(self, pos, index):
        """Save preview splitter position when moved"""
        if self.config:
            splitter_state = self.preview_splitter.saveState().toBase64().data().decode()
            self.config.config["preview_splitter_position"] = splitter_state
            self.config.save_config()


class MayaStyleListView(QListView):
    """Custom QListView with Maya-style interaction and batch import"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.middle_button_pressed = False
        self.drag_start_position = None
        self.drag_started = False
        self.drag_to_collection = False  # Flag to distinguish drag-to-collection from batch import
        # Scroll speed reduction factor (lower = slower scrolling)
        self.scroll_speed_factor = 3.0  # 30% of normal speed
    
    def wheelEvent(self, event):
        """Handle mouse wheel with reduced scroll speed"""
        # Get the scroll delta
        delta = event.angleDelta().y()
        
        # Reduce the scroll amount
        reduced_delta = int(delta * self.scroll_speed_factor)
        
        # Get the scrollbar
        scrollbar = self.verticalScrollBar()
        
        # Apply the reduced scroll
        new_value = scrollbar.value() - reduced_delta // 8  # Divide by 8 for pixel conversion
        scrollbar.setValue(new_value)
        
        # Accept the event to prevent default handling
        event.accept()
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MiddleButton:
            # Get item at click position
            index = self.indexAt(event.pos())
            
            # If clicked on valid item, ensure it's selected
            if index.isValid():
                # If not already selected, select it (single selection)
                if not self.selectionModel().isSelected(index):
                    self.setCurrentIndex(index)
            
            self.middle_button_pressed = True
            self.drag_start_position = event.pos()
            self.drag_started = False
            event.accept()
            return
        else:
            self.middle_button_pressed = False
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        if self.middle_button_pressed and self.drag_start_position:
            if not self.drag_started:
                # Check if we've moved enough to start drag
                distance = (event.pos() - self.drag_start_position).manhattanLength()
                if distance >= 5:
                    self.drag_started = True
                    self.setCursor(Qt.ClosedHandCursor)
            
            if self.drag_started:
                # Continuously check position to see if we're over collections
                global_pos = self.mapToGlobal(event.pos())
                widget_at_cursor = QApplication.widgetAt(global_pos)
                
                # Check if cursor is over DragDropCollectionListWidget
                is_over_collections = False
                check_widget = widget_at_cursor
                while check_widget:
                    if isinstance(check_widget, DragDropCollectionListWidget):
                        is_over_collections = True
                        break
                    check_widget = check_widget.parent()
                
                # Update cursor based on position
                if is_over_collections:
                    if not self.drag_to_collection:
                        self.drag_to_collection = True
                        self.setCursor(Qt.DragMoveCursor)
                        # Start actual Qt drag operation
                        self.startDrag(Qt.CopyAction)
                        # After drag completes, reset flags
                        self.middle_button_pressed = False
                        self.drag_start_position = None
                        self.drag_started = False
                        self.drag_to_collection = False
                        self.setCursor(Qt.ArrowCursor)
                        self.unsetCursor()
                        return
                else:
                    if self.drag_to_collection:
                        # Left collections area
                        self.drag_to_collection = False
                        self.setCursor(Qt.ClosedHandCursor)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MiddleButton:
            # Check if we're still over the ddContentBrowser window
            global_pos = self.mapToGlobal(event.pos())
            widget_at_cursor = QApplication.widgetAt(global_pos)
            
            # Find the top-level browser window
            is_over_browser = False
            check_widget = widget_at_cursor
            while check_widget:
                # Check if this is the main browser window (has 'DDContentBrowser' in title or class name)
                if hasattr(check_widget, 'windowTitle') and 'DD Content Browser' in str(check_widget.windowTitle()):
                    is_over_browser = True
                    break
                # Also check by class name
                if check_widget.__class__.__name__ == 'DDContentBrowser':
                    is_over_browser = True
                    break
                check_widget = check_widget.parent()
            
            # Only do batch import if:
            # 1. Drag was started
            # 2. NOT dragging to collections panel
            # 3. Mouse is NOT over the browser window (must be outside, e.g., Maya viewport)
            if self.drag_started and not self.drag_to_collection and not is_over_browser:
                indexes = self.selectedIndexes()
                if indexes:
                    # Show status message before importing
                    count = len(indexes)
                    browser = self.parent()
                    while browser and not hasattr(browser, 'status_bar'):
                        browser = browser.parent()
                    if browser and hasattr(browser, 'status_bar'):
                        browser.status_bar.showMessage(f"Batch importing {count} file{'s' if count != 1 else ''}...", 2000)
                    
                    self.batch_import_files(indexes)
                else:
                    # No items selected - show warning
                    browser = self.parent()
                    while browser and not hasattr(browser, 'status_bar'):
                        browser = browser.parent()
                    if browser and hasattr(browser, 'status_bar'):
                        browser.status_bar.showMessage("No files selected for batch import", 2000)
            elif self.drag_started and not self.drag_to_collection and is_over_browser:
                # Dragged within browser but not to collections - cancel silently
                pass
            
            # Reset all flags
            self.middle_button_pressed = False
            self.drag_start_position = None
            self.drag_started = False
            self.drag_to_collection = False
            self.setCursor(Qt.ArrowCursor)
            self.unsetCursor()
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event):
        """Reset cursor when leaving"""
        if self.drag_started or self.middle_button_pressed:
            self.setCursor(Qt.ArrowCursor)
            self.unsetCursor()
        super().leaveEvent(event)
    
    def keyPressEvent(self, event):
        """Handle ESC to cancel drag"""
        if event.key() == Qt.Key_Escape:
            if self.drag_started or self.middle_button_pressed:
                self.setCursor(Qt.ArrowCursor)
                self.unsetCursor()
                self.middle_button_pressed = False
                self.drag_start_position = None
                self.drag_started = False
                self.drag_to_collection = False
                
                browser = self.parent()
                while browser and not hasattr(browser, 'status_bar'):
                    browser = browser.parent()
                if browser and hasattr(browser, 'status_bar'):
                    browser.status_bar.showMessage("Drag cancelled", 1500)
                return
        
        super().keyPressEvent(event)
    
    def startDrag(self, supportedActions):
        """Start drag operation when dragging to collections panel"""
        try:
            from PySide6.QtCore import QMimeData
            from PySide6.QtGui import QDrag
        except ImportError:
            from PySide2.QtCore import QMimeData
            from PySide2.QtGui import QDrag
        
        # Create drag object
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Store selected file paths (we'll retrieve them in the drop handler)
        # No need to actually set mime data - we check the source widget directly
        mime_data.setText("drag_from_file_list")
        drag.setMimeData(mime_data)
        
        # Execute drag
        drag.exec_(supportedActions)
    
    def batch_import_files(self, indexes):
        """Batch import files"""
        if not MAYA_AVAILABLE:
            return
        
        paths = []
        for index in indexes:
            if index.isValid():
                asset = self.model().data(index, Qt.UserRole)
                if asset and not asset.is_folder:
                    paths.append(str(asset.file_path))
        
        if not paths:
            return
        
        try:
            imported_count = 0
            failed_count = 0
            image_exts = ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.hdr', '.exr', '.tga', '.bmp', '.iff', '.dds']
            
            for file_path in paths:
                try:
                    file_lower = file_path.lower()
                    is_image = any(file_lower.endswith(ext) for ext in image_exts)
                    
                    if is_image:
                        # Create texture node
                        file_node = cmds.shadingNode('file', asTexture=True, isColorManaged=True)
                        cmds.setAttr(f"{file_node}.fileTextureName", file_path, type="string")
                        
                        # Create place2dTexture
                        place2d = cmds.shadingNode('place2dTexture', asUtility=True)
                        cmds.connectAttr(f"{place2d}.coverage", f"{file_node}.coverage", force=True)
                        cmds.connectAttr(f"{place2d}.translateFrame", f"{file_node}.translateFrame", force=True)
                        cmds.connectAttr(f"{place2d}.rotateFrame", f"{file_node}.rotateFrame", force=True)
                        cmds.connectAttr(f"{place2d}.mirrorU", f"{file_node}.mirrorU", force=True)
                        cmds.connectAttr(f"{place2d}.mirrorV", f"{file_node}.mirrorV", force=True)
                        cmds.connectAttr(f"{place2d}.stagger", f"{file_node}.stagger", force=True)
                        cmds.connectAttr(f"{place2d}.wrapU", f"{file_node}.wrapU", force=True)
                        cmds.connectAttr(f"{place2d}.wrapV", f"{file_node}.wrapV", force=True)
                        cmds.connectAttr(f"{place2d}.repeatUV", f"{file_node}.repeatUV", force=True)
                        cmds.connectAttr(f"{place2d}.offset", f"{file_node}.offset", force=True)
                        cmds.connectAttr(f"{place2d}.rotateUV", f"{file_node}.rotateUV", force=True)
                        cmds.connectAttr(f"{place2d}.noiseUV", f"{file_node}.noiseUV", force=True)
                        cmds.connectAttr(f"{place2d}.vertexUvOne", f"{file_node}.vertexUvOne", force=True)
                        cmds.connectAttr(f"{place2d}.vertexUvTwo", f"{file_node}.vertexUvTwo", force=True)
                        cmds.connectAttr(f"{place2d}.vertexUvThree", f"{file_node}.vertexUvThree", force=True)
                        cmds.connectAttr(f"{place2d}.vertexCameraOne", f"{file_node}.vertexCameraOne", force=True)
                        cmds.connectAttr(f"{place2d}.outUV", f"{file_node}.uv", force=True)
                        cmds.connectAttr(f"{place2d}.outUvFilterSize", f"{file_node}.uvFilterSize", force=True)
                        
                        imported_count += 1
                    else:
                        # Import 3D file
                        if file_lower.endswith('.ma'):
                            file_type = 'mayaAscii'
                        elif file_lower.endswith('.mb'):
                            file_type = 'mayaBinary'
                        elif file_lower.endswith('.obj'):
                            file_type = 'OBJ'
                        elif file_lower.endswith('.fbx'):
                            file_type = 'FBX'
                        elif file_lower.endswith('.abc'):
                            file_type = 'Alembic'
                        elif file_lower.endswith('.usd'):
                            file_type = 'USD Import'
                        else:
                            # Skip unsupported file types
                            continue
                        
                        cmds.file(file_path, i=True, type=file_type, ignoreVersion=True,
                                 mergeNamespacesOnClash=False, namespace=':',
                                 options='v=0', preserveReferences=True)
                        imported_count += 1
                    
                except Exception as e:
                    failed_count += 1
            
            # Update status bar
            browser = self.parent()
            while browser and not hasattr(browser, 'status_bar'):
                browser = browser.parent()
            if browser and hasattr(browser, 'status_bar'):
                if imported_count > 0:
                    msg = f"Imported {imported_count} file{'s' if imported_count != 1 else ''}"
                    if failed_count > 0:
                        msg += f" ({failed_count} failed)"
                    browser.status_bar.showMessage(msg, 3000)
                else:
                    browser.status_bar.showMessage("No files imported", 2000)
        
        except Exception as e:
            print(f"Batch import error: {e}")
            # Show error in status bar
            browser = self.parent()
            while browser and not hasattr(browser, 'status_bar'):
                browser = browser.parent()
            if browser and hasattr(browser, 'status_bar'):
                browser.status_bar.showMessage(f"Batch import error: {e}", 3000)


class DragDropCollectionListWidget(QListWidget):
    """Custom QListWidget that accepts middle-button drag from file list"""
    
    # Signal emitted when files are dropped onto a collection
    files_dropped_on_collection = Signal(str, list)  # collection_name, file_paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.drop_indicator_item = None
    
    def dragEnterEvent(self, event):
        """Handle drag enter - check if it's coming from our file list"""
        # Accept drops from within our application
        if event.source() and isinstance(event.source(), MayaStyleListView):
            event.acceptProposedAction()
            return
        
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move - highlight collection under cursor"""
        if event.source() and isinstance(event.source(), MayaStyleListView):
            # Get item under cursor
            item = self.itemAt(event.pos())
            
            # Clear previous highlight
            if self.drop_indicator_item:
                font = self.drop_indicator_item.font()
                font.setBold(False)
                self.drop_indicator_item.setFont(font)
            
            # Highlight current item
            if item and item.data(Qt.UserRole):  # Has collection name
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.drop_indicator_item = item
                event.acceptProposedAction()
            else:
                self.drop_indicator_item = None
                event.ignore()
            
            return
        
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave - clear highlight"""
        if self.drop_indicator_item:
            font = self.drop_indicator_item.font()
            font.setBold(False)
            self.drop_indicator_item.setFont(font)
            self.drop_indicator_item = None
    
    def dropEvent(self, event):
        """Handle drop - add files to collection"""
        # Clear highlight
        if self.drop_indicator_item:
            font = self.drop_indicator_item.font()
            font.setBold(False)
            self.drop_indicator_item.setFont(font)
            self.drop_indicator_item = None
        
        # Check if dropped on valid collection item
        item = self.itemAt(event.pos())
        if not item:
            event.ignore()
            return
        
        collection_name = item.data(Qt.UserRole)
        if not collection_name:
            event.ignore()
            return
        
        # Get file paths from source
        source = event.source()
        if not isinstance(source, MayaStyleListView):
            event.ignore()
            return
        
        # Get selected assets from file list
        indexes = source.selectedIndexes()
        file_paths = []
        
        for index in indexes:
            if index.isValid():
                asset = source.model().data(index, Qt.UserRole)
                if asset and not asset.is_folder:
                    file_paths.append(str(asset.file_path))
        
        if file_paths:
            # Emit signal with collection name and file paths
            self.files_dropped_on_collection.emit(collection_name, file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()


