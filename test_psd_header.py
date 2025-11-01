import struct

def analyze_psd_header(file_path):
    """Analyze PSD file header to determine format version and properties"""
    try:
        with open(file_path, 'rb') as f:
            # Read signature (4 bytes: '8BPS')
            signature = f.read(4)
            print(f"Signature: {signature} (expected: b'8BPS')")
            
            if signature != b'8BPS':
                print("  ✗ Not a valid PSD file (wrong signature)")
                return
            
            # Read version (2 bytes: 1 or 2)
            version = struct.unpack('>H', f.read(2))[0]
            print(f"Version: {version}")
            if version == 1:
                print("  → PSD format (standard)")
            elif version == 2:
                print("  → PSB format (large document, up to 300,000 x 300,000 pixels)")
            else:
                print(f"  ✗ Unknown version: {version}")
                return
            
            # Skip reserved bytes (6 bytes)
            f.read(6)
            
            # Read channels (2 bytes)
            channels = struct.unpack('>H', f.read(2))[0]
            print(f"Channels: {channels}")
            
            # Read height (4 bytes)
            height = struct.unpack('>I', f.read(4))[0]
            print(f"Height: {height} px")
            
            # Read width (4 bytes)
            width = struct.unpack('>I', f.read(4))[0]
            print(f"Width: {width} px")
            
            # Read bit depth (2 bytes)
            depth = struct.unpack('>H', f.read(2))[0]
            print(f"Bit depth: {depth} bits per channel")
            
            # Read color mode (2 bytes)
            color_mode = struct.unpack('>H', f.read(2))[0]
            color_modes = {
                0: "Bitmap",
                1: "Grayscale",
                2: "Indexed",
                3: "RGB",
                4: "CMYK",
                7: "Multichannel",
                8: "Duotone",
                9: "Lab"
            }
            mode_name = color_modes.get(color_mode, f"Unknown ({color_mode})")
            print(f"Color mode: {mode_name}")
            
            # Check if PIL supports this combination
            print("\nPIL Support Analysis:")
            if version == 2:
                print("  ⚠ PSB format - PIL may have limited support")
            if depth not in [1, 8, 16, 32]:
                print(f"  ⚠ Unusual bit depth: {depth}")
            if color_mode not in [1, 3, 4]:
                print(f"  ⚠ Unusual color mode: {mode_name}")
            
    except Exception as e:
        print(f"✗ Error reading file: {e}")

# Test the problematic file
print("=" * 60)
print("Analyzing: japaneseJungle_render_v001.psd")
print("=" * 60)
analyze_psd_header(r"F:\projects\japaneseJungle\images\japaneseJungle_render_v001.psd")

print("\n" + "=" * 60)
print("Analyzing: alphaTest_gradient.psd (working file)")
print("=" * 60)
analyze_psd_header(r"S:\Download\alphaTest_gradient.psd")
