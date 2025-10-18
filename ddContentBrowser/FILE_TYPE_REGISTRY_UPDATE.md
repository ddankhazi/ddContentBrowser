# File Type Registry - Központosított Fájlformátum Kezelés

## Összefoglaló

A fájlformátumok kezelését központosítottam egy **FILE_TYPE_REGISTRY** rendszerrel az `utils.py` fájlban.

## Mi változott?

### 1. **utils.py** - Új FILE_TYPE_REGISTRY létrehozva

Egy központi dictionary, ami minden támogatott fájlformátumot kategóriákba rendez:
- `maya`: .ma, .mb
- `3d_models`: .obj, .fbx, .abc, .usd, .vdb
- `blender`: .blend (🆕 most már benne van mindenben!)
- `houdini`: .hda
- `substance`: .sbsar
- `images`: .tif, .jpg, .png, .hdr, .exr, .tga
- `pdf`: .pdf
- `scripts`: .mel, .py
- `text`: .txt

Minden kategória tartalmazza:
- `extensions`: kiterjesztések listája
- `label`: megjelenítési név
- `filter_label`: filter menüben használt név
- `importable`: Maya-ba importálható-e
- `generate_thumbnail`: generáljon-e thumbnail-t
- `is_3d`: 3D file-e

### 2. **models.py** (AssetItem osztály)

A hard-coded extension listák helyett most a registry-t használja:
```python
# RÉGI:
self.is_image_file = self.extension in ['.tif', '.tiff', '.jpg', ...]

# ÚJ:
self.category = get_extension_category(self.extension)
self.is_image_file = self.category == "images"
```

### 3. **browser.py** (Filter menük)

A filter group-ok most a registry-ből jönnek:
```python
# RÉGI:
file_type_groups = [
    ("Maya Files (.ma/.mb)", [".ma", ".mb"]),
    ...
]

# ÚJ:
from .utils import get_filter_groups
file_type_groups = get_filter_groups()
```

Az importable files listája is a registry-ből:
```python
# RÉGI:
maya_importable = ['.ma', '.mb', '.obj', ...]

# ÚJ:
from .utils import get_importable_extensions
maya_importable = get_importable_extensions()
```

### 4. **widgets.py** (FilterPanel)

A simple filter checkbox-ok dinamikusan generálódnak:
```python
# RÉGI:
file_types = [
    (".ma", "MA"),
    (".mb", "MB"),
    ...
]

# ÚJ:
from .utils import get_simple_filter_types
file_types = get_simple_filter_types()
```

### 5. **config.py**

A default supported_formats a registry-ből jön:
```python
# ÚJ:
from .utils import get_all_supported_extensions
supported_formats = get_all_supported_extensions()
```

### 6. **config.json**

Frissítve a .sbsar kiterjesztéssel (eddig hiányzott).

## Új Helper Funkciók (utils.py)

1. `get_all_supported_extensions()` - összes támogatott kiterjesztés
2. `get_extension_category(ext)` - kategória név egy kiterjesztéshez
3. `is_extension_supported(ext)` - támogatott-e a kiterjesztés
4. `get_importable_extensions()` - Maya-ba importálható kiterjesztések
5. `should_generate_thumbnail(ext)` - generáljon-e thumbnail-t
6. `get_filter_groups()` - filter menühöz group-ok
7. `get_simple_filter_types()` - simple filter panel-hez típusok

## Előnyök

✅ **Egy helyen kell módosítani** - ha új formátumot adsz hozzá, csak az `utils.py` FILE_TYPE_REGISTRY-t kell frissíteni
✅ **Konzisztens** - minden komponens ugyanazt a definíciót használja
✅ **Karbantartható** - világos struktúra, könnyű megérteni
✅ **Bővíthető** - új kategóriák és tulajdonságok könnyen hozzáadhatók
✅ **.blend fájlok most már mindenhol működnek** - benne vannak a filter-ekben is!

## Hogyan adj hozzá új fájlformátumot?

Csak az `utils.py` FILE_TYPE_REGISTRY-ben adj hozzá egy új kategóriát vagy bővítsd a meglévőt:

```python
"new_category": {
    "extensions": [".new", ".ext"],
    "label": "New Files",
    "filter_label": "New Files (.new/.ext)",
    "importable": True,
    "generate_thumbnail": True,
    "is_3d": False
}
```

És kész! Minden más automatikusan működik.

## Tesztelendő

- [x] .blend fájlok megjelennek a simple filter panel-ben
- [x] .blend fájlok megjelennek a header filter menüben
- [x] Thumbnail generálódik .blend fájlokhoz
- [x] Importálás működik minden formátumhoz
- [x] Config.json frissült

---
**Készítve:** 2025-10-17  
**Állapot:** ✅ Kész, működik
