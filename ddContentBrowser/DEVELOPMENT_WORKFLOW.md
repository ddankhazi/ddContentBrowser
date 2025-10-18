# DD Content Browser - Development Workflow

## Working with Reloads

When developing/modifying the Content Browser, you need to reload the module to see changes.

### Why Reload is Needed:

Python caches imported modules. When you run:
```python
import ddContentBrowser
```

The module is loaded into memory. If you edit `ddContentBrowser.py` and import again, Python will use the cached version, not your new changes!

### Solution - Auto-Reload:

All launcher scripts now include automatic reload:

```python
import importlib
import ddContentBrowser
importlib.reload(ddContentBrowser)  # This reloads the latest code!
```

## Development Workflow:

### 1. Edit the Code
Open and modify `ddContentBrowser.py` in your editor

### 2. Save Changes
Save the file (Ctrl+S)

### 3. Launch with Reload
In Maya Python Script Editor:
```python
exec(open(r'C:/Users/Danki/Documents/maya/2026/scripts/launch_browser_simple.py').read())
```

This will:
- ✅ Import the module
- ✅ Reload to get latest changes
- ✅ Launch the browser with your modifications

### 4. Test
Test your changes in the browser

### 5. Repeat
Go back to step 1 and continue developing!

## Quick Commands:

### For Development (with reload):
```python
# Recommended - uses launcher file
exec(open(r'C:/Users/Danki/Documents/maya/2026/scripts/launch_browser_simple.py').read())

# Or direct reload
import importlib, ddContentBrowser
importlib.reload(ddContentBrowser)
ddContentBrowser.show_content_browser()
```

### For Production (first time only):
```python
# No reload needed for first import
from ddContentBrowser import show_content_browser
show_content_browser()
```

## Shelf Button for Development:

Create a shelf button with reload command for quick testing:

**Command:**
```python
exec(open(r'C:/Users/Danki/Documents/maya/2026/scripts/launch_browser_simple.py').read())
```

**Label:** DD Browser (DEV)

**Icon:** Optional - use a Python icon

Now you can click this button after each code change to test immediately!

## Important Notes:

### ⚠️ Window Instance Management:
The browser uses a global singleton pattern:
```python
_content_browser_instance = None
```

If you make major changes to the `__init__` method, you might need to:
1. Close the browser window
2. Reload the module
3. Reopen the browser

Or manually reset the instance:
```python
import ddContentBrowser
ddContentBrowser._content_browser_instance = None
importlib.reload(ddContentBrowser)
ddContentBrowser.show_content_browser()
```

### ⚠️ UI Changes:
- Simple property changes (labels, sizes) → Just reload
- Major UI restructuring → Close window, then reload
- Signal/slot changes → Usually just reload works

### ⚠️ PySide/Qt Objects:
If you get Qt-related errors after reload, restart Maya. This happens rarely but can occur with significant UI changes.

## Debugging Tips:

### Print Statements:
```python
print("Debug: navigation history:", self.history)
```
Will show in Maya Script Editor output.

### Try-Except for Testing:
```python
try:
    # Your test code
    print("Test passed!")
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()
```

### Check Module Reload:
```python
import ddContentBrowser
print("Module file:", ddContentBrowser.__file__)
print("Module reload count:", getattr(ddContentBrowser, '_reload_count', 0))
```

Happy developing! 🚀
