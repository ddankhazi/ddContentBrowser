# -*- coding: utf-8 -*-
"""
DD Content Browser - Advanced Filters Panel
Complex filtering system with presets and custom filter combinations

Author: ddankhazi
License: MIT
"""

from pathlib import Path
from datetime import datetime, timedelta

try:
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QButtonGroup, QGroupBox, QScrollArea,
                                   QCheckBox, QSpinBox, QComboBox, QLineEdit,
                                   QRadioButton, QListWidget, QMessageBox)
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QButtonGroup, QGroupBox, QScrollArea,
                                   QCheckBox, QSpinBox, QComboBox, QLineEdit,
                                   QRadioButton, QListWidget, QMessageBox)
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtGui import QFont
    PYSIDE_VERSION = 2

# Debug flag
DEBUG_MODE = False


class FilterPreset:
    """Represents a saved filter preset"""
    
    def __init__(self, name, filter_config):
        self.name = name
        self.filter_config = filter_config  # Dictionary of filter settings
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "filter_config": self.filter_config
        }
    
    @staticmethod
    def from_dict(data):
        """Create FilterPreset from dictionary"""
        return FilterPreset(data["name"], data["filter_config"])


class AdvancedFiltersPanel(QWidget):
    """Advanced filters panel widget"""
    
    # Signal emitted when filter is applied
    filter_applied = Signal(dict)  # Emits filter configuration dict
    filter_cleared = Signal()
    
    def __init__(self, file_model, settings_manager=None, parent=None):
        super().__init__(parent)
        self.file_model = file_model
        self.settings_manager = settings_manager
        self.saved_presets = []  # List of FilterPreset objects
        
        self.init_ui()
        self.load_presets()
    
    def init_ui(self):
        """Initialize UI"""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Scroll area for all filter options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        # === QUICK PRESETS Section ===
        quick_group = QGroupBox("⚡ Quick Filters")
        quick_layout = QVBoxLayout()
        quick_layout.setSpacing(4)
        
        # Time-based quick filters
        time_label = QLabel("<b>Recently Modified:</b>")
        time_label.setStyleSheet("color: #aaa; font-size: 10px;")
        quick_layout.addWidget(time_label)
        
        time_btn_layout = QHBoxLayout()
        self.today_btn = QPushButton("Today")
        self.week_btn = QPushButton("This Week")
        self.month_btn = QPushButton("This Month")
        
        for btn in [self.today_btn, self.week_btn, self.month_btn]:
            btn.setCheckable(True)
            btn.setMaximumHeight(24)
            btn.clicked.connect(self.on_quick_filter_clicked)
            time_btn_layout.addWidget(btn)
        
        quick_layout.addLayout(time_btn_layout)
        
        # Size-based quick filters
        size_label = QLabel("<b>File Size:</b>")
        size_label.setStyleSheet("color: #aaa; font-size: 10px; margin-top: 5px;")
        quick_layout.addWidget(size_label)
        
        size_btn_layout = QHBoxLayout()
        self.small_btn = QPushButton("< 10 MB")
        self.medium_btn = QPushButton("10-100 MB")
        self.large_btn = QPushButton("> 100 MB")
        
        for btn in [self.small_btn, self.medium_btn, self.large_btn]:
            btn.setCheckable(True)
            btn.setMaximumHeight(24)
            btn.clicked.connect(self.on_quick_filter_clicked)
            size_btn_layout.addWidget(btn)
        
        quick_layout.addLayout(size_btn_layout)
        
        # Type-based quick filters
        type_label = QLabel("<b>File Types:</b>")
        type_label.setStyleSheet("color: #aaa; font-size: 10px; margin-top: 5px;")
        quick_layout.addWidget(type_label)
        
        type_btn_layout1 = QHBoxLayout()
        self.maya_btn = QPushButton("Maya Scenes")
        self.images_btn = QPushButton("Images")
        self.scripts_btn = QPushButton("Scripts")
        
        for btn in [self.maya_btn, self.images_btn, self.scripts_btn]:
            btn.setCheckable(True)
            btn.setMaximumHeight(24)
            btn.clicked.connect(self.on_quick_filter_clicked)
            type_btn_layout1.addWidget(btn)
        
        quick_layout.addLayout(type_btn_layout1)
        
        type_btn_layout2 = QHBoxLayout()
        self.models_3d_btn = QPushButton("3D Models")
        self.hdr_btn = QPushButton("HDR/EXR")
        
        for btn in [self.models_3d_btn, self.hdr_btn]:
            btn.setCheckable(True)
            btn.setMaximumHeight(24)
            btn.clicked.connect(self.on_quick_filter_clicked)
            type_btn_layout2.addWidget(btn)
        
        type_btn_layout2.addStretch()
        quick_layout.addLayout(type_btn_layout2)
        
        quick_group.setLayout(quick_layout)
        scroll_layout.addWidget(quick_group)
        
        # === CUSTOM FILTERS Section ===
        custom_group = QGroupBox("🔧 Custom Filters")
        custom_layout = QVBoxLayout()
        custom_layout.setSpacing(6)
        
        # File name pattern
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name contains:"))
        self.name_pattern_input = QLineEdit()
        self.name_pattern_input.setPlaceholderText("e.g. *_proxy, char_*")
        self.name_pattern_input.textChanged.connect(self.on_custom_filter_changed)
        name_layout.addWidget(self.name_pattern_input)
        custom_layout.addLayout(name_layout)
        
        # Extension filter
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("Extensions:"))
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText(".ma, .mb, .obj")
        self.ext_input.textChanged.connect(self.on_custom_filter_changed)
        ext_layout.addWidget(self.ext_input)
        custom_layout.addLayout(ext_layout)
        
        # Size range
        size_range_label = QLabel("Size Range:")
        size_range_label.setStyleSheet("margin-top: 5px;")
        custom_layout.addWidget(size_range_label)
        
        size_range_layout = QHBoxLayout()
        self.size_min_spin = QSpinBox()
        self.size_min_spin.setRange(0, 10000)
        self.size_min_spin.setSuffix(" MB")
        self.size_min_spin.valueChanged.connect(self.on_custom_filter_changed)
        
        self.size_max_spin = QSpinBox()
        self.size_max_spin.setRange(0, 10000)
        self.size_max_spin.setSuffix(" MB")
        self.size_max_spin.valueChanged.connect(self.on_custom_filter_changed)
        
        size_range_layout.addWidget(QLabel("Min:"))
        size_range_layout.addWidget(self.size_min_spin)
        size_range_layout.addWidget(QLabel("Max:"))
        size_range_layout.addWidget(self.size_max_spin)
        size_range_layout.addStretch()
        custom_layout.addLayout(size_range_layout)
        
        custom_group.setLayout(custom_layout)
        scroll_layout.addWidget(custom_group)
        
        # === SAVED PRESETS Section ===
        presets_group = QGroupBox("💾 Saved Presets")
        presets_layout = QVBoxLayout()
        
        self.presets_list = QListWidget()
        self.presets_list.setMaximumHeight(100)
        self.presets_list.itemDoubleClicked.connect(self.load_preset)
        presets_layout.addWidget(self.presets_list)
        
        preset_btn_layout = QHBoxLayout()
        self.save_preset_btn = QPushButton("Save Current")
        self.save_preset_btn.clicked.connect(self.save_current_preset)
        self.load_preset_btn = QPushButton("Load")
        self.load_preset_btn.clicked.connect(self.load_preset)
        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.clicked.connect(self.delete_preset)
        
        preset_btn_layout.addWidget(self.save_preset_btn)
        preset_btn_layout.addWidget(self.load_preset_btn)
        preset_btn_layout.addWidget(self.delete_preset_btn)
        presets_layout.addLayout(preset_btn_layout)
        
        presets_group.setLayout(presets_layout)
        scroll_layout.addWidget(presets_group)
        
        # Add stretch at bottom
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # === ACTION BUTTONS at bottom ===
        action_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("✓ Apply Filters")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #5CBF60;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_filters)
        
        self.clear_btn = QPushButton("✕ Clear All")
        self.clear_btn.clicked.connect(self.clear_all_filters)
        
        action_layout.addWidget(self.apply_btn)
        action_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(action_layout)
    
    def on_quick_filter_clicked(self):
        """Handle quick filter button clicks"""
        sender = self.sender()
        
        # Uncheck other buttons in the same group
        # Time group
        time_buttons = [self.today_btn, self.week_btn, self.month_btn]
        if sender in time_buttons:
            for btn in time_buttons:
                if btn != sender:
                    btn.setChecked(False)
        
        # Size group
        size_buttons = [self.small_btn, self.medium_btn, self.large_btn]
        if sender in size_buttons:
            for btn in size_buttons:
                if btn != sender:
                    btn.setChecked(False)
        
        # Type buttons can be multi-selected (no unchecking needed)
        
        if DEBUG_MODE:
            print(f"[AdvancedFilters] Quick filter clicked: {sender.text()}")
    
    def on_custom_filter_changed(self):
        """Handle custom filter input changes"""
        if DEBUG_MODE:
            print("[AdvancedFilters] Custom filter changed")
    
    def get_current_filter_config(self):
        """Get current filter configuration as dictionary"""
        config = {
            "quick_filters": {
                "time": None,
                "size": None,
                "types": []
            },
            "custom_filters": {
                "name_pattern": self.name_pattern_input.text().strip(),
                "extensions": [ext.strip() for ext in self.ext_input.text().split(',') if ext.strip()],
                "size_min_mb": self.size_min_spin.value(),
                "size_max_mb": self.size_max_spin.value()
            }
        }
        
        # Time filters
        if self.today_btn.isChecked():
            config["quick_filters"]["time"] = "today"
        elif self.week_btn.isChecked():
            config["quick_filters"]["time"] = "week"
        elif self.month_btn.isChecked():
            config["quick_filters"]["time"] = "month"
        
        # Size filters
        if self.small_btn.isChecked():
            config["quick_filters"]["size"] = "small"
        elif self.medium_btn.isChecked():
            config["quick_filters"]["size"] = "medium"
        elif self.large_btn.isChecked():
            config["quick_filters"]["size"] = "large"
        
        # Type filters
        if self.maya_btn.isChecked():
            config["quick_filters"]["types"].append("maya")
        if self.images_btn.isChecked():
            config["quick_filters"]["types"].append("images")
        if self.scripts_btn.isChecked():
            config["quick_filters"]["types"].append("scripts")
        if self.models_3d_btn.isChecked():
            config["quick_filters"]["types"].append("3d_models")
        if self.hdr_btn.isChecked():
            config["quick_filters"]["types"].append("hdr")
        
        return config
    
    def apply_filters(self):
        """Apply current filter configuration to file model"""
        config = self.get_current_filter_config()
        
        # Apply to file model
        self.apply_config_to_model(config)
        
        # Emit signal
        self.filter_applied.emit(config)
        
        if DEBUG_MODE:
            print(f"[AdvancedFilters] Applied filters: {config}")
    
    def apply_config_to_model(self, config):
        """Apply filter configuration to file model"""
        # Reset filters first
        self.file_model.filter_file_types = []
        self.file_model.filter_min_size = 0
        self.file_model.filter_max_size = 0
        self.file_model.filter_date_from = None
        self.file_model.filter_date_to = None
        
        # Apply quick time filters
        time_filter = config["quick_filters"]["time"]
        if time_filter == "today":
            self.file_model.filter_date_from = datetime.now().replace(hour=0, minute=0, second=0)
        elif time_filter == "week":
            self.file_model.filter_date_from = datetime.now() - timedelta(days=7)
        elif time_filter == "month":
            self.file_model.filter_date_from = datetime.now() - timedelta(days=30)
        
        # Apply quick size filters
        size_filter = config["quick_filters"]["size"]
        if size_filter == "small":
            self.file_model.filter_max_size = 10 * 1024 * 1024  # 10 MB
        elif size_filter == "medium":
            self.file_model.filter_min_size = 10 * 1024 * 1024
            self.file_model.filter_max_size = 100 * 1024 * 1024
        elif size_filter == "large":
            self.file_model.filter_min_size = 100 * 1024 * 1024
        
        # Apply quick type filters
        type_filters = config["quick_filters"]["types"]
        extensions = []
        
        for type_filter in type_filters:
            if type_filter == "maya":
                extensions.extend([".ma", ".mb"])
            elif type_filter == "images":
                extensions.extend([".tif", ".tiff", ".jpg", ".jpeg", ".png", ".tga"])
            elif type_filter == "scripts":
                extensions.extend([".mel", ".py", ".txt"])
            elif type_filter == "3d_models":
                extensions.extend([".obj", ".fbx", ".abc", ".usd", ".vdb", ".dae", ".stl"])
            elif type_filter == "hdr":
                extensions.extend([".hdr", ".exr"])
        
        # Apply custom extension filters (override if specified)
        custom_exts = config["custom_filters"]["extensions"]
        if custom_exts:
            extensions = custom_exts
        
        if extensions:
            self.file_model.filter_file_types = extensions
        
        # Apply custom size filters (override quick filters if specified)
        if config["custom_filters"]["size_min_mb"] > 0:
            self.file_model.filter_min_size = config["custom_filters"]["size_min_mb"] * 1024 * 1024
        if config["custom_filters"]["size_max_mb"] > 0:
            self.file_model.filter_max_size = config["custom_filters"]["size_max_mb"] * 1024 * 1024
        
        # Apply custom name pattern to search text
        name_pattern = config["custom_filters"]["name_pattern"]
        if name_pattern:
            # Convert wildcard pattern to regex (simple implementation)
            # * -> .*, ? -> .
            import re
            regex_pattern = name_pattern.replace('*', '.*').replace('?', '.')
            self.file_model.filter_text = regex_pattern
            self.file_model.regex_search = True
        
        # Refresh model
        self.file_model.refresh()
    
    def clear_all_filters(self):
        """Clear all filters"""
        # Uncheck all quick filter buttons
        for btn in [self.today_btn, self.week_btn, self.month_btn,
                   self.small_btn, self.medium_btn, self.large_btn,
                   self.maya_btn, self.images_btn, self.scripts_btn,
                   self.models_3d_btn, self.hdr_btn]:
            btn.setChecked(False)
        
        # Clear custom inputs
        self.name_pattern_input.clear()
        self.ext_input.clear()
        self.size_min_spin.setValue(0)
        self.size_max_spin.setValue(0)
        
        # Clear file model filters
        self.file_model.clearFilters()
        self.file_model.filter_text = ""
        self.file_model.refresh()
        
        # Emit signal
        self.filter_cleared.emit()
        
        if DEBUG_MODE:
            print("[AdvancedFilters] All filters cleared")
    
    def save_current_preset(self):
        """Save current filter configuration as a preset"""
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PySide2.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        
        if ok and name:
            config = self.get_current_filter_config()
            preset = FilterPreset(name, config)
            self.saved_presets.append(preset)
            self.update_presets_list()
            self.save_presets()
            
            if DEBUG_MODE:
                print(f"[AdvancedFilters] Saved preset: {name}")
    
    def load_preset(self):
        """Load selected preset"""
        current_item = self.presets_list.currentItem()
        if not current_item:
            return
        
        preset_name = current_item.text()
        preset = next((p for p in self.saved_presets if p.name == preset_name), None)
        
        if preset:
            self.set_filter_config(preset.filter_config)
            self.apply_filters()
            
            if DEBUG_MODE:
                print(f"[AdvancedFilters] Loaded preset: {preset_name}")
    
    def delete_preset(self):
        """Delete selected preset"""
        current_item = self.presets_list.currentItem()
        if not current_item:
            return
        
        preset_name = current_item.text()
        self.saved_presets = [p for p in self.saved_presets if p.name != preset_name]
        self.update_presets_list()
        self.save_presets()
        
        if DEBUG_MODE:
            print(f"[AdvancedFilters] Deleted preset: {preset_name}")
    
    def set_filter_config(self, config):
        """Set UI state from filter configuration"""
        # Clear all first
        for btn in [self.today_btn, self.week_btn, self.month_btn,
                   self.small_btn, self.medium_btn, self.large_btn,
                   self.maya_btn, self.images_btn, self.scripts_btn,
                   self.models_3d_btn, self.hdr_btn]:
            btn.setChecked(False)
        
        # Set time filters
        time_filter = config["quick_filters"]["time"]
        if time_filter == "today":
            self.today_btn.setChecked(True)
        elif time_filter == "week":
            self.week_btn.setChecked(True)
        elif time_filter == "month":
            self.month_btn.setChecked(True)
        
        # Set size filters
        size_filter = config["quick_filters"]["size"]
        if size_filter == "small":
            self.small_btn.setChecked(True)
        elif size_filter == "medium":
            self.medium_btn.setChecked(True)
        elif size_filter == "large":
            self.large_btn.setChecked(True)
        
        # Set type filters
        for type_filter in config["quick_filters"]["types"]:
            if type_filter == "maya":
                self.maya_btn.setChecked(True)
            elif type_filter == "images":
                self.images_btn.setChecked(True)
            elif type_filter == "scripts":
                self.scripts_btn.setChecked(True)
            elif type_filter == "3d_models":
                self.models_3d_btn.setChecked(True)
            elif type_filter == "hdr":
                self.hdr_btn.setChecked(True)
        
        # Set custom filters
        self.name_pattern_input.setText(config["custom_filters"]["name_pattern"])
        self.ext_input.setText(", ".join(config["custom_filters"]["extensions"]))
        self.size_min_spin.setValue(config["custom_filters"]["size_min_mb"])
        self.size_max_spin.setValue(config["custom_filters"]["size_max_mb"])
    
    def update_presets_list(self):
        """Update presets list widget"""
        self.presets_list.clear()
        for preset in self.saved_presets:
            self.presets_list.addItem(preset.name)
    
    def save_presets(self):
        """Save presets to settings file"""
        if not self.settings_manager:
            return
        
        # Convert presets to dict list for JSON serialization
        presets_data = [p.to_dict() for p in self.saved_presets]
        self.settings_manager.set("advanced_filters", "saved_presets", presets_data)
        self.settings_manager.save()
        
        if DEBUG_MODE:
            print(f"[AdvancedFilters] Saved {len(self.saved_presets)} presets")
    
    def load_presets(self):
        """Load presets from settings file"""
        if not self.settings_manager:
            return
        
        presets_data = self.settings_manager.get("advanced_filters", "saved_presets", [])
        self.saved_presets = [FilterPreset.from_dict(p) for p in presets_data]
        self.update_presets_list()
        
        if DEBUG_MODE:
            print(f"[AdvancedFilters] Loaded {len(self.saved_presets)} presets")
