# FILE TYPE CENTRALIZATION - Részletes Elemzés

**Dátum:** 2025-10-18  
**Cél:** Központosítani a fájltípus definíciókat a `FILE_TYPE_REGISTRY`-be

---

## 📋 JELENLEGI HELYZET

### ✅ MÁR HASZNÁLJA a FILE_TYPE_REGISTRY-t:

#### 1. **config.py** (lines 18-31)
```python
from .utils import get_all_supported_extensions
supported_formats = get_all_supported_extensions()
# ... majd használja a default_config-ban
"supported_formats": supported_formats,  # Now from registry
```
**STATUS:** ✅ DONE - Már központosítva!

#### 2. **widgets.py - SimpleFilterPanel** (lines 655-657)
```python
from .utils import get_simple_filter_types
file_types = get_simple_filter_types()
# ... majd létrehozza a checkbox-okat
```
**STATUS:** ✅ DONE - Már használja a registry-t!

#### 3. **browser.py** (lines 104, 1735-1767)
```python
from .utils import get_filter_groups, get_importable_extensions
file_type_groups = get_filter_groups()
maya_importable = get_importable_extensions()
```
**STATUS:** ✅ DONE - Használja az importálható formátumok listáját!

---

## ❌ MÉG NEM HASZNÁLJA - JAVÍTANDÓ:

### 1. **models.py - FileSystemModel.__init__** (lines 147-157)

**JELENLEGI KÓD:**
```python
# Base supported formats
self.base_formats = [
    ".ma", ".mb",           # Maya scene files
    ".obj", ".fbx", ".abc", ".usd", ".vdb",  # 3D formats
    ".hda",                 # Houdini Digital Assets
    ".blend",               # Blender files
    ".sbsar",               # Substance Archive (shader)
    ".tif", ".tiff", ".jpg", ".jpeg", ".png", ".hdr", ".exr", ".tga",  # Images
    ".pdf",                 # PDF documents
    ".mel", ".py", ".txt"   # Scripts and text files
]
self.supported_formats = self.base_formats.copy()
```

**PROBLÉMA:** Hardcoded lista!

**MEGOLDÁS:**
```python
# Base supported formats - from central registry
from .utils import get_all_supported_extensions
self.base_formats = get_all_supported_extensions()
self.supported_formats = self.base_formats.copy()
```

**FÜGGŐSÉGEK:**
- `self.image_formats` (line 160) - Ez is használható lehet a registry-ből
- `self.script_formats` (line 161) - Ez is használható lehet a registry-ből

---

### 2. **models.py - image_formats & script_formats** (lines 160-161)

**JELENLEGI KÓD:**
```python
self.image_formats = [".tif", ".tiff", ".jpg", ".jpeg", ".png", ".hdr", ".exr", ".tga"]
self.script_formats = [".mel", ".py", ".txt"]
```

**MEGOLDÁS - Option A:** Használd a registry kategóriákat:
```python
# Get specific categories from registry
from .utils import FILE_TYPE_REGISTRY
self.image_formats = FILE_TYPE_REGISTRY['images']['extensions']
self.script_formats = FILE_TYPE_REGISTRY['scripts']['extensions']
```

**MEGOLDÁS - Option B:** Új helper funkció utils.py-ban:
```python
# In utils.py add:
def get_extensions_by_category(category_name):
    """Get extensions for a specific category"""
    if category_name in FILE_TYPE_REGISTRY:
        return FILE_TYPE_REGISTRY[category_name]['extensions']
    return []

# Then in models.py:
from .utils import get_extensions_by_category
self.image_formats = get_extensions_by_category('images')
self.script_formats = get_extensions_by_category('scripts')
```

---

### 3. **settings.py - FiltersSettingsTab** (lines 647-667)

**JELENLEGI KÓD:** Hardcoded HTML szöveg!
```python
import_label = QLabel(
    "<b>🔵 Import & Reference to Maya:</b><br>"
    "• <b>Scenes:</b> .ma, .mb<br>"
    "• <b>3D Models:</b> .obj, .fbx, .abc, .usd<br>"
    "• <b>Textures:</b> .jpg, .jpeg, .png, .tif, .tiff, .tga, .hdr, .exr<br>"
    "• <b>Scripts:</b> .mel, .py"
)
```

**MEGOLDÁS:** Dinamikusan generált HTML a FILE_TYPE_REGISTRY-ből:

```python
def _generate_supported_formats_html():
    """Generate HTML description of supported formats from registry"""
    from .utils import FILE_TYPE_REGISTRY
    
    # Importable formats
    importable_html = "<b>🔵 Import & Reference to Maya:</b><br>"
    for cat_name, cat_data in FILE_TYPE_REGISTRY.items():
        if cat_data['importable'] and cat_data['is_3d']:
            ext_list = ", ".join(cat_data['extensions'])
            importable_html += f"• <b>{cat_data['label']}:</b> {ext_list}<br>"
    
    # Non-importable formats (browse only)
    browse_html = "<b>⚪ Browse & Preview Only:</b><br>"
    for cat_name, cat_data in FILE_TYPE_REGISTRY.items():
        if not cat_data['importable'] and cat_data['is_3d']:
            ext_list = ", ".join(cat_data['extensions'])
            browse_html += f"• <b>{cat_data['label']}:</b> {ext_list}<br>"
    
    return importable_html, browse_html

# Then in init_ui:
import_html, browse_html = _generate_supported_formats_html()
import_label = QLabel(import_html)
browse_label = QLabel(browse_html)
```

---

## 🔍 LISTA ÖSSZEHASONLÍTÁS

### FILE_TYPE_REGISTRY (utils.py):
```
['.ma', '.mb', '.obj', '.fbx', '.abc', '.usd', '.vdb', 
 '.hda', '.blend', '.sbsar', '.tif', '.tiff', '.jpg', 
 '.jpeg', '.png', '.hdr', '.exr', '.tga', '.pdf', 
 '.mel', '.py', '.txt']
```
**Total: 22 extensions**

### models.py base_formats (hardcoded):
```
['.ma', '.mb', '.obj', '.fbx', '.abc', '.usd', '.vdb',
 '.hda', '.blend', '.sbsar', '.tif', '.tiff', '.jpg',
 '.jpeg', '.png', '.hdr', '.exr', '.tga', '.pdf',
 '.mel', '.py', '.txt']
```
**Total: 22 extensions**

### ✅ RESULT: IDENTICAL!
Nincs eltérés a két lista között, biztonságosan cserélhető!

---

## 🎯 IMPLEMENTÁCIÓS TERV

### LÉPÉSEK:

1. ✅ **utils.py** - Új helper funkció hozzáadása (opcionális):
   ```python
   def get_extensions_by_category(category_name):
       """Get extensions for a specific category"""
       if category_name in FILE_TYPE_REGISTRY:
           return FILE_TYPE_REGISTRY[category_name]['extensions']
       return []
   ```

2. ✅ **models.py** - FileSystemModel.__init__ módosítása:
   - Import hozzáadása: `from .utils import get_all_supported_extensions`
   - `self.base_formats` cseréje
   - `self.image_formats` és `self.script_formats` központosítása

3. ✅ **settings.py** - FiltersSettingsTab.init_ui módosítása:
   - HTML generátor függvény létrehozása
   - Statikus HTML lecserélése dinamikusra

4. ✅ **config.json** - `supported_formats` mező:
   - **NEM KELL TÖRÖLNI!** 
   - A config.py már használja a FILE_TYPE_REGISTRY-t az inicializáláshoz
   - A JSON-ban tárolt érték csak a felhasználói adatok mentésére van

---

## ⚠️ KRITIKUS TESZTELENDŐ FUNKCIÓK

### models.py változás után:
- [ ] Simple filter panel működik (checkbox lista)
- [ ] Fájl szűrés extension alapján
- [ ] Custom extensions hozzáadása
- [ ] `self.image_formats` használata (show_images kapcsoló)
- [ ] `self.script_formats` használata (show_scripts kapcsoló)

### settings.py változás után:
- [ ] Settings dialog megnyílik
- [ ] Filters tab megjelenítése
- [ ] HTML formázás helyes (sortörések, stílusok)
- [ ] Új fájltípus hozzáadásakor automatikusan megjelenik

---

## 🚀 ELŐNYÖK A KÖZPONTOSÍTÁS UTÁN

1. **Single Source of Truth**: Egy helyen kell csak editálni
2. **Automatikus szinkronizáció**: Minden komponens frissül
3. **Új fájltípus hozzáadása**: Csak a FILE_TYPE_REGISTRY-be kell felvenni
4. **Metaadatok**: importable, generate_thumbnail, is_3d info elérhető
5. **Kevesebb hiba**: Nincs duplikáció, nincs drift

---

## ❓ ELLENŐRZÉS ELŐTT

- [ ] Van-e más fájl ami használja a `base_formats`-ot?
- [ ] Van-e más fájl ami hardcoded extension listát használ?
- [ ] A simple filter panel logikája megmarad-e ugyanúgy?
- [ ] A config.json supported_formats mezője megmarad-e (csak olvasásra)?

---

## 📝 KÖVETKEZŐ LÉPÉS

~~**VÁRJ A JÓVÁHAGYÁSRA!**~~

✅ **IMPLEMENTÁLVA! 2025-10-18**

### Elvégzett változtatások:

1. ✅ **utils.py** - Új helper funkció hozzáadva:
   - `get_extensions_by_category(category_name)` - Kategória alapú extension lekérés

2. ✅ **models.py** - FileSystemModel.__init__ módosítva:
   - Import hozzáadva: `from .utils import get_all_supported_extensions, get_extensions_by_category`
   - `self.base_formats` = `get_all_supported_extensions()` ✅
   - `self.image_formats` = `get_extensions_by_category('images')` ✅
   - `self.script_formats` = `get_extensions_by_category('scripts') + get_extensions_by_category('text')` ✅

3. ✅ **settings.py** - FiltersSettingsTab módosítva:
   - `_generate_supported_formats_html()` metódus hozzáadva
   - Dinamikus HTML generálás a FILE_TYPE_REGISTRY-ből
   - Importable vs Non-importable formátumok automatikus csoportosítása

### 🎉 EREDMÉNY:
**SINGLE SOURCE OF TRUTH = FILE_TYPE_REGISTRY (utils.py)**

Mostantól minden fájltípus információ egy helyről jön! Új formátum hozzáadásakor csak a FILE_TYPE_REGISTRY-t kell szerkeszteni.

---

## 🧪 TESZTELENDŐ

A változtatások után ellenőrizd:
- [ ] Browser elindul hibátlanul
- [ ] Type Filter menü megjelenik (képernyőképen látható menü)
- [ ] Simple filter panel működik
- [ ] Settings dialog → Filters tab megnyílik
- [ ] Fájltípus listák helyesen jelennek meg
- [ ] Show Images / Show Scripts kapcsolók működnek
- [ ] Custom extensions hozzáadása működik

