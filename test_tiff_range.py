import sys
import os

# Add external_libs to path
external_libs = os.path.join(os.path.dirname(__file__), 'ddContentBrowser', 'external_libs')
sys.path.insert(0, external_libs)

import tifffile
import numpy as np

file_path = r'F:\projects\spaceShipA\images\tmp\spaceShipA - Copy - Copy.tif'
img = tifffile.imread(file_path)

print(f"Shape: {img.shape}")
print(f"Dtype: {img.dtype}")
print(f"Min value: {img.min()}")
print(f"Max value: {img.max()}")
print(f"Mean value: {img.mean():.2f}")

# Check per-channel stats
for i in range(3):
    print(f"Channel {i}: min={img[:,:,i].min()}, max={img[:,:,i].max()}, mean={img[:,:,i].mean():.2f}")

# Test current conversion
print("\nCurrent conversion (÷ 16777216):")
converted_wrong = (img / 16777216).astype(np.uint8)
print(f"  Min: {converted_wrong.min()}, Max: {converted_wrong.max()}")

# Test correct conversion (÷ max value)
print("\nCorrect conversion (÷ max × 255):")
converted_correct = ((img.astype(np.float64) / img.max()) * 255).astype(np.uint8)
print(f"  Min: {converted_correct.min()}, Max: {converted_correct.max()}")
