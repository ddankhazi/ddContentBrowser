# DD Content Browser v1.0

Professional Maya Asset Browser with advanced features, visual previews, and intuitive workflow.

---

## ✨ Overview

**DD Content Browser** is a modern, feature-rich file browser for Autodesk Maya that replaces the built-in Content Browser with a faster, more intuitive interface. Designed for production environments with large asset libraries.

### Key Highlights:
- 🚀 **Lightning fast** - Instant navigation and search
- 🖼️ **Visual previews** - Thumbnails, image preview, Quick View
- 🎯 **Smart selection** - Box select, multi-select, drag-and-drop
- 📁 **Collections** - Organize assets with virtual folders and color coding
- 🔍 **Advanced filtering** - Type, size, date, tags, and more
- ⚡ **Performance** - Dual cache system, background processing
- 🎨 **Professional UI** - Maya-style interface with dark theme

---

## 🚀 Installation

### Quick Start

The browser is already installed in your Maya scripts directory:
```
C:/Users/[USERNAME]/Documents/maya/2026/scripts/ddContentBrowser/
```

### Launch Methods

**Method 1 - Quick Launch (Recommended):**
```python
from ddContentBrowser.launch_browser import launch
launch()
```

**Method 2 - Script Editor One-Liner:**
```python
exec("from ddContentBrowser.launch_browser import launch; launch()")
```

**Method 3 - Shelf Button:**
1. Open `launch_browser.py` from the package
2. Copy the `launch()` function call
3. **Ctrl+Shift+Drag** to your shelf
4. Optional: Add icon and label

**Method 4 - Hotkey:**
1. Windows → Hotkey Editor → Runtime Command Editor
2. New Command: `DDContentBrowser`
3. Command: `from ddContentBrowser.launch_browser import launch; launch()`
4. Assign hotkey (e.g., `Ctrl+3`)

---

## 📚 Features

### 🗂️ Navigation

- **Breadcrumb Path** - Click any segment to jump to that folder
- **Back/Forward** - Browser-style navigation history (Alt+Left/Right)
- **Recent Paths** - Quick access dropdown (⏱)
- **Favorites** - Star folders for instant access (⭐)
- **Parent Folder** - Backspace or click ".." to go up
- **Path Edit** - Click ⋮ button to manually type path
- **Browse Dialog** - 📁 button to pick folder visually

### 🔍 Search & Filtering

**Quick Search:**
- Type in search box to filter by filename
- Real-time filtering as you type
- Case-insensitive by default

**Advanced Filters (▼ button):**
- **File Types** - Checkboxes for .ma, .mb, .obj, .fbx, .abc, .usd, images
- **Size Range** - Min/max file size in MB
- **Date Range** - Today/Week/Month/Custom date picker
- **Tags** - Autocomplete tag search (79 built-in tags)
- **Show Folders** - Toggle folder visibility
- **Clear All** - Reset all filters instantly

### 📊 View Modes

**Grid View (⊞):**
- Large visual thumbnails (64-256px)
- Drag slider to adjust size
- Perfect for visual assets
- Ctrl+Scroll to zoom

**List View (☰):**
- Compact list with details
- Sortable columns: Name, Size, Date, Type
- Click headers to sort (▲/▼)
- Better for text-based browsing

### 🖱️ Selection & Interaction

**Selection Modes:**
- **Left Click** - Select single item
- **Ctrl+Click** - Toggle selection (add/remove)
- **Shift+Click** - Range selection
- **Left Drag** - Box selection (rubber band)

**Drag & Drop:**
- **Alt+Left Drag** - Standard file drag (Maya viewport import)
- **Middle Drag** - Batch import dialog with options
- **Middle Drag to Collections** - Add files to collection

**Double-Click:**
- Folders → Navigate into
- Files → Import into Maya scene

### 📋 Collections System

**Organize assets without moving files:**
- Create virtual folders (Manual Collections)
- Color-code collections (12 colors)
- Drag files from browser to collections
- Drag collections to import all files
- Persistent across sessions
- Stored in JSON format

**Collection Features:**
- Right-click menu: Rename, Delete, Import All
- Color picker with visual swatches
- 6px colored bar indicator
- Works with favorites and recent paths

### 🖼️ Preview System

**Preview Panel (right side):**
- **Image preview** - JPG, PNG, TIF, HDR, EXR, etc.
- **PDF preview** - View PDF pages (navigate with arrows)
- **Zoom mode** - Click image to enter zoom (scroll to zoom, drag to pan)
- **Metadata** - File info, dimensions, size
- **Background modes** - Dark, light, checkerboard (right-click)
- **HDR/EXR support** - Exposure slider for HDR images
- **8K limit** - Large images auto-scaled with warning

**Quick View (macOS-style):**
- Press **Space** to open floating preview
- Works with multi-select (grid view)
- Pin window to keep open (📌)
- Zoom, pan, and scroll through files
- Arrow keys to navigate
- ESC or Space to close

### ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Quick View (floating preview) |
| `F5` | Refresh current folder |
| `Delete` | Delete selected files (with confirmation) |
| `F2` | Rename selected file |
| `Ctrl+C` | Copy path to clipboard |
| `Ctrl+F` | Focus search box |
| `Enter` | Import selected file |
| `Backspace` | Go to parent folder |
| `Ctrl+Scroll` | Zoom thumbnails (grid mode) |
| `Alt+Left/Right` | Back/Forward navigation |
| `Escape` | Cancel path edit / Close Quick View |
| `Arrow Keys` | Navigate in Quick View |

### 🎬 File Operations

**Import/Reference:**
- Import button - Load assets into scene
- Reference button - Reference Maya files with namespace
- Batch import - Middle-drag for import dialog
- Smart detection - Automatically recognizes file types

**Context Menu (Right-Click):**

*On Files:*
- Import / Reference
- Add to Collection
- Open in Explorer
- Copy Path (Ctrl+C)
- Rename (F2)
- Delete (Del)
- Properties (metadata)

*On Folders:*
- Open Folder
- Add to Favorites
- Open in Explorer
- Copy Path

*On Empty Space:*
- Refresh (F5)
- Paste Path and Navigate
- Add Current Folder to Favorites
- View Options

### 🎨 Visual Features

**Thumbnails:**
- **Maya Files** - Gradient icons (.ma blue, .mb dark blue)
- **3D Files** - Type-specific colors (.obj purple, .fbx yellow, .usd red)
- **Images** - Actual image preview (JPG, PNG, TIF, etc.)
- **HDR/EXR** - Tone-mapped preview
- **PDF** - First page thumbnail
- **Folders** - Folder icon

**Cache System:**
- **Memory cache** - 200 items, instant access (<1ms)
- **Disk cache** - 500MB persistent storage
- **Background generation** - Non-blocking thumbnail creation
- **Smart invalidation** - Auto-refresh on file changes

**Status Info Bar:**
- **Left** - Selection count (e.g., "3 files + 2 folders selected")
- **Right** - Controls hint (LMB/Alt+LMB/MMB usage)
- Real-time updates

---

## 📁 Supported Formats

### Maya Files
- `.ma` - Maya ASCII
- `.mb` - Maya Binary

### 3D Formats
- `.obj` - Wavefront OBJ
- `.fbx` - Autodesk FBX
- `.abc` - Alembic
- `.usd` / `.usda` / `.usdc` - USD/Pixar

### Images
- `.jpg` / `.jpeg` - JPEG
- `.png` - PNG
- `.tif` / `.tiff` - TIFF
- `.tga` - Targa
- `.bmp` - Bitmap
- `.exr` - OpenEXR (HDR)
- `.hdr` - Radiance HDR
- `.psd` - Photoshop (preview only)

### Documents
- `.pdf` - PDF (preview + page navigation)

### Scripts
- `.py` - Python
- `.mel` - MEL script

---

## ⚙️ Configuration

Settings auto-save to:
```
C:/Users/[USERNAME]/.dd_content_browser_config.json
```

### Configurable Settings:
```json
{
  "recent_paths": [],
  "favorites": [],
  "thumbnail_size": 128,
  "view_mode": "grid",
  "show_preview": true,
  "preview_resolution": 2048,
  "cache_size_mb": 500,
  "auto_refresh": true,
  "window_geometry": {...}
}
```

### Clear Cache:
Delete folder: `C:/Users/[USERNAME]/.dd_browser_thumbnails/`

### Reset Settings:
Delete file: `C:/Users/[USERNAME]/.dd_content_browser_config.json`

---

## 🎯 Workflow Tips

### Organizing Assets:
1. Create Collections for projects/asset types
2. Drag files from browser into collections
3. Color-code by project phase (e.g., blue = WIP, green = approved)
4. Use favorites for active project folders

### Fast Navigation:
1. Add frequently used paths to Favorites (⭐)
2. Use Recent Paths dropdown for quick access
3. Middle-click breadcrumb segments to copy path
4. Type path directly with ⋮ button

### Selection Power:
1. Box select (left drag) for rectangular areas
2. Ctrl+Click to add/remove specific items
3. Shift+Click for ranges
4. Select all in folder: Ctrl+A (standard)

### Preview Workflow:
1. Quick preview: Hover mouse + wait
2. Detailed preview: Click item → see in Preview Panel
3. Full screen: Press Space for Quick View
4. Multi-preview: Select multiple → Space → grid view

### Import Strategies:
- **Single file** - Double-click or Enter
- **Multiple files** - Alt+Drag to Maya viewport
- **Batch with options** - Middle-drag outside browser
- **Collection import** - Middle-drag collection

---

## 🔧 Troubleshooting

### Browser won't open
- Check Script Editor for errors
- Verify PySide6 is installed (Maya 2026+)
- Try: `from ddContentBrowser.launch_browser import launch; launch()`

### Thumbnails not showing
- Check if image files exist
- Clear cache: Delete `~/.dd_browser_thumbnails/`
- Restart browser with F5

### Slow performance
- Reduce thumbnail size (drag slider left)
- Use List View instead of Grid
- Enable filters to reduce visible items
- Check if network drive is slow

### Can't delete/rename files
- Check file permissions
- Close file in Maya if open
- Verify file isn't locked

### Quick View crash
- Very large images (>16K) may fail
- Browser auto-scales to 8K max
- Check console for error messages

### Collections not saving
- Check write permissions on `~/.dd_browser_collections.json`
- Verify JSON file isn't corrupted
- Restart browser to force save

---

## 🚀 Performance

### Load Times:
- **100 files:** <100ms (instant)
- **1,000 files:** ~500ms (fast)
- **10,000 files:** ~5s (background loading)

### Memory Usage:
- **Base:** ~50MB
- **+1MB** per 100 thumbnails in memory
- **Disk cache:** 500MB (configurable)

### Optimization:
- Background thumbnail generation
- Lazy loading (only visible items)
- LRU cache eviction
- Image downscaling (8K limit)
- Deferred preview updates

---

## 📊 What's New in v1.0

### Major Features:
✅ **Collections System** - Virtual folders with color coding  
✅ **Quick View** - macOS-style floating preview  
✅ **Advanced Filters** - Type, size, date, tags  
✅ **Zoom Mode** - Full zoom/pan in Preview Panel  
✅ **Box Selection** - Left-drag rubber band select  
✅ **Alt+Drag Import** - Standard file drag-and-drop  
✅ **Info Bar** - Selection count + controls hint  
✅ **8K Image Limit** - Memory protection for large images  
✅ **PDF Support** - Preview and page navigation  
✅ **HDR/EXR** - Exposure control for HDR images  

### UI Improvements:
- Collection color picker (12 colors)
- Status info bar (selection + controls)
- Zoom level indicator with scale warning
- Improved drag-and-drop feedback
- Better keyboard navigation

### Performance:
- Dual cache system (memory + disk)
- Background thumbnail generation
- Image downscaling for large files
- Deferred preview updates
- Smart cache invalidation

---

## 🔮 Roadmap

### Planned Features:
- [ ] Asset metadata extraction (poly count, textures, etc.)
- [ ] Batch operations (rename, convert, export)
- [ ] Version control integration (Git/Perforce)
- [ ] Network path optimization
- [ ] Custom thumbnail generators
- [ ] Asset database integration
- [ ] Theme support (dark/light)
- [ ] Plugin system

---

## 📝 License

Personal/Studio tool. Free to use and modify for your workflow.

---

## 🙏 Credits

**Author:** ddankhazi  
**Version:** 1.0  
**Maya Version:** 2026+ (PySide6)  
**Python:** 3.11+

### Libraries Used:
- PySide6 (Qt for Python)
- Pillow (Image processing)
- OpenCV (Advanced image ops)
- PyMuPDF (PDF rendering)
- OpenEXR (HDR/EXR support)

---

## 💡 Quick Reference

### Mouse Controls:
```
LMB:           Selection
LMB Drag:      Box select (rubber band)
Alt+LMB Drag:  File drag (Maya import)
MMB Drag:      Batch import / Add to collection
RMB:           Context menu
Ctrl+Scroll:   Zoom thumbnails (grid mode)
```

### Keyboard:
```
Space:         Quick View
F5:            Refresh
Del:           Delete
F2:            Rename
Ctrl+C:        Copy path
Ctrl+F:        Search
Enter:         Import
Backspace:     Parent folder
ESC:           Cancel / Close
```

### Info Bar:
```
Left:  "3 files + 2 folders selected"
Right: "💡 LMB: Selection | Alt+LMB+Drag: Standard Import | MMB+Drag: Batch Import"
```

---

**Happy browsing! 🚀✨**

For issues or questions, check the troubleshooting section or review the code comments.
