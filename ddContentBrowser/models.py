"""
DD Content Browser - Data Models
Asset representation and file system model

Author: DankHazid
License: MIT
"""

import os
import re
import time
from pathlib import Path
from datetime import datetime

# UI Font - Default value (can be overridden by browser at runtime)
UI_FONT = "Segoe UI"

try:
    from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QMimeData, QUrl
    from PySide6 import QtCore
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt, QMimeData, QUrl
    from PySide2 import QtCore
    PYSIDE_VERSION = 2

# Import file type registry from utils
from .utils import (
    get_extension_category,
    is_extension_supported,
    get_importable_extensions,
    should_generate_thumbnail as utils_should_generate_thumbnail,
    FILE_TYPE_REGISTRY
)

# Debug flag - set to False to disable verbose logging
DEBUG_MODE = False


def natural_sort_key(text):
    """
    Generate a key for natural sorting (handles numbers correctly)
    Example: "file1.jpg", "file2.jpg", "file10.jpg" instead of "file1.jpg", "file10.jpg", "file2.jpg"
    """
    def convert(part):
        return int(part) if part.isdigit() else part.lower()
    
    return [convert(c) for c in re.split(r'(\d+)', text)]


class AssetItem:
    """Asset item representation with lazy stat loading"""
    
    def __init__(self, file_path, lazy_load=False):
        self.file_path = Path(file_path)
        self.name = self.file_path.name
        self.is_folder = self.file_path.is_dir()
        self.extension = "" if self.is_folder else self.file_path.suffix.lower()
        
        # Lazy loading - csak akkor töltjük be a stat infót, ha kell
        self._stat_loaded = False
        self._size = None
        self._modified_time = None
        self._modified = None
        
        # Ha nem lazy load, azonnal betöltjük (backward compatibility)
        if not lazy_load:
            self._load_stat()
        
        # Get category from registry
        self.category = get_extension_category(self.extension) if not self.is_folder else None
        
        # Fájltípus attribútumok - using registry
        self.is_maya_file = self.category == "maya"
        self.is_image_file = self.category == "images"
        self.is_script_file = self.category in ["scripts", "text"]
        self.is_pdf_file = self.category == "pdf"
        self.is_hda_file = self.category == "houdini"
        self.is_blend_file = self.category == "blender"
        self.is_sbsar_file = self.category == "substance"
        
        # Thumbnail generation - using registry
        self.should_generate_thumbnail = not self.is_folder and utils_should_generate_thumbnail(self.extension)
    
    def _load_stat(self):
        """Load file stat info (size, modified time) - called on demand"""
        if self._stat_loaded:
            return
        
        try:
            if self.file_path.exists():
                stat_info = self.file_path.stat()
                self._size = 0 if self.is_folder else stat_info.st_size
                self._modified_time = stat_info.st_mtime
                # Convert to datetime for filtering
                self._modified = datetime.fromtimestamp(stat_info.st_mtime)
            else:
                self._size = 0
                self._modified_time = 0
                self._modified = datetime.fromtimestamp(0)
        except Exception as e:
            # Hálózati hiba esetén alapértékek
            self._size = 0
            self._modified_time = 0
            self._modified = datetime.fromtimestamp(0)
        
        self._stat_loaded = True
    
    @property
    def size(self):
        """Lazy load size on first access"""
        if not self._stat_loaded:
            self._load_stat()
        return self._size
    
    @property
    def modified_time(self):
        """Lazy load modified_time on first access"""
        if not self._stat_loaded:
            self._load_stat()
        return self._modified_time
    
    @property
    def modified(self):
        """Lazy load modified datetime on first access"""
        if not self._stat_loaded:
            self._load_stat()
        return self._modified
        
    def get_display_name(self):
        """Get display name"""
        return self.name
    
    def get_size_string(self):
        """Get size as formatted string"""
        if self.is_folder:
            return "Folder"
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"
    
    def get_modified_string(self):
        """Get modification date as formatted string"""
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(self.modified_time))


class FileSystemModel(QAbstractListModel):
    """File system model for list view"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.assets = []
        self.current_path = None
        self.filter_text = ""
        
        # Base supported formats - from central FILE_TYPE_REGISTRY
        from .utils import get_all_supported_extensions, get_extensions_by_category
        self.base_formats = get_all_supported_extensions()
        self.supported_formats = self.base_formats.copy()
        self.custom_extensions = []  # User-defined custom extensions
        
        # Get specific format categories from registry
        self.image_formats = get_extensions_by_category('images')
        self.script_formats = get_extensions_by_category('scripts') + get_extensions_by_category('text')
        
        # Search options
        self.case_sensitive_search = False
        self.regex_search = False
        
        # Advanced filters
        self.filter_file_types = []  # Empty = all types
        self.filter_min_size = 0  # Bytes
        self.filter_max_size = 0  # 0 = no limit
        self.filter_date_from = None  # datetime or None
        self.filter_date_to = None  # datetime or None
        self.show_folders = True
        self.show_images = True  # Show image files by default
        self.show_scripts = True  # Show script files by default
        self.collection_filter = []  # Collection filter (list of file paths)
        
        # Collection mode - when active, show collection files instead of directory
        self.collection_mode = False
        self.collection_files = []  # List of file paths to display in collection mode
        
        # Sorting
        self.sort_column = "name"  # "name", "size", "date", "type"
        self.sort_ascending = True
        
        # Recursive subfolder browsing
        self.include_subfolders = False
        self.max_recursive_files = 10000  # Limit for performance
        
        # Directory cache system - cache AssetItem objects instead of Path objects
        self._dir_cache = {}  # {path_str: {'assets': [AssetItem], 'timestamp': float, 'mtime': float}}
        self._cache_max_size = 20  # Maximum number of cached directories
        self._cache_ttl = 300  # Cache time-to-live in seconds (5 minutes)
        self._cache_enabled = True
    
    def set_custom_extensions(self, extensions):
        """Set custom file extensions to support
        Args:
            extensions: List of extension strings (e.g. ['.gltf', '.blend'])
        """
        self.custom_extensions = [ext.lower() for ext in extensions if ext.startswith('.')]
        # Rebuild supported formats with base + custom
        self.supported_formats = self.base_formats + self.custom_extensions
        print(f"[FileSystemModel] Custom extensions added: {self.custom_extensions}")
        print(f"[FileSystemModel] Total supported formats: {len(self.supported_formats)}")
    
    def _get_dir_mtime(self, path):
        """Get directory modification time"""
        try:
            return path.stat().st_mtime
        except:
            return 0
    
    def _is_cache_valid(self, path_str, current_mtime):
        """Check if cached data is still valid"""
        if not self._cache_enabled or path_str not in self._dir_cache:
            return False
        
        cache_entry = self._dir_cache[path_str]
        cache_age = time.time() - cache_entry['timestamp']
        
        # Check if cache expired or directory was modified
        if cache_age > self._cache_ttl:
            return False
        if cache_entry['mtime'] != current_mtime:
            return False
        
        return True
    
    def _add_to_cache(self, path_str, assets, mtime):
        """Add directory listing to cache (stores AssetItem objects)"""
        if not self._cache_enabled:
            return
        
        # Remove oldest entry if cache is full
        if len(self._dir_cache) >= self._cache_max_size:
            oldest_key = min(self._dir_cache.keys(), 
                           key=lambda k: self._dir_cache[k]['timestamp'])
            del self._dir_cache[oldest_key]
            if DEBUG_MODE:
                print(f"[CACHE] Removed oldest cache entry: {oldest_key}")
        
        self._dir_cache[path_str] = {
            'assets': assets.copy(),  # Cache the AssetItem objects
            'timestamp': time.time(),
            'mtime': mtime
        }
        if DEBUG_MODE:
            print(f"[CACHE] Added to cache: {path_str} ({len(assets)} assets)")
    
    def _get_from_cache(self, path_str):
        """Get cached AssetItem objects"""
        if path_str in self._dir_cache:
            return self._dir_cache[path_str]['assets'].copy()
        return None
    
    def clear_cache(self):
        """Clear all cached directory data"""
        self._dir_cache.clear()
        if DEBUG_MODE:
            print("[CACHE] Cache cleared")
    
    def set_cache_enabled(self, enabled):
        """Enable or disable caching"""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
        if DEBUG_MODE:
            print(f"[CACHE] Caching {'enabled' if enabled else 'disabled'}")
    
    def setPath(self, path):
        """Set current path"""
        self.beginResetModel()
        self.current_path = Path(path)
        self.refresh()
        self.endResetModel()
    
    def refresh(self, force=False):
        """Refresh file list
        Args:
            force: If True, bypass cache and reload from filesystem
        """
        # Collection mode - load files from collection list instead of directory
        if self.collection_mode:
            self._load_collection_files()
            return
        
        if not self.current_path or not self.current_path.exists():
            self.assets = []
            return
        
        # Check cache first (only for non-recursive mode)
        path_str = str(self.current_path)
        current_mtime = self._get_dir_mtime(self.current_path)
        
        cached_assets = None
        if not force and not self.include_subfolders and self._is_cache_valid(path_str, current_mtime):
            cached_assets = self._get_from_cache(path_str)
        
        try:
            all_items = []
            
            if self.include_subfolders:
                # Recursive mode - collect files from all subfolders
                file_count = 0
                
                for root, dirs, files in os.walk(self.current_path):
                    root_path = Path(root)
                    
                    # Add folders if enabled
                    if self.show_folders and root == str(self.current_path):
                        # Only show direct subfolders (not nested)
                        for dir_name in dirs:
                            if not dir_name.startswith('.'):
                                all_items.append(root_path / dir_name)
                    
                    # Add files
                    for file_name in files:
                        file_path = root_path / file_name
                        
                        # Check if extension is supported
                        ext = file_path.suffix.lower()
                        if ext in self.supported_formats:
                            # Check file type filters
                            if self.filter_file_types and ext not in self.filter_file_types:
                                continue
                            
                            all_items.append(file_path)
                            file_count += 1
                            
                            # Safety limit
                            if file_count >= self.max_recursive_files:
                                print(f"[FileSystemModel] Recursive limit reached: {self.max_recursive_files} files")
                                break
                    
                    if file_count >= self.max_recursive_files:
                        break
            else:
                # Normal mode - only current folder
                
                # Check if we have cached AssetItem objects
                if cached_assets is not None:
                    # Use cached AssetItem objects but still apply ALL filters!
                    
                    # Check if we need stat info for size/date filtering
                    needs_stat_for_filter = (
                        self.filter_min_size > 0 or 
                        self.filter_max_size > 0 or 
                        self.filter_date_from is not None or 
                        self.filter_date_to is not None
                    )
                    
                    # Load stat info if needed
                    if needs_stat_for_filter:
                        for asset in cached_assets:
                            if not asset.is_folder:
                                asset._load_stat()
                    
                    filtered_assets = []
                    for asset in cached_assets:
                        # Apply folder visibility filter
                        if asset.is_folder:
                            if self.show_folders:
                                filtered_assets.append(asset)
                            continue
                        
                        # Apply file type filter
                        ext = asset.extension
                        if self.filter_file_types:
                            # Only specific types
                            if ext not in self.filter_file_types:
                                continue
                            if ext not in self.supported_formats:
                                continue
                        else:
                            # All supported types
                            if ext not in self.supported_formats:
                                continue
                        
                        # Apply show_images filter
                        if asset.is_image_file and not self.show_images:
                            continue
                        
                        # Apply show_scripts filter
                        if asset.is_script_file and not self.show_scripts:
                            continue
                        
                        # Apply size filter
                        if self.filter_min_size > 0 or self.filter_max_size > 0:
                            size = asset.size
                            if self.filter_min_size > 0 and size < self.filter_min_size:
                                continue
                            if self.filter_max_size > 0 and size > self.filter_max_size:
                                continue
                        
                        # Apply date filter
                        if self.filter_date_from or self.filter_date_to:
                            mod_time = asset.modified
                            if self.filter_date_from and mod_time < self.filter_date_from:
                                continue
                            if self.filter_date_to and mod_time > self.filter_date_to:
                                continue
                        
                        # Apply search filter
                        if self.filter_text:
                            if not self._matches_search(asset.name, self.filter_text):
                                continue
                        
                        filtered_assets.append(asset)
                    
                    self.assets = filtered_assets
                else:
                    # No cache - load from filesystem using os.scandir() for maximum performance
                    # scandir() returns DirEntry objects with cached stat info (1 filesystem call!)
                    all_items = []
                    
                    # Use os.scandir() - much faster than iterdir() + glob()
                    # DirEntry.is_dir() uses cached data from the initial scandir() call
                    for entry in os.scandir(self.current_path):
                        # Skip hidden files/folders (starting with .)
                        if entry.name.startswith('.'):
                            continue
                        
                        # Check if it's a directory
                        try:
                            is_directory = entry.is_dir(follow_symlinks=False)
                        except OSError:
                            # Handle permission errors or broken symlinks
                            continue
                        
                        if is_directory:
                            # Add folder if folders are enabled
                            if self.show_folders:
                                all_items.append(Path(entry.path))
                        else:
                            # Check file extension
                            ext = Path(entry.name).suffix.lower()
                            
                            # Apply file type filters
                            if self.filter_file_types:
                                # Only specific types
                                if ext in self.filter_file_types and ext in self.supported_formats:
                                    all_items.append(Path(entry.path))
                            else:
                                # All supported types
                                if ext in self.supported_formats:
                                    all_items.append(Path(entry.path))
            
            # Only process if we didn't use cache
            if cached_assets is None:
                # Filter based on search text
                if self.filter_text:
                    all_items = [f for f in all_items if self._matches_search(f.name, self.filter_text)]
                
                # Convert to AssetItem objects with LAZY LOADING
                self.assets = [AssetItem(f, lazy_load=True) for f in all_items]
                
                # Apply advanced filters
                # Ellenőrizzük, hogy kell-e stat info (méret/dátum szűrés)
                needs_stat_for_filter = (
                    self.filter_min_size > 0 or 
                    self.filter_max_size > 0 or 
                    self.filter_date_from is not None or 
                    self.filter_date_to is not None
                )
                
                # Ha kell stat info szűréshez, batch-ben töltjük be
                if needs_stat_for_filter:
                    for asset in self.assets:
                        if not asset.is_folder:  # Csak fájlokhoz kell
                            asset._load_stat()
                
                filtered_assets = []
                for asset in self.assets:
                    # Check if folders should be shown
                    if asset.is_folder:
                        if self.show_folders:
                            filtered_assets.append(asset)
                        continue
                    
                    # Check if images should be shown
                    if asset.is_image_file and not self.show_images:
                        continue
                    
                    # Check if scripts should be shown
                    if asset.is_script_file and not self.show_scripts:
                        continue
                    
                    # Size filter (for files only) - már be van töltve ha kell
                    if self.filter_min_size > 0 and asset.size < self.filter_min_size:
                        continue
                    if self.filter_max_size > 0 and asset.size > self.filter_max_size:
                        continue
                    
                    # Date filter (for files only) - már be van töltve ha kell
                    if self.filter_date_from and asset.modified < self.filter_date_from:
                        continue
                    if self.filter_date_to and asset.modified > self.filter_date_to:
                        continue
                    
                    filtered_assets.append(asset)
                
                self.assets = filtered_assets
            
            # Apply sorting
            self._sort_assets()
            
            # Add to cache AFTER filtering and sorting (only if we loaded from filesystem)
            if cached_assets is None:
                self._add_to_cache(path_str, self.assets, current_mtime)
            
        except Exception as e:
            print(f"File loading error: {e}")
            self.assets = []
    
    def _sort_assets(self):
        """Sort assets based on current sort settings"""
        # Batch load stat info if sorting by size or date
        if self.sort_column in ["size", "date"]:
            for asset in self.assets:
                if not asset.is_folder:
                    asset._load_stat()
        
        if self.sort_column == "name":
            # Natural sorting: 1, 2, 10 instead of 1, 10, 2
            self.assets.sort(key=lambda x: (not x.is_folder, natural_sort_key(x.name)), reverse=not self.sort_ascending)
        elif self.sort_column == "size":
            self.assets.sort(key=lambda x: (not x.is_folder, x.size), reverse=not self.sort_ascending)
        elif self.sort_column == "date":
            self.assets.sort(key=lambda x: (not x.is_folder, x.modified), reverse=not self.sort_ascending)
        elif self.sort_column == "type":
            self.assets.sort(key=lambda x: (not x.is_folder, x.extension.lower()), reverse=not self.sort_ascending)
    
    def _matches_search(self, filename, search_text):
        """
        Check if filename matches search text
        Supports case-sensitive and regex search based on settings
        """
        if self.regex_search:
            # Regex search
            try:
                import re
                flags = 0 if self.case_sensitive_search else re.IGNORECASE
                return bool(re.search(search_text, filename, flags))
            except re.error:
                # Invalid regex - fall back to plain text search
                pass
        
        # Plain text search
        if self.case_sensitive_search:
            return search_text in filename
        else:
            return search_text.lower() in filename.lower()
    
    def setSortOrder(self, column, ascending=True):
        """Set sort order"""
        self.beginResetModel()
        self.sort_column = column
        self.sort_ascending = ascending
        self._sort_assets()
        self.endResetModel()
    
    def setFilterText(self, text):
        """Set filter text"""
        if self.filter_text != text:
            self.beginResetModel()
            self.filter_text = text
            self.refresh()
            self.endResetModel()
    
    def setFilterFileTypes(self, types):
        """Set file type filter - list of extensions like ['.ma', '.mb']"""
        print(f"[DEBUG] setFilterFileTypes called with: {types}")
        print(f"[DEBUG] Current assets count: {len(self.assets)}")
        self.beginResetModel()
        self.filter_file_types = types
        self.refresh()  # Filters are now properly applied to cached assets
        print(f"[DEBUG] After refresh, assets count: {len(self.assets)}")
        self.endResetModel()
    
    def setFilterSize(self, min_size=0, max_size=0):
        """Set size filter in bytes"""
        self.beginResetModel()
        self.filter_min_size = min_size
        self.filter_max_size = max_size
        self.refresh()  # Filters are now properly applied to cached assets
        self.endResetModel()
    
    def setFilterDate(self, date_from=None, date_to=None):
        """Set date filter - datetime objects"""
        self.beginResetModel()
        self.filter_date_from = date_from
        self.filter_date_to = date_to
        self.refresh()  # Filters are now properly applied to cached assets
        self.endResetModel()
    
    def setShowFolders(self, show):
        """Toggle folder visibility"""
        self.beginResetModel()
        self.show_folders = show
        self.refresh()  # Filters are now properly applied to cached assets
        self.endResetModel()
    
    def setShowImages(self, show):
        """Toggle image file visibility"""
        self.beginResetModel()
        self.show_images = show
        self.refresh()  # Filters are now properly applied to cached assets
        self.endResetModel()
    
    def setShowScripts(self, show):
        """Toggle script file visibility"""
        self.beginResetModel()
        self.show_scripts = show
        self.refresh()  # Filters are now properly applied to cached assets
        self.endResetModel()
    
    def clearFilters(self):
        """Clear all advanced filters"""
        self.beginResetModel()
        self.filter_file_types = []
        self.filter_min_size = 0
        self.filter_max_size = 0
        self.filter_date_from = None
        self.filter_date_to = None
        self.show_folders = True
        self.show_images = True
        self.show_scripts = True
        self.refresh()  # Filters are now properly applied to cached assets
        self.endResetModel()
    
    def setCollectionFilter(self, file_paths):
        """Switch to collection mode and show only collection files"""
        self.beginResetModel()
        self.collection_mode = True
        self.collection_files = [str(Path(p).resolve()) for p in file_paths]
        self.refresh()
        self.endResetModel()
    
    def clearCollectionFilter(self):
        """Exit collection mode and return to normal directory browsing"""
        self.beginResetModel()
        self.collection_mode = False
        self.collection_files = []
        self.refresh()
        self.endResetModel()
    
    def _load_collection_files(self):
        """Load files from collection list (collection mode)"""
        try:
            all_assets = []
            
            # Load each file from collection
            for file_path_str in self.collection_files:
                file_path = Path(file_path_str)
                
                # Check if file exists
                if not file_path.exists():
                    continue
                if not file_path.is_file():
                    continue
                
                # Check if extension is supported
                ext = file_path.suffix.lower()
                if ext not in self.supported_formats:
                    continue
                
                # Check file type filters
                if self.filter_file_types and ext not in self.filter_file_types:
                    continue
                
                # Create AssetItem
                try:
                    asset = AssetItem(file_path, lazy_load=False)
                    
                    # Apply size filter
                    if self.filter_min_size > 0 and asset.size < self.filter_min_size:
                        continue
                    if self.filter_max_size > 0 and asset.size > self.filter_max_size:
                        continue
                    
                    # Apply date filter
                    if self.filter_date_from and asset.modified < self.filter_date_from:
                        continue
                    if self.filter_date_to and asset.modified > self.filter_date_to:
                        continue
                    
                    all_assets.append(asset)
                    
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"[Collection] Error loading {file_path}: {e}")
                    continue
            
            self.assets = all_assets
            
            # Apply sorting
            self._sort_assets()
        
        except Exception as e:
            print(f"[Collection] Load error: {e}")
            import traceback
            traceback.print_exc()
            self.assets = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.assets)
    
    def columnCount(self, parent=QModelIndex()):
        """Return number of columns: Name, Size, Date, Type"""
        return 4
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header labels for columns"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["Name", "Size", "Date Modified", "Type"]
            if section < len(headers):
                return headers[section]
        return None
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.assets):
            return None
        
        asset = self.assets[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Name
                return asset.get_display_name()
            elif column == 1:  # Size
                return asset.get_size_string()
            elif column == 2:  # Date Modified
                return asset.get_modified_string()
            elif column == 3:  # Type
                if asset.is_folder:
                    return "Folder"
                elif asset.extension:
                    return asset.extension.upper()[1:]  # Remove dot, uppercase
                else:
                    return ""
        elif role == Qt.ToolTipRole and column == 0:
            # Rich HTML tooltip with dark theme
            icon = "📁" if asset.is_folder else "📄"
            
            # Type and color
            if asset.is_folder:
                file_type = "Folder"
                color = "#FFA726"  # Orange
            elif asset.is_maya_file:
                file_type = f"{asset.extension.upper()[1:]} Maya Scene"
                color = "#42A5F5"  # Light Blue
            else:
                file_type = f"{asset.extension.upper()[1:]} File" if asset.extension else "Unknown"
                color = "#aaa"  # Light Gray
            
            # Truncate path if too long
            path_str = str(asset.file_path.parent)
            if len(path_str) > 50:
                path_str = "..." + path_str[-47:]
            
            # Build HTML tooltip for dark background - single line layout
            html = f"""
            <div style="font-family: '{UI_FONT}', Arial, sans-serif; white-space: nowrap;">
                <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: bold; color: {color};">
                    {icon} {asset.name}
                </p>
                <div style="border-top: 1px solid #555; padding-top: 6px;">
                    <div style="margin: 2px 0;"><span style="color: #999;">📍 Path:</span> <span style="color: #ddd;">{path_str}</span></div>
                    <div style="margin: 2px 0;"><span style="color: #999;">📦 Type:</span> <span style="color: {color}; font-weight: bold;">{file_type}</span></div>
                    <div style="margin: 2px 0;"><span style="color: #999;">📊 Size:</span> <span style="color: #ddd; font-weight: bold;">{asset.get_size_string()}</span></div>
                    <div style="margin: 2px 0;"><span style="color: #999;">📅 Modified:</span> <span style="color: #ddd; font-weight: bold;">{asset.get_modified_string()}</span></div>
                </div>
            </div>
            """
            return html.strip()
        elif role == Qt.UserRole:
            return asset
        
        return None
    
    def flags(self, index):
        """Return item flags for drag & drop support"""
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled
        return default_flags | Qt.ItemIsDropEnabled
    
    def supportedDragActions(self):
        """Return supported drag actions"""
        return Qt.CopyAction | Qt.MoveAction
    
    def supportedDropActions(self):
        """Return supported drop actions"""
        return Qt.CopyAction | Qt.MoveAction
    
    def mimeTypes(self):
        """Return supported MIME types"""
        return ['text/plain', 'text/uri-list']
    
    def mimeData(self, indexes):
        """Create MIME data for drag operation with MEL batch import command"""
        mime_data = QMimeData()
        urls = []
        paths = []
        assets = []
        
        for index in indexes:
            if index.isValid():
                asset = self.data(index, Qt.UserRole)
                if asset and not asset.is_folder:
                    url = QUrl.fromLocalFile(str(asset.file_path))
                    urls.append(url)
                    paths.append(str(asset.file_path))
                    assets.append(asset)
        
        if paths:
            # For Maya: Generate MEL/Python command for batch import
            if len(paths) == 1:
                # Single file - generate appropriate command based on file type
                asset = assets[0]
                escaped_path = paths[0].replace('\\', '/')
                
                if asset.is_sbsar_file:
                    # Substance Archive - create substance texture node
                    mel_cmd = f'python("import maya.cmds as cmds; '
                    mel_cmd += f'try:\\n'
                    mel_cmd += f'    if not cmds.pluginInfo(\'substance\', query=True, loaded=True): cmds.loadPlugin(\'substance\')\\n'
                    mel_cmd += f'except: pass\\n'
                    mel_cmd += f'substance_node = cmds.shadingNode(\'substance\', asTexture=True)\\n'
                    mel_cmd += f'cmds.setAttr(substance_node + \'.filePath\', r\'{escaped_path}\', type=\'string\')\\n'
                    mel_cmd += f'print(\'Substance texture created: \' + substance_node)");'
                else:
                    # Regular Maya file import
                    mel_cmd = f'file -import -type "mayaAscii" -ignoreVersion -mergeNamespacesOnClash false -namespace ":" -options "v=0;" -preserveReferences "{escaped_path}";'
            else:
                # Multiple files - generate Python code for batch import
                mel_cmd = "python(\"import maya.cmds as cmds\\n"
                for i, path in enumerate(paths):
                    asset = assets[i]
                    escaped_path = path.replace('\\', '/').replace('"', '\\"')
                    
                    if asset.is_sbsar_file:
                        # Substance files
                        mel_cmd += f"try:\\n"
                        mel_cmd += f"    if not cmds.pluginInfo('substance', query=True, loaded=True): cmds.loadPlugin('substance')\\n"
                        mel_cmd += f"except: pass\\n"
                        mel_cmd += f"substance_node = cmds.shadingNode('substance', asTexture=True)\\n"
                        mel_cmd += f"cmds.setAttr(substance_node + '.filePath', r'{escaped_path}', type='string')\\n"
                    else:
                        # Regular files
                        mel_cmd += f"cmds.file(r'{escaped_path}', i=True, ignoreVersion=True, mergeNamespacesOnClash=False, namespace=':', options='v=0', preserveReferences=True)\\n"
                mel_cmd += "\");"
            
            # Set as plain text (Maya Script Editor and viewport accept this)
            mime_data.setText(mel_cmd)
            
            # Also set URLs for compatibility
            mime_data.setUrls(urls)
        
        return mime_data
    
    def canDropMimeData(self, data, action, row, column, parent):
        """Check if we can accept the drop"""
        if not data.hasUrls():
            return False
        return True
    
    def dropMimeData(self, data, action, row, column, parent):
        """Handle drop event - navigate to folder if a folder is dropped"""
        if not data.hasUrls():
            return False
        
        # Get first URL
        urls = data.urls()
        if urls:
            file_path = Path(urls[0].toLocalFile())
            
            # If it's a folder, navigate to it
            if file_path.exists() and file_path.is_dir():
                self.setPath(file_path)
                return True
            # If it's a file, navigate to its parent folder
            elif file_path.exists() and file_path.is_file():
                self.setPath(file_path.parent)
                return True
        
        return False
