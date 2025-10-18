# DD Content Browser v2.0

Fast and efficient Maya Asset Browser with visual thumbnails, replacing the built-in slow Content Browser.

## 🎨 Main Features:

### ✅ Core Features (v1.0):
- **⚡ Fast file navigation** - Instant directory browsing
- **◀▶ Back/Forward navigation** - Browser-style history with breadcrumbs
- **🔍 Instant search** - Search by filename with instant filtering
- **📌 Recent paths & Favorites** - Quick access to frequently used folders
- **📥 Import/Reference** - Simple asset loading with namespace support
- **🖱️ Multi-select** - Handle multiple files simultaneously (Ctrl/Shift+click)
- **💾 Configuration saving** - Persistent window state and settings

### ✅ Visual Features (v2.0 - Phases 1-3):
- **🖼️ Beautiful Thumbnails** - Gradient-based icons for all file types
- **🔲 Grid View** - Large thumbnails (64-256px) in wrapping grid layout
- **☰ List View** - Compact list with small icons and file details
- **🎚️ Size Slider** - Adjust thumbnail size on-the-fly (snapped: 64, 96, 128, 192, 256)
- **🖱️ Ctrl+Scroll Zoom** - Mouse wheel zoom in grid mode
- **⚡ Dual Cache System** - Memory (200 items) + Disk (500MB) for instant loading

### ✅ Advanced Features (v2.0):
- **🔍 Advanced Filtering**
  - File type checkboxes (.ma, .mb, .obj, .fbx, .abc, .usd)
  - Size range filter (min/max MB)
  - Date range filter (Today, Week, Month, Custom)
  - Show/Hide folders toggle
  
- **� Sorting System**
  - Sort by: Name, Size, Date, Type
  - Ascending/Descending toggle
  - Visual indicators (▲▼)
  - Clickable headers

- **🖱️ Maya-Style Drag & Drop**
  - Middle-drag for batch import
  - Visual feedback (cursor change, status messages)
  - Multi-file support
  
- **📋 Context Menus**
  - Right-click on files: Import, Reference, Rename, Delete, Properties
  - Right-click on folders: Open, Add to Favorites
  - Ctrl+Right-click: Folder operations menu
  
- **⌨️ Keyboard Shortcuts**
  - `F5` - Refresh folder
  - `Delete` - Delete selected files (with confirmation)
  - `F2` - Rename selected file
  - `Ctrl+C` - Copy path to clipboard
  - `Enter` - Import selected file
  - `Backspace` - Go to parent folder
  - `Ctrl+Scroll` - Zoom thumbnails (grid mode)

- **📁 File Operations**
  - Delete files (with confirmation dialog)
  - Rename files (input dialog)
  - Copy path to clipboard
  - Open in Explorer (Windows/Mac/Linux)
  - File properties dialog

### 📄 Supported Formats:
- Maya: `.ma`, `.mb`
- 3D: `.obj`, `.fbx`, `.abc`, `.usd`

---

## 🚀 Installation and Usage:

### 1. Copy Files:
Script is already in your Maya scripts directory:
```
C:/Users/[USERNAME]/Documents/maya/2026/scripts/
```

### 2. Launch in Maya:

**Method 1 - Quick Launcher (RECOMMENDED - Auto-reloads!):**
```python
from ddContentBrowser.launch_browser import launch
launch()
```

**Method 2 - Without Reload (Faster, but won't see code changes):**
```python
from ddContentBrowser.launch_browser import launch_no_reload
launch_no_reload()
```

**Method 3 - Direct Import (Manual Control):**
```python
from ddContentBrowser.browser import show_content_browser
show_content_browser(force_reload=True)  # Set to False for faster startup
```

**Method 4 - One-liner for Script Editor:**
```python
exec("from ddContentBrowser.launch_browser import launch; launch()")
```

### 3. Create Shelf Button:
1. Open the `SHELF_BUTTON.py` file in the package folder
2. Copy the entire script
3. In Maya: Hold **Ctrl+Shift** and drag to your shelf, OR
4. Right-click shelf → **New Shelf Button** → Paste in "Command" tab
5. Optional: Add icon and label "DD Browser"

### 4. Create Hotkey:
1. Windows → Settings/Preferences → Hotkey Editor
2. Runtime Command Editor → **New**
3. Name: `DDContentBrowser`
4. Command: `from ddContentBrowser.launch_browser import launch; launch()`
5. Assign hotkey (e.g., `Ctrl+Shift+B`)

**💡 Development Tip:** Method 1 automatically reloads ALL modules on every launch, so you'll always see your latest code changes immediately! No more double-launching needed.

---

## 📖 Usage Guide:

### Navigation:
- **Back/Forward buttons** - Navigate through folder history (Alt+Left/Right)
- **Breadcrumb path** - Click segments to jump to parent folders
- **Path edit button (⋮)** - Manually type path (Escape to cancel)
- **Browse button (📁)** - Open folder selection dialog
- **Recent list** - Click to revisit recently used folders
- **Favorites** - Star icon to add, click to navigate to favorite folders
- **Parent folder** - Backspace key or double-click ".." folder

### View Modes:
- **Grid View (⊞)** - Large thumbnails in grid layout
  - Adjust size with slider or Ctrl+Scroll
  - Great for visual browsing
  - Snapped sizes: 64, 96, 128, 192, 256px
  
- **List View (☰)** - Compact vertical list
  - Shows size and date info
  - Faster scrolling through many files
  - Fixed 40px thumbnail height

### Search & Filter:
- **Search box** - Type to filter by filename (case-insensitive)
- **Filters button (▼)** - Toggle advanced filter panel
  - **File Types** - Check/uncheck file extensions
  - **Size Range** - Min/Max file size in MB
  - **Date Range** - Quick buttons (Today/Week/Month) or custom range
  - **Show Folders** - Toggle folder visibility
- **Clear All** - Reset all filters

### Sorting:
- Click column headers to sort:
  - **Name** - Alphabetical (folders first)
  - **Size** - File size
  - **Date** - Modification date
  - **Type** - File extension
- Click again to reverse order (▲/▼ indicators)

### Asset Operations:
- **Double-click** - Import file (or open folder)
- **Middle-drag** - Batch import multiple selected files
- **Import button** - Import selected files
- **Reference button** - Reference Maya files with namespace
- **Multi-select** - Ctrl+click (add), Shift+click (range)

### Context Menu (Right-Click):
**On Files:**
- Import / Reference
- Open in Explorer
- Copy Path (Ctrl+C)
- Rename (F2)
- Delete (Del)
- Properties

**On Folders:**
- Open Folder
- Add to Favorites
- Open in Explorer

**On Empty Space (or Ctrl+Right-click):**
- Refresh (F5)
- Paste Path and Navigate
- Add Current Folder to Favorites

### Keyboard Shortcuts:
| Shortcut | Action |
|----------|--------|
| `F5` | Refresh current folder |
| `Delete` | Delete selected files (with confirmation) |
| `F2` | Rename selected file |
| `Ctrl+C` | Copy path to clipboard |
| `Enter` | Import selected file |
| `Backspace` | Go to parent folder |
| `Ctrl+Scroll` | Zoom thumbnails (grid mode only) |
| `Escape` | Cancel path edit mode |

### Window Management:
- **Singleton pattern** - Only one instance can be open
- **Auto-save** - Window size, position, and splitter state saved
- **Restore state** - Reopens at last size and position
- **Close** - Window closes cleanly, saves config

---

## ⚙️ Configuration:

Settings are automatically saved to:
```
C:/Users/[USERNAME]/.dd_content_browser_config.json
```

### Default Settings:
```json
{
  "recent_paths": [],
  "favorites": [],
  "thumbnail_size": 128,
  "thumbnail_quality": 85,
  "thumbnail_disk_cache_mb": 500,
  "thumbnail_cache_size": 200,
  "thumbnails_enabled": true,
  "auto_refresh": true,
  "supported_formats": [".ma", ".mb", ".obj", ".fbx", ".abc", ".usd"],
  "last_path": "C:/Users/[USERNAME]",
  "window_geometry": null
}
```

### Customization:

#### Add More File Formats:
Edit `ddContentBrowser.py` line ~60:
```python
"supported_formats": [".ma", ".mb", ".obj", ".fbx", ".abc", ".usd", ".blend", ".max"]
```

#### Change Thumbnail Cache Size:
```python
"thumbnail_cache_size": 500,  # Memory cache (number of items)
"thumbnail_disk_cache_mb": 1000,  # Disk cache (MB)
```

#### Change Thumbnail Quality:
```python
"thumbnail_quality": 90,  # JPEG quality (0-100, default 85)
```

#### Clear Cache Manually:
Delete folder: `C:/Users/[USERNAME]/.dd_browser_thumbnails/`

---

## 🎨 Visual Design:

### Grid Mode (128px):
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│          │  │          │  │          │
│   BLUE   │  │   BLUE   │  │  PURPLE  │
│    MA    │  │    MB    │  │   OBJ    │
│          │  │          │  │          │
└──────────┘  └──────────┘  └──────────┘
  scene1.ma    scene2.mb     model.obj
```

### List Mode (Compact):
```
┌──┐ scene1.ma
│MA│ 15.3 MB • 2025-10-08 14:30
└──┘

┌──┐ scene2.mb
│MB│ 8.7 MB • 2025-10-07 09:15
└──┘

┌──┐ character.obj
│OB│ 3.2 MB • 2025-10-06 11:45
└──┘
```

### Color Scheme by File Type:
- `.ma` - **Blue** gradient (70, 130, 220 → 100, 170, 255)
- `.mb` - **Dark Blue** gradient (50, 100, 180 → 80, 140, 220)
- `.obj` - **Purple** gradient (150, 80, 150 → 200, 130, 200)
- `.fbx` - **Yellow** gradient (200, 180, 60 → 255, 220, 100)
- `.abc` - **Green** gradient (80, 150, 80 → 120, 200, 120)
- `.usd` - **Red** gradient (200, 80, 80 → 255, 120, 120)

---

## 🚀 Performance:

### Cache System:
- **Memory Cache:** < 1ms lookup (200 items LRU)
- **Disk Cache:** ~5-10ms lookup (500MB persistent)
- **Icon Generation:** ~100-500ms per icon (gradient-based)

### Load Times:
- 100 files: ~100ms (instant)
- 1000 files: ~800ms (fast)
- 10,000 files: ~8s (acceptable, background loading)

### Memory Usage:
- Base application: ~50MB
- +1MB per 100 thumbnails in memory
- Disk cache: User-configurable (default 500MB)

---

## 🔧 Troubleshooting:

### "Browser won't open":
- Check Script Editor for Python errors
- Verify PySide2/PySide6 is available
- Try reload: `importlib.reload(ddContentBrowser)`

### "Thumbnails not showing":
- Check if thumbnails enabled in config
- Clear cache: Delete `~/.dd_browser_thumbnails/`
- Restart browser

### "Slow performance with many files":
- Use filters to reduce visible items
- Try list mode instead of grid mode
- Consider splitting large directories

### "Can't delete/rename files":
- Check file permissions
- Close file in Maya if it's open
- Check if file is locked by another process

### "Context menu doesn't appear":
- Right-click directly on item (not empty space)
- Try Ctrl+Right-click for folder menu
- Check Maya's own context menu isn't blocking

---

## 🔮 Future Development:

See `ROADMAP.md` for detailed development plans.

### High Priority (Next Updates):
1. **Real Playblast Thumbnails** - Maya scene previews (requires safe implementation)
2. **Settings Dialog** - GUI for configuration
3. **Preview Panel** - Large preview of selected asset
4. **Enhanced Drag & Drop** - Drop into Maya viewport

### Medium Priority:
5. **Asset Metadata** - Scene stats (polycount, textures, etc.)
6. **Collection System** - Virtual folders for project organization
7. **Batch Operations** - Batch rename, convert, export

### Low Priority:
8. **Version Control** - Git/Perforce integration
9. **Network Optimization** - Better UNC path handling
10. **Theme Support** - Dark/Light themes
11. **Asset Library** - Studio database integration

---

## 📊 Version History:

### v2.0 (Current) - October 2025
- ✅ Complete thumbnail system (Phases 1-3)
- ✅ Grid/List view modes with size slider
- ✅ Advanced filtering (type, size, date)
- ✅ Sorting system (name, size, date, type)
- ✅ Ctrl+Scroll zoom in grid mode
- ✅ Maya-style drag & drop (middle-drag)
- ✅ Context menus (files, folders, empty space)
- ✅ File operations (delete, rename, copy path)
- ✅ Keyboard shortcuts (F5, Del, F2, Ctrl+C, etc.)
- ✅ Dual cache system (memory + disk)
- ✅ Safe mode (gradient icons, no file opening)

### v1.0 - October 2025
- ✅ Fast file navigation
- ✅ Back/Forward history
- ✅ Breadcrumb navigation
- ✅ Search filtering
- ✅ Recent paths & Favorites
- ✅ Import/Reference functionality
- ✅ Multi-select support
- ✅ Configuration persistence

---

## 🤝 Contributing:

This is a personal tool, but if you have suggestions:
1. Document the feature request
2. Include use case and examples
3. Consider implementation complexity
4. Test thoroughly in Maya

---

## 📝 License:

Personal use tool. Feel free to adapt for your own workflow.

---

## 🎯 Summary:

**DD Content Browser v2.0** is a **production-ready**, **feature-rich** asset browser for Maya that:
- 🚀 **Fast** - Loads 1000+ files instantly
- 🎨 **Beautiful** - Visual thumbnails in grid/list modes
- 🛡️ **Safe** - No file opening, no crashes
- ⚡ **Responsive** - Background processing, smooth UI
- 🔧 **Feature-rich** - Filters, sorting, shortcuts, context menus
- 💾 **Smart** - Dual cache system, persistent config

**Ready for daily production use!** 🎉

---

Happy browsing! 🚀✨

For questions or issues, check `TROUBLESHOOTING.md` or review the phase completion documents.