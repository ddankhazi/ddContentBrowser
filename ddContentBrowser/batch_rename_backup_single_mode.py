# -*- coding: utf-8 -*-
"""
Batch Rename Module for DD Content Browser

Provides a standalone batch rename dialog with comprehensive functionality.
Can be used independently or integrated with the main browser.
"""

import os
import re
from pathlib import Path

try:
    # Try PySide6 first
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
        QGroupBox, QTextEdit, QProgressBar, QMessageBox
    )
    from PySide6.QtGui import QFont
    PYSIDE_VERSION = 6
except ImportError:
    # Fall back to PySide2
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtCore import Qt, QTimer
    from PySide2.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
        QGroupBox, QTextEdit, QProgressBar, QMessageBox
    )
    from PySide2.QtGui import QFont
    PYSIDE_VERSION = 2


class RenameRule:
    """Single rename rule with specific operation"""
    
    def __init__(self, rule_type="Find & Replace"):
        self.enabled = True
        self.rule_type = rule_type
        self.params = {}
        
    def apply(self, names):
        """Apply this rule to a list of filenames"""
        if not self.enabled:
            return names
        
        return names  # Will be implemented by rule widgets


class BatchRenameDialog(QDialog):
    """
    Comprehensive batch rename dialog with multiple rename rules.
    Supports chaining multiple operations together.
    """
    
    def __init__(self, file_paths, parent=None):
        super().__init__(parent)
        self.file_paths = [Path(p) for p in file_paths]
        self.original_names = [p.name for p in self.file_paths]
        self.preview_names = self.original_names.copy()
        
        # Rule system
        self.rules = []
        self.rule_widgets = []
        
        self.setWindowTitle("Batch Rename Files")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.update_preview()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Batch Rename Files")
        title.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Main content in horizontal layout
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)
        
        # Left panel - rename options
        options_panel = self.create_options_panel()
        main_layout.addWidget(options_panel)
        
        # Right panel - preview table
        preview_panel = self.create_preview_panel()
        main_layout.addWidget(preview_panel)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply Rename")
        self.apply_btn.clicked.connect(self.apply_rename)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
    
    def create_options_panel(self):
        """Create the left options panel"""
        group = QGroupBox("Rename Options")
        group.setMaximumWidth(350)
        layout = QVBoxLayout(group)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Find & Replace",
            "New Name",
            "Add Prefix",
            "Add Suffix", 
            "Numbering",
            "Case Change",
            "Regex Pattern"
        ])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # Dynamic options area
        self.options_area = QVBoxLayout()
        layout.addLayout(self.options_area)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Initialize with Find & Replace
        self.setup_find_replace_options()
        
        return group
    
    def create_preview_panel(self):
        """Create the right preview panel"""
        group = QGroupBox("Preview")
        layout = QVBoxLayout(group)
        
        # Info label
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["Original", "New Name"])
        
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.preview_table)
        
        return group
    
    def clear_options_area(self):
        """Clear the current options"""
        while self.options_area.count():
            child = self.options_area.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif child.layout():
                layout = child.layout()
                self.clear_layout(layout)
    
    def clear_layout(self, layout):
        """Recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
    
    def on_mode_changed(self, mode):
        """Handle mode change"""
        self.clear_options_area()
        
        if mode == "Find & Replace":
            self.setup_find_replace_options()
        elif mode == "New Name":
            self.setup_new_name_options()
        elif mode == "Add Prefix":
            self.setup_prefix_options()
        elif mode == "Add Suffix":
            self.setup_suffix_options()
        elif mode == "Numbering":
            self.setup_numbering_options()
        elif mode == "Case Change":
            self.setup_case_options()
        elif mode == "Regex Pattern":
            self.setup_regex_options()
        
        self.update_preview()
    
    def setup_find_replace_options(self):
        """Setup Find & Replace options"""
        # Find text
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.textChanged.connect(self.update_preview)
        find_layout.addWidget(self.find_input)
        self.options_area.addLayout(find_layout)
        
        # Replace text
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.textChanged.connect(self.update_preview)
        replace_layout.addWidget(self.replace_input)
        self.options_area.addLayout(replace_layout)
        
        # Options
        self.case_sensitive_cb = QCheckBox("Case sensitive")
        self.case_sensitive_cb.stateChanged.connect(self.update_preview)
        self.options_area.addWidget(self.case_sensitive_cb)
        
        self.whole_name_cb = QCheckBox("Replace whole name only")
        self.whole_name_cb.stateChanged.connect(self.update_preview)
        self.options_area.addWidget(self.whole_name_cb)
    
    def setup_new_name_options(self):
        """Setup New Name options"""
        # New name pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("New Name:"))
        self.new_name_input = QLineEdit("File_{num}")
        self.new_name_input.textChanged.connect(self.update_preview)
        pattern_layout.addWidget(self.new_name_input)
        self.options_area.addLayout(pattern_layout)
        
        # Start number
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start number:"))
        self.new_name_start = QSpinBox()
        self.new_name_start.setMinimum(0)
        self.new_name_start.setMaximum(9999)
        self.new_name_start.setValue(1)
        self.new_name_start.valueChanged.connect(self.update_preview)
        start_layout.addWidget(self.new_name_start)
        self.options_area.addLayout(start_layout)
        
        # Digits
        digits_layout = QHBoxLayout()
        digits_layout.addWidget(QLabel("Digits:"))
        self.new_name_digits = QSpinBox()
        self.new_name_digits.setMinimum(1)
        self.new_name_digits.setMaximum(6)
        self.new_name_digits.setValue(2)
        self.new_name_digits.valueChanged.connect(self.update_preview)
        digits_layout.addWidget(self.new_name_digits)
        self.options_area.addLayout(digits_layout)
        
        # Help text
        help_text = QLabel("Use {num} for number, {original} for original name (without extension)")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #888; font-size: 10px;")
        self.options_area.addWidget(help_text)
    
    def setup_prefix_options(self):
        """Setup Add Prefix options"""
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefix:"))
        self.prefix_input = QLineEdit()
        self.prefix_input.textChanged.connect(self.update_preview)
        prefix_layout.addWidget(self.prefix_input)
        self.options_area.addLayout(prefix_layout)
    
    def setup_suffix_options(self):
        """Setup Add Suffix options"""
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Suffix:"))
        self.suffix_input = QLineEdit()
        self.suffix_input.textChanged.connect(self.update_preview)
        suffix_layout.addWidget(self.suffix_input)
        self.options_area.addLayout(suffix_layout)
    
    def setup_numbering_options(self):
        """Setup Numbering options"""
        # Start number
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start number:"))
        self.start_number = QSpinBox()
        self.start_number.setMinimum(0)
        self.start_number.setMaximum(9999)
        self.start_number.setValue(1)
        self.start_number.valueChanged.connect(self.update_preview)
        start_layout.addWidget(self.start_number)
        self.options_area.addLayout(start_layout)
        
        # Digits
        digits_layout = QHBoxLayout()
        digits_layout.addWidget(QLabel("Digits:"))
        self.digits_spin = QSpinBox()
        self.digits_spin.setMinimum(1)
        self.digits_spin.setMaximum(6)
        self.digits_spin.setValue(2)
        self.digits_spin.valueChanged.connect(self.update_preview)
        digits_layout.addWidget(self.digits_spin)
        self.options_area.addLayout(digits_layout)
        
        # Pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Pattern:"))
        self.number_pattern = QLineEdit("File_{num}")
        self.number_pattern.textChanged.connect(self.update_preview)
        pattern_layout.addWidget(self.number_pattern)
        self.options_area.addLayout(pattern_layout)
        
        # Help text
        help_text = QLabel("Use {num} for number, {name} for original name")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #888; font-size: 10px;")
        self.options_area.addWidget(help_text)
    
    def setup_case_options(self):
        """Setup Case Change options"""
        self.case_combo = QComboBox()
        self.case_combo.addItems([
            "UPPERCASE",
            "lowercase", 
            "Title Case",
            "Sentence case"
        ])
        self.case_combo.currentTextChanged.connect(self.update_preview)
        self.options_area.addWidget(self.case_combo)
    
    def setup_regex_options(self):
        """Setup Regex Pattern options"""
        # Pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Pattern:"))
        self.regex_pattern = QLineEdit()
        self.regex_pattern.textChanged.connect(self.update_preview)
        pattern_layout.addWidget(self.regex_pattern)
        self.options_area.addLayout(pattern_layout)
        
        # Replacement
        replacement_layout = QHBoxLayout()
        replacement_layout.addWidget(QLabel("Replace with:"))
        self.regex_replacement = QLineEdit()
        self.regex_replacement.textChanged.connect(self.update_preview)
        replacement_layout.addWidget(self.regex_replacement)
        self.options_area.addLayout(replacement_layout)
        
        # Help text
        help_text = QLabel("Regex example: (\\d+) -> File_\\1 (capture numbers)")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #888; font-size: 10px;")
        self.options_area.addWidget(help_text)
    
    def update_preview(self):
        """Update the preview table"""
        mode = self.mode_combo.currentText()
        
        try:
            if mode == "Find & Replace":
                self.preview_names = self.apply_find_replace(preview=True)
            elif mode == "New Name":
                self.preview_names = self.apply_new_name(preview=True)
            elif mode == "Add Prefix":
                self.preview_names = self.apply_prefix(preview=True)
            elif mode == "Add Suffix":
                self.preview_names = self.apply_suffix(preview=True)
            elif mode == "Numbering":
                self.preview_names = self.apply_numbering(preview=True)
            elif mode == "Case Change":
                self.preview_names = self.apply_case_change(preview=True)
            elif mode == "Regex Pattern":
                self.preview_names = self.apply_regex(preview=True)
        except Exception as e:
            # Show error in preview
            self.preview_names = [f"ERROR: {str(e)}" for _ in self.original_names]
        
        # Update table
        self.preview_table.setRowCount(len(self.original_names))
        
        changes_count = 0
        for i, (original, new) in enumerate(zip(self.original_names, self.preview_names)):
            # Original name
            original_item = QTableWidgetItem(original)
            self.preview_table.setItem(i, 0, original_item)
            
            # New name
            new_item = QTableWidgetItem(new)
            if new != original and not new.startswith("ERROR:"):
                new_item.setBackground(QtGui.QColor(100, 200, 100, 50))  # Light green
                changes_count += 1
            elif new.startswith("ERROR:"):
                new_item.setBackground(QtGui.QColor(200, 100, 100, 50))  # Light red
            
            self.preview_table.setItem(i, 1, new_item)
        
        # Update info
        self.info_label.setText(f"{len(self.file_paths)} files, {changes_count} will be renamed")
        
        # Enable/disable apply button
        self.apply_btn.setEnabled(changes_count > 0 and not any(name.startswith("ERROR:") for name in self.preview_names))
    
    def apply_find_replace(self, preview=False):
        """Apply find and replace"""
        if not hasattr(self, 'find_input'):
            return self.original_names.copy()
        
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        case_sensitive = self.case_sensitive_cb.isChecked()
        whole_name = self.whole_name_cb.isChecked()
        
        if not find_text:
            return self.original_names.copy()
        
        new_names = []
        for original in self.original_names:
            name_without_ext = Path(original).stem
            ext = Path(original).suffix
            
            if whole_name:
                if (case_sensitive and name_without_ext == find_text) or \
                   (not case_sensitive and name_without_ext.lower() == find_text.lower()):
                    new_name = replace_text + ext
                else:
                    new_name = original
            else:
                if case_sensitive:
                    new_name_without_ext = name_without_ext.replace(find_text, replace_text)
                else:
                    # Case insensitive replace
                    pattern = re.escape(find_text)
                    new_name_without_ext = re.sub(pattern, replace_text, name_without_ext, flags=re.IGNORECASE)
                
                new_name = new_name_without_ext + ext
            
            new_names.append(new_name)
        
        return new_names
    
    def apply_new_name(self, preview=False):
        """Apply new name pattern"""
        if not hasattr(self, 'new_name_input'):
            return self.original_names.copy()
        
        pattern = self.new_name_input.text()
        start_num = self.new_name_start.value()
        digits = self.new_name_digits.value()
        
        if not pattern:
            return self.original_names.copy()
        
        new_names = []
        for i, original in enumerate(self.original_names):
            original_without_ext = Path(original).stem
            ext = Path(original).suffix
            
            current_num = start_num + i
            formatted_num = str(current_num).zfill(digits)
            
            # Replace placeholders
            new_name_without_ext = pattern.replace("{num}", formatted_num)
            new_name_without_ext = new_name_without_ext.replace("{original}", original_without_ext)
            
            new_name = new_name_without_ext + ext
            new_names.append(new_name)
        
        return new_names
    
    def apply_prefix(self, preview=False):
        """Apply prefix"""
        if not hasattr(self, 'prefix_input'):
            return self.original_names.copy()
        
        prefix = self.prefix_input.text()
        if not prefix:
            return self.original_names.copy()
        
        new_names = []
        for original in self.original_names:
            name_without_ext = Path(original).stem
            ext = Path(original).suffix
            new_name = prefix + name_without_ext + ext
            new_names.append(new_name)
        
        return new_names
    
    def apply_suffix(self, preview=False):
        """Apply suffix"""
        if not hasattr(self, 'suffix_input'):
            return self.original_names.copy()
        
        suffix = self.suffix_input.text()
        if not suffix:
            return self.original_names.copy()
        
        new_names = []
        for original in self.original_names:
            name_without_ext = Path(original).stem
            ext = Path(original).suffix
            new_name = name_without_ext + suffix + ext
            new_names.append(new_name)
        
        return new_names
    
    def apply_numbering(self, preview=False):
        """Apply numbering"""
        if not hasattr(self, 'start_number'):
            return self.original_names.copy()
        
        start_num = self.start_number.value()
        digits = self.digits_spin.value()
        pattern = self.number_pattern.text()
        
        if not pattern or "{num}" not in pattern:
            return self.original_names.copy()
        
        new_names = []
        for i, original in enumerate(self.original_names):
            name_without_ext = Path(original).stem
            ext = Path(original).suffix
            
            current_num = start_num + i
            formatted_num = str(current_num).zfill(digits)
            
            new_name_without_ext = pattern.replace("{num}", formatted_num).replace("{name}", name_without_ext)
            new_name = new_name_without_ext + ext
            new_names.append(new_name)
        
        return new_names
    
    def apply_case_change(self, preview=False):
        """Apply case change"""
        if not hasattr(self, 'case_combo'):
            return self.original_names.copy()
        
        case_type = self.case_combo.currentText()
        
        new_names = []
        for original in self.original_names:
            name_without_ext = Path(original).stem
            ext = Path(original).suffix
            
            if case_type == "UPPERCASE":
                new_name_without_ext = name_without_ext.upper()
            elif case_type == "lowercase":
                new_name_without_ext = name_without_ext.lower()
            elif case_type == "Title Case":
                new_name_without_ext = name_without_ext.title()
            elif case_type == "Sentence case":
                new_name_without_ext = name_without_ext.capitalize()
            else:
                new_name_without_ext = name_without_ext
            
            new_name = new_name_without_ext + ext
            new_names.append(new_name)
        
        return new_names
    
    def apply_regex(self, preview=False):
        """Apply regex pattern"""
        if not hasattr(self, 'regex_pattern'):
            return self.original_names.copy()
        
        pattern = self.regex_pattern.text()
        replacement = self.regex_replacement.text()
        
        if not pattern:
            return self.original_names.copy()
        
        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            raise Exception(f"Invalid regex pattern: {e}")
        
        new_names = []
        for original in self.original_names:
            name_without_ext = Path(original).stem
            ext = Path(original).suffix
            
            new_name_without_ext = compiled_pattern.sub(replacement, name_without_ext)
            new_name = new_name_without_ext + ext
            new_names.append(new_name)
        
        return new_names
    
    def apply_rename(self):
        """Apply the actual file renaming"""
        # Confirm dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Rename", 
            f"Are you sure you want to rename {len([n for n, o in zip(self.preview_names, self.original_names) if n != o])} files?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Apply renames
        errors = []
        success_count = 0
        
        for file_path, new_name, original_name in zip(self.file_paths, self.preview_names, self.original_names):
            if new_name != original_name and not new_name.startswith("ERROR:"):
                try:
                    new_path = file_path.parent / new_name
                    file_path.rename(new_path)
                    success_count += 1
                except Exception as e:
                    errors.append(f"{original_name} → {new_name}: {str(e)}")
        
        # Show results
        if errors:
            error_text = "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_text += f"\n... and {len(errors) - 10} more errors"
            
            QMessageBox.warning(
                self,
                "Rename Errors",
                f"Successfully renamed {success_count} files.\n\nErrors:\n{error_text}"
            )
        else:
            QMessageBox.information(
                self,
                "Rename Complete",
                f"Successfully renamed {success_count} files."
            )
        
        if success_count > 0:
            self.accept()


# Standalone test function
def test_batch_rename():
    """Test function to run the dialog standalone"""
    import sys
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    # Create some test files in a temp directory for testing
    test_files = [
        "test_file_001.txt",
        "another_file.jpg", 
        "document.pdf",
        "image_001.png",
        "video_file.mp4"
    ]
    
    dialog = BatchRenameDialog(test_files)
    dialog.show()
    
    if app is None:
        sys.exit(app.exec())


if __name__ == "__main__":
    test_batch_rename()