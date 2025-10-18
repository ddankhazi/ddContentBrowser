# UI Font Configuration

## Single Source of Truth

The UI font for the entire application is defined in **ONE PLACE** at the top of each module:

### widgets.py (line ~10):
```python
UI_FONT = "Segoe UI"
```

### delegates.py (line ~10):
```python
UI_FONT = "Segoe UI"
```

## Benefits

1. **Easy to change**: Modify one constant instead of 20+ hardcoded strings
2. **Consistent**: All UI elements use the same font
3. **Maintainable**: No need to search through entire codebase
4. **Extensible**: Can be loaded from settings.json in the future

## How to Change

Simply change the `UI_FONT` constant:

```python
UI_FONT = "Segoe UI"  # Windows modern font
UI_FONT = "San Francisco"  # macOS native font
UI_FONT = "Roboto"  # Material Design
```

## Future Enhancement

The font could be loaded from settings:

```json
{
  "general": {
    "ui_font": "Arial"
  }
}
```

And then in __init__ or startup:
```python
from .settings import SettingsManager
settings = SettingsManager()
UI_FONT = settings.get("general", "ui_font", "Arial")
```

## Current Usage

All UI elements now reference `UI_FONT` constant:
- Breadcrumb navigation
- Search bar
- Labels and text
- Metadata panel
- List/Grid view text
- Thumbnail placeholders
