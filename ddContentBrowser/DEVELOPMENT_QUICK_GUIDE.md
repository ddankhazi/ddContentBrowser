# 🚀 Quick Development Guide

## Development Workflow (No more double-launching!)

### The Problem (SOLVED ✅)
Previously, you had to launch the browser **twice** to see code changes:
1. Edit code
2. Close browser
3. Launch browser (old code loads)
4. Close browser again
5. Launch browser (new code finally loads)

### The Solution
The browser now has **automatic module reloading** built-in!

---

## 🔧 How to Use During Development

### Option 1: Auto-Reload (Recommended for Development)
```python
from ddContentBrowser.launch_browser import launch
launch()  # Always reloads modules automatically!
```

**Workflow:**
1. ✏️ Edit your code in VS Code
2. 💾 Save the file (Ctrl+S)
3. 🚀 Run the launcher in Maya Script Editor
4. ✅ See your changes immediately!

### Option 2: Manual Control
```python
from ddContentBrowser.browser import show_content_browser

# With reload (slower, but sees changes)
show_content_browser(force_reload=True)

# Without reload (faster, but won't see changes)
show_content_browser(force_reload=False)
```

---

## 📋 Development Checklist

### Before You Start Coding:
- [ ] Have the browser open in Maya
- [ ] Have VS Code open with the project
- [ ] Know which file you need to edit

### While Coding:
- [ ] Make your changes in VS Code
- [ ] Save the file (Ctrl+S)
- [ ] Close the browser in Maya (just close the window)
- [ ] Run `launch()` in Maya Script Editor
- [ ] Test your changes

### Testing Tips:
✅ **DO**: Use `launch()` - it auto-reloads everything
✅ **DO**: Close the browser window before relaunching
✅ **DO**: Check the Script Editor for reload messages
❌ **DON'T**: Use old import methods without reload
❌ **DON'T**: Keep the browser open when relaunching

---

## 🐛 Troubleshooting

### "I still see old code after relaunching"
**Check:**
1. Did you save the file in VS Code? (Ctrl+S)
2. Did you close the browser window before relaunching?
3. Are you using `launch()` or `launch(force_reload=True)`?
4. Check Maya Script Editor for reload messages

**Fix:**
```python
# Force a complete reload
from ddContentBrowser.browser import show_content_browser
show_content_browser(force_reload=True)
```

### "Module not found" error
**Fix:**
Make sure the ddContentBrowser folder is in Maya's scripts directory:
```
C:/Users/[USERNAME]/Documents/maya/2026/scripts/ddContentBrowser/
```

### "Cannot close browser" error
**Fix:**
Just ignore it and relaunch - the reload system handles it.

---

## 📊 Performance Notes

### Auto-Reload Performance:
- **First launch**: ~1-2 seconds (normal)
- **Reload launch**: ~0.5-1 second (fast enough)
- **No-reload launch**: ~0.2-0.3 seconds (fastest)

### When to Use Each:
- **Development**: Always use `launch()` (auto-reload)
- **Production/Daily Use**: Use `launch_no_reload()` (faster)
- **Testing Specific Module**: Use `show_content_browser(force_reload=True)`

---

## 💡 Pro Tips

### Shelf Button Setup:
Create a shelf button with this code for one-click launching:
```python
from ddContentBrowser.launch_browser import launch
launch()
```

### Hotkey Setup:
Assign `Ctrl+Shift+B` (or your preferred key) to run:
```python
from ddContentBrowser.launch_browser import launch; launch()
```

### Debug Mode:
Watch the Script Editor output when launching - you'll see:
```
[Reload] Cleared 15 module(s) from cache
[Reload] Re-imported package modules successfully
[DD Content Browser] Launched successfully!
```

---

## 🎯 Quick Reference

| Command | Use Case | Speed | Sees Changes |
|---------|----------|-------|--------------|
| `launch()` | Development | Medium | ✅ Yes |
| `launch_no_reload()` | Production | Fast | ❌ No |
| `show_content_browser(True)` | Force reload | Medium | ✅ Yes |
| `show_content_browser(False)` | Skip reload | Fast | ❌ No |

**Bottom Line:** For development, just use `launch()` and you're done! 🎉
