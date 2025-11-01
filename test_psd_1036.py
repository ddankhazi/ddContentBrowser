import struct

def analyze_psd_resource_1036(file_path):
    """Detailed analysis of resource 1036"""
    with open(file_path, 'rb') as f:
        # Read PSD header
        signature = f.read(4)
        version = struct.unpack('>H', f.read(2))[0]
        f.read(6)  # Reserved
        channels = struct.unpack('>H', f.read(2))[0]
        height = struct.unpack('>I', f.read(4))[0]
        width = struct.unpack('>I', f.read(4))[0]
        depth = struct.unpack('>H', f.read(2))[0]
        color_mode = struct.unpack('>H', f.read(2))[0]
        
        # Skip color mode data
        color_mode_data_len = struct.unpack('>I', f.read(4))[0]
        f.read(color_mode_data_len)
        
        # Read image resources
        image_resources_len = struct.unpack('>I', f.read(4))[0]
        resources_start = f.tell()
        resources_end = resources_start + image_resources_len
        
        print(f"Image resources section: {image_resources_len} bytes")
        
        while f.tell() < resources_end:
            res_signature = f.read(4)
            if res_signature != b'8BIM':
                break
            
            res_id = struct.unpack('>H', f.read(2))[0]
            
            # Pascal string name
            name_len = struct.unpack('B', f.read(1))[0]
            if name_len > 0:
                f.read(name_len)
            if (name_len + 1) % 2 != 0:
                f.read(1)
            
            res_size = struct.unpack('>I', f.read(4))[0]
            res_data_start = f.tell()
            
            if res_id == 1036:
                print(f"\n{'='*60}")
                print(f"Resource ID 1036 found at position {res_data_start}")
                print(f"Total resource size: {res_size} bytes")
                
                # Read header
                thumb_format = struct.unpack('>I', f.read(4))[0]
                thumb_width = struct.unpack('>I', f.read(4))[0]
                thumb_height = struct.unpack('>I', f.read(4))[0]
                widthbytes = struct.unpack('>I', f.read(4))[0]
                total_size = struct.unpack('>I', f.read(4))[0]
                compressed_size = struct.unpack('>I', f.read(4))[0]
                bpp = struct.unpack('>H', f.read(2))[0]
                planes = struct.unpack('>H', f.read(2))[0]
                
                print(f"\nHeader (28 bytes):")
                print(f"  Format: {thumb_format} (1=kRawRGB)")
                print(f"  Width: {thumb_width}")
                print(f"  Height: {thumb_height}")
                print(f"  Width bytes: {widthbytes}")
                print(f"  Total size: {total_size}")
                print(f"  Compressed size: {compressed_size}")
                print(f"  Bits per pixel: {bpp}")
                print(f"  Planes: {planes}")
                
                rgb_data_size = res_size - 28
                print(f"\nRGB data size: {rgb_data_size} bytes")
                print(f"Expected size (W×H×3): {thumb_width * thumb_height * 3} bytes")
                
                # Check if it's JFIF/JPEG
                rgb_data = f.read(min(rgb_data_size, 100))
                if rgb_data[:4] == b'\xff\xd8\xff\xe0':
                    print(f"\n⚠ Data starts with JFIF marker (JPEG thumbnail)!")
                    jfif_len = struct.unpack('>H', rgb_data[4:6])[0]
                    print(f"  JFIF header length: {jfif_len}")
                else:
                    print(f"\nFirst 20 bytes of RGB data: {rgb_data[:20].hex()}")
                
                print(f"{'='*60}")
            
            # Skip to next resource
            f.seek(res_data_start + res_size)
            if res_size % 2 != 0:
                f.read(1)

# Test
analyze_psd_resource_1036(r"F:\projects\japaneseJungle\images\japaneseJungle_render_v001.psd")
