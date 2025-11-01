"""
DD Content Browser - Delegates
Custom rendering for thumbnails in grid and list views

Author: ddankhazi
License: MIT
"""

# UI Font - Default value (matches Windows/Maya UI)
UI_FONT = "Segoe UI"

try:
    from PySide6.QtWidgets import QStyledItemDelegate, QStyle
    from PySide6.QtCore import QSize, QRect, Qt
    from PySide6.QtGui import QPainter, QPen, QColor, QFont, QLinearGradient, QBrush, QPixmap
    from PySide6 import QtCore, QtGui, QtWidgets
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import QStyledItemDelegate, QStyle
    from PySide2.QtCore import QSize, QRect, Qt
    from PySide2.QtGui import QPainter, QPen, QColor, QFont, QLinearGradient, QBrush, QPixmap
    from PySide2 import QtCore, QtGui, QtWidgets
    PYSIDE_VERSION = 2


class ThumbnailDelegate(QStyledItemDelegate):
    """Custom delegate for rendering thumbnails in grid/list view"""
    
    def __init__(self, memory_cache, thumbnail_size=128, parent=None):
        super().__init__(parent)
        self.memory_cache = memory_cache
        self.thumbnail_size = thumbnail_size
        self.icon_mode = False  # False = List mode, True = Grid mode
        self.browser = None  # Reference to browser for column widths
        
    def set_browser(self, browser):
        """Set browser reference for accessing column widths"""
        self.browser = browser
    
    def set_view_mode(self, icon_mode):
        """Set view mode (list or grid)"""
        self.icon_mode = icon_mode
        
    def set_thumbnail_size(self, size):
        """Set thumbnail size"""
        self.thumbnail_size = size
    
    def draw_gradient_placeholder(self, painter, rect, extension):
        """Draw attractive gradient placeholder for file type"""
        from .utils import get_icon_colors
        
        # Get colors from config
        color_primary, color_secondary = get_icon_colors(extension)
        colors = (QColor(*color_primary), QColor(*color_secondary))
        
        # Create gradient
        gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        gradient.setColorAt(0, colors[0])
        gradient.setColorAt(1, colors[1])
        
        # Draw rounded rectangle with gradient
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        inner_rect = rect.adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(inner_rect, 8, 8)
        
        # Draw border
        painter.setPen(QPen(QColor(0, 0, 0, 60), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(inner_rect, 8, 8)
        
        # Draw file extension text
        painter.setPen(QColor(255, 255, 255, 230))
        # Font size scales with thumbnail size - smaller for tiny thumbnails
        font_size = max(6, min(14, rect.height() // 8))
        font = QFont(UI_FONT, font_size, QFont.Bold)
        painter.setFont(font)
        
        text = extension[1:].upper() if len(extension) > 1 else "FILE"
        painter.drawText(rect, Qt.AlignCenter, text)
        
    def sizeHint(self, option, index):
        """Return size hint for item"""
        if self.icon_mode:
            # Grid mode - square items with text below
            return QSize(self.thumbnail_size + 20, self.thumbnail_size + 40)
        else:
            # List mode - row height scales directly with thumbnail_size
            # Minimum 16px for very compact view, adds small padding
            row_height = max(16, min(self.thumbnail_size + 4, self.thumbnail_size + 4))
            return QSize(400, row_height)
    
    def paint(self, painter, option, index):
        """Paint the item"""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get asset data
        asset = index.data(Qt.UserRole)
        if not asset:
            super().paint(painter, option, index)
            painter.restore()
            return
        
        # Draw selection/hover background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QStyle.State_MouseOver:
            hover_color = option.palette.highlight().color()
            hover_color.setAlpha(50)
            painter.fillRect(option.rect, hover_color)
        
        if self.icon_mode:
            self._paint_grid_mode(painter, option, asset)
        else:
            self._paint_list_mode(painter, option, asset)
        
        painter.restore()
    
    def _paint_grid_mode(self, painter, option, asset):
        """Paint item in grid mode (icon above text)"""
        rect = option.rect
        
        # Calculate thumbnail position (centered horizontally)
        thumb_size = self.thumbnail_size
        thumb_x = rect.x() + (rect.width() - thumb_size) // 2
        thumb_y = rect.y() + 5
        thumb_rect = QRect(thumb_x, thumb_y, thumb_size, thumb_size)
        
        # Special handling for folders
        if asset.is_folder:
            # Draw folder icon (gray/neutral to not distract from files)
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.setBrush(QColor(160, 160, 160))
            
            # Draw main folder body
            folder_body = QRect(thumb_x + 5, thumb_y + 10, thumb_size - 10, thumb_size - 15)
            painter.drawRoundedRect(folder_body, 4, 4)
            
            # Draw folder tab
            tab_width = thumb_size // 3
            tab_rect = QRect(thumb_x + 5, thumb_y + 5, tab_width, 8)
            painter.drawRoundedRect(tab_rect, 2, 2)
        else:
            # Check if thumbnails are enabled
            thumbnails_enabled = True
            if self.browser and hasattr(self.browser, 'thumbnails_enabled_checkbox'):
                thumbnails_enabled = self.browser.thumbnails_enabled_checkbox.isChecked()
            
            # Get thumbnail from cache only if enabled
            file_path_key = str(asset.file_path)
            thumbnail = self.memory_cache.get(file_path_key) if thumbnails_enabled else None
            
            if thumbnail and not thumbnail.isNull():
                # Draw thumbnail
                scaled = thumbnail.scaled(thumb_size, thumb_size, 
                                         Qt.KeepAspectRatio, 
                                         Qt.SmoothTransformation)
                # Center the scaled image
                offset_x = (thumb_size - scaled.width()) // 2
                offset_y = (thumb_size - scaled.height()) // 2
                painter.drawPixmap(thumb_x + offset_x, thumb_y + offset_y, scaled)
            else:
                # Draw gradient placeholder (no scaling, always sharp!)
                self.draw_gradient_placeholder(painter, thumb_rect, asset.extension)
        
        # Draw file name below thumbnail
        text_rect = QRect(rect.x(), thumb_y + thumb_size + 5, 
                                rect.width(), rect.height() - thumb_size - 10)
        
        painter.setPen(option.palette.text().color() if not (option.state & QStyle.State_Selected)
                      else option.palette.highlightedText().color())
        
        # Fixed font size for grid mode file names
        painter.setFont(QFont(UI_FONT, 9))
        
        # Elide text if too long
        metrics = painter.fontMetrics()
        elided_text = metrics.elidedText(asset.name, Qt.ElideMiddle, text_rect.width() - 10)
        painter.drawText(text_rect, Qt.AlignTop | Qt.AlignHCenter, elided_text)
    
    def _paint_list_mode(self, painter, option, asset):
        """Paint item in list mode with columns (Name, Type, Size, Date)"""
        rect = option.rect
        
        # Get column widths from browser's header splitter if available
        if self.browser and hasattr(self.browser, 'header_splitter'):
            sizes = self.browser.header_splitter.sizes()
            total = sum(sizes)
            if total > 0:
                # Calculate proportional widths
                total_width = rect.width()
                name_width = int((sizes[0] / total) * total_width)
                type_width = int((sizes[1] / total) * total_width)
                size_width = int((sizes[2] / total) * total_width)
                date_width = int((sizes[3] / total) * total_width)
            else:
                # Fallback to default percentages
                total_width = rect.width()
                name_width = int(total_width * 0.40)
                type_width = int(total_width * 0.20)
                size_width = int(total_width * 0.20)
                date_width = int(total_width * 0.20)
        else:
            # Default column widths (40%, 20%, 20%, 20%)
            total_width = rect.width()
            name_width = int(total_width * 0.40)
            type_width = int(total_width * 0.20)
            size_width = int(total_width * 0.20)
            date_width = int(total_width * 0.20)
        
        # Column X positions
        name_x = rect.x() + 4
        type_x = name_x + name_width
        size_x = type_x + type_width
        date_x = size_x + size_width
        
        # Text color
        text_color = option.palette.text().color() if not (option.state & QStyle.State_Selected) \
                     else option.palette.highlightedText().color()
        painter.setPen(text_color)
        
        # ===== COLUMN 1: NAME (with thumbnail) =====
        # Thumbnail size scales with row height but has reasonable limits
        thumb_size = max(16, min(rect.height() - 4, self.thumbnail_size))
        thumb_x = name_x
        thumb_y = rect.y() + (rect.height() - thumb_size) // 2
        thumb_rect = QRect(thumb_x, thumb_y, thumb_size, thumb_size)
        
        # Special handling for folders
        if asset.is_folder:
            # Draw folder icon - scale with thumb_size
            painter.setPen(QPen(QColor(100, 100, 100), max(1, thumb_size // 28)))
            painter.setBrush(QColor(160, 160, 160))
            folder_body = QRect(thumb_x + 2, thumb_y + thumb_size // 4, 
                               thumb_size - 4, thumb_size - thumb_size // 4 - 2)
            painter.drawRoundedRect(folder_body, 2, 2)
            tab_rect = QRect(thumb_x + 2, thumb_y + thumb_size // 7, 
                            thumb_size // 3, thumb_size // 7)
            painter.drawRoundedRect(tab_rect, 1, 1)
        else:
            # Check if thumbnails are enabled
            thumbnails_enabled = True
            if self.browser and hasattr(self.browser, 'thumbnails_enabled_checkbox'):
                thumbnails_enabled = self.browser.thumbnails_enabled_checkbox.isChecked()
            
            # Get thumbnail from cache only if enabled
            thumbnail = self.memory_cache.get(str(asset.file_path)) if thumbnails_enabled else None
            if thumbnail and not thumbnail.isNull():
                scaled = thumbnail.scaled(thumb_size, thumb_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # Center the scaled image within thumb_rect (both horizontally and vertically)
                offset_x = (thumb_size - scaled.width()) // 2
                offset_y = (thumb_size - scaled.height()) // 2
                painter.drawPixmap(thumb_x + offset_x, thumb_y + offset_y, scaled)
            else:
                self.draw_gradient_placeholder(painter, thumb_rect, asset.extension)
        
        # Draw file name next to thumbnail
        painter.setPen(text_color)
        text_x = thumb_x + thumb_size + 6
        name_rect = QRect(text_x, rect.y(), name_width - thumb_size - 10, rect.height())
        # Fixed font size for file name (even in compact 16px rows)
        painter.setFont(QFont(UI_FONT, 9))
        painter.drawText(name_rect, Qt.AlignVCenter, asset.name)
        
        # ===== COLUMN 2: TYPE =====
        type_rect = QRect(type_x + 5, rect.y(), type_width - 10, rect.height())
        # Fixed font size for type column
        painter.setFont(QFont(UI_FONT, 8))
        if asset.is_folder:
            painter.drawText(type_rect, Qt.AlignVCenter, "Folder")
        elif asset.extension:
            painter.drawText(type_rect, Qt.AlignVCenter, asset.extension.upper()[1:])  # Remove dot
        
        # ===== COLUMN 3: SIZE =====
        size_rect = QRect(size_x + 5, rect.y(), size_width - 10, rect.height())
        painter.setFont(QFont(UI_FONT, 8))
        painter.drawText(size_rect, Qt.AlignVCenter, asset.get_size_string())
        
        # ===== COLUMN 4: DATE =====
        date_rect = QRect(date_x + 5, rect.y(), date_width - 10, rect.height())
        painter.setFont(QFont(UI_FONT, 8))
        painter.drawText(date_rect, Qt.AlignVCenter, asset.get_modified_string())

