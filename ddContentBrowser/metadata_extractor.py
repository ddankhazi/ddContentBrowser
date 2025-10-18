# -*- coding: utf-8 -*-
"""
DD Content Browser - Metadata Extractor
Extracts metadata from various file types for advanced filtering

Author: DankHazid
License: MIT
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Debug flag
DEBUG_MODE = False


class FileMetadata:
    """Stores metadata for a single file"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.metadata = {}
        self.extract_basic_metadata()
    
    def extract_basic_metadata(self):
        """Extract basic metadata available for all files"""
        try:
            stat = self.file_path.stat()
            
            # Basic info
            self.metadata['file_name'] = self.file_path.name
            self.metadata['file_type'] = self.file_path.suffix.lower()
            self.metadata['file_size'] = stat.st_size
            self.metadata['file_size_category'] = self._categorize_size(stat.st_size)
            
            # Dates
            self.metadata['date_created'] = datetime.fromtimestamp(stat.st_ctime)
            self.metadata['date_modified'] = datetime.fromtimestamp(stat.st_mtime)
            
            # Type category
            self.metadata['type_category'] = self._get_type_category()
            
            # Extract format-specific metadata
            if self.metadata['type_category'] == 'image':
                self._extract_image_metadata()
            elif self.metadata['type_category'] == 'maya':
                self._extract_maya_metadata()
            elif self.metadata['type_category'] == '3d_model':
                self._extract_3d_metadata()
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MetadataExtractor] Error extracting metadata for {self.file_path}: {e}")
    
    def _categorize_size(self, size_bytes: int) -> str:
        """Categorize file size"""
        if size_bytes < 1024 * 1024:  # < 1 MB
            return "Tiny (< 1 MB)"
        elif size_bytes < 10 * 1024 * 1024:  # < 10 MB
            return "Small (1-10 MB)"
        elif size_bytes < 100 * 1024 * 1024:  # < 100 MB
            return "Medium (10-100 MB)"
        elif size_bytes < 1024 * 1024 * 1024:  # < 1 GB
            return "Large (100 MB - 1 GB)"
        else:
            return "Huge (> 1 GB)"
    
    def _get_type_category(self) -> str:
        """Get file type category"""
        ext = self.metadata['file_type']
        
        if ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.tga', '.bmp', '.gif']:
            return 'image'
        elif ext in ['.hdr', '.exr']:
            return 'hdr_image'
        elif ext in ['.ma', '.mb']:
            return 'maya'
        elif ext in ['.obj', '.fbx', '.abc', '.usd']:
            return '3d_model'
        elif ext in ['.vdb']:
            return 'volume'
        elif ext in ['.hda']:
            return 'houdini'
        elif ext in ['.mel', '.py', '.txt']:
            return 'script'
        elif ext in ['.pdf']:
            return 'document'
        else:
            return 'other'
    
    def _extract_image_metadata(self):
        """Extract image-specific metadata"""
        try:
            # Try using PIL/Pillow
            from PIL import Image
            import warnings
            
            # Increase decompression bomb limit for large images (e.g., 8K textures)
            # Set to 200 megapixels (default is ~89 MP)
            Image.MAX_IMAGE_PIXELS = 200000000
            
            # Suppress decompression bomb warnings
            warnings.filterwarnings('ignore', category=Image.DecompressionBombWarning)
            
            with Image.open(self.file_path) as img:
                self.metadata['width'] = img.width
                self.metadata['height'] = img.height
                self.metadata['dimensions'] = f"{img.width} x {img.height}"
                
                # Aspect ratio category
                aspect = img.width / img.height if img.height > 0 else 1.0
                if 0.9 <= aspect <= 1.1:
                    self.metadata['aspect_ratio'] = "Square (1:1)"
                elif 1.7 <= aspect <= 1.8:
                    self.metadata['aspect_ratio'] = "16:9"
                elif 1.3 <= aspect <= 1.4:
                    self.metadata['aspect_ratio'] = "4:3"
                elif aspect > 2:
                    self.metadata['aspect_ratio'] = "Panoramic"
                elif aspect < 0.8:
                    self.metadata['aspect_ratio'] = "Portrait"
                else:
                    self.metadata['aspect_ratio'] = "Other"
                
                # Color mode
                self.metadata['color_mode'] = img.mode
                
                # Bit depth (approximate)
                if img.mode in ['1', 'L', 'P']:
                    self.metadata['bit_depth'] = "8-bit"
                elif img.mode in ['RGB', 'RGBA']:
                    self.metadata['bit_depth'] = "8-bit per channel"
                elif img.mode == 'I':
                    self.metadata['bit_depth'] = "32-bit"
                else:
                    self.metadata['bit_depth'] = img.mode
                
                # Try to extract EXIF
                try:
                    exif = img._getexif()
                    if exif:
                        # Camera info
                        if 272 in exif:  # Model
                            self.metadata['camera_model'] = exif[272]
                        if 271 in exif:  # Make
                            self.metadata['camera_make'] = exif[271]
                        
                        # Orientation
                        if 274 in exif:
                            orientation = exif[274]
                            if orientation in [1, 2]:
                                self.metadata['orientation'] = "Landscape"
                            elif orientation in [5, 6, 7, 8]:
                                self.metadata['orientation'] = "Portrait"
                except:
                    pass
                
        except ImportError:
            # PIL not available
            pass
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MetadataExtractor] Error extracting image metadata: {e}")
    
    def _extract_maya_metadata(self):
        """Extract Maya-specific metadata (if possible)"""
        # For now, just basic categorization
        self.metadata['maya_type'] = 'Scene'
        
        # Could potentially parse .ma files (ASCII) for more info
        # But that would be slow, so skip for now
    
    def _extract_3d_metadata(self):
        """Extract 3D model metadata"""
        # Basic categorization
        ext = self.metadata['file_type']
        
        if ext == '.obj':
            self.metadata['3d_format'] = 'Wavefront OBJ'
        elif ext == '.fbx':
            self.metadata['3d_format'] = 'Autodesk FBX'
        elif ext == '.abc':
            self.metadata['3d_format'] = 'Alembic Cache'
        elif ext == '.usd':
            self.metadata['3d_format'] = 'Universal Scene Description'
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata dictionary"""
        return self.metadata


class MetadataCache:
    """Cache for file metadata"""
    
    def __init__(self):
        self.cache = {}  # {file_path_str: FileMetadata}
    
    def get(self, file_path: Path) -> Optional[FileMetadata]:
        """Get metadata from cache"""
        path_str = str(file_path)
        return self.cache.get(path_str)
    
    def add(self, file_path: Path, metadata: FileMetadata):
        """Add metadata to cache"""
        path_str = str(file_path)
        self.cache[path_str] = metadata
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
    
    def get_or_create(self, file_path: Path) -> FileMetadata:
        """Get from cache or create new"""
        cached = self.get(file_path)
        if cached:
            return cached
        
        # Create new
        metadata = FileMetadata(file_path)
        self.add(file_path, metadata)
        return metadata
