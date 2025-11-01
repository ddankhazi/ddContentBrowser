import sys
import os

# Add external_libs to path
script_dir = os.path.dirname(os.path.abspath(__file__))
external_libs = os.path.join(script_dir, 'ddContentBrowser', 'external_libs')
sys.path.insert(0, external_libs)

from PIL import Image, PsdImagePlugin

file_path = r"F:\projects\japaneseJungle\images\japaneseJungle_render_v001.psd"

print("Attempting to open PSD with PIL...")
print(f"File: {file_path}\n")

try:
    # Try opening the PSD
    with Image.open(file_path) as psd:
        print(f"✓ PSD opened")
        print(f"  Format: {psd.format}")
        print(f"  Mode: {psd.mode}")
        print(f"  Size: {psd.size}")
        
        # Check if it has layers
        if hasattr(psd, 'n_frames'):
            print(f"  Frames/Layers: {psd.n_frames}")
        
        # Try to seek to composite image (frame 0 is usually the flattened image)
        try:
            psd.seek(0)
            print(f"\n✓ Composite image available")
            print(f"  Composite mode: {psd.mode}")
            print(f"  Composite size: {psd.size}")
            
            # Try to load pixel data
            try:
                psd.load()
                print(f"  ✓ Composite pixel data loaded successfully!")
                
                # Try converting to RGB
                rgb = psd.convert('RGB')
                print(f"  ✓ Converted to RGB: {rgb.size}")
                
                # Save a test thumbnail
                rgb.thumbnail((512, 512), Image.Resampling.LANCZOS)
                test_output = "test_psd_composite.jpg"
                rgb.save(test_output, "JPEG")
                print(f"\n✓ Test thumbnail saved: {test_output}")
                
            except Exception as e:
                print(f"  ✗ Failed to load composite: {e}")
        except Exception as e:
            print(f"\n✗ No composite image: {e}")
            
except Exception as e:
    print(f"✗ Failed to open PSD: {e}")
    print(f"  Error type: {type(e).__name__}")
