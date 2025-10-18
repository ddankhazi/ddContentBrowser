# DD Content Browser - Current Status

**Version:** 2.5.0-dev (Tag System Complete + Advanced Filters Integration!)  
**Status:** � Development - Tag System Basic Integration Working!  
**Last Updated:** October 18, 2025

------

## 📊 Project Overview

DD Content Browser is a **fast, visual asset browser** for Autodesk Maya featuring advanced HDR/EXR preview, exposure control, 16/32-bit TIFF support, and Maya-style workflow integration.

**Current Development:** Tag System (v3.0 Phase 2) - ✅ **Phase 1 & 2 Complete!** Tag management + Advanced Filters integration working with SQLite backend!

------

## 🔥 Latest Updates (v2.5.0-dev) - October 18, 2025

### UI Enhancement: Dark Theme Unification 🎨
**Completion Date:** October 18, 2025 (Today - Evening!)

#### What's New:

1. **✅ Maya-Style Dark Theme for Standalone** - Professional appearance
   - Applied comprehensive Qt StyleSheet to standalone launcher
   - Maya-like color palette (#444444, #3c3c3c, #2a2a2a)
   - Consistent with Maya version styling
   - Blue accent color (#0078d4) for highlights and active elements

2. **✅ Enhanced Tab Styling** - Modern UI polish
   - Active tabs now feature blue bottom border (2px solid #0078d4)
   - Hover effects on tabs, buttons, and interactive elements
   - Professional scrollbar styling (14px width, rounded handles)
   - Splitter handles with hover highlight

3. **✅ Unified Theme Across Versions** - Consistent look and feel
   - Standalone version matches Maya plugin appearance
   - Same stylesheet applied to both `standalone_launcher_home.py` and `browser.py`
   - All UI elements (menus, buttons, inputs, checkboxes) themed consistently

**Visual Improvements:**
- QTabBar tabs with blue underline when selected
- Smooth hover transitions on all interactive elements
- Consistent color scheme across all panels
- Professional dark theme matching industry standards

**Files Modified:**
- ✅ `standalone_launcher_home.py` - Added comprehensive Maya-style stylesheet
- ✅ `browser.py` - Replaced tooltip-only stylesheet with full theme

**User Experience:**
- Standalone version now looks identical to Maya plugin
- More polished, professional appearance
- Better visual feedback on interactive elements
- Consistent with Maya 2026 dark theme

---

### Tag System - Phase 2: Advanced Filters Integration Complete! 🏷️🔍✨
**Completion Date:** October 18, 2025 (Today - Earlier!)

#### What's New Today:

1. **✅ Tags Category in Advanced Filters** - Full integration
   - Tag filtering with file usage counts (e.g., "painting (49)")
   - OR logic within Tags category (match ANY selected tag)
   - AND logic across different filter categories
   - Real-time filtering as you check/uncheck tags
   - MetadataManager integration for database queries

2. **✅ UI Improvements**
   - Dimensions category collapsed by default for cleaner UI
   - Attempted Maya-style drag selection on checkboxes (deferred for technical reasons)
   - Fixed event handling (Qt event type constants)

3. **✅ Bug Fixes**
   - Fixed AttributeError: get_file_tags() → get_file_metadata()
   - Fixed Maya crash from incorrect event type access
   - Removed drag selection feature (requires global event tracking)

#### Technical Implementation:

```python
# How Tag Filtering Works:

1. User opens Advanced Filters panel
2. "Analyze Folder" scans current directory files
3. Tags category populated with all tags found in files
   - Shows tag name + count (e.g., "environment (23)")
4. User selects tags to filter by
5. Files filtered instantly:
   - File matches if it has ANY of the selected tags (OR logic)
   - Must also match other active filters (AND logic across categories)
6. File list updates in real-time
```

**Filter Categories Available:**
- File Type (MA, MB, OBJ, FBX, etc.)
- Category (3D Model, Image, etc.)
- File Size (MB ranges)
- **✨ Tags** (from database)
- Dimensions (collapsed by default)
- Aspect Ratio
- Color Mode (RGB, RGBA, Grayscale)
- Bit Depth (8-bit, 16-bit, 32-bit)

**Files Modified:**
- ✅ `advanced_filters_v2.py`:
  - Added MetadataManager import and initialization
  - Modified `build_filter_categories()` - Tags category with counts
  - Modified `apply_active_filters()` - Tag filtering logic (OR within Tags)
  - Modified `analyze_current_files()` - Added file_path to metadata
  - Updated `collapsed_by_default` - Only Dimensions collapsed
  - Removed drag selection code (eventFilter, is_dragging, etc.)

---

## 🔥 Previous Updates (v2.5.0-dev) - October 17, 2025

### Tag System - Phase 1 Implementation Complete! 🏷️✨
**Completion Date:** October 17, 2025

#### What's Working Now:

1. **✅ SQLite Backend (`metadata.py`)** - ~400 lines
   - MetadataManager class with full CRUD operations
   - Database schema: file_metadata, tags, file_tags tables
   - Search & filter by tags, rating, color
   - Singleton pattern with auto-initialization
   - Default tags auto-loading on first run

2. **✅ Default Tags System (`default_tags.json`)** - ~100 lines
   - 7 categories: Asset Type, Environment, Lighting, Source, Technical, Material, Status
   - 75+ production-ready tags for Environment/Lighting artists
   - Color-coded categories

3. **✅ Preview Panel Tags Tab - Full Integration**
   - Add tags to files (saves to SQLite database)
   - Tag chips with remove button
   - Tags auto-load when selecting files
   - Tags persist across sessions
   - QCompleter autocomplete with all available tags
   - Case-insensitive tag search

4. **✅ Database Location**
   - `~/.ddContentBrowser/tags.db` (user home directory)
   - Cross-platform compatible
   - Single file for easy backup

#### Technical Implementation:

```python
# What happens when you add a tag:
1. User types tag name (autocomplete suggests from database)
2. Press Enter or click "+ Add" button
3. Tag saved to SQLite database (file_path → tag_id relationship)
4. Tag chip widget created and displayed
5. Tag persists - reopen file later, tag still there!

# What happens when you remove a tag:
1. Click X button on tag chip
2. Database relationship removed (file_path ↔ tag_id)
3. Chip widget deleted from UI
4. Tag removed permanently

# What happens when you select a file:
1. show_single_file() called
2. load_tags(asset) called at end
3. MetadataManager queries database for file's tags
4. Tag chips created for each tag found
5. UI updated with existing tags
```

#### Files Created:
- ✅ `metadata.py` - SQLite backend (~400 lines)
- ✅ `default_tags.json` - Default tag structure (~100 lines)

#### Files Modified:
- ✅ `widgets.py`:
  - Added QCompleter import for autocomplete
  - Updated `add_tag()` - Database integration
  - Updated `create_tag_chip()` - Stores tag_id
  - Updated `remove_tag_chip()` - Database removal
  - Updated `load_tags()` - Database loading
  - Added `setup_tag_autocomplete()` - Autocomplete setup
  - Added tag loading call in `show_single_file()`

#### Next Steps (Phase 3):
- [x] ✅ Tag Filter Panel (filter files by tags) - **DONE!**
- [ ] Star Rating System (0-5 stars)
- [ ] Color Label System (8 colors)
- [ ] Bulk tagging (multi-file operations)
- [ ] Tag badges on thumbnails
- [ ] Keyboard shortcuts
- [ ] Edit Mode for tag management

------

## 🔥 Previous Updates (v2.4.3) - October 17, 2025 (Earlier Today)

### Cache + Filter System Complete Overhaul 🔧
**Completion Date:** October 17, 2025

#### Critical Bug Fixes - Cache Bypass Issues 🐛

**Problem Statement:**
The cache optimization system was bypassing filter logic, causing filters to not work correctly when using cached directory data. This affected ALL filter types (file type, size, date, folders, images, scripts, search).

#### 1. Cache + Filter Integration Fix ✅
**Root Cause:**
- Cached assets were used directly without applying current filters
- Only fresh filesystem scans had filters applied
- Result: Filters appeared broken after first directory visit

**Solution Implemented:**
```python
# BEFORE (broken):
if cached_assets is not None:
    self.assets = cached_assets  # Used directly, no filtering!
    
# AFTER (fixed):
if cached_assets is not None:
    # Apply ALL filters to cached assets
    filtered_assets = []
    for asset in cached_assets:
        # Apply: folder visibility, file type, show_images, show_scripts
        # Apply: size filter, date filter, search filter
        if passes_all_filters(asset):
            filtered_assets.append(asset)
    self.assets = filtered_assets
```

**Filters Now Applied to Cached Assets:**
- ✅ **File Type Filter** - Extension filtering (.ma, .mb, .obj, etc.)
- ✅ **Size Filter** - Min/max file size filtering
- ✅ **Date Filter** - Date range filtering
- ✅ **Show Folders** - Folder visibility toggle
- ✅ **Show Images** - Image file visibility toggle
- ✅ **Show Scripts** - Script file visibility toggle
- ✅ **Search Filter** - Text search with regex support

**Performance Optimization:**
- Stat info (size/date) only loaded when needed
- Lazy loading preserved for thumbnails
- Cache still provides speed benefit

#### 2. Clear Filters + Recursive Mode Fix ✅
**Problem:**
- Simple filter applied → Include subfolders enabled → Clear Filters pressed
- Result: Filters cleared but file list not refreshed (cache was blocking)

**Root Cause:**
```python
# Cache check didn't account for recursive mode
if not force and self._is_cache_valid(path_str, current_mtime):
    cached_assets = self._get_from_cache(path_str)
    # In recursive mode, we need fresh scan, not cache!
```

**Solution:**
```python
# Disable cache for recursive mode
if not force and not self.include_subfolders and self._is_cache_valid(...):
    cached_assets = self._get_from_cache(path_str)
```

**Result:**
- Recursive mode always rescans filesystem
- Filters apply correctly during recursive scan
- Clear Filters works properly in all modes

#### 3. Advanced Filters + Clear Filters Button Sync ✅
**Problem:**
- Advanced Filters activated → Clear Filters button remained visible
- Should hide since Advanced Filters has its own Clear button

**Solution Implemented:**
```python
# Added state tracking
self.advanced_filters_active = False  # In __init__

# Hide Clear Filters when Advanced Filters active
def on_advanced_filters_activated(self, is_active):
    self.advanced_filters_active = is_active
    if is_active:
        self.clear_filters_btn.setVisible(False)
    else:
        self.update_filter_visual_feedback()

# Check state in visibility logic
def update_filter_visual_feedback(self):
    if self.advanced_filters_active:
        self.clear_filters_btn.setVisible(False)  # Always hidden
    else:
        self.clear_filters_btn.setVisible(has_active_filters)  # Show if needed
```

**Result:**
- Clear Filters button hides when Advanced Filters active
- Clear Filters button shows when basic filters active
- No duplicate Clear buttons visible

#### Files Modified:
- `models.py` - `refresh()` method (lines 283-500)
  - Cache check now excludes recursive mode
  - Complete filter application for cached assets
  - Removed duplicate filter logic
- `browser.py` - Filter button visibility logic
  - Added `self.advanced_filters_active` flag
  - Updated `on_advanced_filters_activated()` 
  - Updated `update_filter_visual_feedback()`
- `advanced_filters_v2.py` - Removed duplicate refresh call

**Testing Verified:**
- ✅ File type filters work with cache
- ✅ Size filters work with cache
- ✅ Date filters work with cache
- ✅ Clear Filters works in normal mode
- ✅ Clear Filters works in recursive mode
- ✅ Clear Filters button syncs with Advanced Filters
- ✅ All filter combinations work correctly
- ✅ Cache optimization still active (fast navigation)

------

## 🔥 Previous Updates (v2.4.2) - October 16, 2025

### Preview Panel Zoom Controls & Search Filter Fix 🔍
**Completion Date:** October 16, 2025

#### 1. Professional Zoom Controls - Center-Point Zoom 🎯
- ✅ **100% Button Fixed** - Now zooms to 1:1 pixel ratio centered on current view
- ✅ **Zoom In/Out Buttons** - Center-point based zoom (like Photoshop)
- ✅ **GPU Transform Zoom** - Uses `QGraphicsView.scale()` instead of pixmap rescaling
- ✅ **Position Compensation** - Keeps viewport center point stable during zoom
- ✅ **No More Corner Jump** - All zoom operations preserve current view focus

**Technical Implementation:**
```python
# Center-point zoom algorithm (applied to all zoom buttons)
1. Get viewport center in scene coordinates BEFORE zoom
2. Calculate and apply zoom factor via transform
3. Get viewport center in scene coordinates AFTER zoom  
4. Calculate position delta
5. Translate view to compensate (keeps center point stable)
```

**Before vs After:**
```
BEFORE: 100% button → jumps to top-left corner (not useful!)
AFTER:  100% button → zooms current view center to 1:1 ratio (professional!)

BEFORE: +/- buttons → resets to top-left after each click
AFTER:  +/- buttons → smooth zoom in/out from center (like Photoshop)
```

**Files Modified:**
- `widgets.py` - `zoom_100()`, `zoom_in()`, `zoom_out()` methods
- All three now use identical center-point compensation logic
- Removed calls to `update_zoom_display()` (which caused corner jumps)

**Zoom Behavior Summary:**
- 🖱️ **Scroll Wheel**: Zooms around mouse cursor position (unchanged)
- ➕ **Zoom In (+)**: Zooms into viewport center (1.25x per click)
- ➖ **Zoom Out (-)**: Zooms out from viewport center (0.8x per click)  
- 💯 **100% Button**: Sets 1:1 pixel ratio centered on current view
- 📐 **Fit Button**: Fits entire image to viewport (unchanged)

#### 2. Search Filter Cache Bug Fix 🔍
- ✅ **Cache + Search Compatibility** - Search now works with cached directory data
- ✅ **Root Cause Found** - Search filter only applied when `cached_assets is None`
- ✅ **Fix Applied** - Added `else` branch to filter cached assets by search text
- ✅ **Case-Sensitive & Regex** - All search modes work correctly now

**Bug Details:**
```python
# BEFORE (broken):
if cached_assets is None:
    # Filter search text
    all_items = [f for f in all_items if self._matches_search(f.name, self.filter_text)]
# If using cache → search filter skipped!

# AFTER (fixed):
if cached_assets is None:
    # Filter search text on filesystem data
    all_items = [f for f in all_items if self._matches_search(f.name, self.filter_text)]
else:
    # Filter search text on cached assets
    self.assets = [asset for asset in self.assets if self._matches_search(asset.name, self.filter_text)]
```

**Effect:**
- Search now works consistently whether directory is freshly loaded or from cache
- Fast navigation (Back/Forward) no longer breaks search functionality
- Files modified: `models.py` - `refresh()` method (line ~371)

------

## 🔥 Previous Updates (v2.4.1) - October 16, 2025

### Navigation Panel Restructure & UI Polish 🎨
**Completion Date:** October 16, 2025

#### 1. Recent Folders Dropdown Button ⏰
- ✅ **Clock Icon Button** - Replaced Recent folders list with elegant dropdown (🕒 emoji)
- ✅ **Toolbar Integration** - Positioned before Back/Forward buttons (Adobe Bridge style)
- ✅ **Hover-Only Visibility** - Transparent background, highlights on hover only
- ✅ **Custom Styling** - Larger emoji (16px), no border, rounded hover effect
- ✅ **Max 20 Recent Paths** - Increased from 10 to 20 folders
- ✅ **UI Font Consistency** - Uses settings-based `UI_FONT` variable
- ✅ **Dropdown Menu Integration** - Full path tooltips, folder names as labels

**Visual Design:**
```css
Normal state:   transparent background, no border
Hover state:    rgba(255,255,255,30) background, 3px border-radius
Button size:    35px width, 28px height
Icon size:      16px font-size (larger emoji)
Menu indicator: hidden (width: 0px)
```

**Implementation:**
- New button: `self.recent_btn` in `create_toolbar()` (browser.py)
- Method: `update_recent_menu()` - populates dropdown with recent paths
- Method: `navigate_from_recent_menu()` - handles menu item clicks
- Styling: QPushButton stylesheet with hover pseudo-selector
- Font handling: `widgets.UI_FONT` variable used for menu consistency
- Files modified: `browser.py` (toolbar creation, recent menu), `config.py` (max_recent_paths: 20)

#### 2. Tab System for Collections & Advanced Filters 📑
- ✅ **QTabWidget Added** - Bottom half of navigation panel (40% height)
- ✅ **Collections Tab** - Placeholder for future Collections feature
- ✅ **Advanced Filters Tab** - Placeholder for future filter presets/rules
- ✅ **Vertical Splitter** - Favorites (60%) / Tabs (40%) resizable split
- ✅ **"Coming soon..." Messages** - Clear indication of planned features

**Layout Structure:**
```
Navigation Panel (Vertical Splitter)
├── Favorites Section (60%)
│   └── QListWidget (multi-select enabled)
└── QTabWidget (40%)
    ├── Collections Tab (placeholder)
    └── Advanced Filters Tab (placeholder)
```

**Future Plans:**
- Collections: User-created asset groups (similar to Lightroom)
- Advanced Filters: Saved filter presets (file type, date range, size, etc.)

#### 3. Multi-Select Favorites Removal 🗑️
- ✅ **Multi-Selection Enabled** - `ExtendedSelection` mode on favorites list
- ✅ **Context Menu Update** - Shows count when multiple items selected
- ✅ **Batch Removal** - Delete multiple favorites at once
- ✅ **Dynamic Labels** - "Remove from Favorites" vs "Remove X from Favorites"

**Example:**
```
Single selection:   "Remove from Favorites"
Multiple (3 items): "Remove 3 from Favorites"
```

#### 4. Include Subfolders Cache Fix 🐛
- ✅ **Fixed Non-Working Checkbox** - Include Subfolders now properly toggles
- ✅ **Cache Bypass on Toggle** - Uses `force=True` parameter in `refresh()`
- ✅ **Root Cause** - Cache didn't track `include_subfolders` state
- ✅ **Solution** - Force filesystem reload when checkbox changes

**Technical Details:**
- Problem: Cache stored assets for normal mode only
- Effect: Toggling checkbox returned stale cached data instead of rescanning
- Fix: `on_subfolder_toggle()` now calls `refresh(force=True)` 
- Files modified: `browser.py` (line 993 - added force parameter)

------

## 🔥 Previous Updates (v2.4.0) - October 16, 2025

### Performance Optimizations & UX Improvements
**Completion Date:** October 16, 2025

#### 1. Directory Loading Performance - Lazy Loading & Caching 🚀
- ✅ **os.scandir() API** - Single filesystem call instead of 2000+ (54x faster!)
- ✅ **Lazy Loading System** - Asset metadata (size, date) loaded only when needed
- ✅ **Intelligent Cache** - AssetItem objects cached for instant reload (5 min TTL)
- ✅ **1785x Speed Improvement** - Network directories: 12.5s → 0.007s on second load
- ✅ **Automatic Cache Invalidation** - Detects directory modifications via mtime check
- ✅ **F5 Force Refresh** - Bypasses cache for fresh data
- ✅ **Memory Management** - Max 20 cached directories with LRU eviction

**Performance Metrics:**
```
Network folder (2000 files):
- Original:    12.5s  (iterdir + 15× glob + stat calls)
- Optimized:    2.5s  (scandir once + lazy loading)
- Cached:      0.007s (AssetItem objects from cache)
- Speed gain:  5x first load, 1785x cached load
```

**Breakdown - First Load:**
```
Phase                   Old Time    New Time    Improvement
────────────────────────────────────────────────────────────
scandir/iterdir/glob    5.1s        0.092s      55x faster!
AssetItem creation      2.5s        2.37s       Slightly faster
Filtering/Sorting       0.01s       0.001s      10x faster
────────────────────────────────────────────────────────────
TOTAL                   7.7s        2.47s       3.1x faster!
```

**Breakdown - Cached Load:**
```
Cache lookup:           0.001s
Asset loading:          0.006s (from memory)
────────────────────────────────────────────────────────────
TOTAL                   0.007s      353x faster than first!
```

**Technical Implementation:**
- **os.scandir()** instead of `iterdir() + glob()`:
  - Returns `DirEntry` objects with cached `is_dir()` and stat info
  - Single API call retrieves all file metadata at once
  - Eliminates 2000+ redundant filesystem calls
  - Uses native Win32 `FindFirstFileEx` API (same as Windows Explorer)
  
- **AssetItem lazy loading**: 
  - `stat()` deferred until property access (size, modified_time)
  - Properties use `@property` decorator with on-demand loading
  - Batch stat loading only when filtering/sorting requires it
  
- **Directory cache**: 
  - Complete AssetItem objects stored, not just Paths
  - Avoids recreating objects on repeated visits
  - Cache validation: TTL (300s) + directory mtime comparison
  
- **Files modified**: `models.py` (AssetItem class, FileSystemModel.refresh())

**Cache Settings:**
- Max cached directories: 20
- Cache TTL: 5 minutes (300 seconds)
- Cache enabled by default
- Methods: `clear_cache()`, `set_cache_enabled(bool)`

#### 2. Favorites Management - Remove from Favorites 📌
- ✅ **Right-Click Context Menu** - Added to Favorites list
- ✅ **Remove from Favorites** - Delete favorite paths with confirmation
- ✅ **Normalized Path Comparison** - Handles Windows/Unix path differences
- ✅ **Status Bar Feedback** - Shows confirmation message
- ✅ **Auto-Save to Config** - Changes persist immediately

**Implementation:**
- New method: `show_favorites_context_menu()` in `browser.py`
- New method: `remove_from_favorites()` with path normalization
- Context menu policy: `Qt.CustomContextMenu` on `favorites_list`
- Files modified: `browser.py` (lines 567-568, new methods added)

#### 3. Password Protected PDF Preview 🔒
- ✅ **Encrypted PDF Detection** - Checks `doc.is_encrypted` flag
- ✅ **User-Friendly Message** - Shows "🔒 Password Protected PDF" instead of error
- ✅ **Special Return Value** - `load_pdf_page()` returns `(None, -1, "encrypted")`
- ✅ **Consistent UI** - Same message for initial load and page navigation
- ✅ **No Generic Error** - Distinguishes encrypted vs corrupted PDFs

**Before:**
```
Failed to load PDF:
document.pdf
```

**After:**
```
🔒 Password Protected PDF

document.pdf
```

**Technical Details:**
- Modified `load_pdf_page()` to return special tuple for encrypted PDFs
- Updated `show_pdf_preview()` to check for encrypted status
- Updated `reload_pdf_page()` with same logic
- Files modified: `widgets.py` (`load_pdf_page`, `show_pdf_preview`, `reload_pdf_page`)

------

## 🔥 Previous Updates (v2.3.1) - October 16, 2025

### Bug Fixes & UI Improvements
**Completion Date:** October 16, 2025

#### 1. Text Preview Resize Bug Fix 🐛
- ✅ **Fixed separator jumping/teleporting** during text file preview resize
- ✅ **Root Cause:** Two `QApplication.processEvents()` calls in `resizeEvent()` created feedback loop
- ✅ **Solution:** Removed synchronous event processing, let Qt handle layout naturally
- ✅ **Result:** Smooth separator dragging without unpredictable jumps
- ✅ **Files Modified:** `widgets.py` (lines 1646-1668)

**Technical Details:**
- Problem: `processEvents()` forced immediate event loop iteration during resize
- Effect: Panel resize → event processing → layout recalc → new resize event → repeat → separator teleports
- Fix: Removed both `processEvents()` calls and unnecessary `documentSizeChanged.emit()`
- New logic: Simple text width update + scene rect adjustment (Qt batches events automatically)

#### 2. Open File Feature 📂
- ✅ **New "Open" Button** added to toolbar (between Reference and Favorites)
- ✅ **Context Menu Integration** - "📂 Open" option in right-click file menu
- ✅ **Windows Default Program** - Opens files with OS default application
- ✅ **Cross-Platform Support** - Windows (os.startfile), macOS (open), Linux (xdg-open)
- ✅ **Multi-File Support** - Opens multiple selected files simultaneously
- ✅ **Error Handling** - Shows status messages for each file

**Use Cases:**
- Open `.txt` files in Notepad/Text Editor
- Open `.jpg`/`.png` images in Windows Photos/Preview
- Open `.pdf` files in Adobe Reader/default PDF viewer
- Open `.mel`/`.py` scripts in external code editor
- Any file type opens with Windows-defined default app

**Implementation:**
- New method: `open_selected_files()` in `browser.py`
- Button added to toolbar between Import/Reference and Favorites
- Context menu item: "📂 Open" (positioned after Import/Reference)
- Uses `os.startfile()` on Windows (most reliable)
- Fallback to `subprocess.Popen()` for macOS/Linux

------

## 🔥 Previous Updates (v2.3) - October 15, 2025

### Multi-Rule Batch Renamer System (NEW!)
**Completion Date:** October 15, 2025

- ✅ **Multi-Rule System** - Chain multiple rename operations sequentially
- ✅ **7 Rename Rule Types** - Find/Replace, New Name, Prefix, Suffix, Numbering, Case Change, Regex
- ✅ **Live Preview** - Real-time preview of all changes with highlighting
- ✅ **Rule Management** - Add, remove, reorder rules with + and − buttons
- ✅ **Advanced Options** - Case sensitivity, whole name match, padding, positioning
- ✅ **Smart Placeholders** - {num} for numbering, {original} for original name
- ✅ **Regex Support** - Full regex pattern matching with capture groups
- ✅ **Error Handling** - Invalid operations highlighted in preview
- ✅ **Compact UI** - Space-efficient design with splitter (900x700px resizable)
- ✅ **Batch Operations** - Rename multiple files at once with confirmation

**Technical Details:**
- Created `batch_rename.py` module (~700 lines) with 2 main classes
- `RenameRule` widget - Individual rule with dynamic options (~400 lines)
- `BatchRenameDialog` - Main dialog with splitter layout (40% rules, 60% preview)
- Signal-based architecture for live preview updates
- Sequential rule application with index tracking for numbering
- Extension preservation with Path.stem/suffix handling
- Compact styling: 11px fonts, 20px row height, minimal margins
- Green highlight for changes, red for errors in preview table

**Rename Rule Types:**

1. **Find & Replace**
   - Find/Replace text with case sensitivity option
   - Whole name match option
   - Partial or full name replacement

2. **New Name**
   - Template-based renaming with placeholders
   - `{num}` - Sequential numbering (3-digit padding)
   - `{original}` - Keep original filename
   - Example: `File_{num}` or `{original}_new`

3. **Add Prefix**
   - Prepend text to filename

4. **Add Suffix**
   - Append text before extension

5. **Numbering**
   - Sequential numbering with customizable:
     - Start number (0-99999)
     - Padding (1-10 digits)
     - Position (Start/End)
   - Format: `001_filename` or `filename_001`

6. **Case Change**
   - UPPERCASE, lowercase, Title Case, Sentence case

7. **Regex Pattern**
   - Full regex pattern matching
   - Capture group support (\\1, \\2, etc.)
   - Example: `(\d+)` → `File_\1`

**UI Features:**
- **Resizable Splitter** - Adjust rules/preview panel sizes
- **Scrollable Rules** - Add unlimited rules with scroll
- **Live Preview Table** - Original vs New name comparison
- **Status Counter** - Shows number of files to be renamed
- **Add Rule After** - Insert rules at any position (+button)
- **Remove Rule** - Delete unwanted rules (− button, min 1 rule)
- **Change Counter** - Real-time count of modified files
- **Apply Button** - Executes rename with confirmation dialog

---

### Complete Settings System
**Completion Date:** October 15, 2025

- ✅ **Full Settings GUI** - Multi-tab settings dialog with organized categories
- ✅ **General Settings Tab** - Startup directory, window size, UI font, behavior options
- ✅ **Thumbnail Settings Tab** - Size, quality, 3D generation, cache management
- ✅ **Preview Settings Tab** - HDR/EXR cache, resolution, exposure defaults
- ✅ **Filters Settings Tab** - Custom extensions, visibility, search options, recursive limits
- ✅ **JSON Persistence** - Settings saved to `~/.ddContentBrowser/settings.json`
- ✅ **Cache Management** - Visual cache size display, one-click cache clearing
- ✅ **Restore Defaults** - Reset to default settings button
- ✅ **Settings Signal** - `settings_changed` signal for live updates

**Technical Details:**
- Created `settings.py` module (~800 lines) with 5 main classes
- `SettingsManager` - JSON-based settings persistence with recursive merge
- `SettingsDialog` - Main dialog with QTabWidget (600x500px)
- `GeneralSettingsTab` - UI font selection (Segoe UI/Arial/Calibri/Verdana/Tahoma)
- `ThumbnailSettingsTab` - Discrete size values [32, 64, 128, 256, 512], quality levels
- `PreviewSettingsTab` - HDR resolution [512, 1024, 2048, 4096], cache size (1-20 files)
- `FiltersSettingsTab` - Custom extensions parser, recursive file limit (100-100,000)
- Cache directory correctly points to `~/.dd_browser_thumbnails`
- Auto-refresh interval control (1-60 seconds)

**New Settings Categories:**
```json
{
  "general": {
    "startup_directory": "",
    "ui_font": "Segoe UI",
    "confirm_delete": true,
    "auto_refresh": false
  },
  "thumbnails": {
    "size": 128,
    "quality": "medium",
    "cache_size_mb": 500
  },
  "preview": {
    "resolution": 1024,
    "hdr_cache_size": 5,
    "default_exposure": 0.0
  },
  "filters": {
    "custom_extensions": [],
    "show_hidden": false,
    "max_recursive_files": 10000
  }
}
```

------

## 🔥 Previous Updates (v2.2) - October 14, 2025

### 16/32-bit TIFF Support Enhancement
**Completion Date:** October 14, 2025

- ✅ **Enhanced TIFF Support** - Full OpenCV integration for 16/32-bit TIFF files
- ✅ **Preview Panel Fix** - 16/32-bit TIFF files now display properly in preview
- ✅ **Zoom Mode Support** - Full zoom functionality for high bit-depth TIFF files  
- ✅ **Intelligent Normalization** - Proper 16-bit (/256) and 32-bit float (0-1 clipping) handling
- ✅ **Search Thumbnail Fix** - Search results now properly trigger thumbnail generation
- ✅ **EXR Cache Optimization** - Fixed EXR thumbnail generation using dedicated OpenEXR loader

**Technical Details:**
- Modified `widgets.py` preview logic to use OpenCV for TIFF files
- Enhanced `enter_zoom_mode()` with same TIFF handling as preview
- Fixed `on_search_text_changed()` to trigger thumbnail requests
- Restored EXR cache to use `load_hdr_exr_image()` instead of OpenCV
- TIFF files maintain normal image behavior (no exposure slider, standard cache)

------

## ✅ Completed Features

### Multi-Rule Batch Renamer (v2.3 - NEW!)
**Lines of Code:** ~700 lines  
**Completion Date:** October 15, 2025

- ✅ **7 Rename Rule Types** - Comprehensive rename operations
- ✅ **Sequential Rule Chain** - Apply multiple rules in order
- ✅ **Live Preview** - Real-time before/after comparison
- ✅ **Dynamic UI** - Rule-specific options with signals
- ✅ **Placeholder System** - {num}, {original} template variables
- ✅ **Regex Engine** - Full pattern matching with capture groups
- ✅ **Error Detection** - Invalid operations highlighted
- ✅ **Rule Management** - Add/remove/reorder rules
- ✅ **Compact Design** - Space-efficient 11px font, 20px rows
- ✅ **Batch Processing** - Multi-file rename with confirmation

**Rule Types:**
- Find & Replace (case sensitive, whole name options)
- New Name (template with {num}/{original} placeholders)
- Add Prefix (prepend text)
- Add Suffix (append before extension)
- Numbering (start, padding, position control)
- Case Change (4 case styles)
- Regex Pattern (full regex with capture groups)

**UI Components:**
- Resizable splitter (rules 40%, preview 60%)
- Scrollable rule container
- Live preview table with change highlighting
- Status counter and apply button
- + button (add rule after)
- − button (remove rule, min 1)

---

### Settings System (v2.3 - NEW!)
**Lines of Code:** ~800 lines  
**Completion Date:** October 15, 2025

- ✅ **Settings GUI** - Professional multi-tab dialog
- ✅ **4 Settings Categories** - General, Thumbnails, Preview, Filters
- ✅ **JSON Persistence** - Auto-save/load from `~/.ddContentBrowser/settings.json`
- ✅ **UI Customization** - Font selection, window size, startup directory
- ✅ **Thumbnail Control** - Discrete sizes [32-512px], quality presets, cache limit
- ✅ **HDR Control** - Resolution [512-4096px], cache size (1-20 files), default exposure
- ✅ **Filter Control** - Custom file extensions, show hidden, case-sensitive search
- ✅ **Cache Management** - Visual cache size, one-click clear
- ✅ **Restore Defaults** - One-click settings reset
- ✅ **Live Updates** - Settings signal for component refresh

**Settings Dialog Features:**
- 600x500px resizable dialog with QTabWidget
- Browse button for directory selection
- Spinboxes with units (px, MB, sec, EV, files)
- Discrete thumbnail size slider (5 snap points)
- Quality presets (Low/Medium/High)
- Resolution presets (512/1024/2048/4096)
- Custom extensions parser (comma-separated input)
- Cache size calculator with real-time display
- Warning labels for performance impact
- Confirm dialogs for destructive actions

---

### HDR/EXR Preview System

**Completion Date:** October 13, 2025**Lines of Code:** ~400 lines  

**Completion Date:** October 2025

- ✅ **Full HDR/EXR Support** - Native float image handling

- ✅ **Exposure Control** - Real-time exposure adjustment (-5.0 to +5.0 stops)- ✅ `ThumbnailCache` - In-memory LRU cache (200 items)

- ✅ **ACES Tone Mapping** - Professional tone mapping workflow  - ✅ `ThumbnailDiskCache` - Persistent disk cache (500MB, JPEG compression)

- ✅ **OpenCV Integration** - Native HDR (Radiance RGBE) support- ✅ MD5-based cache keys with mtime validation

- ✅ **OpenEXR Support** - Multi-channel EXR rendering- ✅ Automatic LRU cleanup

- ✅ **Raw Data Caching** - Fast exposure adjustment (35-45ms)- ✅ Statistics tracking (hits, misses, generated)

- ✅ **Smart Debouncing** - Smooth slider interaction (50ms)

- ✅ **Auto Reset** - Exposure resets to 0.0 on file change**Performance:**

- Memory cache hit: < 1ms

**Performance:**- Disk cache hit: 5-10ms

- Initial HDR load: ~100-200ms (with caching)- Auto-cleanup when cache exceeds limit

- Exposure adjustment: ~35-45ms (from cache)

- Cache size: Last 5 HDR raw data (~100-150 MB)---

- Preview resolution: 1024px (optimal speed/quality)

### Phase 2: Thumbnail Generator (COMPLETE)

**Dependencies:****Lines of Code:** ~230 lines  

- OpenCV (cv2) - HDR support (~50 MB)**Completion Date:** October 2025

- OpenEXR - EXR support (~5 MB)

- NumPy - Float processing (~50 MB)- ✅ `ThumbnailGenerator` QThread for background processing

- Total: ~100-150 MB in external_libs/- ✅ Queue-based generation with priority

- ✅ Beautiful gradient icons for each file type

---- ✅ Progress signals (thumbnail_ready, progress_update, generation_failed)

- ✅ Safe mode (no file opening to prevent crashes)

## ✅ Core Features

**File Type Colors:**

### Preview Panel- `.ma` → Blue gradient

- ✅ Image preview with metadata- `.mb` → Dark Blue gradient

- ✅ HDR/EXR exposure control slider- `.obj` → Purple gradient

- ✅ Zoom mode (double-click)- `.fbx` → Yellow gradient

- ✅ Pan & scroll (1:1 pixel zoom)- `.abc` → Green gradient

- ✅ Multi-file summary- `.usd` → Red gradient

- ✅ Resolution display

- ✅ File size & date info---



### Navigation### Phase 3: Visual Interface (COMPLETE)

- ✅ Breadcrumb navigation (clickable segments)**Lines of Code:** ~250 lines  

- ✅ Manual path input (⋮ button)**Completion Date:** October 2025

- ✅ Back/Forward history

- ✅ Browse to folder dialog- ✅ `ThumbnailDelegate` - Custom QStyledItemDelegate

- ✅ Quick parent folder (Backspace)- ✅ Grid Mode - Large thumbnails (64-256px)

- ✅ List Mode - Compact list with details

### Filtering & Sorting- ✅ Size slider with value snapping

- ✅ File type filters (MA, MB, OBJ, FBX, ABC, USD)- ✅ View mode toolbar

- ✅ Size range filter (min/max MB)- ✅ Smooth antialiased rendering

- ✅ Date range filter (Today, Week, Month, Custom)

- ✅ Show/Hide folders, images, scripts---

- ✅ Sort by Name, Size, Date, Type

- ✅ Ascending/Descending toggle### Phase 3.5: Advanced Features (COMPLETE)

**Lines of Code:** ~800 lines  

### Maya Integration**Completion Date:** October 2025

- ✅ Middle-drag batch import

- ✅ Context menu (Import, Reference, Delete, Rename)#### FilterPanel:

- ✅ Drag & drop support- ✅ File type checkboxes (MA, MB, OBJ, FBX, ABC, USD)

- ✅ Safe file operations- ✅ Size range filter (min/max MB)

- ✅ Date range filter (Today, Week, Month, Custom)

### View Modes- ✅ Show/Hide folders toggle

- ✅ Grid Mode - Large thumbnails (64-256px)- ✅ Collapsible UI (▼ toggle button)

- ✅ List Mode - Compact list with details- ✅ Clear all filters button

- ✅ Thumbnail size slider with snapping

- ✅ Ctrl+Scroll zoom#### Sorting System:

- ✅ Sort by Name, Size, Date, Type

---- ✅ Ascending/Descending toggle

- ✅ Visual indicators (▲▼)

## 📈 Performance Metrics- ✅ Clickable column headers



### HDR/EXR Performance:#### Maya-Style Drag & Drop:

- Load 1024px HDR: ~100-200ms (first time)- ✅ `MayaStyleListView` class

- Exposure adjustment: ~35-45ms (cached)- ✅ Middle-drag for batch import

- Tone mapping: ~30-40ms (ACES + gamma)- ✅ Distance threshold detection

- QPixmap creation: ~3-5ms- ✅ Visual feedback (cursor, status messages)

- Total latency: ~50ms (with debounce)- ✅ Multi-file support



### General Performance:

- Load 100 files: ~100ms
- Load 1000 files: ~800ms
- Memory cache: < 1ms lookup
- UI frame time: ~16ms (60fps)

#### Context Menus:

- ✅ File menu (Import, Reference, **Open**, Rename, Delete, Properties)
- ✅ Folder menu (Open, Add to Favorites)
- ✅ Empty space menu (Refresh, Paste path)
- ✅ Ctrl+Right-click for folder operations

#### File Operations:

- ✅ Delete files (with confirmation)
- ✅ Rename files (input dialog)
- ✅ **Open files with default program** (NEW v2.3.1!)
- ✅ Copy path to clipboard
- ✅ Open in Explorer (Win/Mac/Linux)
- ✅ File properties dialog

#### Keyboard Shortcuts:

- ✅ F5 - Refresh

├── config.py                - Configuration management- ✅ Delete - Delete files

├── delegates.py             - Custom item rendering- ✅ F2 - Rename

├── models.py                - Data models- ✅ Ctrl+C - Copy path

├── utils.py                 - Utility functions- ✅ Enter - Import

├── widgets.py               - UI widgets (2,100+ lines)- ✅ Backspace - Parent folder

│- ✅ **Ctrl+Scroll - Zoom thumbnails**

├── external_libs/           - Dependencies (~150 MB)

│   ├── cv2/                 - OpenCV (HDR support)#### Navigation Enhancements:

│   ├── OpenEXR.pyd          - OpenEXR (EXR support)- ✅ `BreadcrumbWidget` with clickable path segments

│   ├── numpy/               - NumPy (float processing)- ✅ Manual path edit mode (⋮ button)

│   └── Imath.py             - OpenEXR helper- ✅ Escape to cancel path edit

│- ✅ Scroll area for long paths

└── Documentation:

    ├── README.md            - Main documentation---

    ├── CURRENT_STATUS.md    - This file

    ├── DEVELOPMENT_WORKFLOW.md - Development process## 📈 Statistics

    ├── STRUCTURE.md         - Code architecture

    ├── TROUBLESHOOTING.md   - Problem solving
    └── QUICK_START.md       - Quick start guide

```

---

## 📈 Statistics

### Code Metrics:
- **Total Lines:** ~4,300 lines (+27 from today's fixes/features)
- **Main Classes:** 17
- **Functions/Methods:** 152+ (+1 for open_selected_files)
- **Supported File Types:** 10 (.ma, .mb, .obj, .fbx, .abc, .usd, .vdb, .hda, .blend, .pdf)
- **Modules:** 8 (config, utils, cache, models, delegates, widgets, settings, batch_rename)



## 🎨 Architecture### Performance Metrics:

- Load 100 files: ~100ms

### HDR Processing Pipeline:- Load 1000 files: ~800ms

- Memory cache: < 1ms lookup

```- Disk cache: ~5-10ms lookup

1. Load HDR/EXR (OpenCV/OpenEXR)- Icon generation: ~100-500ms per file
- UI frame time: ~16ms (60fps)

### Feature Count:
- ✅ **78+ implemented features** (+3 from today: separator fix, open button, context menu)
- 🔮 **10+ planned features**

---

5. Apply exposure multiplier (2^stops)

   ↓## 🎯 Current Capabilities

6. ACES tone mapping

   ↓### What It Does Well:

7. Gamma correction (2.2)1. **Fast Navigation** - Instant directory browsing

   ↓2. **Visual Browsing** - Beautiful gradient icons

8. Convert to 8-bit3. **Flexible Views** - Grid and List modes

   ↓4. **Smart Filtering** - Type, size, date filters

9. Create QPixmap5. **Intuitive Sorting** - Multiple sort columns

   ↓6. **Maya Integration** - Import, Reference, Drag & Drop

10. Display (35-45ms total)7. **File Management** - Rename, Delete, Copy

```8. **User Experience** - Keyboard shortcuts, context menus

9. **Performance** - Background processing, caching

---10. **Stability** - Safe mode, no crashes



## 🎯 Current Capabilities

### What It Does Well:
1. **Fast Navigation** - Instant directory browsing
2. **Visual Browsing** - Beautiful gradient icons
3. **Flexible Views** - Grid and List modes
4. **Smart Filtering** - Type, size, date filters
5. **Intuitive Sorting** - Multiple sort columns
6. **Maya Integration** - Import, Reference, Drag & Drop
7. **File Management** - Rename, Delete, Copy
8. **User Experience** - Keyboard shortcuts, context menus
9. **Performance** - Background processing, caching
10. **Stability** - Safe mode, no crashes
11. **Settings System** - ✨ Complete GUI configuration
12. **Batch Renamer** - ✨ Multi-rule rename system
13. **Open Externally** - ✨ Windows default program integration

### What It Doesn't Do (Yet):
1. ~~**Settings GUI**~~ - ✅ **COMPLETED v2.3!**
2. ~~**Batch Operations**~~ - ✅ **COMPLETED v2.3!** (Batch Rename)
3. ~~**Open with Default Program**~~ - ✅ **COMPLETED v2.3.1!**
4. **Real Playblast Thumbnails** - Currently uses safe gradient icons
5. **Preview Panel** - No large preview of selected asset
6. **Collections** - No virtual folder system
7. **Asset Metadata** - No scene stats display
8. **Version Control** - No Git/Perforce integration
9. **Theme Support** - No dark/light theme option

---

## 🚀 Usage

### Launch:
```python
import ddContentBrowser
ddContentBrowser.show_content_browser()
```

### Open Settings:
```python
# From menu: File → Settings
# Or programmatically:
from ddContentBrowser.settings import SettingsDialog, SettingsManager
settings_mgr = SettingsManager()
dialog = SettingsDialog(settings_mgr)
dialog.exec_()
```

### Open Batch Rename:
```python
# From context menu: Right-click files → Batch Rename
# Or programmatically:
from ddContentBrowser.batch_rename import BatchRenameDialog
file_paths = ["/path/to/file1.ma", "/path/to/file2.ma"]
dialog = BatchRenameDialog(file_paths)
dialog.exec_()
```

### HDR/EXR Workflow:
1. Select HDR or EXR file
2. Preview appears with exposure slider
3. Adjust exposure (-5.0 to +5.0 stops)
4. Double-click for zoom mode
5. Scroll to zoom, drag to pan

---

## 🔮 Future Improvements

### High Priority (Next Major Release - v3.0):

**Phase Order Based on Complexity & Existing Code:**

#### 🥇 **Priority 1: Smart Import Functions** 🧠 (EASIEST - Existing Code!)
   - **Material Graph Generator** - Integration of existing shader graph builder
     - ✅ **Shader graph builder already exists** - just needs browser integration!
     - Detect texture types from filenames (diffuse, normal, roughness, metallic, AO, displacement)
     - Auto-create aiStandardSurface with all maps connected
     - Smart naming pattern recognition (user-configurable in Settings)
     - UDIM support
     - Pattern examples: `*_diffuse`, `*_albedo`, `*_base_color`, `*_normal`, `*_rough*`
     - **Integration task:** Wire existing shader builder to browser's import system
   
   - **SkyDome Auto-Linker** - Replace HDR/EXR paths in SkyDome lights
     - Drag HDR → auto-detect and update aiSkyDomeLight texture path
     - Preserve exposure value when updating path
     - Batch SkyDome update for multiple lights
     - Works with both .hdr and .exr files
     - **Simple implementation:** Maya API queries + file node path update

   - **Smart Material Assignment** - Auto-assign materials based on object/file names
   - **Reference Update Helper** - Update reference paths in bulk
   
   **Estimated Time:** 1-2 weeks (since shader graph exists)

---

#### 🥈 **Priority 2: Star/Color Rating System** ⭐ (SIMPLE & USEFUL)
   - 5-star rating system (Adobe Bridge style)
   - Color labels: Red, Orange, Yellow, Green, Blue, Purple, Gray, None
   - Quick keyboard shortcuts (1-5 for stars, Ctrl+1-7 for colors)
   - Filter by rating/color in filter panel
   - Sort by rating
   - Bulk rating operations (rate multiple files at once)
   - Visual indicators in thumbnails (stars overlay, colored border)
   - **Integration with Tags:** Colors can act as quick visual tags
   - JSON-based storage: `~/.ddContentBrowser/ratings.json`
   
   **Data Structure:**
   ```json
   {
       "file_path": "C:/project/character.ma",
       "rating": 5,
       "color": "Red",
       "date_rated": "2025-10-15"
   }
   ```
   
   **Estimated Time:** 3-5 days

---

#### 🥉 **Priority 3: Tag System** 🏷️ (MORE COMPLEX)
   - Custom metadata editor (better than Adobe Bridge!)
   - User-defined tags with autocomplete
   - Tag categories/hierarchies (e.g., Project → Assets → Characters)
   - Bulk tag operations
   - Tag-based search and filtering
   - Tag color coding (visual grouping)
   - Export/import tag database (share between artists)
   - SQLite or JSON backend
   - **Can integrate with Star/Color system** for unified metadata
   
   **Data Structure:**
   ```json
   {
       "file_path": "C:/project/character.ma",
       "tags": ["Character", "Main", "Rigged", "Approved"],
       "tag_hierarchy": {
           "Project": ["Production"],
           "Type": ["Character"],
           "Status": ["Approved"]
       },
       "notes": "Final approved version",
       "artist": "John Doe"
   }
   ```
   
   **Estimated Time:** 1-2 weeks

---

#### 🏆 **Priority 4: Collection System** 📁 (COMPLEX BUT POWERFUL)
   - Virtual folders for project organization
   - **Smart Collections** - Rule-based, auto-updating
     - Example: "All FBX files tagged 'Character' with 5-star rating"
     - Example: "HDR files modified in last 7 days"
   - **Manual Collections** - Drag & drop assets
   - Collection nesting and hierarchy
   - Cross-project collections
   - Share collections between artists (export/import)
   - Collection-based batch operations
   
   **Smart Collection Rules:**
   ```json
   {
       "name": "Hero_Assets",
       "type": "smart",
       "rules": {
           "file_types": [".ma", ".mb"],
           "tags": ["Character", "Main"],
           "min_rating": 4,
           "color": ["Red", "Orange"]
       },
       "auto_update": true
   }
   ```
   
   **Estimated Time:** 1-2 weeks

---

#### ⚠️ **Priority 5: Texture Converter** 🎨 (COMPLEX - Past Experience!)
   - **Note:** Previous attempts were challenging, but we're smarter now! 😊
   - Batch texture format conversion
   - Formats: JPEG ↔ PNG ↔ TGA ↔ TIFF ↔ EXR ↔ HDR
   - Resolution scaling (50%, 25%, custom)
   - Color space conversion (sRGB ↔ Linear ↔ ACEScg)
   - Compression quality control
   - Batch processing with progress bar
   - Output naming templates
   - **Tech Options:**
     - OpenImageIO (comes with Maya! - **RECOMMENDED**)
     - OpenCV (already in external_libs)
     - Pillow (Python standard)
   - **Challenges to solve:**
     - Color space preservation
     - 16/32-bit handling
     - Metadata preservation (EXIF, color profile)
     - EXR channel handling
   
   **Estimated Time:** 1-2 weeks (learning from past mistakes!)

---

### Medium Priority (v3.5+):

6. **Real Maya Playblast Thumbnails** - Safe implementation
7. **Preview Panel** - Large preview with metadata
8. **Asset Metadata Display** - Scene stats (poly count, etc.)
9. **Recent/Frequent Assets** - Quick access widget
10. **Favorites/Bookmarks** - Enhanced bookmark system

### Nice to Have (Future):

11. **Theme Support** - Dark/Light themes
12. **Version Control Integration** - Git/Perforce indicators
13. **Network Optimization** - Better UNC paths
14. **AI-Powered Search** - Natural language queries
15. **Cloud Integration** - Dropbox/Google Drive sync

---

## 🛡️ Safety Features

### Why Safe Mode?
The current version uses **gradient-based icons** instead of real Maya playblast thumbnails because:

1. **Thread Safety** - Maya API is not thread-safe
2. **Crash Prevention** - Opening files can crash Maya if scene is dirty
3. **User Control** - No files opened without user permission
4. **Performance** - Gradient icons generate faster (100-500ms vs 2-5s)
5. **Reliability** - No dependency on Maya scene state

### Future Safe Playblast Options:
- **Option 1:** User confirmation before opening files
- **Option 2:** Subprocess isolation (mayapy)
- **Option 3:** Main thread execution with queue
- **Option 4:** Optional setting (advanced users only)

---

## 📁 File Structure

```
ddContentBrowser/
├── __init__.py              - Package initialization
├── browser.py               - Main browser window
├── cache.py                 - Thumbnail caching system
├── config.py                - Configuration management
├── delegates.py             - Custom item rendering
├── models.py                - Data models
├── settings.py              - ✨ Settings GUI system (~800 lines)
├── batch_rename.py          - ✨ NEW! Multi-rule batch renamer (~700 lines)
├── utils.py                 - Utility functions
├── widgets.py               - UI widgets (2,100+ lines)
│
├── external_libs/           - Dependencies (~150 MB)
│   ├── cv2/                 - OpenCV (HDR support)
│   ├── OpenEXR.pyd          - OpenEXR (EXR support)
│   ├── numpy/               - NumPy (float processing)
│   └── Imath.py             - OpenEXR helper
│
└── Documentation:
    ├── README.md            - Main documentation
    ├── CURRENT_STATUS.md    - This file
    ├── DEVELOPMENT_WORKFLOW.md - Development process
    ├── STRUCTURE.md         - Code architecture
    ├── TROUBLESHOOTING.md   - Problem solving
    ├── QUICK_START.md       - Quick start guide
    ├── SETTINGS_GUIDE.md    - Settings documentation
    └── BATCH_RENAME_GUIDE.md - ✨ NEW! Batch rename guide
```

---

## 🎉 Key Achievements

1. ✅ **Multi-Rule Batch Renamer** - Professional rename system with 7 rule types
2. ✅ **Complete Settings System** - Professional multi-tab configuration GUI
3. ✅ **Professional HDR/EXR Support** - Industry-standard exposure control
4. ✅ **Fast Performance** - Sub-50ms exposure adjustments
5. ✅ **ACES Workflow** - Film-quality tone mapping
6. ✅ **Smart Caching** - Efficient memory usage
7. ✅ **Production Ready** - Stable, tested, daily-use ready

---

## 📊 Version History

- **v2.3.1** (Oct 16, 2025) - Text preview resize bug fix + Open file feature
- **v2.3** (Oct 15, 2025) - Multi-rule batch renamer + complete settings system
- **v2.2** (Oct 14, 2025) - 16/32-bit TIFF support enhancement
- **v2.1** (Oct 13, 2025) - HDR/EXR preview + exposure control
- **v2.0** (Oct 11, 2025) - Production ready with filters, sorting, zoom
- **v1.0** (Oct 2025) - Initial release with caching and thumbnails

- **v1.0** (Oct 2025) - Initial release with caching and thumbnails├── PHASE2_COMPLETE.md             - Phase 2 documentation

├── PHASE3_COMPLETE.md             - Phase 3 documentation

---├── PHASE2_SAFE.md                 - Safe mode explanation

└── TEST_CHECKLIST.md              - Testing checklist

---

## 🎨 Architecture

### Class Hierarchy:

```
ContentBrowserConfig
  └─ Configuration management

ThumbnailCache
  └─ In-memory LRU cache

ThumbnailDiskCache
  └─ Persistent disk cache

ThumbnailGenerator (QThread)
  └─ Background thumbnail generation

AssetItem
  └─ File/Folder representation

ThumbnailDelegate (QStyledItemDelegate)
  └─ Custom rendering

BreadcrumbWidget (QWidget)
  └─ Path navigation

FilterPanel (QWidget)
  └─ Advanced filtering UI

MayaStyleListView (QListView)
  └─ Maya-style drag interaction

FileSystemModel (QAbstractListModel)
  └─ File system data model

DDContentBrowser (QMainWindow)
  └─ Main application window
```

### Signal Flow:

```
User Navigation
    ↓
FileSystemModel.setPath()
    ↓
FileSystemModel.refresh()
    ↓
ThumbnailGenerator.add_to_queue()
    ↓
[Background Thread Processing]
    ↓
ThumbnailGenerator.thumbnail_ready Signal
    ↓
DDContentBrowser.on_thumbnail_ready()
    ↓
View Update (triggers delegate repaint)
```

### Cache Strategy:

```
Request Thumbnail
    ↓
ThumbnailCache.get() → Hit? Return (< 1ms)
    ↓ Miss
ThumbnailDiskCache.get() → Hit? Return (~5ms)
    ↓ Miss
ThumbnailGenerator.add_to_queue()
    ↓
Generate gradient icon (~100-500ms)
    ↓
Save to both caches
    ↓
Emit thumbnail_ready signal
```

---

## 🚀 Usage Examples

### Launch:
```python
# Simplest method
exec(open(r'C:/Users/Danki/Documents/maya/2026/scripts/launch_browser_simple.py').read())
```

### Navigate:
1. Click Browse (📁) or type path
2. Use breadcrumbs to jump to parent folders
3. Back/Forward buttons for history

### Filter:
1. Click "▼ Filters" button
2. Select file types (MA, MB, OBJ, etc.)
3. Set size range (min/max MB)
4. Choose date range (Today, Week, Month)

### Import:
1. Select file(s) - Ctrl+click or Shift+click
2. Press Enter or double-click
3. Or middle-drag for batch import

### Customize View:
1. Toggle Grid (⊞) or List (☰) mode
2. Adjust size slider (grid mode only)
3. Or use Ctrl+Scroll to zoom

---

## 🔮 Next Development Steps

### Immediate Priority:
1. **Settings Dialog** - GUI for configuration (2-3 hours)
2. **Preview Panel** - Large asset preview (4-5 hours)
3. **Enhanced Drag & Drop** - Drop to viewport (2-3 hours)

### Medium Term:
4. **Real Playblast** - Safe implementation (6-8 hours)
5. **Collection System** - Virtual folders (3-4 hours)
6. **Asset Metadata** - Scene stats display (3-4 hours)

### Long Term:
7. **Batch Operations** - Rename, convert, export (3-4 hours)
8. **Version Control** - Git/Perforce integration (4-6 hours)
9. **Theme Support** - Dark/Light themes (2-3 hours)

---

## 🎉 Achievements

### What Makes This Special:

1. **Fast** - 10x faster than Maya's Content Browser
2. **Visual** - Beautiful thumbnails without opening files
3. **Safe** - No crashes, no file opening
4. **Feature-Rich** - Filters, sorting, shortcuts, menus
5. **Professional** - Production-ready code quality
6. **Extensible** - Clean architecture, easy to add features
7. **User-Friendly** - Intuitive Maya-style workflow
8. **Efficient** - Smart caching, background processing
9. **Stable** - No known bugs, handles edge cases
10. **Well-Documented** - Comprehensive docs and examples
11. **Configurable** - ✨ Complete settings GUI with 4 categories
12. **Batch Renamer** - ✨ Multi-rule system with live preview

---

## � Development Roadmap Timeline

### **Q4 2025 - v3.0 (Smart Import & Metadata)**

**Week 1-2: Smart Import Functions** 🧠
- Integrate existing shader graph builder
- Implement texture pattern detection
- Add SkyDome auto-linker
- Test with various naming conventions

**Week 3: Star/Color System** ⭐
- Design rating UI overlay
- Implement color label system
- Add keyboard shortcuts
- Create ratings.json storage

**Week 4-5: Tag System** 🏷️
- Design tag UI dialog
- Implement tag autocomplete
- Add tag hierarchy support
- Create tag database

**Week 6-7: Collection System** 📁
- Design collection UI
- Implement smart collections
- Add manual collections
- Test collection rules

### **Q1 2026 - v3.5 (Polish & Advanced Features)**

**Week 1-2: Texture Converter** 🎨
- Research OpenImageIO integration
- Implement batch conversion
- Add color space handling
- Test with various formats

**Week 3-4: Polish & Testing**
- Bug fixes
- Performance optimization
- User testing
- Documentation updates

---

## �📝 Notes

### Development Notes & Lessons:

**Shader Graph Builder Integration (Existing Code):**
- ✅ Shader graph builder already implemented separately
- 📝 Integration task: Connect to browser's import system
- 💡 Advantage: Can test and validate patterns before integration
- 🎯 Goal: Right-click textures → "Auto-Generate Material"

**Texture Converter Challenges (Past Experience):**
- ⚠️ Previous attempts were complex
- 📚 Lessons learned will help new implementation
- 💡 Solution: Use OpenImageIO (ships with Maya!)
- 🔍 Key issues to solve:
  - Color space preservation
  - 16/32-bit data handling
  - Metadata preservation
  - Multi-channel EXR support

**Star/Color + Tag Integration:**
- 💭 Considering unified metadata system
- 🎨 Colors could act as quick visual tags
- 📊 Single JSON database vs separate files?
- 🔄 Decision: Build Star/Color first, see if merge makes sense

---

### Design Decisions:

1. **Safe Mode First** - Stability over features
2. **Performance Focus** - Background processing, caching
3. **Maya-Style UX** - Middle-drag, familiar shortcuts
4. **Modular Design** - Easy to extend and maintain
5. **Comprehensive Docs** - Every phase documented
6. **Settings-Driven** - ✨ User preferences with JSON persistence
7. **Rule-Based Batch Ops** - ✨ Sequential multi-rule processing

### Lessons Learned:

1. **Thread Safety Matters** - Maya API requires careful handling
2. **Caching is Critical** - Dual cache system essential
3. **UX is Everything** - Small details make big difference
4. **Testing is Key** - Safe mode prevents production issues
5. **Documentation Saves Time** - Future self will thank you

---

## 🎯 Summary

**DD Content Browser v2.4.1** is a **fully functional**, **production-ready** asset browser for Maya with:

- ✅ **Navigation Panel Restructure** (v2.4.1) - Recent dropdown, tab system, multi-select favorites
- ✅ **Performance Optimizations** (v2.4.0) - os.scandir(), lazy loading, intelligent caching (1785x faster!)
- ✅ **Multi-Rule Batch Renamer** (v2.3) - 7 rule types with live preview
- ✅ **Complete Settings System** (v2.3) - GUI configuration with 4 categories
- ✅ **Open File Feature** (v2.3.1) - Windows default program integration  
- ✅ **Text Preview Bug Fix** (v2.3.1) - Smooth separator dragging
- ✅ **16/32-bit TIFF Support** (v2.2) - High bit-depth preview
- ✅ **HDR/EXR Support** (v2.1) - Professional exposure control
- ✅ **Advanced Features** (v2.0) - Filters, sorting, shortcuts
- ✅ **Professional Quality** (Clean code, comprehensive docs)
- ✅ **Daily Use Ready** (Stable, fast, intuitive)

### 🆕 **Today's Updates (v2.4.1 - October 16, 2025):**
- 🎨 **UI Polish:** Recent folders dropdown with clock icon (🕒), elegant hover effect
- 📑 **Tab System:** Collections & Advanced Filters tabs (placeholders for future features)
- �️ **Multi-Select:** Remove multiple favorites at once with batch deletion
- 🐛 **Bug Fix:** Include Subfolders checkbox now works correctly (cache bypass)
- 🎯 **Consistency:** All UI elements use settings-based font (widgets.UI_FONT)

### 🚀 **Performance Highlights (v2.4.0):**
- ⚡ **54x faster** directory scanning with os.scandir()
- 💾 **1785x faster** on cached reload (12.5s → 0.007s)
- 🧠 **Lazy loading** - Metadata loaded only when needed
- � **Intelligent cache** - 5min TTL, mtime validation, max 20 dirs

### 📅 **Coming Soon (v3.0):**
- 🧠 **Smart Import** - Auto-generate materials from textures (existing shader graph!)
- ⭐ **Star/Color System** - Adobe Bridge-style ratings
- 🏷️ **Tag System** - Advanced metadata editor
- 📁 **Collection System** - Smart & manual collections (tab ready!)
- 🎨 **Texture Converter** - Batch format conversion

**Current Status:** v2.5.0-dev Tag System Phase 1 & 2 Complete! 🚀  
**Next Phase:** v3.0 Star Rating & Color Labels! 🎯

---

*For detailed usage instructions, see `README.md`*  
*For batch rename guide, see `BATCH_RENAME_GUIDE.md`*  
*For settings documentation, see `SETTINGS_GUIDE.md`*  
*For troubleshooting, see `TROUBLESHOOTING.md`*
