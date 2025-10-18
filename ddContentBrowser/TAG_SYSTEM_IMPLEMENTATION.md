# Tag System Implementation Guide

**Created:** October 17, 2025  
**Status:** ✅ Phase 1 Complete - Basic Integration Working!  
**Last Updated:** October 17, 2025

---

## 🎉 Implementation Progress

### ✅ **Phase 1: Core Backend & Preview Panel Integration** (COMPLETE!)

**Completed Today - October 17, 2025:**

1. ✅ **`metadata.py` created** - Full SQLite backend implementation
   - MetadataManager class with all CRUD operations
   - Database schema (file_metadata, tags, file_tags tables)
   - Search & filter methods
   - Singleton pattern with auto-initialization
   - Default tags loader

2. ✅ **`default_tags.json` created** - Production-ready tag structure
   - 7 categories (Asset Type, Environment, Lighting, Source, Technical, Material, Status)
   - 75+ tags optimized for Environment/Lighting artists
   - Color-coded categories

3. ✅ **Preview Panel Tags Tab - Full Integration**
   - `add_tag()` - Now saves to database via MetadataManager
   - `create_tag_chip()` - Stores tag_id for database operations
   - `remove_tag_chip()` - Removes from database when deleted
   - `load_tags()` - Loads tags from database when file selected
   - `setup_tag_autocomplete()` - QCompleter with all available tags
   - Auto-load tags when selecting files

4. ✅ **QCompleter Integration** - Autocomplete working
   - Case-insensitive matching
   - Popup completion mode
   - Loads all tags from database

5. ✅ **Database Initialization**
   - Singleton pattern ensures one instance
   - Auto-creates tables on first run
   - Auto-loads default tags if database empty

---

## Files Created/Modified

### ✅ Created:
- `metadata.py` (~400 lines) - SQLite backend
- `default_tags.json` (~100 lines) - Default tag structure

### ✅ Modified:
- `widgets.py`:
  - Added QCompleter import
  - Updated `add_tag()` method (lines ~3420-3450)
  - Updated `create_tag_chip()` method (stores tag_id)
  - Updated `remove_tag_chip()` method (removes from DB)
  - Updated `load_tags()` method (loads from DB)
  - Added `setup_tag_autocomplete()` method
  - Added `self.load_tags(asset)` call in `show_single_file()`

---

## 🧪 Testing Instructions

### Test 1: Database Creation
```python
# In Maya Script Editor:
from ddContentBrowser.metadata import get_metadata_manager

mm = get_metadata_manager()
print(f"Database: {mm.db_path}")
# Expected: C:/Users/YourName/.ddContentBrowser/tags.db

# Check default tags loaded
tags = mm.get_tags_by_category()
for category, tag_list in tags.items():
    print(f"\n{category}: {len(tag_list)} tags")
# Expected: 7 categories with ~75 tags total
```

### Test 2: Tag System in Browser
```python
# Launch browser
import ddContentBrowser
ddContentBrowser.show_content_browser()

# 1. Select any file
# 2. Click Tags tab in Preview Panel
# 3. Start typing in tag input - autocomplete should show suggestions
# 4. Add a tag (e.g., "HDRI / Skydome")
# 5. Tag chip should appear
# 6. Click X on tag chip - should be removed
# 7. Select different file - tags should clear
# 8. Select first file again - tag should reload!
```

### Test 3: Tag Persistence
```python
# After adding tags, query database:
from ddContentBrowser.metadata import get_metadata_manager

mm = get_metadata_manager()
file_path = "D:/your_test_file.ma"  # Replace with actual file

metadata = mm.get_file_metadata(file_path)
print(f"Tags for {file_path}:")
for tag in metadata['tags']:
    print(f"  - {tag['name']} (category: {tag['category']})")
```

---

## Overview

Implement SQLite-based tag/rating/color system for DD Content Browser.

**Storage Location:** `~/.ddContentBrowser/tags.db`  
**GUI Reference:** Apple Photos-style hierarchical tag panel (see attached screenshot)

---

## Decision Summary

✅ **Storage:** SQLite database (not Windows metadata - Maya files don't support it)  
✅ **Location:** User home directory (`~/.ddContentBrowser/`)  
✅ **Hierarchy:** Collapsible categories with checkboxes  
✅ **Default Tags:** Environment/Lighting artist focused

---

## Files to Create

### 1. `default_tags.json`

Location: Project root  
Purpose: Default tag structure for first-time setup

```json
{
  "Asset Type": {
    "color": "#4CAF50",
    "description": "Type of asset or file",
    "tags": [
      "HDRI / Skydome",
      "Texture Set",
      "PBR Material",
      "Tileable Texture",
      "3D Model",
      "Environment Prop",
      "Vegetation",
      "Rock / Ground",
      "Reference Image",
      "Concept Art",
      "Camera / Lens Data"
    ]
  },
  "Environment": {
    "color": "#2196F3",
    "description": "Environment category and setting",
    "tags": [
      "Natural / Forest",
      "Natural / Jungle",
      "Natural / Desert",
      "Natural / Mountain",
      "Natural / Rock",
      "Natural / Water",
      "Natural / Ocean",
      "Natural / Sky",
      "Urban / Street",
      "Urban / Road",
      "Urban / Building",
      "Urban / Architecture",
      "Urban / Industrial",
      "Interior / Room",
      "Interior / Props",
      "Interior / Furniture"
    ]
  },
  "Lighting": {
    "color": "#FF9800",
    "description": "Lighting and time of day",
    "tags": [
      "Day / Morning",
      "Day / Noon",
      "Day / Afternoon",
      "Evening / Golden Hour",
      "Night / Blue Hour",
      "Night / Moonlight",
      "Night / City Lights",
      "Overcast / Cloudy",
      "Sunset / Sunrise",
      "Studio / Neutral"
    ]
  },
  "Source": {
    "color": "#9C27B0",
    "description": "Origin or source of asset",
    "tags": [
      "Quixel Megascans",
      "Polyhaven",
      "HDRI Haven",
      "Texture Haven",
      "Personal Work",
      "Client Project",
      "Free Asset",
      "Purchased Asset"
    ]
  },
  "Technical": {
    "color": "#607D8B",
    "description": "Technical specifications",
    "tags": [
      "8K / High Resolution",
      "4K / Medium Resolution",
      "2K / Low Resolution",
      "UDIM",
      "Tileable",
      "LOD Available",
      "Scanned / Photogrammetry",
      "Procedural"
    ]
  },
  "Material": {
    "color": "#795548",
    "description": "Material type or surface",
    "tags": [
      "Concrete",
      "Metal",
      "Wood",
      "Fabric / Cloth",
      "Stone / Rock",
      "Ground / Dirt",
      "Grass / Vegetation",
      "Water",
      "Glass / Transparent",
      "Plastic",
      "Ceramic",
      "Brick"
    ]
  },
  "Status": {
    "color": "#F44336",
    "description": "Project status and usage",
    "tags": [
      "Favorite / Go-to",
      "Frequently Used",
      "Ready to Use",
      "Work In Progress",
      "Needs Cleanup",
      "Archive",
      "Hero Asset",
      "Background Asset",
      "Test / Experiment"
    ]
  }
}
```

---

### 2. `metadata.py`

Location: Project root  
Purpose: SQLite database operations for tags/ratings/colors

```python
"""
DD Content Browser - Metadata Module
SQLite-based tag, rating, and color label system
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class MetadataManager:
    """Manage file metadata (tags, ratings, colors) in SQLite database"""
    
    def __init__(self, db_path: Path = None):
        """
        Initialize metadata manager
        
        Args:
            db_path: Path to SQLite database (default: ~/.ddContentBrowser/tags.db)
        """
        if db_path is None:
            from .utils import get_metadata_db_path
            db_path = get_metadata_db_path()
        
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection and create tables if needed"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        
        cursor = self.conn.cursor()
        
        # File metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_path TEXT PRIMARY KEY,
                rating INTEGER DEFAULT 0,
                color_label TEXT DEFAULT NULL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tags table (hierarchical)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT DEFAULT NULL,
                color TEXT DEFAULT NULL,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES tags(id)
            )
        ''')
        
        # File-tag relationship (many-to-many)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_tags (
                file_path TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (file_path, tag_id),
                FOREIGN KEY (file_path) REFERENCES file_metadata(file_path),
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_rating ON file_metadata(rating)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_color ON file_metadata(color_label)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tag_category ON tags(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_tags_path ON file_tags(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id)')
        
        self.conn.commit()
    
    def load_default_tags(self, json_path: Path = None):
        """
        Load default tags from JSON file
        
        Args:
            json_path: Path to default_tags.json (default: script dir)
        """
        if json_path is None:
            script_dir = Path(__file__).parent
            json_path = script_dir / "default_tags.json"
        
        if not json_path.exists():
            print(f"Warning: {json_path} not found, skipping default tags")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            default_tags = json.load(f)
        
        cursor = self.conn.cursor()
        
        for category, data in default_tags.items():
            color = data.get("color", None)
            tags = data.get("tags", [])
            
            for tag_name in tags:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO tags (name, category, color)
                        VALUES (?, ?, ?)
                    ''', (tag_name, category, color))
                except sqlite3.IntegrityError:
                    pass  # Tag already exists
        
        self.conn.commit()
        print(f"Loaded default tags from {json_path}")
    
    # ========================================================================
    # TAG OPERATIONS
    # ========================================================================
    
    def add_tag(self, tag_name: str, category: str = None, color: str = None) -> int:
        """Add new tag to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO tags (name, category, color)
            VALUES (?, ?, ?)
        ''', (tag_name, category, color))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_tags(self) -> List[Dict]:
        """Get all tags grouped by category"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tags ORDER BY category, name')
        
        tags = []
        for row in cursor.fetchall():
            tags.append({
                'id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'color': row['color']
            })
        return tags
    
    def get_tags_by_category(self) -> Dict[str, List[Dict]]:
        """Get tags grouped by category"""
        tags = self.get_all_tags()
        grouped = {}
        
        for tag in tags:
            category = tag['category'] or 'Uncategorized'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(tag)
        
        return grouped
    
    # ========================================================================
    # FILE METADATA OPERATIONS
    # ========================================================================
    
    def set_file_rating(self, file_path: str, rating: int):
        """Set rating for file (0-5 stars)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO file_metadata (file_path, rating, date_modified)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) DO UPDATE SET
                rating = excluded.rating,
                date_modified = CURRENT_TIMESTAMP
        ''', (file_path, rating))
        self.conn.commit()
    
    def set_file_color(self, file_path: str, color: str):
        """Set color label for file"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO file_metadata (file_path, color_label, date_modified)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) DO UPDATE SET
                color_label = excluded.color_label,
                date_modified = CURRENT_TIMESTAMP
        ''', (file_path, color))
        self.conn.commit()
    
    def add_tag_to_file(self, file_path: str, tag_id: int):
        """Add tag to file"""
        cursor = self.conn.cursor()
        
        # Ensure file exists in file_metadata
        cursor.execute('''
            INSERT OR IGNORE INTO file_metadata (file_path)
            VALUES (?)
        ''', (file_path,))
        
        # Add tag relationship
        cursor.execute('''
            INSERT OR IGNORE INTO file_tags (file_path, tag_id)
            VALUES (?, ?)
        ''', (file_path, tag_id))
        
        self.conn.commit()
    
    def remove_tag_from_file(self, file_path: str, tag_id: int):
        """Remove tag from file"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM file_tags
            WHERE file_path = ? AND tag_id = ?
        ''', (file_path, tag_id))
        self.conn.commit()
    
    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        """Get all metadata for a file"""
        cursor = self.conn.cursor()
        
        # Get basic metadata
        cursor.execute('''
            SELECT * FROM file_metadata WHERE file_path = ?
        ''', (file_path,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        metadata = {
            'file_path': row['file_path'],
            'rating': row['rating'],
            'color_label': row['color_label'],
            'date_added': row['date_added'],
            'date_modified': row['date_modified']
        }
        
        # Get tags
        cursor.execute('''
            SELECT t.* FROM tags t
            JOIN file_tags ft ON t.id = ft.tag_id
            WHERE ft.file_path = ?
        ''', (file_path,))
        
        metadata['tags'] = []
        for tag_row in cursor.fetchall():
            metadata['tags'].append({
                'id': tag_row['id'],
                'name': tag_row['name'],
                'category': tag_row['category'],
                'color': tag_row['color']
            })
        
        return metadata
    
    # ========================================================================
    # SEARCH & FILTER
    # ========================================================================
    
    def search_files_by_tags(self, tag_ids: List[int], match_all: bool = False) -> List[str]:
        """
        Search files by tags
        
        Args:
            tag_ids: List of tag IDs to search for
            match_all: If True, file must have ALL tags; if False, ANY tag
        
        Returns:
            List of file paths
        """
        if not tag_ids:
            return []
        
        cursor = self.conn.cursor()
        
        if match_all:
            # File must have ALL tags
            placeholders = ','.join('?' * len(tag_ids))
            query = f'''
                SELECT file_path FROM file_tags
                WHERE tag_id IN ({placeholders})
                GROUP BY file_path
                HAVING COUNT(DISTINCT tag_id) = ?
            '''
            cursor.execute(query, tag_ids + [len(tag_ids)])
        else:
            # File must have ANY tag
            placeholders = ','.join('?' * len(tag_ids))
            query = f'''
                SELECT DISTINCT file_path FROM file_tags
                WHERE tag_id IN ({placeholders})
            '''
            cursor.execute(query, tag_ids)
        
        return [row[0] for row in cursor.fetchall()]
    
    def filter_files_by_rating(self, min_rating: int = 0, max_rating: int = 5) -> List[str]:
        """Get files with rating in range"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT file_path FROM file_metadata
            WHERE rating >= ? AND rating <= ?
        ''', (min_rating, max_rating))
        return [row[0] for row in cursor.fetchall()]
    
    def filter_files_by_color(self, colors: List[str]) -> List[str]:
        """Get files with specific color labels"""
        if not colors:
            return []
        
        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(colors))
        query = f'''
            SELECT file_path FROM file_metadata
            WHERE color_label IN ({placeholders})
        '''
        cursor.execute(query, colors)
        return [row[0] for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton instance
_metadata_manager = None

def get_metadata_manager() -> MetadataManager:
    """Get or create singleton MetadataManager instance"""
    global _metadata_manager
    if _metadata_manager is None:
        _metadata_manager = MetadataManager()
        
        # Load default tags on first init if database is empty
        cursor = _metadata_manager.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tags')
        tag_count = cursor.fetchone()[0]
        
        if tag_count == 0:
            _metadata_manager.load_default_tags()
    
    return _metadata_manager
```

---

## Already Completed

✅ **utils.py** - Added helper functions:
- `get_metadata_db_path()` - Returns `~/.ddContentBrowser/tags.db`
- `get_browser_data_dir()` - Returns `~/.ddContentBrowser/`

---

## Database Schema

```sql
-- File metadata (rating, color label)
CREATE TABLE file_metadata (
    file_path TEXT PRIMARY KEY,
    rating INTEGER DEFAULT 0,           -- 0-5 stars
    color_label TEXT DEFAULT NULL,      -- Red, Orange, Yellow, etc.
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tags (hierarchical)
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT NULL,         -- Asset Type, Lighting, etc.
    color TEXT DEFAULT NULL,            -- Hex color for UI
    parent_id INTEGER,                  -- For future hierarchy
    FOREIGN KEY (parent_id) REFERENCES tags(id)
);

-- File-tag relationship (many-to-many)
CREATE TABLE file_tags (
    file_path TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (file_path, tag_id),
    FOREIGN KEY (file_path) REFERENCES file_metadata(file_path),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- Performance indexes
CREATE INDEX idx_file_rating ON file_metadata(rating);
CREATE INDEX idx_file_color ON file_metadata(color_label);
CREATE INDEX idx_tag_category ON tags(category);
CREATE INDEX idx_file_tags_path ON file_tags(file_path);
CREATE INDEX idx_file_tags_tag ON file_tags(tag_id);
```

---

## GUI Integration Plan

### 1. Preview Panel - Tags Tab (ALREADY EXISTS!)

Location: `widgets.py` - PreviewPanel class, Tags tab  
Current: Empty placeholder with "No tags assigned" label

**Update needed:**
- Show tag chips for selected file
- Add tag input/autocomplete
- Load tags from MetadataManager
- Save tags on add/remove

### 2. New Widget: Tag Filter Panel

Similar to existing FilterPanel, but for tags:
- Collapsible category tree (like screenshot)
- Checkboxes for each tag
- Multi-select support
- "Match All" vs "Match Any" toggle

### 3. Thumbnail Overlay

Optional: Show small tag badges on thumbnails (Phase 2)

---

## Testing Commands

```python
# Test database init
from metadata import get_metadata_manager

mm = get_metadata_manager()
print(f"Database: {mm.db_path}")

# Check default tags loaded
tags = mm.get_tags_by_category()
for category, tag_list in tags.items():
    print(f"\n{category}:")
    for tag in tag_list:
        print(f"  - {tag['name']}")

# Test adding metadata to file
test_file = "D:/test.ma"
mm.set_file_rating(test_file, 5)
mm.set_file_color(test_file, "Red")

# Add tags
hdri_tag = mm.add_tag("HDRI / Skydome", "Asset Type", "#4CAF50")
mm.add_tag_to_file(test_file, hdri_tag)

# Retrieve
metadata = mm.get_file_metadata(test_file)
print(f"\nMetadata: {metadata}")

# Search
files = mm.search_files_by_tags([hdri_tag])
print(f"\nFiles with HDRI tag: {files}")
```

---

## Next Steps (At Home)

1. ✅ Create `default_tags.json` (this file blocked by firewall)
2. ✅ Create `metadata.py` module
3. Test database creation
4. Test default tags loading
5. Integrate with Preview Panel Tags tab
6. Create Tag Filter Panel widget
7. Add keyboard shortcuts (1-5 for rating, Ctrl+1-7 for colors)

---

## Notes

- **Cross-platform:** SQLite works on Windows/Linux/macOS
- **Performance:** Indexed for fast search/filter
- **Scalable:** Can handle thousands of files
- **Backup-friendly:** Single .db file to backup
- **Future:** Can add full-text search, tag aliases, smart collections

---

*Resume from here when at home!* 🏠
