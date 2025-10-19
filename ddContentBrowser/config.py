"""
DD Content Browser - Configuration Module
Handles loading and saving user configuration
"""

import json
from pathlib import Path


class ContentBrowserConfig:
    """Configuration manager class"""
    
    def __init__(self):
        # Store config in script directory (version controlled, updates with tool)
        self.script_dir = Path(__file__).parent.resolve()
        self.config_file = self.script_dir / "config.json"
        
        # Get supported formats from central registry
        from .utils import get_all_supported_extensions
        supported_formats = get_all_supported_extensions()
        
        self.default_config = {
            "recent_paths": [],
            "favorites": [],
            "thumbnail_size": 128,
            "thumbnail_quality": 85,
            "thumbnail_disk_cache_mb": 500,
            "thumbnail_cache_size": 2000,  # Increased from 200 to handle large folders
            "thumbnails_enabled": True,
            "auto_refresh": True,
            "supported_formats": supported_formats,  # Now from registry
            "show_images": True,
            "last_path": str(Path.home()),
            "window_geometry": None,
            "view_mode": "grid",  # "grid" or "list"
            "preview_panel_visible": True  # Show preview panel by default
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults for missing keys
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"Configuration load error: {e}")
        return self.default_config.copy()
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Configuration save error: {e}")
    
    def add_recent_path(self, path):
        """Add path to recent paths"""
        path = str(path)
        if path in self.config["recent_paths"]:
            self.config["recent_paths"].remove(path)
        self.config["recent_paths"].insert(0, path)
        # Keep maximum 20 recent paths
        self.config["recent_paths"] = self.config["recent_paths"][:20]
        self.save_config()
