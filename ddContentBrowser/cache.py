"""
DD Content Browser - Cache Module
Thumbnail caching system with memory and disk storage

OPTIMIZATIONS (2025-11):
- OpenCV IMREAD_REDUCED_* for faster TIFF/HDR decoding (2-8× speedup)
- Smart routing: Large files (>50MB) → OpenCV, others → QImageReader
- Optimized scaling logic: Load at 8-16× thumbnail size for quality/speed balance

Author: ddankhazi
License: MIT
"""

__all__ = [
    'ThumbnailCache',
    'ThumbnailDiskCache', 
    'ThumbnailGenerator',
    'apply_exif_orientation'
]

# UI Font - Default value (matches Windows/Maya UI)
UI_FONT = "Segoe UI"

# Debug flag - set to True to enable verbose logging
DEBUG_MODE = False

import os
import sys
import time
import hashlib
import json
from pathlib import Path
from datetime import datetime

# Suppress OpenCV error messages for unsupported formats
# (We handle them gracefully with PIL fallback)
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
if hasattr(sys, 'stderr'):
    # Redirect stderr temporarily to suppress OpenCV errors
    original_stderr = sys.stderr
    
    class SuppressedStderr:
        def write(self, text):
            # Only suppress OpenCV TIFF errors, pass through others
            if "opencv" in text.lower() and "channels" in text.lower():
                return
            if "cv::imread_" in text and "can't read header" in text:
                return
            original_stderr.write(text)
        
        def flush(self):
            original_stderr.flush()
    
    sys.stderr = SuppressedStderr()

try:
    from PySide6.QtCore import QThread, Signal, Qt
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QLinearGradient, QBrush, QTransform
    from PySide6.QtCore import QRect
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtCore import QThread, Signal, Qt
    from PySide2.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QLinearGradient, QBrush, QTransform
    from PySide2.QtCore import QRect
    PYSIDE_VERSION = 2


def apply_exif_orientation(pixmap, file_path):
    """
    Apply EXIF orientation to pixmap (auto-rotate based on camera orientation)
    FOR PREVIEW AND ZOOM MODE (+90° adjustment)
    
    NOTE: This function is now DEPRECATED - use QImageReader.setAutoTransform(True) instead!
    Kept for backward compatibility only.
    
    Args:
        pixmap: QPixmap to transform
        file_path: Path to image file (to read EXIF)
    
    Returns:
        Original pixmap unchanged (EXIF handling now done by QImageReader)
    """
    # QImageReader.setAutoTransform(True) handles EXIF orientation automatically
    # This function is no longer needed but kept for compatibility
    return pixmap


def apply_exif_orientation_thumbnail(pixmap, file_path):
    """
    Apply EXIF orientation to pixmap (auto-rotate based on camera orientation)
    FOR THUMBNAILS ONLY (no extra rotation)
    
    Args:
        pixmap: QPixmap to transform
        file_path: Path to image file (to read EXIF)
    
    Returns:
        Transformed QPixmap or original if no rotation needed
    """
    try:
        from PIL import Image
        
        # Open image and get EXIF orientation
        img = Image.open(str(file_path))
        exif = img._getexif()
        
        if not exif or 274 not in exif:
            return pixmap  # No orientation tag
        
        orientation = exif[274]
        
        if orientation == 1:
            return pixmap  # Normal, no rotation needed
        
        if orientation == 2:
            # Flip horizontal
            pixmap = pixmap.transformed(QTransform().scale(-1, 1), Qt.SmoothTransformation)
        elif orientation == 3:
            # Rotate 180°
            pixmap = pixmap.transformed(QTransform().rotate(180), Qt.SmoothTransformation)
        elif orientation == 4:
            # Flip vertical
            pixmap = pixmap.transformed(QTransform().scale(1, -1), Qt.SmoothTransformation)
        elif orientation == 5:
            # Flip horizontal (no extra rotation)
            pixmap = pixmap.transformed(QTransform().scale(-1, 1), Qt.SmoothTransformation)
        elif orientation == 6:
            # No rotation - most common for portrait photos
            pass
        elif orientation == 7:
            # Flip horizontal only
            pixmap = pixmap.transformed(QTransform().scale(-1, 1), Qt.SmoothTransformation)
        elif orientation == 8:
            # Rotate 180°
            pixmap = pixmap.transformed(QTransform().rotate(180), Qt.SmoothTransformation)
        
        return pixmap
        
    except Exception as e:
        # If PIL not available or any error, return original
        return pixmap


class ThumbnailCache:
    """In-memory thumbnail cache manager"""
    
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get(self, file_path):
        """Get thumbnail from cache"""
        if file_path in self.cache:
            self.access_times[file_path] = time.time()
            return self.cache[file_path]
        return None
    
    def set(self, file_path, thumbnail):
        """Set thumbnail in cache"""
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        self.cache[file_path] = thumbnail
        self.access_times[file_path] = time.time()
    
    def clear(self):
        """Clear all cached thumbnails"""
        self.cache.clear()
        self.access_times.clear()
    
    def remove(self, file_path):
        """Remove specific thumbnail from cache"""
        if file_path in self.cache:
            del self.cache[file_path]
        if file_path in self.access_times:
            del self.access_times[file_path]
    
    def _cleanup(self):
        """LRU cache cleanup"""
        # Remove oldest accessed items
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])
        items_to_remove = len(sorted_items) // 4  # Remove 25%
        
        for file_path, _ in sorted_items[:items_to_remove]:
            if file_path in self.cache:
                del self.cache[file_path]
            if file_path in self.access_times:
                del self.access_times[file_path]


class ThumbnailDiskCache:
    """Persistent disk-based thumbnail cache"""
    
    def __init__(self, cache_dir=None, max_size_mb=500):
        """
        Initialize disk cache.
        
        Args:
            cache_dir: Directory to store thumbnails (default: ~/.ddContentBrowser/thumbnails)
            max_size_mb: Maximum cache size in megabytes (default: 500 MB)
        """
        if cache_dir is None:
            # Unified config directory - all DD Content Browser data in one place
            cache_dir = Path.home() / ".ddContentBrowser" / "thumbnails"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size_mb = max_size_mb
        self.stats = {
            'hits': 0,
            'misses': 0,
            'generated': 0
        }
        
        # Load or create cache info
        self.info_file = self.cache_dir / "cache_info.json"
        self.load_info()
    
    def load_info(self):
        """Load cache information"""
        if self.info_file.exists():
            try:
                with open(self.info_file, 'r') as f:
                    self.stats = json.load(f)
            except:
                pass
    
    def save_info(self):
        """Save cache information"""
        try:
            with open(self.info_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Error saving cache info: {e}")
    
    def get_cache_key(self, file_path, file_mtime):
        """
        Generate unique cache key from file path and modification time
        
        Args:
            file_path: Path to the file
            file_mtime: File modification timestamp
            
        Returns:
            MD5 hash string
        """
        key_string = f"{file_path}_{file_mtime}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_thumbnail_path(self, file_path, file_mtime):
        """Get path to cached thumbnail file"""
        cache_key = self.get_cache_key(file_path, file_mtime)
        return self.cache_dir / f"{cache_key}.jpg"
    
    def get(self, file_path, file_mtime):
        """
        Get thumbnail from disk cache
        
        Args:
            file_path: Path to the source file
            file_mtime: File modification timestamp
            
        Returns:
            QPixmap if found, None otherwise
        """
        # Check our own cache
        thumb_path = self.get_thumbnail_path(file_path, file_mtime)
        
        if thumb_path.exists():
            try:
                pixmap = QPixmap(str(thumb_path))
                if not pixmap.isNull():
                    self.stats['hits'] += 1
                    return pixmap
            except Exception as e:
                print(f"Error loading thumbnail from {thumb_path}: {e}")
        
        self.stats['misses'] += 1
        return None
    
    def set(self, file_path, file_mtime, pixmap, quality=85):
        """
        Save thumbnail to disk cache
        
        Args:
            file_path: Path to the source file
            file_mtime: File modification timestamp
            pixmap: QPixmap to save
            quality: JPEG quality (0-100)
        """
        thumb_path = self.get_thumbnail_path(file_path, file_mtime)
        
        try:
            # Ensure parent directory exists
            thumb_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as JPEG for smaller file size
            success = pixmap.save(str(thumb_path), "JPEG", quality)
            
            if success:
                self.stats['generated'] += 1
                self.save_info()
                
                # Check if we need to cleanup old cache
                self._check_cache_size()
            
            return success
            
        except Exception as e:
            print(f"Error saving thumbnail to {thumb_path}: {e}")
            return False
    
    def clear(self):
        """Clear all cached thumbnails"""
        try:
            for thumb_file in self.cache_dir.glob("*.jpg"):
                thumb_file.unlink()
            
            self.stats = {'hits': 0, 'misses': 0, 'generated': 0}
            self.save_info()
            
            print(f"Cache cleared: {self.cache_dir}")
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
    
    def clear_thumbnail(self, file_path):
        """
        Clear cached thumbnail for a specific file
        
        Args:
            file_path: Path to the source file
            
        Returns:
            bool: True if thumbnail was found and deleted, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            # Get file modification time
            file_mtime = file_path.stat().st_mtime
            
            # Get cache path
            thumb_path = self.get_thumbnail_path(file_path, file_mtime)
            
            if thumb_path.exists():
                thumb_path.unlink()
                print(f"Cleared thumbnail cache for: {file_path.name}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error clearing thumbnail for {file_path}: {e}")
            return False
    
    def get_cache_size(self):
        """Get current cache size in MB"""
        total_size = 0
        for thumb_file in self.cache_dir.glob("*.jpg"):
            total_size += thumb_file.stat().st_size
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def _check_cache_size(self):
        """Check cache size and cleanup if needed"""
        current_size = self.get_cache_size()
        
        if current_size > self.max_size_mb:
            print(f"Cache size {current_size:.1f}MB exceeds limit {self.max_size_mb}MB, cleaning up...")
            self._cleanup_old_cache()
    
    def _cleanup_old_cache(self):
        """Remove oldest thumbnails based on access time (LRU)"""
        try:
            # Get all thumbnail files with their stats
            thumbs = []
            for thumb_file in self.cache_dir.glob("*.jpg"):
                stat = thumb_file.stat()
                thumbs.append({
                    'path': thumb_file,
                    'size': stat.st_size,
                    'atime': stat.st_atime,  # Access time
                    'mtime': stat.st_mtime   # Modification time
                })
            
            if not thumbs:
                return
            
            # Sort by access time (least recently accessed first)
            thumbs.sort(key=lambda x: x['atime'])
            
            # Calculate target size (80% of max to leave headroom)
            target_size = self.max_size_mb * 0.8 * 1024 * 1024  # Convert to bytes
            current_size = sum(t['size'] for t in thumbs)
            
            # Remove files until we're under target
            removed_count = 0
            for thumb in thumbs:
                if current_size <= target_size:
                    break
                
                try:
                    thumb['path'].unlink()
                    current_size -= thumb['size']
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {thumb['path']}: {e}")
            
            print(f"Removed {removed_count} old thumbnails, cache now {current_size / (1024*1024):.1f}MB")
            
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
    
    def get_stats(self):
        """Get cache statistics"""
        return {
            **self.stats,
            'cache_size_mb': self.get_cache_size(),
            'cache_dir': str(self.cache_dir),
            'file_count': len(list(self.cache_dir.glob("*.jpg")))
        }


class ThumbnailGenerator(QThread):
    """Background thread for generating thumbnails from Maya files"""
    
    # Signals
    thumbnail_ready = Signal(str, object)  # (file_path, pixmap)
    progress_update = Signal(int, int)     # (current, total)
    generation_failed = Signal(str, str)    # (file_path, error_message)
    cache_status = Signal(str)             # Status message: "cache" or "generating"
    
    def __init__(self, memory_cache, disk_cache, thumbnail_size=128, jpeg_quality=85, metadata_manager=None):
        super().__init__()
        self.memory_cache = memory_cache
        self.disk_cache = disk_cache
        self.thumbnail_size = thumbnail_size
        self.jpeg_quality = jpeg_quality  # JPEG quality for disk cache (0-100)
        self.metadata_manager = metadata_manager  # For auto-tagging color spaces
        self.queue = []
        self.is_running = True
        self.current_file = None
        self.processed_count = 0  # Track how many we've processed
        self.total_count = 0      # Track total in current batch
        
        # Increase Qt image allocation limit from 256MB to 1024MB (1GB)
        # This allows loading very large images (e.g., 8K textures)
        try:
            if PYSIDE_VERSION == 6:
                from PySide6.QtGui import QImageReader
            else:
                from PySide2.QtGui import QImageReader
            QImageReader.setAllocationLimit(1024)  # 1024 MB = 1 GB
        except Exception as e:
            print(f"[Cache] Could not set image allocation limit: {e}")
        
    def add_to_queue(self, file_path, file_mtime, priority=False, asset=None):
        """Add file to generation queue with optional priority and asset
        
        Args:
            file_path: Path to file
            file_mtime: File modification time
            priority: Priority flag (unused, kept for compatibility)
            asset: Optional AssetItem object (for sequence support)
        """
        # Check if already in queue
        for item in self.queue:
            if item[0] == file_path:
                return
        
        # Just append to queue - priority is handled by clearing old items
        # Items are added in visible order (top to bottom)
        self.queue.append((file_path, file_mtime, asset))
        self.total_count += 1  # Increment total when adding to queue
    
    def clear_queue(self):
        """Clear generation queue"""
        self.queue.clear()
        self.processed_count = 0
        self.total_count = 0
    
    def stop(self):
        """Stop the generator thread gracefully"""
        self.is_running = False
        self.queue.clear()
        self.current_file = None  # Clear current processing file
    
    def run(self):
        """Main thread loop - process queue"""
        while self.is_running:
            if not self.queue:
                self.msleep(50)  # Wait 50ms if queue is empty
                continue
            
            # Get next item from queue (pop from END for correct order)
            queue_item = self.queue.pop()  # pop() = pop(-1) = last item
            
            # Extract components (backwards compatible with old tuple format)
            if len(queue_item) == 3:
                file_path, file_mtime, asset = queue_item
            else:
                file_path, file_mtime = queue_item
                asset = None
            
            self.current_file = file_path
            
            # Increment processed count and emit progress
            self.processed_count += 1
            if self.total_count > 0:
                self.progress_update.emit(self.processed_count, self.total_count)
            
            try:
                # For sequences, use pattern as cache key instead of file path
                cache_key = file_path
                is_sequence = asset and asset.is_sequence and asset.sequence
                if is_sequence:
                    # Use sequence pattern as cache key (e.g. "render_####.jpg")
                    cache_key = str(asset.sequence.pattern)
                
                if DEBUG_MODE:
                    print(f"[CACHE-THREAD] Processing: {Path(file_path).name}")
                    import sys
                    sys.stdout.flush()  # Force immediate print
                
                # Check memory cache first
                cached = self.memory_cache.get(cache_key)
                if cached:
                    if DEBUG_MODE:
                        print(f"[CACHE-THREAD] → Found in memory cache")
                    self.cache_status.emit("cache")
                    self.thumbnail_ready.emit(file_path, cached)
                    continue
                
                # Check disk cache (skip for sequences for now - always regenerate)
                if not is_sequence:
                    cached = self.disk_cache.get(file_path, file_mtime)
                    if cached and not cached.isNull():
                        # Valid cached pixmap
                        if DEBUG_MODE:
                            print(f"[CACHE-THREAD] → Found in disk cache")
                        self.cache_status.emit("cache")
                        self.memory_cache.set(file_path, cached)
                        self.thumbnail_ready.emit(file_path, cached)
                        continue
                    elif DEBUG_MODE:
                        print(f"[CACHE-THREAD] → NOT in disk cache, generating...")
                
                # Generate new thumbnail
                if DEBUG_MODE:
                    print(f"[CACHE-THREAD] → Generating new thumbnail...")
                self.cache_status.emit("generating")
                pixmap = self._generate_thumbnail(file_path, asset)
                
                if pixmap and not pixmap.isNull():
                    # Save to caches with configured JPEG quality
                    if not is_sequence:
                        self.disk_cache.set(file_path, file_mtime, pixmap, quality=self.jpeg_quality)
                    self.memory_cache.set(cache_key, pixmap)
                    
                    # Emit signal
                    self.thumbnail_ready.emit(file_path, pixmap)
                # If None returned: no thumbnail generated (normal for 3D files)
                # Delegate will draw placeholder directly - no error needed
                    
            except Exception as e:
                # Only emit error for actual exceptions (image loading failures, etc.)
                self.generation_failed.emit(file_path, str(e))
            
            finally:
                self.current_file = None
    
    def _get_opencv_imread_flags(self):
        """
        Calculate optimal OpenCV imread flags based on thumbnail size.
        Uses IMREAD_REDUCED_* for faster decoding of large TIFF/HDR images.
        
        Optimized logic: Loaded size should be ~8-16× thumbnail size for best quality/speed balance.
        
        Returns:
            OpenCV imread flags (int)
        """
        import cv2
        
        # For small thumbnails, use aggressive downsampling during decode
        # This is MUCH faster for large TIFF files (2-8× speedup)
        # 
        # OPTIMIZED LOGIC:
        # - thumbnail ≤ 64px  → load at 1/8 scale (e.g., 16k→2048, 8k→1024) = 32-16× thumbnail
        # - thumbnail ≤ 128px → load at 1/4 scale (e.g., 16k→4096, 8k→2048) = 32-16× thumbnail  
        # - thumbnail ≤ 256px → load at 1/8 scale (e.g., 16k→2048, 8k→1024) = 8-4× thumbnail
        # - thumbnail > 256px → load at 1/2 scale (e.g., 16k→8192) = preserve detail
        
        if self.thumbnail_size <= 64:
            # 1/8 scale - fastest for tiny thumbnails
            # 16k TIFF → 2048px → resize to 64px (32× downscale total)
            if DEBUG_MODE:
                print(f"[OPENCV] Using 1/8 scale (IMREAD_REDUCED_COLOR_8) for thumbnail_size={self.thumbnail_size}")
            return cv2.IMREAD_REDUCED_COLOR_8 | cv2.IMREAD_ANYDEPTH
        elif self.thumbnail_size <= 128:
            # 1/4 scale - good balance for default size
            # 16k TIFF → 4096px → resize to 128px (32× downscale total)
            if DEBUG_MODE:
                print(f"[OPENCV] Using 1/4 scale (IMREAD_REDUCED_COLOR_4) for thumbnail_size={self.thumbnail_size}")
            return cv2.IMREAD_REDUCED_COLOR_4 | cv2.IMREAD_ANYDEPTH
        elif self.thumbnail_size <= 256:
            # 1/8 scale - OPTIMIZED! Previously was 1/2 (too much data)
            # 16k TIFF → 2048px → resize to 256px (8× downscale, perfect quality)
            if DEBUG_MODE:
                print(f"[OPENCV] Using 1/8 scale (IMREAD_REDUCED_COLOR_8) for thumbnail_size={self.thumbnail_size}")
            return cv2.IMREAD_REDUCED_COLOR_8 | cv2.IMREAD_ANYDEPTH
        else:
            # 1/2 scale for larger thumbnails (256+) to preserve detail
            # 16k TIFF → 8192px → resize to 512px+ (preserves detail for large thumbnails)
            if DEBUG_MODE:
                print(f"[OPENCV] Using 1/2 scale (IMREAD_REDUCED_COLOR_2) for thumbnail_size={self.thumbnail_size}")
            return cv2.IMREAD_REDUCED_COLOR_2 | cv2.IMREAD_ANYDEPTH
    
    @staticmethod
    def _load_psd_composite(file_path, max_size=None):
        """
        Load full PSD composite image using psd-tools library (STATIC METHOD)
        
        This loads the full-resolution flattened/composite image from a PSD file,
        including support for 32-bit PSDs that PIL cannot handle.
        
        Args:
            file_path: Path to PSD file
            max_size: Optional max dimension (for thumbnails/previews)
            
        Returns:
            QPixmap or None
        """
        import sys
        import os
        
        # Add external_libs to path
        external_libs = os.path.join(os.path.dirname(__file__), 'external_libs')
        if external_libs not in sys.path:
            sys.path.insert(0, external_libs)
        
        try:
            from psd_tools import PSDImage
            from PIL import Image
            
            if DEBUG_MODE:
                print(f"[PSD] Loading composite with psd-tools: {Path(file_path).name}")
            
            # Open PSD
            psd = PSDImage.open(str(file_path))
            
            if DEBUG_MODE:
                print(f"[PSD] PSD size: {psd.width}x{psd.height}, depth={psd.depth}-bit")
            
            # Get composite (flattened) image as PIL Image
            composite = psd.composite()
            
            if composite is None:
                if DEBUG_MODE:
                    print(f"[PSD] No composite available")
                return None
            
            # Convert to RGB if needed
            if composite.mode not in ('RGB', 'L'):
                if DEBUG_MODE:
                    print(f"[PSD] Converting {composite.mode} → RGB")
                composite = composite.convert('RGB')
            elif composite.mode == 'L':
                composite = composite.convert('RGB')
            
            # Resize if max_size specified
            if max_size:
                composite.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                if DEBUG_MODE:
                    print(f"[PSD] Resized to: {composite.size}")
            
            # Convert PIL Image to QPixmap
            import numpy as np
            img_array = np.array(composite)
            height, width = img_array.shape[:2]
            
            if PYSIDE_VERSION == 6:
                from PySide6.QtGui import QImage
            else:
                from PySide2.QtGui import QImage
            
            bytes_per_line = width * 3
            q_image = QImage(img_array.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
            
            if DEBUG_MODE:
                print(f"[PSD] ✓ Composite loaded: {width}x{height}")
            
            return QPixmap.fromImage(q_image.copy())
            
        except ImportError:
            if DEBUG_MODE:
                print(f"[PSD] psd-tools not available, falling back to thumbnail extraction")
            return None
        except Exception as e:
            if DEBUG_MODE:
                print(f"[PSD] Failed to load composite: {e}")
            return None
    
    @staticmethod
    def _extract_psd_thumbnail(file_path, thumbnail_size=256):
        """
        Extract embedded thumbnail from PSD file (STATIC METHOD)
        
        Many PSD files (especially 32-bit) contain embedded JPEG/PNG thumbnails
        that can be extracted without loading the full image data.
        
        Args:
            file_path: Path to PSD file
            thumbnail_size: Max dimension for the thumbnail
            
        Returns:
            QPixmap or None
        """
        import struct
        from io import BytesIO
        import sys
        import os
        
        # Add external_libs to path for PIL import
        external_libs = os.path.join(os.path.dirname(__file__), 'external_libs')
        if external_libs not in sys.path:
            sys.path.insert(0, external_libs)
        
        try:
            with open(str(file_path), 'rb') as f:
                # Read PSD header
                signature = f.read(4)
                if signature != b'8BPS':
                    return None
                
                version = struct.unpack('>H', f.read(2))[0]
                f.read(6)  # Reserved
                channels = struct.unpack('>H', f.read(2))[0]
                height = struct.unpack('>I', f.read(4))[0]
                width = struct.unpack('>I', f.read(4))[0]
                depth = struct.unpack('>H', f.read(2))[0]
                color_mode = struct.unpack('>H', f.read(2))[0]
                
                # Skip color mode data section
                color_mode_data_len = struct.unpack('>I', f.read(4))[0]
                f.read(color_mode_data_len)
                
                # Read image resources section (contains thumbnails)
                image_resources_len = struct.unpack('>I', f.read(4))[0]
                resources_start = f.tell()
                resources_end = resources_start + image_resources_len
                
                # Look for thumbnail resources
                # Resource ID 1033 = Thumbnail (Photoshop 5.0+, JPEG)
                # Resource ID 1036 = Thumbnail (Photoshop 4.0, RGB)
                while f.tell() < resources_end:
                    try:
                        # Read resource block
                        res_signature = f.read(4)
                        if res_signature != b'8BIM':
                            break
                        
                        res_id = struct.unpack('>H', f.read(2))[0]
                        
                        # Read pascal string name (padded to even length)
                        name_len = struct.unpack('B', f.read(1))[0]
                        if name_len > 0:
                            f.read(name_len)
                        if (name_len + 1) % 2 != 0:
                            f.read(1)  # Padding
                        
                        # Read resource data size
                        res_size = struct.unpack('>I', f.read(4))[0]
                        res_data_start = f.tell()
                        
                        # Check if this is a thumbnail resource
                        if res_id in [1033, 1036]:
                            if DEBUG_MODE:
                                print(f"[PSD] Found thumbnail resource ID {res_id}, size={res_size}")
                            
                            if res_id == 1033:
                                # JPEG thumbnail (Photoshop 5.0+)
                                # Skip format (4), width (4), height (4), widthbytes (4), 
                                # total size (4), compressed size (4), bpp (2), planes (2) = 28 bytes
                                f.read(28)
                                jpeg_data = f.read(res_size - 28)
                                
                                # Load JPEG thumbnail
                                from PIL import Image
                                thumb_img = Image.open(BytesIO(jpeg_data))
                                
                                # Resize to thumbnail size
                                thumb_img.thumbnail((thumbnail_size, thumbnail_size), Image.Resampling.LANCZOS)
                                
                                # Convert to QPixmap
                                import numpy as np
                                img_array = np.array(thumb_img.convert('RGB'))
                                height, width = img_array.shape[:2]
                                
                                if PYSIDE_VERSION == 6:
                                    from PySide6.QtGui import QImage
                                else:
                                    from PySide2.QtGui import QImage
                                
                                bytes_per_line = width * 3
                                q_image = QImage(img_array.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                                return QPixmap.fromImage(q_image.copy())
                            
                            elif res_id == 1036:
                                # RGB thumbnail (Photoshop 4.0)
                                # Format: format (4), width (4), height (4), widthbytes (4), 
                                # total size (4), compressed size (4), bpp (2), planes (2) = 28 bytes
                                # Then raw RGB data OR JPEG data (check compressed_size)
                                if DEBUG_MODE:
                                    print(f"[PSD] Processing resource 1036 (Photoshop 4.0 RGB thumbnail)")
                                
                                thumb_format = struct.unpack('>I', f.read(4))[0]  # 1 = kRawRGB
                                thumb_width = struct.unpack('>I', f.read(4))[0]
                                thumb_height = struct.unpack('>I', f.read(4))[0]
                                widthbytes = struct.unpack('>I', f.read(4))[0]
                                total_size = struct.unpack('>I', f.read(4))[0]
                                compressed_size = struct.unpack('>I', f.read(4))[0]
                                bpp = struct.unpack('>H', f.read(2))[0]
                                planes = struct.unpack('>H', f.read(2))[0]
                                
                                if DEBUG_MODE:
                                    print(f"[PSD] Thumb size: {thumb_width}x{thumb_height}, format={thumb_format}, bpp={bpp}")
                                    print(f"[PSD] Total size: {total_size}, Compressed: {compressed_size}")
                                
                                # Read thumbnail data (remaining bytes after header)
                                rgb_data_size = res_size - 28
                                rgb_data = f.read(rgb_data_size)
                                
                                # Check if it's compressed (JPEG)
                                from PIL import Image
                                try:
                                    if compressed_size > 0 and compressed_size < total_size:
                                        # Compressed thumbnail (usually JPEG)
                                        if DEBUG_MODE:
                                            print(f"[PSD] Thumbnail is compressed (JPEG), size={compressed_size}")
                                        thumb_img = Image.open(BytesIO(rgb_data))
                                    else:
                                        # Uncompressed RGB data
                                        if DEBUG_MODE:
                                            print(f"[PSD] Thumbnail is raw RGB data")
                                        thumb_img = Image.frombytes('RGB', (thumb_width, thumb_height), rgb_data)
                                    
                                    # Resize to thumbnail size
                                    thumb_img.thumbnail((thumbnail_size, thumbnail_size), Image.Resampling.LANCZOS)
                                    
                                    # Convert to QPixmap
                                    import numpy as np
                                    img_array = np.array(thumb_img.convert('RGB'))
                                    height, width = img_array.shape[:2]
                                    
                                    if PYSIDE_VERSION == 6:
                                        from PySide6.QtGui import QImage
                                    else:
                                        from PySide2.QtGui import QImage
                                    
                                    bytes_per_line = width * 3
                                    q_image = QImage(img_array.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                                    if DEBUG_MODE:
                                        print(f"[PSD] ✓ Resource 1036 thumbnail extracted: {width}x{height}")
                                    return QPixmap.fromImage(q_image.copy())
                                except Exception as rgb_error:
                                    if DEBUG_MODE:
                                        print(f"[PSD] Failed to decode RGB thumbnail: {rgb_error}")
                        
                        # Skip to next resource (data is padded to even length)
                        f.seek(res_data_start + res_size)
                        if res_size % 2 != 0:
                            f.read(1)  # Padding
                            
                    except struct.error:
                        break
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"[PSD] Thumbnail extraction error: {e}")
            return None
        
        return None
    
    def _generate_thumbnail(self, file_path, asset=None):
        """
        Generate thumbnail from file
        
        For images/PDFs: Load and scale the actual image/first page
        For sequences: Load middle frame and add badge overlay
        For 3D files: Generate gradient icon (safe mode)
        
        Args:
            file_path: Path to file (or sequence pattern for sequences)
            asset: Optional AssetItem object (for sequence support)
            
        Returns:
            QPixmap or None
        """
        # Early exit if thread is stopping
        if not self.is_running:
            return None
        
        from .utils import get_thumbnail_method
        
        # Check if this is a sequence - use middle frame for thumbnail
        if asset and asset.is_sequence and asset.sequence:
            middle_frame_path = asset.sequence.get_middle_frame()
            if middle_frame_path:
                # Generate thumbnail from middle frame (WITHOUT badge - delegate will add it)
                pixmap = self._generate_image_thumbnail(middle_frame_path)
                
                # Don't add badge here - the delegate will draw it at the correct display size
                # if pixmap and not pixmap.isNull():
                #     pixmap = self._add_sequence_badge(pixmap, asset.sequence.frame_count)
                
                return pixmap
        
        extension = os.path.splitext(str(file_path))[1].lower()
        
        # Get thumbnail method from config
        thumbnail_method = get_thumbnail_method(extension)
        
        if thumbnail_method != 'none':
            # Generate actual thumbnail from file
            return self._generate_image_thumbnail(file_path)
        
        # 3D files and other types - don't generate placeholder in cache
        # The delegate will draw gradient placeholder directly (faster, no scaling)
        return None
    
    def _add_sequence_badge(self, pixmap, frame_count):
        """
        Add badge overlay to sequence thumbnail showing frame count
        
        Args:
            pixmap: Original thumbnail pixmap
            frame_count: Number of frames in sequence
            
        Returns:
            QPixmap with badge overlay
        """
        if PYSIDE_VERSION == 6:
            from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
            from PySide6.QtCore import Qt, QRect
        else:
            from PySide2.QtGui import QPainter, QColor, QFont, QPen, QBrush
            from PySide2.QtCore import Qt, QRect
        
        # Create a copy to draw on
        result = pixmap.copy()
        
        # Setup painter
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Badge dimensions - scale with thumbnail size but keep readable minimum
        # For very small thumbnails, use aggressive scaling to remain visible
        thumb_size = result.height()
        
        if thumb_size <= 32:
            # Tiny thumbnails (list view): use 35% with higher minimum
            badge_height = max(20, int(thumb_size * 0.35))
        elif thumb_size < 64:
            # Small thumbnails: use 28% with higher minimum
            badge_height = max(18, int(thumb_size * 0.28))
        else:
            # Normal thumbnails: use 15% with standard minimum
            badge_height = max(16, int(thumb_size * 0.15))
        
        badge_margin = 2
        
        # Badge text
        badge_text = f"{frame_count} frames"
        
        # Setup font - larger minimum for small thumbnails
        font = QFont()
        if thumb_size <= 32:
            # Tiny thumbnails: much larger relative font (min 11px)
            font_size = max(11, int(badge_height * 0.65))
            font.setPixelSize(font_size)
        elif thumb_size < 64:
            # Small thumbnails: larger font (min 10px)
            font_size = max(10, int(badge_height * 0.62))
            font.setPixelSize(font_size)
        else:
            # Normal thumbnails: standard font (min 9px)
            font_size = max(9, int(badge_height * 0.6))
            font.setPixelSize(font_size)
        font.setBold(True)
        painter.setFont(font)
        
        # Calculate text size
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(badge_text)
        text_height = metrics.height()
        
        # Badge rectangle (bottom of thumbnail)
        badge_width = text_width + badge_margin * 4
        badge_rect = QRect(
            (result.width() - badge_width) // 2,  # Centered horizontally
            result.height() - badge_height - badge_margin,  # Bottom
            badge_width,
            badge_height
        )
        
        # Draw semi-transparent background
        painter.setPen(Qt.NoPen)
        bg_color = QColor(0, 0, 0, 180)  # Black with 70% opacity
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(badge_rect, 3, 3)
        
        # Draw text
        painter.setPen(QPen(QColor(255, 255, 255)))  # White text
        text_rect = QRect(
            badge_rect.x() + badge_margin * 2,
            badge_rect.y() + (badge_height - text_height) // 2,
            text_width,
            text_height
        )
        painter.drawText(text_rect, Qt.AlignCenter, badge_text)
        
        painter.end()
        
        return result
    
    def _generate_image_thumbnail(self, file_path):
        """
        Generate thumbnail from image file (including PDF first page)
        Fast image loading and scaling
        
        Args:
            file_path: Path to image file or PDF
            
        Returns:
            QPixmap or None
        """
        try:
            extension = os.path.splitext(str(file_path))[1].lower()
            
            # Special handling for PDF files - render first page
            if extension == '.pdf':
                try:
                    from .widgets import load_pdf_page
                    pixmap, page_count, status = load_pdf_page(file_path, page_number=0, max_size=self.thumbnail_size)
                    
                    # Check if PDF is encrypted
                    if status == "encrypted":
                        # Password protected PDF - use default icon without extra error message
                        return self._get_default_icon(file_path)
                    
                    if pixmap and not pixmap.isNull():
                        return pixmap
                    else:
                        raise Exception("PDF loader returned null pixmap")
                except Exception as e:
                    # Only print error for non-encrypted PDFs
                    if "encrypted" not in str(e).lower():
                        print(f"[Cache] PDF loading failed: {e}, using default icon...")
                    return self._get_default_icon(file_path)
            
            # Special handling for .tx files - use OpenImageIO
            if extension == '.tx':
                # Auto-tag color space FIRST (before thumbnail generation)
                if self.metadata_manager:
                    try:
                        from .aces_color import auto_tag_file_colorspace
                        auto_tag_file_colorspace(file_path, self.metadata_manager)
                    except Exception as tag_error:
                        if DEBUG_MODE:
                            print(f"[Cache] Warning: Auto-tagging .tx failed: {tag_error}")
                
                try:
                    from .widgets import load_oiio_image
                    # Load mip level 1 for fast thumbnail (half resolution)
                    pixmap, _, _ = load_oiio_image(file_path, max_size=self.thumbnail_size, mip_level=1)
                    if pixmap and not pixmap.isNull():
                        return pixmap
                    else:
                        raise Exception("OIIO loader returned null pixmap")
                except Exception as e:
                    print(f"[Cache] OIIO .tx loading failed: {e}, using default icon...")
                    return self._get_default_icon(file_path)
            
            # Special handling for EXR files - OPTIMIZED fast thumbnail generation
            if extension == '.exr':
                # Use optimized EXR thumbnail loader (much faster than full loader)
                try:
                    pixmap = self._generate_exr_thumbnail_optimized(file_path)
                    if pixmap and not pixmap.isNull():
                        return pixmap
                    else:
                        raise Exception("EXR loader returned null pixmap")
                except Exception as e:
                    error_msg = str(e)
                    # Deep/volumetric EXR files are not supported
                    if "deep/volumetric" in error_msg.lower() or "non-numeric dtype" in error_msg:
                        if DEBUG_MODE:
                            print(f"[Cache] Deep/volumetric EXR not supported: {Path(file_path).name}")
                        return self._get_default_icon(file_path)
                    else:
                        if DEBUG_MODE:
                            print(f"[Cache] EXR loading failed: {e}, trying QPixmap fallback...")
                    # Fall through to QPixmap method below
            
            # Special handling for HDR/TIFF/TGA/PSD files - use OpenCV or PIL for better format support
            elif extension in ['.hdr', '.tif', '.tiff', '.tga', '.psd']:
                if DEBUG_MODE:
                    print(f"[THUMB] Loading {extension} file: {Path(file_path).name}")
                
                # OPTIMIZED: Use dedicated fast thumbnail generator for HDR files
                if extension == '.hdr':
                    try:
                        pixmap = self._generate_hdr_thumbnail_optimized(file_path)
                        if pixmap and not pixmap.isNull():
                            return pixmap
                        else:
                            if DEBUG_MODE:
                                print(f"[THUMB] HDR optimized loader failed, trying fallback...")
                    except Exception as e:
                        if DEBUG_MODE:
                            print(f"[THUMB] HDR optimized loader exception: {e}, trying fallback...")
                
                try:
                    # Try OpenCV first for 16-bit/32-bit TIFF and TGA support
                    import cv2
                    import numpy as np
                    
                    # Get optimized imread flags (uses IMREAD_REDUCED_* for faster decoding)
                    imread_flags = self._get_opencv_imread_flags()
                    
                    # OpenCV can't handle Unicode paths, check for non-ASCII first
                    file_path_str = str(file_path)
                    has_non_ascii = any(ord(c) > 127 for c in file_path_str)
                    
                    img = None
                    if has_non_ascii:
                        # Use buffer method for non-ASCII paths (ékezetes karakterek)
                        try:
                            if DEBUG_MODE:
                                print(f"[THUMB] Using buffer method (non-ASCII path) with flags={imread_flags}")
                            with open(file_path_str, 'rb') as f:
                                file_bytes = np.frombuffer(f.read(), np.uint8)
                            img = cv2.imdecode(file_bytes, imread_flags)
                        except Exception as e:
                            if DEBUG_MODE:
                                print(f"[THUMB] Buffer decode failed: {e}")
                    else:
                        # ASCII-only path, use direct imread with optimized flags
                        try:
                            if DEBUG_MODE:
                                print(f"[THUMB] Using imread with optimized flags={imread_flags}")
                            img = cv2.imread(file_path_str, imread_flags)
                        except Exception as e:
                            if DEBUG_MODE:
                                print(f"[THUMB] OpenCV imread failed: {e}")
                    
                    if img is None:
                        if DEBUG_MODE:
                            print(f"[THUMB] First attempt failed, trying IMREAD_COLOR...")
                        # Try alternative loading method
                        if has_non_ascii:
                            try:
                                with open(file_path_str, 'rb') as f:
                                    file_bytes = np.frombuffer(f.read(), np.uint8)
                                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                            except Exception as e:
                                if DEBUG_MODE:
                                    print(f"[THUMB] Buffer COLOR decode failed: {e}")
                        else:
                            try:
                                img = cv2.imread(file_path_str, cv2.IMREAD_COLOR)
                            except Exception as e:
                                if DEBUG_MODE:
                                    print(f"[THUMB] OpenCV COLOR imread failed: {e}")
                    
                    if img is None:
                        raise Exception("OpenCV could not load the image")
                    
                    # Check channel count
                    if len(img.shape) == 3:
                        channels = img.shape[2]
                        if DEBUG_MODE:
                            print(f"[THUMB] Image loaded: {img.shape[1]}×{img.shape[0]}, {channels} channels, dtype={img.dtype}")
                        
                        # Handle unsupported channel counts (e.g., 5-channel TIFF)
                        if channels > 4:
                            if DEBUG_MODE:
                                print(f"[THUMB] Unsupported {channels} channels, extracting first 4...")
                            img = img[:, :, :4]  # Keep only first 4 channels
                    else:
                        if DEBUG_MODE:
                            print(f"[THUMB] Image loaded: {img.shape[1]}×{img.shape[0]}, grayscale, dtype={img.dtype}")
                    
                    # FIRST: Convert color space (BGR/BGRA → RGB) BEFORE normalization
                    if len(img.shape) == 2:
                        # Grayscale - convert to RGB
                        if DEBUG_MODE:
                            print(f"[THUMB] Converting grayscale to RGB")
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                    elif len(img.shape) == 3 and img.shape[2] == 4:
                        # RGBA - convert to RGB (keeping 16-bit if present)
                        if DEBUG_MODE:
                            print(f"[THUMB] Converting BGRA to RGB")
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                    elif len(img.shape) == 3 and img.shape[2] == 3:
                        # BGR - convert to RGB
                        if DEBUG_MODE:
                            print(f"[THUMB] Converting BGR to RGB")
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    
                    # THEN: Normalize bit depth AFTER color conversion
                    if img.dtype == np.uint16:
                        # 16-bit image - normalize to 8-bit
                        # 16-bit range: 0-65535 → 8-bit range: 0-255
                        # Correct conversion: divide by 257 (65535/255), not 256
                        if DEBUG_MODE:
                            print(f"[THUMB] Normalizing 16-bit to 8-bit (÷257)")
                        img = (img / 257).astype(np.uint8)
                    elif img.dtype == np.float32 or img.dtype == np.float64:
                        # 32-bit float - normalize and apply simple tone mapping
                        if DEBUG_MODE:
                            print(f"[THUMB] Normalizing 32-bit float to 8-bit")
                        img = np.clip(img, 0, 1)  # Clip to 0-1 range
                        img = (img * 255).astype(np.uint8)
                    
                    if DEBUG_MODE:
                        print(f"[THUMB] Converted to RGB: {img.shape[1]}×{img.shape[0]}")
                    
                    # Resize for thumbnail
                    height, width = img.shape[:2]
                    if width > self.thumbnail_size or height > self.thumbnail_size:
                        scale = min(self.thumbnail_size / width, self.thumbnail_size / height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                        if DEBUG_MODE:
                            print(f"[THUMB] Resized to: {new_width}×{new_height}")
                    
                    # Convert numpy array to QPixmap
                    height, width, channels = img.shape
                    bytes_per_line = width * channels
                    
                    if PYSIDE_VERSION == 6:
                        from PySide6.QtGui import QImage
                    else:
                        from PySide2.QtGui import QImage
                    
                    q_image = QImage(img.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_image.copy())
                    
                    if not pixmap.isNull():
                        if DEBUG_MODE:
                            print(f"[THUMB] ✓ Successfully created thumbnail")
                        return pixmap
                    else:
                        raise Exception("Failed to convert to QPixmap")
                        
                except Exception as e:
                    # Try multiple fallback methods
                    if DEBUG_MODE:
                        print(f"[THUMB] OpenCV failed: {e}")
                    pixmap = None
                    
                    # For multi-channel images, always try PIL/Pillow as fallback
                    # (OpenCV prints errors to stderr, not in exception message)
                    if DEBUG_MODE:
                        print(f"[THUMB] Trying PIL/Pillow fallback for special format...")
                    try:
                        from PIL import Image
                        # Disable decompression bomb warning for large images
                        Image.MAX_IMAGE_PIXELS = None
                        pil_image = Image.open(str(file_path))
                        
                        if DEBUG_MODE:
                            print(f"[THUMB] PIL loaded: {pil_image.size}, mode={pil_image.mode}")
                        
                        # Convert to RGB (discard extra channels)
                        if pil_image.mode not in ('RGB', 'L'):
                            if DEBUG_MODE:
                                print(f"[THUMB] Converting {pil_image.mode} to RGB...")
                            pil_image = pil_image.convert('RGB')
                        elif pil_image.mode == 'L':
                            if DEBUG_MODE:
                                print(f"[THUMB] Converting grayscale to RGB...")
                            pil_image = pil_image.convert('RGB')
                        
                        # Resize
                        pil_image.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
                        
                        # Convert to QPixmap
                        import numpy as np
                        img_array = np.array(pil_image)
                        height, width = img_array.shape[:2]
                        channels = img_array.shape[2] if len(img_array.shape) == 3 else 1
                        
                        if PYSIDE_VERSION == 6:
                            from PySide6.QtGui import QImage
                        else:
                            from PySide2.QtGui import QImage
                        
                        if channels == 3:
                            bytes_per_line = width * 3
                            q_image = QImage(img_array.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                            pixmap = QPixmap.fromImage(q_image.copy())
                            if DEBUG_MODE:
                                print(f"[THUMB] ✓ PIL fallback successful: {width}×{height}")
                            if pixmap and not pixmap.isNull():
                                return pixmap
                        
                        if DEBUG_MODE:
                            print(f"[THUMB] PIL unexpected channels={channels}, falling through...")
                    except Exception as pil_error:
                        if DEBUG_MODE:
                            print(f"[THUMB] PIL fallback also failed: {pil_error}")
                        
                        # Special handling for PSD files: try psd-tools first, then embedded thumbnail
                        if extension == '.psd':
                            try:
                                if DEBUG_MODE:
                                    print(f"[THUMB] Trying to load PSD composite with psd-tools...")
                                pixmap = ThumbnailGenerator._load_psd_composite(file_path, max_size=self.thumbnail_size)
                                if pixmap and not pixmap.isNull():
                                    if DEBUG_MODE:
                                        print(f"[THUMB] ✓ PSD composite loaded successfully")
                                    return pixmap
                                else:
                                    if DEBUG_MODE:
                                        print(f"[THUMB] psd-tools failed, trying embedded thumbnail...")
                                    pixmap = ThumbnailGenerator._extract_psd_thumbnail(file_path, thumbnail_size=self.thumbnail_size)
                                    if pixmap and not pixmap.isNull():
                                        if DEBUG_MODE:
                                            print(f"[THUMB] ✓ PSD thumbnail extracted successfully")
                                        return pixmap
                            except Exception as thumb_error:
                                if DEBUG_MODE:
                                    print(f"[THUMB] PSD loading failed: {thumb_error}")
                        
                        # Check if it's an unsupported multi-channel TIFF
                        if "unknown pixel mode" in str(pil_error) or "KeyError" in str(pil_error):
                            if DEBUG_MODE:
                                print(f"[THUMB] → Unsupported TIFF format (5+ channels), skipping: {file_path.name}")
                    
                    # Method 1: Try QImageReader with explicit format and increased limit
                    try:
                        if PYSIDE_VERSION == 6:
                            from PySide6.QtGui import QImageReader, QImage
                        else:
                            from PySide2.QtGui import QImageReader, QImage
                        
                        reader = QImageReader(str(file_path))
                        
                        # Increase allocation limit for this reader (TGA files can be huge)
                        reader.setAllocationLimit(2048)  # 2 GB limit
                        
                        # Force format detection
                        if extension == '.tga':
                            reader.setFormat(b'tga')
                            if DEBUG_MODE:
                                print(f"[THUMB] QImageReader trying TGA with 2GB limit...")
                        elif extension in ['.tif', '.tiff']:
                            reader.setFormat(b'tiff')
                        
                        image = reader.read()
                        if not image.isNull():
                            pixmap = QPixmap.fromImage(image)
                            if DEBUG_MODE:
                                print(f"[THUMB] ✓ QImageReader successful")
                    except Exception as reader_error:
                        print(f"[THUMB] QImageReader failed: {reader_error}")
                    
                    # Method 2: Standard QPixmap
                    if pixmap is None or pixmap.isNull():
                        pixmap = QPixmap(str(file_path))
                    
                    # If we got a valid pixmap, resize it
                    if pixmap is not None and not pixmap.isNull():
                        pixmap = pixmap.scaled(
                            self.thumbnail_size,
                            self.thumbnail_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        return pixmap
                    # Fall through to default handling below
            
            # Standard image files - use QPixmap (for 8-bit JPEG, PNG, etc.)
            # For very large images (16K+), try OpenCV first for better memory handling
            try:
                # Check file size first - if over 50MB, use OpenCV
                file_size_mb = os.path.getsize(str(file_path)) / (1024 * 1024)
                
                if DEBUG_MODE:
                    print(f"[Cache] Standard image: {Path(file_path).name}, size={file_size_mb:.1f}MB, ext={extension}")
                    import sys
                    sys.stdout.flush()  # Force immediate print
                
                # OPTIMIZED: Only large files go to OpenCV (removed auto JPG routing)
                # Small/medium JPG/PNG work better with QImageReader (native DCT/progressive decode)
                # IMPORTANT: PNG files should ALWAYS use QImageReader (better 16-bit support)
                if file_size_mb > 50 and extension != '.png':
                    if DEBUG_MODE:
                        print(f"[Cache] → Large file, using OpenCV path")
                    # Try OpenCV for large files - better memory handling with optimized flags
                    import cv2
                    import numpy as np
                    
                    # Get optimized imread flags (uses IMREAD_REDUCED_* for faster decoding)
                    imread_flags = self._get_opencv_imread_flags()
                    
                    # OpenCV can't handle Unicode paths, check for non-ASCII first
                    file_path_str = str(file_path)
                    has_non_ascii = any(ord(c) > 127 for c in file_path_str)
                    
                    img = None
                    if has_non_ascii:
                        # Use buffer method for non-ASCII paths (ékezetes karakterek)
                        try:
                            if DEBUG_MODE:
                                print(f"[Cache] Using buffer method (non-ASCII path) with flags={imread_flags}")
                            with open(file_path_str, 'rb') as f:
                                file_bytes = np.frombuffer(f.read(), np.uint8)
                            img = cv2.imdecode(file_bytes, imread_flags)
                        except Exception as e:
                            print(f"[Cache] Buffer decode failed: {e}")
                    else:
                        # ASCII-only path, use direct imread with optimized flags
                        try:
                            if DEBUG_MODE:
                                print(f"[Cache] Using imread with optimized flags={imread_flags}")
                            img = cv2.imread(file_path_str, imread_flags)
                        except:
                            pass
                    
                    if img is not None:
                        # Convert BGR to RGB
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        
                        # Calculate thumbnail size
                        h, w = img.shape[:2]
                        
                        # Only resize if still too large (IMREAD_REDUCED_* already downscaled)
                        if w > self.thumbnail_size or h > self.thumbnail_size:
                            scale = min(self.thumbnail_size / w, self.thumbnail_size / h)
                            new_w = int(w * scale)
                            new_h = int(h * scale)
                            
                            # Resize with OpenCV (faster for large images)
                            img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                            
                            if DEBUG_MODE:
                                print(f"[Cache] Resized from {w}×{h} to {new_w}×{new_h}")
                        else:
                            # Already at good size from IMREAD_REDUCED
                            img_resized = img
                            if DEBUG_MODE:
                                print(f"[Cache] No resize needed, already at {w}×{h}")
                        
                        # Convert to QPixmap
                        if PYSIDE_VERSION == 6:
                            from PySide6.QtGui import QImage
                        else:
                            from PySide2.QtGui import QImage
                        
                        height, width, channel = img_resized.shape
                        bytes_per_line = 3 * width
                        q_image = QImage(img_resized.data, width, height, bytes_per_line, QImage.Format_RGB888)
                        
                        pixmap = QPixmap.fromImage(q_image)
                        
                        return pixmap
            except Exception as e:
                print(f"[Cache] OpenCV loading failed for large JPG: {e}, trying QPixmap...")
            
            # OPTIMIZED: Use QImageReader with scaled size for fast thumbnail generation
            # This loads only the necessary data at thumbnail size, not the full image
            # Works best for: JPEG (uses DCT subsampling), PNG (progressive decode), standard 8-bit images
            try:
                if DEBUG_MODE:
                    print(f"[Cache] → Using QImageReader for thumbnail generation")
                
                if PYSIDE_VERSION == 6:
                    from PySide6.QtGui import QImageReader, QImage
                    from PySide6.QtCore import QSize
                else:
                    from PySide2.QtGui import QImageReader, QImage
                    from PySide2.QtCore import QSize
                
                reader = QImageReader(str(file_path))
                
                # Enable EXIF auto-rotation (CRITICAL for correct thumbnail orientation!)
                reader.setAutoTransform(True)
                
                # Get original size
                original_size = reader.size()
                if original_size.isValid():
                    if DEBUG_MODE:
                        print(f"[Cache] → Original size: {original_size.width()}×{original_size.height()}")
                    
                    # Calculate scaled size maintaining aspect ratio
                    scaled_size = original_size.scaled(
                        self.thumbnail_size, 
                        self.thumbnail_size, 
                        Qt.KeepAspectRatio
                    )
                    if DEBUG_MODE:
                        print(f"[Cache] → Scaled size: {scaled_size.width()}×{scaled_size.height()}")
                    
                    # Tell reader to decode at this smaller size (FAST!)
                    # For JPEG: uses DCT coefficient subsampling (4-6× faster)
                    # For PNG: progressive decode, only loads what's needed
                    reader.setScaledSize(scaled_size)
                
                # Read the already-scaled image (no separate scaling step needed!)
                image = reader.read()
                
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    if not pixmap.isNull():
                        if DEBUG_MODE:
                            print(f"[Cache] ✓ QImageReader success: {pixmap.width()}×{pixmap.height()}")
                        return pixmap
                
                # If reader failed, print error and fall through to old method
                if DEBUG_MODE:
                    print(f"[Cache] ✗ QImageReader failed: {reader.errorString()}, using fallback...")
                
            except Exception as e:
                if DEBUG_MODE:
                    print(f"[Cache] ✗ QImageReader exception: {e}, using fallback...")
            
            # Fallback to standard QPixmap loading (slower, but always works)
            if DEBUG_MODE:
                print(f"[Cache] → Using QPixmap fallback")
            
            pixmap = QPixmap(str(file_path))
            
            if pixmap.isNull():
                # Failed to load - check if it's a known unsupported format
                if extension == '.exr':
                    # Deep EXR already logged above, just return default icon quietly
                    if DEBUG_MODE:
                        print(f"[Cache] ✗ Using default icon for unsupported EXR: {Path(file_path).name}")
                else:
                    if DEBUG_MODE:
                        print(f"[Cache] ✗ QPixmap failed to load: {file_path}")
                return self._get_default_icon(file_path)
            
            if DEBUG_MODE:
                print(f"[Cache] → QPixmap loaded: {pixmap.width()}×{pixmap.height()}")
            
            # Scale to thumbnail size (keep aspect ratio)
            scaled = pixmap.scaled(
                self.thumbnail_size,
                self.thumbnail_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            if DEBUG_MODE:
                print(f"[Cache] ✓ Scaled to: {scaled.width()}×{scaled.height()}")
            
            return scaled
            
        except Exception as e:
            print(f"Error loading image thumbnail {file_path}: {e}")
            return self._get_default_icon(file_path)
    
    def _generate_exr_thumbnail_optimized(self, file_path):
        """
        OPTIMIZED: Fast EXR thumbnail generation for cache
        
        Much faster than full EXR loader used in preview panel because:
        1. Loads at reduced resolution (uses downsampling)
        2. Simplified tone mapping (no exposure control)
        3. Only loads RGB channels (no alpha/AOVs)
        
        Args:
            file_path: Path to EXR file
            
        Returns:
            QPixmap or None
        """
        # Check if this is a deep EXR - skip thumbnail generation and TAG it
        from .preview_panel import is_deep_exr
        if is_deep_exr(file_path):
            if DEBUG_MODE:
                print(f"[EXR-OPT] Deep EXR detected - skipping thumbnail and tagging: {Path(file_path).name}")
            
            # Tag as deep data for fast future checks
            if self.metadata_manager:
                try:
                    tag_id = self.metadata_manager.add_tag("deepdata", category=None, color=None)
                    self.metadata_manager.add_tag_to_file(str(file_path), tag_id)
                    if DEBUG_MODE:
                        print(f"[EXR-OPT] Tagged as 'deepdata' for fast future detection")
                except Exception as tag_error:
                    if DEBUG_MODE:
                        print(f"[EXR-OPT] Warning: Failed to tag deep EXR: {tag_error}")
            
            return None
        
        # Auto-tag color space (before thumbnail generation)
        # This ensures tags are available when preview panel loads the file
        if self.metadata_manager:
            try:
                from .aces_color import auto_tag_file_colorspace
                auto_tag_file_colorspace(file_path, self.metadata_manager)
            except Exception as tag_error:
                if DEBUG_MODE:
                    print(f"[EXR-OPT] Warning: Auto-tagging failed: {tag_error}")
        
        import sys
        import os
        
        # Add external_libs to path
        external_libs = os.path.join(os.path.dirname(__file__), 'external_libs')
        if external_libs not in sys.path:
            sys.path.insert(0, external_libs)
        
        try:
            import numpy as np
            
            # Try OpenEXR library first (fast, native)
            try:
                import OpenEXR
                
                if DEBUG_MODE:
                    print(f"[EXR-OPT] Loading EXR with OpenEXR library: {Path(file_path).name}")
                
                # Open EXR file
                with OpenEXR.File(str(file_path)) as exr_file:
                    # Get header info
                    header = exr_file.header()
                    dw = header['dataWindow']
                    width = dw[1][0] - dw[0][0] + 1
                    height = dw[1][1] - dw[0][1] + 1
                    
                    if DEBUG_MODE:
                        print(f"[EXR-OPT] Original size: {width}x{height}")
                    
                    # List all available channels (DEBUG)
                    channels = exr_file.channels()
                    if DEBUG_MODE:
                        channel_list = list(channels.keys())
                        print(f"[EXR-OPT] Available channels: {', '.join(channel_list)}")
                    
                    # Read RGB channels
                    channels = exr_file.channels()
                    rgb = None
                    
                    # Try multiple naming conventions (same as full loader)
                    # 1. Try standard interleaved RGB or RGBA
                    if "RGB" in channels:
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Using interleaved RGB channel")
                        rgb_data = channels["RGB"].pixels
                        if rgb_data is not None:
                            # If RGBA, drop alpha channel
                            if rgb_data.ndim == 3 and rgb_data.shape[2] >= 3:
                                rgb = rgb_data[:, :, :3]
                            else:
                                rgb = rgb_data
                    elif "RGBA" in channels:
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Using interleaved RGBA channel (dropping alpha)")
                        rgba_data = channels["RGBA"].pixels
                        if rgba_data is not None:
                            rgb = rgba_data[:, :, :3]  # Drop alpha, keep RGB only
                    
                    # 2. Try separate R, G, B channels
                    elif all(c in channels for c in ["R", "G", "B"]):
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Using separate R, G, B channels")
                        r = channels["R"].pixels
                        g = channels["G"].pixels
                        b = channels["B"].pixels
                        if r is not None and g is not None and b is not None:
                            rgb = np.stack([r, g, b], axis=2)
                    
                    # 3. Try Beauty pass (common in render layers)
                    elif all(c in channels for c in ["Beauty.R", "Beauty.G", "Beauty.B"]):
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Using Beauty.R/G/B channels")
                        r = channels["Beauty.R"].pixels
                        g = channels["Beauty.G"].pixels
                        b = channels["Beauty.B"].pixels
                        if r is not None and g is not None and b is not None:
                            rgb = np.stack([r, g, b], axis=2)
                    
                    # 4. Try first layer with .R .G .B (generic multi-layer)
                    if rgb is None:
                        channel_names = list(channels.keys())
                        layer_prefixes = set()
                        for name in channel_names:
                            if '.' in name:
                                prefix = name.rsplit('.', 1)[0]
                                layer_prefixes.add(prefix)
                        
                        # Try each layer prefix
                        for prefix in sorted(layer_prefixes):
                            r_name = f"{prefix}.R"
                            g_name = f"{prefix}.G"
                            b_name = f"{prefix}.B"
                            if all(c in channels for c in [r_name, g_name, b_name]):
                                r = channels[r_name].pixels
                                g = channels[g_name].pixels
                                b = channels[b_name].pixels
                                if r is not None and g is not None and b is not None:
                                    rgb = np.stack([r, g, b], axis=2)
                                    if DEBUG_MODE:
                                        print(f"[EXR-OPT] Using layer: {prefix}")
                                    break
                    
                    # 5. If still no RGB, try single channel (grayscale)
                    if rgb is None:
                        single_channels = ["Y", "Z", "depth", "A", "alpha", "luminance"]
                        for ch_name in single_channels:
                            if ch_name in channels:
                                gray = channels[ch_name].pixels
                                if gray is not None:
                                    # Convert to RGB by repeating channel
                                    if gray.ndim == 2:
                                        rgb = np.stack([gray, gray, gray], axis=2)
                                    else:
                                        # Already 3D, just use it
                                        rgb = gray
                                    if DEBUG_MODE:
                                        print(f"[EXR-OPT] Using single channel: {ch_name}")
                                    break
                    
                    # 6. Last resort: use ANY available channel as grayscale
                    if rgb is None and len(channels) > 0:
                        first_channel_name = list(channels.keys())[0]
                        gray = channels[first_channel_name].pixels
                        
                        if gray is not None:
                            # Convert to RGB by repeating channel
                            if gray.ndim == 2:
                                rgb = np.stack([gray, gray, gray], axis=2)
                            elif gray.ndim == 3 and gray.shape[2] == 1:
                                # Single channel as 3D array
                                rgb = np.concatenate([gray, gray, gray], axis=2)
                            else:
                                rgb = gray
                            if DEBUG_MODE:
                                print(f"[EXR-OPT] Using first available channel: {first_channel_name}")
                    
                    if rgb is None:
                        raise Exception("No usable channels found")
                    
                    # Debug: Show what we loaded
                    if DEBUG_MODE:
                        print(f"[EXR-OPT] → Loaded data: shape={rgb.shape}, dtype={rgb.dtype}")
                    
                    # Check if dtype is numeric (deep EXR returns object arrays)
                    if rgb.dtype == np.object_ or not np.issubdtype(rgb.dtype, np.number):
                        raise Exception(f"Non-numeric dtype: {rgb.dtype} (deep/volumetric EXR not supported)")
                    
                    # Convert float16 to float32 (OpenCV resize needs float32)
                    if rgb.dtype == np.float16:
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Converting float16 to float32 (OpenCV compatibility)")
                        rgb = rgb.astype(np.float32)
                    
                    # OPTIMIZATION 1: Downsample BEFORE tone mapping (much faster!)
                    # Use area interpolation for best quality at reduced size
                    import cv2
                    if width > self.thumbnail_size or height > self.thumbnail_size:
                        scale = min(self.thumbnail_size / width, self.thumbnail_size / height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Downsampling to {new_width}x{new_height} (scale={scale:.3f})")
                        
                        # Use INTER_AREA for downsampling (best quality, fast)
                        rgb = cv2.resize(rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
                        width, height = new_width, new_height
                    else:
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → No downsampling needed (already small)")
                    
                    # Check if we should use ACES color management
                    use_aces = False
                    if self.metadata_manager:
                        try:
                            file_metadata = self.metadata_manager.get_file_metadata(str(file_path))
                            file_tags = file_metadata.get('tags', [])
                            tag_names_lower = [tag['name'].lower() for tag in file_tags]
                            
                            # Check for ACEScg tag (case-insensitive)
                            if "acescg" in tag_names_lower or "srgb(aces)" in tag_names_lower:
                                use_aces = True
                                if DEBUG_MODE:
                                    print(f"[EXR-OPT] → Using ACES view transform for thumbnail")
                        except Exception as tag_error:
                            if DEBUG_MODE:
                                print(f"[EXR-OPT] → Tag check failed: {tag_error}")
                    
                    # Apply tone mapping (ACES or standard)
                    if use_aces:
                        # Use ACES RRT + ODT with -1 stop exposure compensation
                        try:
                            from .aces_color import apply_aces_view_transform
                            
                            if DEBUG_MODE:
                                min_val = np.min(rgb)
                                max_val = np.max(rgb)
                                print(f"[EXR-OPT] → HDR range before ACES: min={min_val:.3f}, max={max_val:.3f}")
                            
                            # Apply ACES with -1 stop compensation (matches preview)
                            rgb_tonemapped = apply_aces_view_transform(rgb, exposure=-1.0)
                            
                            if DEBUG_MODE:
                                print(f"[EXR-OPT] → Applied ACES RRT+ODT (exposure: -1.0)")
                        except Exception as aces_error:
                            if DEBUG_MODE:
                                print(f"[EXR-OPT] → ACES failed, falling back to Reinhard: {aces_error}")
                            # Fallback to Reinhard
                            rgb = np.clip(rgb, 0, None)
                            rgb_tonemapped = rgb / (1.0 + rgb)
                            gamma = 1.0 / 2.2
                            rgb_tonemapped = np.power(rgb_tonemapped, gamma)
                    else:
                        # Standard Reinhard tone mapping for Linear sRGB
                        if DEBUG_MODE:
                            min_val = np.min(rgb)
                            max_val = np.max(rgb)
                            mean_val = np.mean(rgb)
                            print(f"[EXR-OPT] → HDR range before tone mapping: min={min_val:.3f}, max={max_val:.3f}, mean={mean_val:.3f}")
                        
                        rgb = np.clip(rgb, 0, None)  # Clamp negatives
                        rgb_tonemapped = rgb / (1.0 + rgb)  # Reinhard
                        
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Applied Reinhard tone mapping")
                        
                        # Gamma correction (2.2 for sRGB)
                        gamma = 1.0 / 2.2
                        rgb_tonemapped = np.power(rgb_tonemapped, gamma)
                        
                        if DEBUG_MODE:
                            print(f"[EXR-OPT] → Applied gamma correction (2.2)")
                    
                    # Convert to 8-bit
                    rgb_8bit = (rgb_tonemapped * 255).astype(np.uint8)
                    
                    # Create QImage
                    if PYSIDE_VERSION == 6:
                        from PySide6.QtGui import QImage
                    else:
                        from PySide2.QtGui import QImage
                    
                    bytes_per_line = width * 3
                    q_image = QImage(rgb_8bit.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                    q_image = q_image.copy()
                    
                    # Convert to QPixmap
                    pixmap = QPixmap.fromImage(q_image)
                    
                    if DEBUG_MODE:
                        print(f"[EXR-OPT] ✓ Thumbnail generated: {width}x{height}")
                    
                    return pixmap
                    
            except ImportError:
                if DEBUG_MODE:
                    print(f"[EXR-OPT] OpenEXR library not available, trying OpenImageIO...")
                # Fall through to OIIO method
            
            # Fallback: Try OpenImageIO (slower but more compatible)
            try:
                from .widgets import load_oiio_image
                
                if DEBUG_MODE:
                    print(f"[EXR-OPT] Loading EXR with OpenImageIO: {Path(file_path).name}")
                
                # Load with OIIO at reduced size
                pixmap, _, _ = load_oiio_image(file_path, max_size=self.thumbnail_size)
                if pixmap and not pixmap.isNull():
                    if DEBUG_MODE:
                        print(f"[EXR-OPT] ✓ OIIO thumbnail loaded")
                    return pixmap
                else:
                    raise Exception("OIIO loader returned null pixmap")
                    
            except Exception as oiio_error:
                if DEBUG_MODE:
                    print(f"[EXR-OPT] OIIO loading failed: {oiio_error}")
                return None
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"[EXR-OPT] Failed to load EXR: {e}")
            return None
    
    def _generate_hdr_thumbnail_optimized(self, file_path):
        """
        OPTIMIZED: Fast HDR (Radiance RGBE) thumbnail generation for cache
        
        Much faster than full HDR loader because:
        1. Loads at reduced resolution (uses OpenCV downsampling)
        2. Simplified tone mapping (no exposure control)
        
        Args:
            file_path: Path to HDR file
            
        Returns:
            QPixmap or None
        """
        # Auto-tag color space FIRST (before thumbnail generation)
        # This ensures tags are available when preview panel loads the file
        if self.metadata_manager:
            try:
                from .aces_color import auto_tag_file_colorspace
                auto_tag_file_colorspace(file_path, self.metadata_manager)
            except Exception as tag_error:
                if DEBUG_MODE:
                    print(f"[HDR-OPT] Warning: Auto-tagging failed: {tag_error}")
        
        try:
            import cv2
            import numpy as np
            
            if DEBUG_MODE:
                print(f"[HDR-OPT] Loading HDR with OpenCV: {Path(file_path).name}")
            
            # OPTIMIZATION: Use OpenCV imread with REDUCED flag for fast thumbnail
            # This loads the image at 1/2, 1/4, or 1/8 resolution during decode
            imread_flags = self._get_opencv_imread_flags()
            
            if DEBUG_MODE:
                print(f"[HDR-OPT] → Using imread flags: {imread_flags}")
            
            # OpenCV can't handle Unicode paths
            file_path_str = str(file_path)
            has_non_ascii = any(ord(c) > 127 for c in file_path_str)
            
            rgb = None
            if has_non_ascii:
                # Use buffer method for non-ASCII paths
                try:
                    if DEBUG_MODE:
                        print(f"[HDR-OPT] Using buffer method (non-ASCII path)")
                    with open(file_path_str, 'rb') as f:
                        file_bytes = np.frombuffer(f.read(), np.uint8)
                    rgb = cv2.imdecode(file_bytes, imread_flags)
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"[HDR-OPT] Buffer decode failed: {e}")
            else:
                # ASCII-only path
                try:
                    if DEBUG_MODE:
                        print(f"[HDR-OPT] Using imread with flags={imread_flags}")
                    rgb = cv2.imread(file_path_str, imread_flags)
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"[HDR-OPT] OpenCV imread failed: {e}")
            
            if rgb is None:
                raise Exception("OpenCV could not load HDR file")
            
            # Convert BGR to RGB
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            
            if DEBUG_MODE:
                print(f"[HDR-OPT] → Loaded: {rgb.shape[1]}x{rgb.shape[0]}, dtype={rgb.dtype}")
            
            # Additional resize if still too large (imread_flags may not be enough)
            height, width = rgb.shape[:2]
            if width > self.thumbnail_size or height > self.thumbnail_size:
                scale = min(self.thumbnail_size / width, self.thumbnail_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                if DEBUG_MODE:
                    print(f"[HDR-OPT] → Additional resize to {new_width}x{new_height}")
                
                rgb = cv2.resize(rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
                width, height = new_width, new_height
            else:
                if DEBUG_MODE:
                    print(f"[HDR-OPT] → No additional resize needed")
            
            # Simplified tone mapping (Reinhard - fast for thumbnails)
            # HDR files are always Linear sRGB, no ACES needed
            if DEBUG_MODE:
                min_val = np.min(rgb)
                max_val = np.max(rgb)
                mean_val = np.mean(rgb)
                print(f"[HDR-OPT] → HDR range: min={min_val:.3f}, max={max_val:.3f}, mean={mean_val:.3f}")
            
            rgb = np.clip(rgb, 0, None)  # Clamp negatives
            rgb_tonemapped = rgb / (1.0 + rgb)
            
            if DEBUG_MODE:
                print(f"[HDR-OPT] → Applied Reinhard tone mapping")
            
            # Gamma correction (2.2 for sRGB)
            gamma = 1.0 / 2.2
            rgb_tonemapped = np.power(rgb_tonemapped, gamma)
            
            if DEBUG_MODE:
                print(f"[HDR-OPT] → Applied gamma correction (2.2)")
            
            # Convert to 8-bit
            rgb_8bit = (rgb_tonemapped * 255).astype(np.uint8)
            
            # Create QImage
            if PYSIDE_VERSION == 6:
                from PySide6.QtGui import QImage
            else:
                from PySide2.QtGui import QImage
            
            bytes_per_line = width * 3
            q_image = QImage(rgb_8bit.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
            q_image = q_image.copy()
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            if DEBUG_MODE:
                print(f"[HDR-OPT] ✓ Thumbnail generated: {width}x{height}")
            
            return pixmap
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"[HDR-OPT] Failed to load HDR: {e}")
            return None
    
    def _get_default_icon(self, file_path):
        """
        Get attractive default icon based on file type
        Creates gradient-based icon with file extension
        """
        from .utils import get_icon_colors
        
        extension = os.path.splitext(str(file_path))[1].lower()
        
        # Create pixmap
        pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        pixmap.fill(Qt.transparent)
        
        # Get colors from config
        color_primary, color_secondary = get_icon_colors(extension)
        colors = (
            QColor(*color_primary),   # Convert [R,G,B] to QColor
            QColor(*color_secondary)
        )
        
        # Create gradient background
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Gradient from top to bottom
        gradient = QLinearGradient(0, 0, 0, self.thumbnail_size)
        gradient.setColorAt(0, colors[0])
        gradient.setColorAt(1, colors[1])
        
        # Draw rounded rectangle
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        rect = QRect(2, 2, self.thumbnail_size - 4, self.thumbnail_size - 4)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Draw border
        painter.setPen(QPen(QColor(0, 0, 0, 60), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Draw file extension text
        painter.setPen(QColor(255, 255, 255, 230))
        font = QFont(UI_FONT, max(12, self.thumbnail_size // 10), QFont.Bold)
        painter.setFont(font)
        
        text = extension[1:].upper() if len(extension) > 1 else "FILE"
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        
        # Draw file icon (simple document shape)
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
        icon_size = self.thumbnail_size // 4
        icon_x = self.thumbnail_size - icon_size - 8
        icon_y = 8
        painter.drawRect(icon_x, icon_y, icon_size, icon_size)
        
        painter.end()
        
        return pixmap
