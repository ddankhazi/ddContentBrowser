"""
DD Content Browser - Cache Module
Thumbnail caching system with memory and disk storage

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

# Debug flag - set to False to disable verbose logging
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
    
    def __init__(self, memory_cache, disk_cache, thumbnail_size=128):
        super().__init__()
        self.memory_cache = memory_cache
        self.disk_cache = disk_cache
        self.thumbnail_size = thumbnail_size
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
        
    def add_to_queue(self, file_path, file_mtime, priority=False):
        """Add file to generation queue with optional priority"""
        # Check if already in queue
        for item in self.queue:
            if item[0] == file_path:
                return
        
        # Just append to queue - priority is handled by clearing old items
        # Items are added in visible order (top to bottom)
        self.queue.append((file_path, file_mtime))
        self.total_count += 1  # Increment total when adding to queue
    
    def clear_queue(self):
        """Clear generation queue"""
        self.queue.clear()
        self.processed_count = 0
        self.total_count = 0
    
    def stop(self):
        """Stop the generator thread"""
        self.is_running = False
        self.queue.clear()
    
    def run(self):
        """Main thread loop - process queue"""
        while self.is_running:
            if not self.queue:
                self.msleep(50)  # Wait 50ms if queue is empty
                continue
            
            # Get next item from queue (pop from END for correct order)
            file_path, file_mtime = self.queue.pop()  # pop() = pop(-1) = last item
            self.current_file = file_path
            
            # Increment processed count and emit progress
            self.processed_count += 1
            if self.total_count > 0:
                self.progress_update.emit(self.processed_count, self.total_count)
            
            try:
                # Check memory cache first
                cached = self.memory_cache.get(file_path)
                if cached:
                    self.cache_status.emit("cache")
                    self.thumbnail_ready.emit(file_path, cached)
                    continue
                
                # Check disk cache
                cached = self.disk_cache.get(file_path, file_mtime)
                if cached and not cached.isNull():
                    # Valid cached pixmap
                    self.cache_status.emit("cache")
                    self.memory_cache.set(file_path, cached)
                    self.thumbnail_ready.emit(file_path, cached)
                    continue
                
                # Generate new thumbnail
                self.cache_status.emit("generating")
                pixmap = self._generate_thumbnail(file_path)
                
                if pixmap and not pixmap.isNull():
                    # Save to caches
                    self.disk_cache.set(file_path, file_mtime, pixmap)
                    self.memory_cache.set(file_path, pixmap)
                    
                    # Emit signal
                    self.thumbnail_ready.emit(file_path, pixmap)
                # If None returned: no thumbnail generated (normal for 3D files)
                # Delegate will draw placeholder directly - no error needed
                    
            except Exception as e:
                # Only emit error for actual exceptions (image loading failures, etc.)
                self.generation_failed.emit(file_path, str(e))
            
            finally:
                self.current_file = None
    
    def _generate_thumbnail(self, file_path):
        """
        Generate thumbnail from file
        
        For images/PDFs: Load and scale the actual image/first page
        For 3D files: Generate gradient icon (safe mode)
        
        Args:
            file_path: Path to file
            
        Returns:
            QPixmap or None
        """
        extension = os.path.splitext(str(file_path))[1].lower()
        
        # Image files and PDF - load actual image/first page
        if extension in ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.hdr', '.exr', '.tga', '.pdf']:
            return self._generate_image_thumbnail(file_path)
        
        # 3D files and other types - don't generate placeholder in cache
        # The delegate will draw gradient placeholder directly (faster, no scaling)
        return None
        
        # TODO Phase 3: Implement safe playblast generation for Maya files
        # This requires:
        # 1. Main thread execution (Maya API not thread-safe)
        # 2. Proper scene state management
        # 3. User confirmation before opening files
        # 4. Optional: Use mayapy subprocess for isolation
    
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
            
            # Special handling for EXR files - use dedicated EXR loader
            if extension == '.exr':
                # Use the same EXR loading logic as the preview panel
                try:
                    from .widgets import load_hdr_exr_image
                    pixmap, _ = load_hdr_exr_image(file_path, max_size=self.thumbnail_size)
                    if pixmap and not pixmap.isNull():
                        return pixmap
                    else:
                        raise Exception("EXR loader returned null pixmap")
                except Exception as e:
                    print(f"[Cache] EXR loading failed: {e}, trying QPixmap fallback...")
                    # Fall through to QPixmap method below
            
            # Special handling for HDR/TIFF/TGA files - use OpenCV for better format support
            elif extension in ['.hdr', '.tif', '.tiff', '.tga']:
                if DEBUG_MODE:
                    print(f"[THUMB] Loading {extension} file: {Path(file_path).name}")
                try:
                    # Try OpenCV first for 16-bit/32-bit TIFF and HDR/EXR support
                    import cv2
                    import numpy as np
                    
                    # OpenCV can't handle Unicode paths, check for non-ASCII first
                    file_path_str = str(file_path)
                    has_non_ascii = any(ord(c) > 127 for c in file_path_str)
                    
                    img = None
                    if has_non_ascii:
                        # Use buffer method for non-ASCII paths (ékezetes karakterek)
                        try:
                            if DEBUG_MODE:
                                print(f"[THUMB] Using buffer method (non-ASCII path)")
                            with open(file_path_str, 'rb') as f:
                                file_bytes = np.frombuffer(f.read(), np.uint8)
                            img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
                        except Exception as e:
                            if DEBUG_MODE:
                                print(f"[THUMB] Buffer decode failed: {e}")
                    else:
                        # ASCII-only path, use direct imread
                        try:
                            img = cv2.imread(file_path_str, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
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
                    
                    # Normalize bit depth FIRST (before color conversion!)
                    if img.dtype == np.uint16:
                        # 16-bit image - normalize to 8-bit
                        img = (img / 256).astype(np.uint8)
                    elif img.dtype == np.float32 or img.dtype == np.float64:
                        # 32-bit float - normalize and apply simple tone mapping
                        img = np.clip(img, 0, 1)  # Clip to 0-1 range
                        img = (img * 255).astype(np.uint8)
                    
                    # NOW convert to RGB (after normalization)
                    if len(img.shape) == 2:
                        # Grayscale - convert to RGB
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                    elif len(img.shape) == 3 and img.shape[2] == 4:
                        # RGBA - convert to RGB
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                    elif len(img.shape) == 3 and img.shape[2] == 3:
                        # BGR - convert to RGB
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    
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
                            print(f"[THUMB] Converting {pil_image.mode} to RGB...")
                            pil_image = pil_image.convert('RGB')
                        elif pil_image.mode == 'L':
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
                            print(f"[THUMB] ✓ PIL fallback successful: {width}×{height}")
                            return pixmap
                    except Exception as pil_error:
                        print(f"[THUMB] PIL fallback also failed: {pil_error}")
                        # Check if it's an unsupported multi-channel TIFF
                        if "unknown pixel mode" in str(pil_error) or "KeyError" in str(pil_error):
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
                            print(f"[THUMB] QImageReader trying TGA with 2GB limit...")
                        elif extension in ['.tif', '.tiff']:
                            reader.setFormat(b'tiff')
                        
                        image = reader.read()
                        if not image.isNull():
                            pixmap = QPixmap.fromImage(image)
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
                
                if file_size_mb > 50 or extension in ['.jpg', '.jpeg']:
                    # Try OpenCV for large files - better memory handling
                    import cv2
                    import numpy as np
                    
                    # OpenCV can't handle Unicode paths, check for non-ASCII first
                    file_path_str = str(file_path)
                    has_non_ascii = any(ord(c) > 127 for c in file_path_str)
                    
                    img = None
                    if has_non_ascii:
                        # Use buffer method for non-ASCII paths (ékezetes karakterek)
                        try:
                            with open(file_path_str, 'rb') as f:
                                file_bytes = np.frombuffer(f.read(), np.uint8)
                            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                        except Exception as e:
                            print(f"[Cache] Buffer decode failed: {e}")
                    else:
                        # ASCII-only path, use direct imread
                        try:
                            img = cv2.imread(file_path_str, cv2.IMREAD_COLOR)
                        except:
                            pass
                    
                    if img is not None:
                        # Convert BGR to RGB
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        
                        # Calculate thumbnail size
                        h, w = img.shape[:2]
                        scale = min(self.thumbnail_size / w, self.thumbnail_size / h)
                        new_w = int(w * scale)
                        new_h = int(h * scale)
                        
                        # Resize with OpenCV (faster for large images)
                        img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                        
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
            
            # Fallback to standard QPixmap loading
            pixmap = QPixmap(str(file_path))
            
            if pixmap.isNull():
                # Failed to load, use default icon
                print(f"[Cache] QPixmap failed to load: {file_path}")
                return self._get_default_icon(file_path)
            
            # Scale to thumbnail size (keep aspect ratio)
            scaled = pixmap.scaled(
                self.thumbnail_size,
                self.thumbnail_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            return scaled
            
        except Exception as e:
            print(f"Error loading image thumbnail {file_path}: {e}")
            return self._get_default_icon(file_path)
    
    def _get_default_icon(self, file_path):
        """
        Get attractive default icon based on file type
        Creates gradient-based icon with file extension
        """
        extension = os.path.splitext(str(file_path))[1].lower()
        
        # Create pixmap
        pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        pixmap.fill(Qt.transparent)
        
        # Color mapping for different file types (gradient colors)
        color_schemes = {
            '.ma': (QColor(70, 130, 220), QColor(100, 170, 255)),   # Blue gradient
            '.mb': (QColor(50, 100, 180), QColor(80, 140, 220)),    # Dark blue gradient
            '.obj': (QColor(150, 80, 150), QColor(200, 130, 200)),  # Purple gradient
            '.fbx': (QColor(200, 180, 60), QColor(255, 220, 100)),  # Yellow gradient
            '.abc': (QColor(80, 150, 80), QColor(120, 200, 120)),   # Green gradient
            '.usd': (QColor(200, 80, 80), QColor(255, 120, 120)),   # Red gradient
            '.hda': (QColor(180, 100, 60), QColor(220, 140, 100)),  # Orange-brown (Houdini)
            '.blend': (QColor(50, 120, 200), QColor(80, 160, 240)), # Blue gradient (Blender)
            '.sbsar': (QColor(220, 120, 40), QColor(255, 160, 80)), # Orange gradient (Substance)
            '.dae': (QColor(150, 80, 150), QColor(200, 130, 200)), # Purple gradient
            '.stl': (QColor(150, 80, 150), QColor(200, 130, 200)), # Purple gradient
            # Image formats (lighter, image-like colors)
            '.tif': (QColor(100, 180, 220), QColor(140, 210, 255)),  # Light blue (TIFF)
            '.tiff': (QColor(100, 180, 220), QColor(140, 210, 255)), # Light blue (TIFF)
            '.jpg': (QColor(220, 180, 100), QColor(255, 210, 140)),  # Light orange (JPEG)
            '.jpeg': (QColor(220, 180, 100), QColor(255, 210, 140)), # Light orange (JPEG)
            '.png': (QColor(180, 220, 180), QColor(210, 255, 210)),  # Light green (PNG)
            '.hdr': (QColor(255, 200, 100), QColor(255, 230, 150)),  # Golden (HDR)
            '.exr': (QColor(220, 140, 220), QColor(255, 180, 255)),  # Light magenta (EXR)
            '.tga': (QColor(180, 180, 220), QColor(210, 210, 255)),  # Light purple (TGA)
            # PDF files
            '.pdf': (QColor(200, 50, 50), QColor(255, 100, 100)),    # Red gradient (Adobe PDF)
            # Script/text files
            '.py': (QColor(60, 120, 180), QColor(100, 160, 220)),    # Python blue
            '.mel': (QColor(70, 160, 100), QColor(100, 200, 140)),   # Maya green (Maya native)
            '.txt': (QColor(160, 160, 160), QColor(200, 200, 200)),  # Gray (plain text)
        }
        
        colors = color_schemes.get(extension, 
                                   (QColor(100, 100, 100), QColor(150, 150, 150)))
        
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
