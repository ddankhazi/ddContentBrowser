"""
Test script for EXR/HDR thumbnail optimization

This script demonstrates the new optimized thumbnail generation
for EXR and HDR files in the DD Content Browser.
"""

import sys
import os
import time
from pathlib import Path

# Add the ddContentBrowser directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "ddContentBrowser"))

# Enable debug mode to see optimization details
import cache
cache.DEBUG_MODE = True

print("=" * 70)
print("EXR/HDR Thumbnail Optimization Test")
print("=" * 70)
print()

# Try to import required libraries
print("Checking dependencies...")
try:
    import numpy
    print("✓ numpy available")
except ImportError:
    print("✗ numpy NOT available (optional)")

try:
    import cv2
    print("✓ OpenCV (cv2) available")
except ImportError:
    print("✗ OpenCV NOT available (optional)")

try:
    import openexr
    print("✓ OpenEXR available")
except ImportError:
    print("✗ OpenEXR NOT available (optional)")

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap
    print("✓ PySide6 available")
    PYSIDE_VERSION = 6
except ImportError:
    try:
        from PySide2.QtWidgets import QApplication
        from PySide2.QtGui import QPixmap
        print("✓ PySide2 available")
        PYSIDE_VERSION = 2
    except ImportError:
        print("✗ PySide6/PySide2 NOT available (REQUIRED)")
        print("\nCannot run test without Qt libraries!")
        sys.exit(1)

print()
print("=" * 70)
print("Creating test environment...")
print("=" * 70)
print()

# Create Qt application (required for QPixmap)
app = QApplication(sys.argv)

# Create thumbnail cache instances
from cache import ThumbnailCache, ThumbnailDiskCache, ThumbnailGenerator

memory_cache = ThumbnailCache(max_size=100)
disk_cache = ThumbnailDiskCache(max_size_mb=100)

# Create thumbnail generator with debug mode
generator = ThumbnailGenerator(
    memory_cache=memory_cache,
    disk_cache=disk_cache,
    thumbnail_size=128,
    jpeg_quality=85
)

print(f"✓ Memory cache created (max_size=100)")
print(f"✓ Disk cache created at: {disk_cache.cache_dir}")
print(f"✓ Thumbnail generator created (size=128px)")
print()

# Test functions
print("=" * 70)
print("Testing optimization functions...")
print("=" * 70)
print()

# Check if optimization methods exist
if hasattr(generator, '_generate_exr_thumbnail_optimized'):
    print("✓ _generate_exr_thumbnail_optimized() method exists")
else:
    print("✗ _generate_exr_thumbnail_optimized() method NOT found")

if hasattr(generator, '_generate_hdr_thumbnail_optimized'):
    print("✓ _generate_hdr_thumbnail_optimized() method exists")
else:
    print("✗ _generate_hdr_thumbnail_optimized() method NOT found")

print()

# Test with sample files (if they exist)
print("=" * 70)
print("Testing with sample files (if available)...")
print("=" * 70)
print()

# Look for test files in common locations
test_locations = [
    Path.home() / "Pictures",
    Path.home() / "Documents",
    Path("C:/temp"),
    Path("C:/test"),
    current_dir / "test_data"
]

exr_files = []
hdr_files = []

for location in test_locations:
    if location.exists():
        exr_files.extend(location.glob("**/*.exr"))
        hdr_files.extend(location.glob("**/*.hdr"))
        if len(exr_files) >= 3 and len(hdr_files) >= 3:
            break

print(f"Found {len(exr_files)} EXR files")
print(f"Found {len(hdr_files)} HDR files")
print()

# Test EXR files
if exr_files:
    print("Testing EXR thumbnail generation:")
    print("-" * 70)
    for i, exr_file in enumerate(exr_files[:3], 1):
        print(f"\n{i}. Testing: {exr_file.name}")
        start_time = time.time()
        try:
            pixmap = generator._generate_exr_thumbnail_optimized(str(exr_file))
            elapsed = (time.time() - start_time) * 1000
            
            if pixmap and not pixmap.isNull():
                print(f"   ✓ Generated in {elapsed:.1f}ms - {pixmap.width()}x{pixmap.height()}px")
            else:
                print(f"   ✗ Failed (returned None or null pixmap) - {elapsed:.1f}ms")
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            print(f"   ✗ Exception: {e} - {elapsed:.1f}ms")
    print()
else:
    print("⚠ No EXR files found for testing")
    print("  Place some .exr files in one of these locations to test:")
    for loc in test_locations[:3]:
        print(f"  - {loc}")
    print()

# Test HDR files
if hdr_files:
    print("Testing HDR thumbnail generation:")
    print("-" * 70)
    for i, hdr_file in enumerate(hdr_files[:3], 1):
        print(f"\n{i}. Testing: {hdr_file.name}")
        start_time = time.time()
        try:
            pixmap = generator._generate_hdr_thumbnail_optimized(str(hdr_file))
            elapsed = (time.time() - start_time) * 1000
            
            if pixmap and not pixmap.isNull():
                print(f"   ✓ Generated in {elapsed:.1f}ms - {pixmap.width()}x{pixmap.height()}px")
            else:
                print(f"   ✗ Failed (returned None or null pixmap) - {elapsed:.1f}ms")
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            print(f"   ✗ Exception: {e} - {elapsed:.1f}ms")
    print()
else:
    print("⚠ No HDR files found for testing")
    print("  Place some .hdr files in one of these locations to test:")
    for loc in test_locations[:3]:
        print(f"  - {loc}")
    print()

print("=" * 70)
print("Test completed!")
print("=" * 70)
print()
print("Summary:")
print(f"  - Optimization methods: {'✓ Available' if hasattr(generator, '_generate_exr_thumbnail_optimized') else '✗ Not found'}")
print(f"  - EXR files tested: {min(len(exr_files), 3)}")
print(f"  - HDR files tested: {min(len(hdr_files), 3)}")
print()
print("To see detailed debug output, check the console output above.")
print()
