import sys
import os

# Add external_libs to path (project root / ddContentBrowser / external_libs)
script_dir = os.path.dirname(os.path.abspath(__file__))
external_libs = os.path.join(script_dir, 'ddContentBrowser', 'external_libs')
sys.path.insert(0, external_libs)
print(f"External libs path: {external_libs}")
print(f"Path exists: {os.path.exists(external_libs)}\n")

from PIL import Image, PsdImagePlugin
import PIL

print("PIL/Pillow version:", PIL.__version__)
print("\nRegistered extensions:")
exts = Image.registered_extensions()
psd_formats = [k for k in exts.keys() if 'psd' in k.lower()]
print(f"  PSD formats: {psd_formats}")

print("\nPSD handler:", exts.get('.psd', 'NOT FOUND'))

print("\nAvailable plugins:")
print(f"  PSDImagePlugin available: {hasattr(PIL, 'PsdImagePlugin')}")

# Try to load a test PSD
test_files = [
    r"S:\Download\alphaTest_gradient.psd",
    r"F:\projects\japaneseJungle\images\japaneseJungle_render_v001.psd"
]

for test_file in test_files:
    if os.path.exists(test_file):
        print(f"\n\nTesting: {test_file}")
        print(f"  File exists: Yes")
        print(f"  File size: {os.path.getsize(test_file) / (1024*1024):.2f} MB")
        
        try:
            # Try opening without loading
            with Image.open(test_file) as img:
                print(f"  ✓ Image opened successfully")
                print(f"  Format: {img.format}")
                print(f"  Mode: {img.mode}")
                print(f"  Size: {img.size}")
                print(f"  Layers: {hasattr(img, 'n_frames') and img.n_frames or 'N/A'}")
                
                # Try loading pixel data
                try:
                    img.load()
                    print(f"  ✓ Pixel data loaded")
                except Exception as e:
                    print(f"  ✗ Pixel load failed: {e}")
                    
        except Exception as e:
            print(f"  ✗ Failed to open: {e}")
            print(f"  Error type: {type(e).__name__}")
    else:
        print(f"\n\nTesting: {test_file}")
        print(f"  File exists: No")
