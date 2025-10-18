# Settings Panel Guide

## Overview
The ddContentBrowser Settings panel provides comprehensive control over application behavior, appearance, and file handling.

## Settings File Location
**New in v2.3.1:** Settings are now stored in the script directory for version control and easy updates:
- **Location**: `Documents\maya\2026\scripts\ddContentBrowser\settings.json`
- **Benefits**: 
  - ✅ Updates automatically with tool updates
  - ✅ Version controlled (can be committed to Git)
  - ✅ Easy backup with script folder
  - ✅ Can be shared across team

**Note:** Cache files remain in user home directory (`~/.dd_browser_thumbnails/`) to avoid bloating the script folder.

## Accessing Settings
- **Menu**: `Settings → Preferences...`
- **Keyboard**: (Future: Ctrl+,)

---

## Settings Tabs

### 1. 🏠 General Tab

#### Startup
- **Startup Directory**: Default folder when launching browser
  - Click "Browse..." to select
  - Leave empty to use last visited location

#### Window
- **Remember window size and position**: Persist window geometry across sessions
- **Width/Height**: Default window size (800-2560 pixels)

#### Behavior
- **Confirm before deleting files**: Show confirmation dialog on delete
- **Auto-refresh directory**: Automatically detect file changes
  - **Refresh interval**: How often to check (1-60 seconds)

---

### 2. 🖼️ Thumbnails Tab

#### Thumbnail Size
- **Size slider**: Choose from 32, 64, 128, 256, or 512 pixels
- Larger = more detail, slower generation
- Can also adjust with **Ctrl+Scroll** in grid mode

#### Quality
- **Low (Fast)**: Quick generation, lower quality
- **Medium**: Balanced (recommended)
- **High (Slow)**: Best quality, slower

#### Generate for 3D
- **Generate thumbnails for 3D files**: Enable/disable 3D thumbnail generation
  - Currently shows colored placeholders only
  - Future: Maya viewport snapshots

#### Cache
- **Cache Size Limit**: Maximum disk space for thumbnails (50-5000 MB)
- **Current cache size**: Shows actual disk usage
- **Clear Cache**: Delete all cached thumbnails (regenerate on next view)

---

### 3. 👁️ Preview Tab

#### Preview Resolution
- **512 px (Fast)**: Quick previews, lower quality
- **1024 px (Balanced)**: Default, good balance
- **2048 px (High Quality)**: Sharp previews, slower HDR
- **4096 px (Maximum)**: Maximum quality, slowest

⚠️ Higher resolution = slower HDR/EXR processing

#### HDR/EXR Settings
- **Raw HDR Cache Size**: Number of HDR files to keep in memory (1-20)
  - Each cached file uses ~20-30 MB RAM
  - Faster switching between HDR images
- **Default Exposure**: Starting exposure value (-10 to +10 EV)

#### Display
- **Auto-fit images to window**: Automatically scale images to fit preview panel

---

### 4. 🔍 Filters Tab

#### Supported File Types
**Currently Built-in:**
- Maya: `.ma`, `.mb`
- 3D Models: `.obj`, `.fbx`, `.abc`, `.usd`, `.vdb`
- Images: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.tga`
- HDR/EXR: `.hdr`, `.exr`
- Scripts: `.mel`, `.py`

#### Custom File Extensions
**Add your own file types!**

Example: `.gltf, .blend, .max`

- Enter comma-separated extensions
- Dot (`.`) is optional (auto-added if missing)
- Case-insensitive
- Files will appear with gray placeholder icons
- **Active custom extensions**: Shows currently loaded extensions in cyan

**Use Cases:**
- Blender files: `.blend`
- glTF models: `.gltf`, `.glb`
- 3ds Max: `.max`
- Substance: `.sbs`, `.sbsar`
- Houdini: `.hip`, `.hipnc`
- Any custom format!

#### Visibility
- **Show hidden files**: Display files/folders starting with `.` (dot)

#### Search Options
- **Case-sensitive search**: Match exact case in search queries
- **Enable regex search**: Use regular expressions in search bar
  - Click the `.*` button in search bar to toggle
  - Example: `texture_\d+` matches `texture_001`, `texture_002`, etc.

---

## Settings Persistence

- **Location**: `~/.ddContentBrowser/settings.json`
- **Auto-save**: Changes saved when clicking "OK"
- **Restore Defaults**: Click button at bottom to reset all settings

---

## Tips & Tricks

### Performance
1. Lower thumbnail size for faster browsing
2. Reduce preview resolution if HDR/EXR feels slow
3. Limit HDR cache size on systems with low RAM
4. Use "Low" quality for quick scans of large folders

### Workflow
1. Set startup directory to your main asset folder
2. Enable auto-refresh when working with external apps
3. Add custom extensions for your pipeline (e.g., `.blend`, `.gltf`)
4. Use regex search for pattern-based file finding

### Storage
- Cache size shows actual disk usage
- Clear cache periodically to free space
- Thumbnails regenerate automatically when needed

---

## Troubleshooting

### Custom extensions not appearing
1. Check Settings → Filters → Custom File Extensions
2. Ensure extensions are comma-separated (e.g., `.gltf, .blend`)
3. Click OK to save and apply
4. Navigate to a different folder and back to refresh

### Settings not persisting
- Settings are stored in the script directory: `Documents\maya\2026\scripts\ddContentBrowser\settings.json`
- This file is version-controlled and updates with the tool
- Click "OK" to save (not "Cancel")
- Check console for save errors
- If settings file is missing, it will be recreated with defaults

### Thumbnails not generating
- Check thumbnail size isn't too large (>512 can be slow)
- Clear cache and retry
- Check disk space for cache directory
- Some formats show colored placeholders (scripts, 3D files)

---

## Future Features
- Keyboard shortcut for settings (Ctrl+,)
- Per-folder thumbnail settings
- Custom thumbnail generation scripts
- Export/import settings profiles
