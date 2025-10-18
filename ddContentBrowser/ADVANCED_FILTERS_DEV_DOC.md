# Advanced Filters - Fejlesztői Dokumentáció

## Áttekintés
Az Advanced Filters modul egy komplex szűrési rendszert biztosít a ddContentBrowser-hez, amely lehetővé teszi a felhasználók számára többszintű, kombinált szűrések végrehajtását.

## Fájl: `advanced_filters.py`

### Főbb osztályok

#### `FilterPreset`
Egy mentett szűrő preset reprezentációja.

**Attribútumok:**
- `name` (str): A preset neve
- `filter_config` (dict): Szűrő konfiguráció dictionary

**Metódusok:**
- `to_dict()`: JSON szerializáláshoz konvertál
- `from_dict(data)`: Dictionary-ből létrehoz egy FilterPreset-et

#### `AdvancedFiltersPanel(QWidget)`
A fő advanced filters panel widget.

**Signals:**
- `filter_applied(dict)`: Amikor szűrő alkalmazásra kerül
- `filter_cleared()`: Amikor szűrők törlésre kerülnek

**Constructor paraméterek:**
- `file_model`: FileSystemModel referencia
- `settings_manager`: SettingsManager referencia (optional)
- `parent`: Qt parent widget (optional)

### Funkciók

#### 1. Quick Filters (Gyors szűrők)
Előre definiált gombok gyors szűréshez:

**Időalapú:**
- Today (Ma)
- This Week (Ez a hét)
- This Month (Ez a hónap)

**Méret alapú:**
- < 10 MB
- 10-100 MB
- \> 100 MB

**Típus alapú:**
- Maya Scenes (.ma, .mb)
- Images (összes image formátum)
- Scripts (.mel, .py, .txt)
- 3D Models (.obj, .fbx, .abc, .usd, .vdb)
- HDR/EXR (.hdr, .exr)

#### 2. Custom Filters (Egyedi szűrők)

**Name Pattern:**
- Fájlnév minta wildcard-okkal
- Példa: `*_proxy`, `char_*`
- Konvertálódik regex-é

**Extensions:**
- Egyedi extension lista
- Példa: `.ma, .mb, .obj`

**Size Range:**
- Min/Max méret MB-ban
- Felülírja a quick size filtereket ha be van állítva

#### 3. Saved Presets (Mentett presetek)
Felhasználók menthetik az aktuális szűrő beállításokat:
- Név megadása
- Mentés a settings.json-ba
- Újratöltés duplakattintással
- Törlés lehetséges

### Integráció a Browser-rel

**Browser.py változások:**

1. **Import:**
```python
from .advanced_filters import AdvancedFiltersPanel
```

2. **Panel inicializálás:**
```python
self.advanced_filters_panel = AdvancedFiltersPanel(self.file_model, self.settings_manager)
self.advanced_filters_panel.filter_applied.connect(self.on_advanced_filter_applied)
self.advanced_filters_panel.filter_cleared.connect(self.on_advanced_filter_cleared)
```

3. **Callback metódusok:**
- `on_advanced_filter_applied(filter_config)`: Szűrő alkalmazás kezelése
- `on_advanced_filter_cleared()`: Szűrő törlés kezelése

### Filter Configuration Format

```python
{
    "quick_filters": {
        "time": "today" | "week" | "month" | None,
        "size": "small" | "medium" | "large" | None,
        "types": ["maya", "images", "scripts", "3d_models", "hdr"]
    },
    "custom_filters": {
        "name_pattern": "*.ma",
        "extensions": [".ma", ".mb"],
        "size_min_mb": 0,
        "size_max_mb": 100
    }
}
```

### Settings Integration

**settings.json structure:**
```json
{
    "advanced_filters": {
        "saved_presets": [
            {
                "name": "My Preset",
                "filter_config": { ... }
            }
        ]
    }
}
```

## Használat

### Felhasználói perspektíva:

1. **Quick Filter alkalmazása:**
   - Kattints egy quick filter gombra
   - Kattints "Apply Filters"
   - Csak a szűrt fájlok látszanak

2. **Custom Filter:**
   - Adj meg name pattern-t: `*_high`
   - Vagy extension listát: `.ma, .mb`
   - Állítsd be size range-t
   - Apply Filters

3. **Preset mentése:**
   - Állítsd be a kívánt szűrőket
   - "Save Current" gomb
   - Adj nevet a preset-nek
   - OK

4. **Preset betöltése:**
   - Dupla klikk a preset-re a listában
   - Vagy jelöld ki és "Load" gomb

5. **Összes szűrő törlése:**
   - "Clear All" gomb
   - Minden szűrő törlődik, összes fájl látszik

## Továbbfejlesztési lehetőségek

### Phase 2:
- [ ] AND/OR logic kombinációk
- [ ] Wildcard pattern preview
- [ ] Regex builder UI
- [ ] Filter history (undo/redo)

### Phase 3:
- [ ] Tag system (user-defined tags)
- [ ] Tag-based filtering
- [ ] Compound filters (nested groups)
- [ ] Filter templates export/import

### Phase 4:
- [ ] Smart filters (machine learning)
- [ ] Recent files detection
- [ ] Duplicate file finder
- [ ] File relationship mapping

## Debug Mode

```python
DEBUG_MODE = True  # advanced_filters.py tetején
```

Debug üzenetek:
- Filter alkalmazás
- Preset mentés/töltés
- Config változások

## Példa workflow

```python
# 1. User betölt egy preset-et
advanced_filters.load_preset("Large Maya Scenes")

# 2. Módosít rajta (hozzáad egy date filter-t)
advanced_filters.week_btn.setChecked(True)

# 3. Alkalmazza
advanced_filters.apply_filters()
# -> filter_applied signal -> browser.on_advanced_filter_applied()
# -> file_model.refresh() -> UI update

# 4. Menti új preset-ként
advanced_filters.save_current_preset("Large Recent Maya Scenes")
```

## Known Issues / TODO

- [ ] Regex syntax ellenőrzés
- [ ] Wildcard pattern validáció
- [ ] Size filter conflict resolution (quick vs custom)
- [ ] Date picker UI (jelenleg csak quick filters)
- [ ] Filter performance optimization large directories-nél

## Tesztelés

Manual testing checklist:
- [ ] Quick time filters működnek
- [ ] Quick size filters működnek  
- [ ] Quick type filters kombinálhatóak
- [ ] Custom name pattern működik
- [ ] Custom extensions működnek
- [ ] Custom size range működik
- [ ] Preset mentés/töltés/törlés működik
- [ ] Clear All resetel mindent
- [ ] Filter applied signal helyes config-ot küld
- [ ] Browser UI frissül filter alkalmazáskor
- [ ] Thumbnails újragenerálódnak szűrés után
