"""
Settings management for ddContentBrowser
Handles application settings storage, loading, and GUI dialog.
"""

import os
import json
from pathlib import Path

try:
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                                   QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
                                   QComboBox, QSlider, QSpinBox, QGroupBox, QFileDialog,
                                   QDialogButtonBox, QMessageBox)
    from PySide6.QtCore import Qt, Signal
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                                   QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
                                   QComboBox, QSlider, QSpinBox, QGroupBox, QFileDialog,
                                   QDialogButtonBox, QMessageBox)
    from PySide2.QtCore import Qt, Signal
    PYSIDE_VERSION = 2

# Debug flag - set to False to disable verbose logging
DEBUG_MODE = False


class SettingsManager:
    """Manages application settings with JSON persistence"""
    
    def __init__(self):
        # Store settings in user home directory for persistence across updates
        self.settings_dir = Path.home() / ".ddContentBrowser"
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.settings_dir / "settings.json"
        self.settings = self.load_default_settings()
        self.load()
    
    def load_default_settings(self):
        """Return default settings dictionary"""
        return {
            # General settings
            "general": {
                "startup_directory": "",
                "remember_window_size": True,
                "window_width": 1200,
                "window_height": 800,
                "confirm_delete": True,
                "auto_refresh": False,
                "refresh_interval": 5,  # seconds
                "ui_font": "Segoe UI"  # Default UI font family (Windows standard, matches Maya UI)
            },
            # Thumbnail settings
            "thumbnails": {
                "size": 128,
                "memory_cache_size": 2000,  # Number of thumbnails in RAM
                "cache_size_mb": 500,  # Disk cache size in MB
                "quality": "medium",  # low, medium, high
                "generate_for_3d": True
            },
            # Preview settings
            "preview": {
                "resolution": 1024,
                "hdr_cache_size": 5,
                "default_exposure": 0.0,
                "auto_fit": True,
                "background_mode": "dark_gray"  # dark_gray, light_gray, checkered, black, white
            },
            # Filter settings
            "filters": {
                "show_images": True,
                "show_3d": True,
                "show_hdr": True,
                "show_video": True,
                "custom_extensions": [],
                "show_hidden": False,
                "case_sensitive_search": False,
                "regex_search": False,
                "max_recursive_files": 10000  # Maximum files when browsing subfolders
            },
            # Advanced Filters - saved filter presets
            "advanced_filters": {
                "saved_presets": []  # List of saved filter preset configurations
            }
        }
    
    def load(self):
        """Load settings from JSON file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._merge_settings(self.settings, loaded)
                if DEBUG_MODE:
                    print(f"[Settings] Loaded from {self.settings_file}")
            except Exception as e:
                print(f"[Settings] Error loading settings: {e}")
                print("[Settings] Using default settings")
    
    def _merge_settings(self, default, loaded):
        """Recursively merge loaded settings with defaults"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
    
    def save(self):
        """Save settings to JSON file"""
        try:
            # Ensure parent directory exists
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            if DEBUG_MODE:
                print(f"[Settings] Saved to {self.settings_file}")
            return True
        except Exception as e:
            print(f"[Settings] Error saving settings: {e}")
            return False
    
    def get(self, category, key, default=None):
        """Get a setting value"""
        try:
            return self.settings.get(category, {}).get(key, default)
        except:
            return default
    
    def set(self, category, key, value):
        """Set a setting value"""
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.load_default_settings()
        self.save()


class GeneralSettingsTab(QWidget):
    """General settings tab"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Startup directory group
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Startup Directory:"))
        self.startup_dir_edit = QLineEdit(self.settings.get("general", "startup_directory", ""))
        dir_layout.addWidget(self.startup_dir_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        startup_layout.addLayout(dir_layout)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Window settings group
        window_group = QGroupBox("Window")
        window_layout = QVBoxLayout()
        
        self.remember_size_cb = QCheckBox("Remember window size and position")
        self.remember_size_cb.setChecked(self.settings.get("general", "remember_window_size", True))
        window_layout.addWidget(self.remember_size_cb)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Default Size:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(800, 3840)
        self.width_spin.setValue(self.settings.get("general", "window_width", 1200))
        self.width_spin.setSuffix(" px")
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(600, 2160)
        self.height_spin.setValue(self.settings.get("general", "window_height", 800))
        self.height_spin.setSuffix(" px")
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.height_spin)
        size_layout.addStretch()
        window_layout.addLayout(size_layout)
        
        # UI Font selection
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("UI Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Segoe UI", "Arial", "Calibri", "Verdana", "Tahoma"])
        current_font = self.settings.get("general", "ui_font", "Segoe UI")
        index = self.font_combo.findText(current_font)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(QLabel("(restart required)"))
        font_layout.addStretch()
        window_layout.addLayout(font_layout)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.confirm_delete_cb = QCheckBox("Confirm before deleting files")
        self.confirm_delete_cb.setChecked(self.settings.get("general", "confirm_delete", True))
        behavior_layout.addWidget(self.confirm_delete_cb)
        
        self.auto_refresh_cb = QCheckBox("Auto-refresh directory")
        self.auto_refresh_cb.setChecked(self.settings.get("general", "auto_refresh", False))
        behavior_layout.addWidget(self.auto_refresh_cb)
        
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("    Refresh interval:"))
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(1, 60)
        self.refresh_spin.setValue(self.settings.get("general", "refresh_interval", 5))
        self.refresh_spin.setSuffix(" sec")
        refresh_layout.addWidget(self.refresh_spin)
        refresh_layout.addStretch()
        behavior_layout.addLayout(refresh_layout)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # Database group
        database_group = QGroupBox("Database")
        database_layout = QVBoxLayout()
        
        # Tag database reset button
        reset_layout = QHBoxLayout()
        reset_layout.addWidget(QLabel("Tag Database:"))
        self.reset_tags_btn = QPushButton("🗑️ Clear All Tag Assignments")
        self.reset_tags_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px 12px;
                color: #cccccc;
            }
            QPushButton:hover {
                background-color: #8B0000;
                border-color: #A00000;
                color: white;
            }
            QPushButton:pressed {
                background-color: #6B0000;
            }
        """)
        self.reset_tags_btn.clicked.connect(self.clear_tag_assignments)
        self.reset_tags_btn.setToolTip("Remove all tag assignments from files (tag names are preserved)")
        reset_layout.addWidget(self.reset_tags_btn)
        reset_layout.addStretch()
        database_layout.addLayout(reset_layout)
        
        # Load default tags button
        default_tags_layout = QHBoxLayout()
        default_tags_layout.addWidget(QLabel("Default Tags:"))
        self.load_defaults_btn = QPushButton("📥 Load Default Tags")
        self.load_defaults_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px 12px;
                color: #cccccc;
            }
            QPushButton:hover {
                background-color: #2a5a2a;
                border-color: #3a7a3a;
                color: #90EE90;
            }
            QPushButton:pressed {
                background-color: #1a4a1a;
            }
        """)
        self.load_defaults_btn.clicked.connect(self.load_default_tags)
        self.load_defaults_btn.setToolTip("Load default tags from default_tags.json (won't duplicate existing tags)")
        default_tags_layout.addWidget(self.load_defaults_btn)
        default_tags_layout.addStretch()
        database_layout.addLayout(default_tags_layout)
        
        database_group.setLayout(database_layout)
        layout.addWidget(database_group)
        
        layout.addStretch()
    
    def browse_directory(self):
        """Browse for startup directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Startup Directory",
                                                     self.startup_dir_edit.text())
        if dir_path:
            self.startup_dir_edit.setText(dir_path)
    
    def clear_tag_assignments(self):
        """Clear all tag assignments but keep tag names"""
        reply = QMessageBox.warning(
            self,
            "⚠️ Clear Tag Assignments",
            "This will remove ALL tag assignments from all files!\n\n"
            "Tag names will be preserved and can be reused.\n\n"
            "This cannot be undone!\n\n"
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            mm.clear_all_tag_assignments()
            
            QMessageBox.information(
                self,
                "Success",
                "All tag assignments have been cleared.\n\n"
                "Tag names are preserved and available for reuse."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear tag assignments:\n{str(e)}"
            )
    
    def load_default_tags(self):
        """Load default tags from default_tags.json"""
        try:
            from .metadata import get_metadata_manager
            mm = get_metadata_manager()
            
            added_count = mm.load_default_tags()
            
            if added_count > 0:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Loaded {added_count} default tags!\n\n"
                    "Tags are now available in the Browse Tags dialog."
                )
            else:
                QMessageBox.information(
                    self,
                    "No Changes",
                    "All default tags are already loaded.\n\n"
                    "No new tags were added."
                )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load default tags:\n{str(e)}"
            )
    
    def save_settings(self):
        """Save settings from UI to settings manager"""
        self.settings.set("general", "startup_directory", self.startup_dir_edit.text())
        self.settings.set("general", "remember_window_size", self.remember_size_cb.isChecked())
        self.settings.set("general", "window_width", self.width_spin.value())
        self.settings.set("general", "window_height", self.height_spin.value())
        self.settings.set("general", "ui_font", self.font_combo.currentText())
        self.settings.set("general", "confirm_delete", self.confirm_delete_cb.isChecked())
        self.settings.set("general", "auto_refresh", self.auto_refresh_cb.isChecked())
        self.settings.set("general", "refresh_interval", self.refresh_spin.value())


class ThumbnailSettingsTab(QWidget):
    """Thumbnail settings tab"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Size group
        size_group = QGroupBox("Thumbnail Generation Size")
        size_layout = QVBoxLayout()
        
        # Add explanation label
        explanation = QLabel(
            "Set the resolution of generated thumbnail files (cached to disk).\n"
            "Higher = better quality when zooming, but larger cache size.\n"
            "Note: Grid/List display size is adjusted separately with the toolbar slider."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("QLabel { color: #888; font-size: 10px; padding: 5px; }")
        size_layout.addWidget(explanation)
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Size:"))
        
        # Define discrete thumbnail sizes (max 256px - matches browser slider max)
        self.size_values = [32, 64, 128, 256]
        
        # Create slider with indices (0-3)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(0, len(self.size_values) - 1)
        
        # Find current value index
        current_size = self.settings.get("thumbnails", "size", 128)
        if current_size in self.size_values:
            current_index = self.size_values.index(current_size)
        else:
            # Find closest value
            current_index = min(range(len(self.size_values)), 
                              key=lambda i: abs(self.size_values[i] - current_size))
        
        self.size_slider.setValue(current_index)
        self.size_slider.setTickInterval(1)
        self.size_slider.setTickPosition(QSlider.TicksBelow)
        slider_layout.addWidget(self.size_slider)
        
        self.size_label = QLabel(f"{self.size_values[self.size_slider.value()]} px")
        self.size_label.setMinimumWidth(60)
        slider_layout.addWidget(self.size_label)
        self.size_slider.valueChanged.connect(
            lambda idx: self.size_label.setText(f"{self.size_values[idx]} px")
        )
        
        size_layout.addLayout(slider_layout)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Quality group
        quality_group = QGroupBox("Quality")
        quality_layout = QVBoxLayout()
        
        quality_h_layout = QHBoxLayout()
        quality_h_layout.addWidget(QLabel("Thumbnail Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low (Fast)", "Medium", "High (Slow)"])
        current_quality = self.settings.get("thumbnails", "quality", "medium")
        quality_map = {"low": 0, "medium": 1, "high": 2}
        self.quality_combo.setCurrentIndex(quality_map.get(current_quality, 1))
        quality_h_layout.addWidget(self.quality_combo)
        quality_h_layout.addStretch()
        quality_layout.addLayout(quality_h_layout)
        
        self.generate_3d_cb = QCheckBox("Generate thumbnails for 3D files (slower)")
        self.generate_3d_cb.setChecked(self.settings.get("thumbnails", "generate_for_3d", True))
        quality_layout.addWidget(self.generate_3d_cb)
        
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Cache group
        cache_group = QGroupBox("Cache")
        cache_layout = QVBoxLayout()
        
        # Memory cache size (number of thumbnails in RAM)
        memory_cache_layout = QHBoxLayout()
        memory_cache_layout.addWidget(QLabel("Memory Cache Size:"))
        self.memory_cache_spin = QSpinBox()
        self.memory_cache_spin.setRange(100, 10000)
        self.memory_cache_spin.setSingleStep(100)
        self.memory_cache_spin.setValue(self.settings.get("thumbnails", "memory_cache_size", 2000))
        self.memory_cache_spin.setSuffix(" thumbnails")
        self.memory_cache_spin.setToolTip("Number of thumbnails to keep in memory (RAM). Increase for large folders.")
        memory_cache_layout.addWidget(self.memory_cache_spin)
        memory_cache_layout.addStretch()
        cache_layout.addLayout(memory_cache_layout)
        
        # Disk cache size (MB)
        cache_size_layout = QHBoxLayout()
        cache_size_layout.addWidget(QLabel("Disk Cache Size Limit:"))
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(50, 5000)
        self.cache_size_spin.setValue(self.settings.get("thumbnails", "cache_size_mb", 500))
        self.cache_size_spin.setSuffix(" MB")
        self.cache_size_spin.setToolTip("Maximum disk space for thumbnail cache.")
        cache_size_layout.addWidget(self.cache_size_spin)
        cache_size_layout.addStretch()
        cache_layout.addLayout(cache_size_layout)
        
        clear_cache_layout = QHBoxLayout()
        self.cache_info_label = QLabel("Current cache size: Calculating...")
        clear_cache_layout.addWidget(self.cache_info_label)
        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        clear_cache_layout.addWidget(clear_cache_btn)
        cache_layout.addLayout(clear_cache_layout)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        layout.addStretch()
        
        # Calculate cache size
        self.update_cache_info()
    
    def update_cache_info(self):
        """Update cache size information"""
        try:
            # Unified cache directory
            cache_dir = Path.home() / ".ddContentBrowser" / "thumbnails"
            if cache_dir.exists():
                total_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                self.cache_info_label.setText(f"Current cache size: {size_mb:.1f} MB")
            else:
                self.cache_info_label.setText("Current cache size: 0 MB")
        except Exception as e:
            self.cache_info_label.setText(f"Error calculating cache size: {e}")
    
    def clear_cache(self):
        """Clear thumbnail cache"""
        reply = QMessageBox.question(self, "Clear Cache",
                                     "Are you sure you want to clear the thumbnail cache?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # Unified cache directory
                cache_dir = Path.home() / ".ddContentBrowser" / "thumbnails"
                if cache_dir.exists():
                    import shutil
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    self.update_cache_info()
                    QMessageBox.information(self, "Success", "Cache cleared successfully!")
                else:
                    self.update_cache_info()
                    QMessageBox.information(self, "Info", "Cache directory does not exist.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear cache: {e}")
    
    def save_settings(self):
        """Save settings from UI to settings manager"""
        # Get actual size value from slider index
        size_index = self.size_slider.value()
        actual_size = self.size_values[size_index]
        self.settings.set("thumbnails", "size", actual_size)
        
        quality_map = {0: "low", 1: "medium", 2: "high"}
        self.settings.set("thumbnails", "quality", quality_map[self.quality_combo.currentIndex()])
        self.settings.set("thumbnails", "memory_cache_size", self.memory_cache_spin.value())
        self.settings.set("thumbnails", "cache_size_mb", self.cache_size_spin.value())
        self.settings.set("thumbnails", "generate_for_3d", self.generate_3d_cb.isChecked())


class PreviewSettingsTab(QWidget):
    """Preview panel settings tab"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Resolution group
        resolution_group = QGroupBox("Preview Resolution")
        resolution_layout = QVBoxLayout()
        
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["512 px (Fast)", "1024 px (Balanced)", 
                                       "2048 px (High Quality)", "4096 px (Maximum)"])
        current_res = self.settings.get("preview", "resolution", 1024)
        res_map = {512: 0, 1024: 1, 2048: 2, 4096: 3}
        self.resolution_combo.setCurrentIndex(res_map.get(current_res, 1))
        res_layout.addWidget(self.resolution_combo)
        res_layout.addStretch()
        resolution_layout.addLayout(res_layout)
        
        res_info = QLabel("⚠ Higher resolution = slower HDR/EXR processing")
        res_info.setStyleSheet("color: #888; font-size: 10px;")
        resolution_layout.addWidget(res_info)
        
        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)
        
        # HDR settings group
        hdr_group = QGroupBox("HDR/EXR Settings")
        hdr_layout = QVBoxLayout()
        
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(QLabel("Raw HDR Cache Size:"))
        self.hdr_cache_spin = QSpinBox()
        self.hdr_cache_spin.setRange(1, 20)
        self.hdr_cache_spin.setValue(self.settings.get("preview", "hdr_cache_size", 5))
        self.hdr_cache_spin.setSuffix(" files")
        cache_layout.addWidget(self.hdr_cache_spin)
        cache_layout.addStretch()
        hdr_layout.addLayout(cache_layout)
        
        cache_info = QLabel("ℹ Each cached file uses ~20-30 MB of RAM")
        cache_info.setStyleSheet("color: #888; font-size: 10px;")
        hdr_layout.addWidget(cache_info)
        
        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(QLabel("Default Exposure:"))
        self.exposure_spin = QSpinBox()
        self.exposure_spin.setRange(-10, 10)
        self.exposure_spin.setValue(int(self.settings.get("preview", "default_exposure", 0.0)))
        self.exposure_spin.setSuffix(" EV")
        exposure_layout.addWidget(self.exposure_spin)
        exposure_layout.addStretch()
        hdr_layout.addLayout(exposure_layout)
        
        hdr_group.setLayout(hdr_layout)
        layout.addWidget(hdr_group)
        
        # Display settings group
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()
        
        self.auto_fit_cb = QCheckBox("Auto-fit images to window")
        self.auto_fit_cb.setChecked(self.settings.get("preview", "auto_fit", True))
        display_layout.addWidget(self.auto_fit_cb)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
    
    def save_settings(self):
        """Save settings from UI to settings manager"""
        res_map = {0: 512, 1: 1024, 2: 2048, 3: 4096}
        self.settings.set("preview", "resolution", res_map[self.resolution_combo.currentIndex()])
        self.settings.set("preview", "hdr_cache_size", self.hdr_cache_spin.value())
        self.settings.set("preview", "default_exposure", float(self.exposure_spin.value()))
        self.settings.set("preview", "auto_fit", self.auto_fit_cb.isChecked())


class FiltersSettingsTab(QWidget):
    """File filters settings tab"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.init_ui()
    
    def _generate_supported_formats_html(self):
        """Generate HTML description of supported formats from FILE_TYPE_REGISTRY"""
        from .utils import FILE_TYPE_REGISTRY
        
        # Import & Reference capable formats (importable=True)
        importable_html = "<b>🔵 Import & Reference to Maya:</b><br>"
        for cat_name, cat_data in FILE_TYPE_REGISTRY.items():
            if cat_data['importable']:
                ext_list = ", ".join(cat_data['extensions'])
                importable_html += f"• <b>{cat_data['label']}:</b> {ext_list}<br>"
        
        # Browse & Preview only formats (importable=False)
        browse_html = "<b>⚪ Browse & Preview Only:</b><br>"
        for cat_name, cat_data in FILE_TYPE_REGISTRY.items():
            if not cat_data['importable']:
                ext_list = ", ".join(cat_data['extensions'])
                browse_html += f"• <b>{cat_data['label']}:</b> {ext_list}<br>"
        
        return importable_html, browse_html
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # File types group - Split into Import/Reference vs Browse-only
        types_group = QGroupBox("Supported File Types")
        types_layout = QVBoxLayout()
        
        # Generate HTML from registry
        import_html, browse_html = self._generate_supported_formats_html()
        
        # Import & Reference capable formats
        import_label = QLabel(import_html)
        import_label.setWordWrap(True)
        import_label.setStyleSheet("QLabel { color: #4CAF50; font-size: 11px; padding: 5px; }")
        types_layout.addWidget(import_label)
        
        # Browse/Preview only formats
        browse_label = QLabel(browse_html)
        browse_label.setWordWrap(True)
        browse_label.setStyleSheet("QLabel { color: #888; font-size: 11px; padding: 5px; }")
        types_layout.addWidget(browse_label)
        
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)
        
        # Custom extensions group
        custom_group = QGroupBox("Custom File Extensions")
        custom_layout = QVBoxLayout()
        
        # Description
        desc_label = QLabel(
            "Add custom file extensions to display (comma-separated).<br>"
            "Example: <code>.gltf, .blend, .max</code>"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { color: #888; font-size: 9px; padding: 5px; }")
        custom_layout.addWidget(desc_label)
        
        # Input field for custom extensions
        input_layout = QHBoxLayout()
        self.custom_ext_input = QLineEdit()
        self.custom_ext_input.setPlaceholderText(".gltf, .blend, .max")
        
        # Load existing custom extensions
        current_extensions = self.settings.get("filters", "custom_extensions", [])
        if current_extensions:
            self.custom_ext_input.setText(", ".join(current_extensions))
        
        input_layout.addWidget(QLabel("Extensions:"))
        input_layout.addWidget(self.custom_ext_input)
        custom_layout.addLayout(input_layout)
        
        # Current custom extensions display
        self.custom_ext_label = QLabel()
        self.update_custom_ext_display()
        custom_layout.addWidget(self.custom_ext_label)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        # Visibility group
        visibility_group = QGroupBox("Visibility")
        visibility_layout = QVBoxLayout()
        
        self.show_hidden_cb = QCheckBox("Show hidden files")
        self.show_hidden_cb.setChecked(self.settings.get("filters", "show_hidden", False))
        visibility_layout.addWidget(self.show_hidden_cb)
        
        visibility_group.setLayout(visibility_layout)
        layout.addWidget(visibility_group)
        
        # Search options group
        search_group = QGroupBox("Search Options")
        search_layout = QVBoxLayout()
        
        self.case_sensitive_cb = QCheckBox("Case-sensitive search")
        self.case_sensitive_cb.setChecked(self.settings.get("filters", "case_sensitive_search", False))
        search_layout.addWidget(self.case_sensitive_cb)
        
        self.regex_search_cb = QCheckBox("Enable regex search")
        self.regex_search_cb.setChecked(self.settings.get("filters", "regex_search", False))
        search_layout.addWidget(self.regex_search_cb)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Recursive browsing group
        recursive_group = QGroupBox("Recursive Browsing")
        recursive_layout = QVBoxLayout()
        
        # Description
        recursive_desc = QLabel(
            "When 'Include Subfolders' is enabled, limit the maximum number of files to load for performance."
        )
        recursive_desc.setWordWrap(True)
        recursive_desc.setStyleSheet("QLabel { color: #888; font-size: 9px; padding: 5px; }")
        recursive_layout.addWidget(recursive_desc)
        
        # Max files spinner
        max_files_layout = QHBoxLayout()
        max_files_layout.addWidget(QLabel("Max files from subfolders:"))
        self.max_recursive_spin = QSpinBox()
        self.max_recursive_spin.setRange(100, 100000)
        self.max_recursive_spin.setSingleStep(1000)
        self.max_recursive_spin.setValue(self.settings.get("filters", "max_recursive_files", 10000))
        self.max_recursive_spin.setSuffix(" files")
        max_files_layout.addWidget(self.max_recursive_spin)
        max_files_layout.addStretch()
        recursive_layout.addLayout(max_files_layout)
        
        recursive_group.setLayout(recursive_layout)
        layout.addWidget(recursive_group)
        
        layout.addStretch()
    
    def update_custom_ext_display(self):
        """Update display of current custom extensions"""
        current_extensions = self.settings.get("filters", "custom_extensions", [])
        if current_extensions:
            ext_text = ", ".join(current_extensions)
            self.custom_ext_label.setText(f"<b>Active custom extensions:</b> {ext_text}")
            self.custom_ext_label.setStyleSheet("QLabel { color: #5dade2; font-size: 9px; padding: 5px; }")
        else:
            self.custom_ext_label.setText("<i>No custom extensions added</i>")
            self.custom_ext_label.setStyleSheet("QLabel { color: #666; font-size: 9px; padding: 5px; }")
    
    def save_settings(self):
        """Save settings from UI to settings manager"""
        # Parse custom extensions from input
        ext_text = self.custom_ext_input.text().strip()
        if ext_text:
            # Split by comma, clean up, and ensure they start with dot
            extensions = []
            for ext in ext_text.split(','):
                ext = ext.strip()
                if ext:
                    # Add dot if missing
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    extensions.append(ext.lower())
            self.settings.set("filters", "custom_extensions", extensions)
        else:
            self.settings.set("filters", "custom_extensions", [])
        
        # Save other settings
        self.settings.set("filters", "show_hidden", self.show_hidden_cb.isChecked())
        self.settings.set("filters", "case_sensitive_search", self.case_sensitive_cb.isChecked())
        self.settings.set("filters", "regex_search", self.regex_search_cb.isChecked())
        self.settings.set("filters", "max_recursive_files", self.max_recursive_spin.value())


class SettingsDialog(QDialog):
    """Main settings dialog with tabs"""
    
    settings_changed = Signal()
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.setWindowTitle("ddContentBrowser Settings")
        self.resize(600, 500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.general_tab = GeneralSettingsTab(self.settings)
        self.thumbnail_tab = ThumbnailSettingsTab(self.settings)
        self.preview_tab = PreviewSettingsTab(self.settings)
        self.filters_tab = FiltersSettingsTab(self.settings)
        
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.thumbnail_tab, "Thumbnails")
        self.tab_widget.addTab(self.preview_tab, "Preview")
        self.tab_widget.addTab(self.filters_tab, "Filters")
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | 
                                      QDialogButtonBox.RestoreDefaults)
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        
        layout.addWidget(button_box)
    
    def accept_settings(self):
        """Save all settings and close dialog"""
        # Save settings from all tabs
        self.general_tab.save_settings()
        self.thumbnail_tab.save_settings()
        self.preview_tab.save_settings()
        self.filters_tab.save_settings()
        
        # Save to disk
        if self.settings.save():
            self.settings_changed.emit()
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings!")
    
    def restore_defaults(self):
        """Restore default settings"""
        reply = QMessageBox.question(self, "Restore Defaults",
                                     "Are you sure you want to restore all settings to default values?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self.settings_changed.emit()
            QMessageBox.information(self, "Success", 
                                   "Settings restored to defaults. Please restart the browser.")
            self.accept()
