
# DD Content Browser v1.0

Content Browser for Maya by Denes Dankhazi
Modern Maya Asset Browser for Autodesk Maya 2025+ (PySide6, Python 3.11+)

---

## ✨ Overview

DD Content Browser is a high-performance, feature-rich asset browser for Maya, designed for large production environments. It replaces the built-in browser with a fast, intuitive, and visually advanced interface.

---


## 🚀 How to Install and Launch

### Installation

1. Copy the full content into your Maya scripts folder:  
	 `C:/Users/%USERPROFILE%/Documents/maya/2026/scripts/ddContentBrowser`

### Launch from Maya (Python):

```python
from ddContentBrowser.launch_browser import launch_no_reload
launch_no_reload()
```

### Portable Launcher

- Install Python 3.11 if you don't have it yet.
- For the first launch use: `launch_standalone_portable.bat`  
	(This will install PySide6 if you don't have it.)
- After that you can use the silent launcher: `ddContentBrowser.pyw`

Cheers, D

---

## 📚 Main Features

### Navigation & Browsing
- Breadcrumb navigation, favorites, recent paths
- Fast folder switching, manual path entry, browse dialog
- Back/forward navigation

### File Operations
- Import, reference, delete, rename (single & batch)
- Batch import dialog (middle mouse drag)
- Batch rename dialog (multi-select + context menu)
- Drag & drop to Maya viewport, collections, or folders

### Search & Filtering
- Quick search (filename, real-time)
- Advanced filters: type, size, date, tags, show folders/images/scripts
- Multi-tag autocomplete, custom date picker, clear/reset all filters

### View Modes
- Grid view: scalable thumbnails (64-256px), zoom (Ctrl+Scroll)
- List view: sortable columns (name, size, date, type)
- Quick View: floating preview (Space), multi-preview, zoom/pan

### Selection & Interaction
- Box select, multi-select, range select, Ctrl+Click, Shift+Click
- Context menu (right-click): import, reference, add to collection, open in explorer, copy path, rename, delete, properties

### Collections System
- Virtual folders, color coding (12 colors)
- Drag files to collections, drag collections to import all
- Persistent (JSON), right-click: rename, delete, import all

### Preview System
- Preview panel: image (JPG, PNG, TIF, HDR, EXR), PDF (page navigation), metadata
- HDR/EXR: exposure slider, auto-downscale (8K limit)
- Background modes: dark, light, checkerboard
- Quick View: Space to open, multi-select grid, zoom/pan, arrow navigation

### Batch Operations
- Batch import (middle mouse drag)
- Batch rename (multi-select + context menu)

### Cache & Performance
- Memory cache (200 items), disk cache (500MB, configurable)
- Background thumbnail generation, lazy loading, LRU cache
- Auto-refresh, smart invalidation

### Settings & Configuration
- All settings are auto-saved to:  
	`%USERPROFILE%/.ddContentBrowser/settings.json`
- Configurable options include: startup directory, window size/position, UI font, confirm delete, auto-refresh, refresh interval, thumbnail size/quality/cache, preview resolution/exposure, filter options, sorting, etc.
- To reset all settings: use the GUI reset option or delete the settings.json file above.
- Thumbnail cache is stored in:  
	`%USERPROFILE%/.ddContentBrowser/thumbnails`  
	(Can be cleared from the GUI or by deleting this folder.)
- Tag assignments can be cleared separately from the settings dialog (tag names are preserved).

### Supported Formats
- Maya: `.ma`, `.mb`
- 3D: `.obj`, `.fbx`, `.abc`, `.usd`, `.usda`, `.usdc`
- Images: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.tga`, `.bmp`, `.exr`, `.hdr`, `.psd`
- Documents: `.pdf`
- Scripts: `.py`, `.mel`

### External Libraries
- PySide6 (Qt for Python)
- Pillow (Image processing)
- OpenCV (Advanced image ops)
- PyMuPDF (PDF rendering)
- OpenEXR (HDR/EXR support)
- NumPy (Maya 2025+)

---

## ⌨️ Keyboard Shortcuts

| Shortcut      | Action                                  |
|-------------- |-----------------------------------------|
| Space         | Quick View (floating preview)           |
| F5            | Refresh current folder                  |
| Delete        | Delete selected files (confirmation)    |
| F2            | Rename selected file                    |
| Ctrl+F        | Focus search box                        |
| Ctrl+C        | Copy path to clipboard                  |
| Enter         | Import selected file                    |
| Backspace     | Go to parent folder                     |
| Ctrl+Scroll   | Zoom thumbnails                         |
| Alt+Left/Right| Back/Forward navigation                 |
| Escape        | Cancel path edit / Close Quick View     |
| Arrow Keys    | Navigation                              |

---

## 🖱️ Mouse Controls

| Control         | Action                                 |
|-----------------|----------------------------------------|
| LMB             | Selection                              |
| LMB Drag        | Box select (rubber band)               |
| Alt+LMB Drag    | File drag (Maya import)                |
| MMB Drag        | Batch import / Add to collection       |
| RMB             | Context menu                           |
| Ctrl+Scroll     | Zoom thumbnails                        |

---

## 🎨 Visual Features

- Maya/3D/image/document/script/folder thumbnails
- Type-specific colors, gradient icons, actual image preview
- HDR/EXR tone-mapped preview, PDF first page thumbnail
- Status info bar: selection count, controls hint

---

## 🚀 Performance

- 100 files: <100ms
- 1,000 files: ~500ms
- 10,000 files: ~5s (background loading)
- Memory: ~50MB base, +1MB/100 thumbnails
- Disk cache: 500MB (configurable)
- Optimizations: background thumbnail generation, lazy loading, LRU cache, deferred preview

---

## 📝 License

This tool is free for personal and studio use.
You may modify, copy, and integrate it into your workflow.
No warranty or liability is provided.
Commercial redistribution is not permitted without the author's permission.

---

## 🙏 Credits

**Author:** ddankhazi
**Version:** 1.0
**Maya Version:** 2025+ (PySide6)
**Python:** 3.11+

---

**Happy browsing! 🚀✨**
