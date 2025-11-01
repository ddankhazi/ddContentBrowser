import sys
import os

# Add external_libs to path
script_dir = os.path.dirname(os.path.abspath(__file__))
external_libs = os.path.join(script_dir, 'ddContentBrowser', 'external_libs')
sys.path.insert(0, external_libs)

from psd_tools import PSDImage

file_path = r"F:\projects\japaneseJungle\images\japaneseJungle_render_v001.psd"

print("Testing psd-tools library...")
print(f"File: {file_path}\n")

try:
    # Open PSD with psd-tools
    psd = PSDImage.open(file_path)
    print(f"✓ PSD opened with psd-tools")
    print(f"  Size: {psd.width}x{psd.height}")
    print(f"  Color mode: {psd.color_mode}")
    print(f"  Bit depth: {psd.depth} bits")
    print(f"  Layers: {len(list(psd.descendants()))}")
    
    # Get composite (flattened) image
    print(f"\nExtracting composite image...")
    composite = psd.composite()
    print(f"  ✓ Composite extracted")
    print(f"  Size: {composite.size}")
    print(f"  Mode: {composite.mode}")
    
    # Convert to RGB if needed
    if composite.mode != 'RGB':
        print(f"  Converting {composite.mode} → RGB...")
        composite = composite.convert('RGB')
    
    # Create thumbnail
    composite.thumbnail((512, 512))
    test_output = "test_psd_tools.jpg"
    composite.save(test_output, "JPEG")
    print(f"\n✓ Test thumbnail saved: {test_output}")
    print(f"  Final size: {composite.size}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
