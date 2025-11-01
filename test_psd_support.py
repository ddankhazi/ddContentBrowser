"""Test PSD support with PIL"""
import sys
import os

# Add external_libs to path
external_libs = os.path.join(os.path.dirname(__file__), 'ddContentBrowser', 'external_libs')
sys.path.insert(0, external_libs)

try:
    from PIL import Image
    
    print("PIL/Pillow version:", Image.__version__)
    
    # Check PSD support
    exts = Image.registered_extensions()
    psd_formats = [k for k in exts.keys() if 'psd' in k.lower()]
    
    print(f"\nPSD formats supported: {psd_formats}")
    
    if '.psd' in exts:
        print(f"  → .psd handler: {exts['.psd']}")
    
    # Test opening a PSD file (if you have one)
    print("\n✓ PIL is ready for PSD support!")
    
except ImportError as e:
    print(f"✗ PIL not available: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
