# 🎨 Adobe Bridge Style Advanced Filters

## Implementáció Összefoglaló

### Új Fájlok:

1. **`metadata_extractor.py`** - Metadata kinyerő rendszer
2. **`advanced_filters_v2.py`** - Adobe Bridge stílusú filter UI

### Főbb Komponensek:

## 1. Metadata Extraction System

### `FileMetadata` osztály
Minden fájlhoz kinyeri:
- **Basic metadata:**
  - File name, type, size
  - Size category (Tiny/Small/Medium/Large/Huge)
  - Creation/modification dates
  - Type category (image/maya/3d_model/hdr/etc.)

- **Image-specific metadata (via PIL/Pillow):**
  - Dimensions (width x height)
  - Aspect ratio (Square/16:9/4:3/Panoramic/Portrait)
  - Color mode (RGB/RGBA/L/etc.)
  - Bit depth (8-bit/16-bit/32-bit)
  - EXIF data (camera model, orientation)

- **Maya-specific metadata:**
  - Scene type
  - (Later: referenced files, poly count)

- **3D model metadata:**
  - Format type (OBJ/FBX/Alembic/USD)

### `MetadataCache` osztály
- In-memory cache a metadata-hoz
- `get_or_create()` - lazy loading

## 2. Advanced Filters UI (Adobe Bridge Style)

### `FilterCategory` osztály
Egyetlen összecsukható filter kategória:
```
▼ File Type
  ☐ .ma (15)
  ☐ .jpg (42)
  ☐ .png (28)
```

**Features:**
- Collapsible (▼/▶ arrow)
- Checkboxes minden értékhez
- Count zárójelben
- Real-time selection tracking

### `AdvancedFiltersPanelV2` osztály

**UI Struktúra:**
```
┌─────────────────────────┐
│ 🔍 Filters    [✕ Clear] │ ← Toolbar
├─────────────────────────┤
│ ▼ File Type             │
│   ☐ .ma (15)            │
│   ☑ .jpg (42)           │
│ ▼ Category              │
│   ☑ image (70)          │
│   ☐ maya (15)           │
│ ▶ File Size             │ ← Collapsed
│ ▼ Dimensions            │
│   ☐ 1920 x 1080 (15)    │
│   ☐ 4096 x 4096 (8)     │
│ ▼ Aspect Ratio          │
│   ☐ 16:9 (20)           │
│   ☐ Square (10)         │
│ ...                     │
└─────────────────────────┘
```

**Dinamikus kategóriák:**
- File Type (.ma, .jpg, .png, etc.)
- Category (image, maya, 3d_model, etc.)
- File Size (Tiny/Small/Medium/Large/Huge)
- Dimensions (1920x1080, etc.)
- Aspect Ratio (16:9, 4:3, Square, etc.)
- Color Mode (RGB, RGBA, L, etc.)
- Bit Depth (8-bit, 16-bit, etc.)

**Logika:**
1. Új mappa betöltésekor: `analyze_current_files()`
2. Metadata extraction minden fájlhoz
3. Kategóriák építése value counts-szal
4. Checkbox kattintás → `on_category_selection_changed()`
5. Active filters alkalmazása (AND logic)
6. File model frissítése

## Integráció Browser-rel

### Import:
```python
from .advanced_filters_v2 import AdvancedFiltersPanelV2
```

### Inicializálás:
```python
def init_advanced_filters(self):
    self.advanced_filters_panel = AdvancedFiltersPanelV2(
        self.file_model, 
        self.settings_manager
    )
    self.advanced_filters_panel.filters_changed.connect(
        self.on_advanced_filters_changed
    )
    self.advanced_filters_panel.filters_cleared.connect(
        self.on_advanced_filters_cleared
    )
```

### Navigation refresh:
```python
def navigate_to_path(self, path):
    # ...
    QTimer.singleShot(200, self.advanced_filters_panel.refresh)
```

## Működés Flow:

```
User navigates to folder
    ↓
navigate_to_path()
    ↓
file_model.setPath() + refresh()
    ↓ (200ms delay)
advanced_filters_panel.refresh()
    ↓
analyze_current_files()
    ↓
For each asset:
    metadata_cache.get_or_create(asset.file_path)
        ↓
    FileMetadata extracts metadata
        ↓
    Returns metadata dict
    ↓
build_filter_categories(metadata_list)
    ↓
Count values per category
    ↓
Create/update FilterCategory widgets
    ↓
Display checkboxes with counts
```

## User Interaction Flow:

```
User checks ".jpg (42)"
    ↓
FilterCategory.on_checkbox_changed()
    ↓
Emit selection_changed signal
    ↓
AdvancedFiltersPanelV2.on_category_selection_changed()
    ↓
Update active_filters dict
    ↓
apply_active_filters()
    ↓
For each asset:
    Check if metadata matches ALL active filters (AND)
    ↓
Update file_model.assets with filtered list
    ↓
Emit layoutChanged signal
    ↓
Browser UI updates
```

## Styling (Dark Theme):

```css
/* Category Headers */
background: #2d2d2d
border: 1px solid #444

/* Checkboxes */
color: #ccc
hover: #fff
indicator: 13x13px

/* Toolbar */
background: #2a2a2a
padding: 4px

/* Scroll Area */
background: #252525
```

## Dependency: PIL/Pillow

Image metadata extraction requires PIL:
```python
try:
    from PIL import Image
    # Extract dimensions, color mode, EXIF
except ImportError:
    # Skip image-specific metadata
    pass
```

**Note:** PIL is optional - basic filtering works without it.

## Adobe Bridge Comparison:

### ✅ Implemented:
- Hierarchical collapsible categories
- Checkbox-based filtering
- Value counts in parentheses
- Multiple filters (AND logic)
- Clear all button
- Dark theme styling
- Dynamic category generation

### 🔄 Future Enhancements:
- Date range sliders (instead of just counts)
- Keywords/Tags system
- Color labels
- Rating system (stars)
- Custom metadata fields
- OR logic option (currently only AND)
- Filter presets/saved searches
- Search within filters

## Performance Considerations:

1. **Lazy metadata extraction:** Only when needed
2. **Metadata caching:** In-memory cache per session
3. **Efficient counting:** Single pass through assets
4. **Deferred refresh:** 200ms delay after navigation
5. **PIL lazy import:** Only loads if available

## Debug Mode:

Set `DEBUG_MODE = True` in both files to see:
- Metadata extraction messages
- Filter application logs
- Count updates

## Known Limitations:

1. **PIL dependency:** Image metadata requires Pillow
2. **No persistent cache:** Metadata re-extracted each session
3. **No background loading:** Blocks UI during analysis
4. **Limited 3D metadata:** No poly counts, vertex info
5. **No Maya scene parsing:** .ma files not analyzed

## Roadmap:

### Phase 1: ✅ DONE
- Basic metadata extraction
- Dynamic filter categories
- Checkbox filtering
- AND logic

### Phase 2: 🔄 TODO
- Date range filters (sliders)
- Persistent metadata cache (JSON/SQLite)
- Background metadata extraction (worker thread)
- Progress indicator

### Phase 3: 📋 PLANNED
- Tags system (user-defined)
- Rating system
- Color labels
- Search within filters

### Phase 4: 🚀 FUTURE
- Maya scene analysis (referenced files, poly count)
- 3D model statistics (vertices, faces)
- Texture resolution detection
- Smart collections
- Filter presets export/import
