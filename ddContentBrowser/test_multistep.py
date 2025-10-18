"""Test if Multi-Step mode exists in batch_rename module"""

# Force reload
import sys
if 'ddContentBrowser.batch_rename' in sys.modules:
    del sys.modules['ddContentBrowser.batch_rename']

# Import the module
from ddContentBrowser.batch_rename import BatchRenameDialog

# Check if the methods exist
print("=== Testing Multi-Step Implementation ===")
print(f"setup_multistep_options exists: {hasattr(BatchRenameDialog, 'setup_multistep_options')}")
print(f"apply_multistep exists: {hasattr(BatchRenameDialog, 'apply_multistep')}")

# Check the mode list
import inspect
source = inspect.getsource(BatchRenameDialog.__init__)
if "Multi-Step" in source:
    print("✓ 'Multi-Step' found in __init__ mode list")
else:
    print("✗ 'Multi-Step' NOT found in __init__ mode list")

# Check on_mode_changed
source = inspect.getsource(BatchRenameDialog.on_mode_changed)
if "setup_multistep_options" in source:
    print("✓ 'setup_multistep_options' called in on_mode_changed")
else:
    print("✗ 'setup_multistep_options' NOT called in on_mode_changed")

# Check update_preview
source = inspect.getsource(BatchRenameDialog.update_preview)
if "apply_multistep" in source:
    print("✓ 'apply_multistep' called in update_preview")
else:
    print("✗ 'apply_multistep' NOT called in update_preview")

print("\n=== All checks complete ===")
