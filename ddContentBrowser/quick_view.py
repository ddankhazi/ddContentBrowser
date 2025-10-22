# -*- coding: utf-8 -*-
"""
DD Content Browser - Quick View System
macOS Quick Look-style floating preview window

Author: ddankhazi
License: MIT
"""

from pathlib import Path

try:
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QWidget, QStackedWidget, 
                                   QGraphicsView, QGraphicsScene, QSizeGrip)
    from PySide6.QtCore import Qt, QPoint, Signal
    from PySide6.QtGui import QPixmap
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QWidget, QStackedWidget, 
                                   QGraphicsView, QGraphicsScene, QSizeGrip)
    from PySide2.QtCore import Qt, QPoint, Signal
    from PySide2.QtGui import QPixmap
    PYSIDE_VERSION = 2

# Import HDR/EXR and PDF loading from widgets
from .widgets import load_hdr_exr_image, load_pdf_page

# UI Font - will be set by browser at runtime
UI_FONT = "Segoe UI"

# Debug mode
DEBUG_MODE = True


class QuickViewWindow(QDialog):
    """
    macOS-style Quick Look window
    
    Features:
    - Non-modal floating window
    - Always on top
    - Draggable titlebar
    - Space/ESC to close
    - Pin functionality to lock preview
    - Multi-file support (single view / grid view)
    """
    
    closed = Signal()  # Emitted when window closes
    
    def __init__(self, browser, parent=None):
        """Initialize Quick View window"""
        if parent is None:
            parent = browser.parent()
        
        super().__init__(parent)
        self.browser = browser
        self.current_assets = []
        self.pinned = False
        self.pinned_assets = []
        
        # Track current file to avoid unnecessary re-fitting
        self.current_file_path = None
        
        # Layout mode for multi-file grid ('3:2', '2:3', 'fit', 'grid')
        self.layout_mode = 'grid'  # Default: grid
        
        # PDF state tracking (simple: just current page and total pages)
        self.is_pdf = False
        self.pdf_path = None
        self.pdf_current_page = 0
        self.pdf_page_count = 0
        self.pdf_nav_items = []  # Store PDF navigation button items (QGraphicsItem)
        
        # Grid mode PDF state: {cell_index: {'path': str, 'page': int, 'page_count': int, 'pixmap_item': item}}
        self.grid_pdf_states = {}
        
        # Resize and drag tracking
        self.resize_dir = None
        self.drag_position = None
        
        # Canvas zoom/pan tracking
        self.zoom_factor = 1.0
        self.is_panning = False
        self.pan_start_pos = None
        
        # Always on top state (can be toggled via context menu)
        self.always_on_top = True
        
        # Setup window flags (non-modal, always on top, frameless)
        self.setWindowFlags(
            Qt.Tool | 
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint
        )
        self.setModal(False)
        
        # Don't steal focus from browser (critical for keyboard navigation)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Enable mouse tracking for resize cursors
        self.setMouseTracking(True)
        
        # Set minimum size
        self.setMinimumSize(300, 200)
        
        # Default size
        self.resize(800, 600)
        
        # Setup UI
        self.setup_ui()
        
        # Apply styling
        self.apply_styling()
        
        # Restore saved state (size/position)
        self.restore_state()
        
        # if DEBUG_MODE:
        #     print("[QuickView] Initialized")
    
    def setup_ui(self):
        """Setup Quick View UI - minimalist canvas-only design"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Preview container (will hold single preview or grid)
        self.preview_container = QStackedWidget()
        main_layout.addWidget(self.preview_container)
        
        # Single file preview widget
        self.single_preview = self.create_single_preview()
        self.preview_container.addWidget(self.single_preview)
        
        # TODO: Grid preview widget (Phase 4)
        # No titlebar, no status bar - just canvas!
    
    def create_single_preview(self):
        """Create single file preview widget - minimalist canvas"""
        preview_widget = QWidget()
        layout = QVBoxLayout(preview_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Graphics view for image display
        self.graphics_view = QGraphicsView()
        self.graphics_view.setStyleSheet("QGraphicsView { background-color: #181818; border: none; }")
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setTransformationAnchor(QGraphicsView.NoAnchor)  # Don't auto-adjust transform
        self.graphics_view.setResizeAnchor(QGraphicsView.NoAnchor)  # Don't auto-adjust on resize
        self.graphics_view.setDragMode(QGraphicsView.NoDrag)  # We'll handle drag ourselves
        self.graphics_view.setInteractive(True)  # Allow interaction
        
        # Install event filter to catch mouse events on graphics view
        self.graphics_view.viewport().installEventFilter(self)
        self.graphics_view.viewport().setMouseTracking(True)
        
        # Install event filter on graphics_view itself to catch arrow key events
        self.graphics_view.installEventFilter(self)
        
        # Create scene
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.pixmap_item = None
        
        layout.addWidget(self.graphics_view)
        
        # No global info label - will be per-image in scene later
        
        return preview_widget
    
    def apply_styling(self):
        """Apply minimal dark theme - thinner border"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                border: 3px solid #2a2a2a;
            }
        """)
    
    def show_preview(self, assets):
        """
        Show preview for selected assets
        
        Args:
            assets: List of AssetItem objects
        """
        if self.pinned:
            # if DEBUG_MODE:
            #     print("[QuickView] Ignoring selection change (pinned)")
            return  # Ignore if pinned
        
        if not assets:
            # if DEBUG_MODE:
            #     print("[QuickView] No assets to preview")
            return
        
        # if DEBUG_MODE:
        #     asset_names = [Path(a.file_path).name for a in assets]
        #     print(f"[QuickView] show_preview called with {len(assets)} asset(s): {asset_names}")
        
        self.current_assets = assets
        
        # Single file or multiple?
        if len(assets) == 1:
            # if DEBUG_MODE:
            #     print(f"[QuickView] Calling show_single_file for: {Path(assets[0].file_path).name}")
            self.show_single_file(assets[0])
            self.preview_container.setCurrentWidget(self.single_preview)
        else:
            # Multi-file grid (Phase 4)
            self.show_multi_file_grid(assets)
            self.preview_container.setCurrentWidget(self.single_preview)  # Use same canvas
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Finished showing preview for {len(assets)} asset(s)")

    
    # Pin functionality removed - will be in right-click context menu later
    
    # ========== Event Filter (for graphics_view viewport and graphics_view itself) ==========
    
    def eventFilter(self, obj, event):
        """Filter events from graphics_view viewport to enable window resize/drag/zoom, and from graphics_view for arrow keys"""
        # Handle keyboard events from graphics_view (arrow keys)
        if obj == self.graphics_view:
            try:
                from PySide6.QtCore import QEvent
            except ImportError:
                from PySide2.QtCore import QEvent
            
            if event.type() == QEvent.KeyPress:
                # Forward to keyPressEvent
                self.keyPressEvent(event)
                return True  # Event handled
        
        # Handle mouse/wheel events from viewport
        if obj == self.graphics_view.viewport():
            try:
                from PySide6.QtCore import QEvent
                try:
                    from PySide6.QtWidgets import QApplication
                except:
                    from PySide6.QtGui import QApplication
            except ImportError:
                from PySide2.QtCore import QEvent
                from PySide2.QtWidgets import QApplication
            
            # Handle Wheel event (Scroll zoom - no modifier needed)
            if event.type() == QEvent.Wheel:
                # Scroll = Zoom (like PreviewPanel)
                delta = event.angleDelta().y()
                zoom_in = delta > 0
                
                # Get position (PySide6 uses position(), PySide2 uses pos())
                try:
                    wheel_pos = event.position().toPoint()  # PySide6
                except AttributeError:
                    wheel_pos = event.pos()  # PySide2
                
                self.zoom_canvas(zoom_in, wheel_pos)
                # Consume event to prevent browser scrolling during zoom
                return True
            
            # Only process mouse events (they have pos())
            # Block double-click events to prevent them interfering with rapid clicking
            if event.type() not in [QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonRelease]:
                if event.type() == QEvent.MouseButtonDblClick:
                    # Treat double-click as single click for PDF navigation
                    # Don't return, let it fall through to MouseButtonPress handling below
                    pass
                else:
                    return super().eventFilter(obj, event)
            
            # Map viewport position to dialog position
            dialog_pos = self.graphics_view.mapTo(self, event.pos())
            
            if event.type() == QEvent.MouseButtonPress or event.type() == QEvent.MouseButtonDblClick:
                if event.button() == Qt.LeftButton:
                    # Check if clicked on PDF navigation buttons (single or grid mode)
                    if (self.is_pdf or self.grid_pdf_states) and self.pdf_nav_items:
                        # Map click position to scene
                        scene_pos = self.graphics_view.mapToScene(event.pos())
                        
                        # Check which item was clicked
                        clicked_item = self.graphics_scene.itemAt(scene_pos, self.graphics_view.transform())
                        
                        if clicked_item and hasattr(clicked_item, 'data'):
                            button_type = clicked_item.data(0)
                            
                            # Single PDF navigation
                            if button_type == "pdf_prev":
                                self.pdf_navigate_page(-1)
                                return True  # Consume event
                            elif button_type == "pdf_next":
                                self.pdf_navigate_page(1)
                                return True  # Consume event
                            
                            # Grid PDF navigation
                            elif button_type and button_type.startswith("grid_pdf_"):
                                parts = button_type.split("_")
                                if len(parts) >= 4:
                                    cell_index = int(parts[3])
                                    if "prev" in button_type:
                                        self.pdf_navigate_grid_page(cell_index, -1)
                                        return True
                                    elif "next" in button_type:
                                        self.pdf_navigate_grid_page(cell_index, 1)
                                        return True
                    
                    # Check if near edge (resize) or in center (pan)
                    self.resize_dir = self.get_resize_direction(dialog_pos)
                    
                    if self.resize_dir:
                        # Edge/corner resize
                        return True  # Consume event
                    else:
                        # Center area - start panning (use GLOBAL position like PreviewPanel)
                        self.is_panning = True
                        try:
                            self.pan_start_pos = event.globalPosition().toPoint()
                        except AttributeError:
                            self.pan_start_pos = event.globalPos()
                        self.graphics_view.setCursor(Qt.ClosedHandCursor)
                        return True
                        
                elif event.button() == Qt.MiddleButton:
                    # Middle button drag to move window
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    self.setCursor(Qt.SizeAllCursor)
                    return True  # Consume event
            
            elif event.type() == QEvent.MouseMove:
                # Check if hovering over PDF (for navigation overlay auto-show)
                if self.pdf_nav_items:
                    scene_pos = self.graphics_view.mapToScene(event.pos())
                    
                    # Hover margin (extend hit area slightly to avoid flickering)
                    hover_margin = 20
                    
                    # Check if hovering over any pixmap (single or grid)
                    hovered_cell_index = None
                    if self.pixmap_item and self.is_pdf:
                        # Single PDF mode (with margin)
                        pdf_rect = self.pixmap_item.sceneBoundingRect().adjusted(-hover_margin, -hover_margin, hover_margin, hover_margin)
                        if pdf_rect.contains(scene_pos):
                            hovered_cell_index = -1  # Special marker for single mode
                    elif self.grid_pdf_states:
                        # Grid mode - find which PDF cell is hovered (with margin)
                        for cell_idx, state in self.grid_pdf_states.items():
                            if 'pixmap_item' in state and state['pixmap_item']:
                                cell_rect = state['pixmap_item'].sceneBoundingRect().adjusted(-hover_margin, -hover_margin, hover_margin, hover_margin)
                                if cell_rect.contains(scene_pos):
                                    hovered_cell_index = cell_idx
                                    break
                    
                    # Show/hide navigation overlays based on hover
                    for item in self.pdf_nav_items:
                        item_tag = item.data(0)
                        if hovered_cell_index == -1:
                            # Single PDF mode - show all PDF nav items
                            item.setVisible(True)
                        elif hovered_cell_index is not None:
                            # Grid mode - only show items for hovered cell
                            if f"_{hovered_cell_index}" in str(item_tag):
                                item.setVisible(True)
                            else:
                                item.setVisible(False)
                        else:
                            # Not hovering over any PDF
                            item.setVisible(False)
                
                if event.buttons() == Qt.LeftButton and self.resize_dir:
                    # Resizing window
                    self.perform_resize(event.globalPos())
                    return True
                
                elif event.buttons() == Qt.LeftButton and self.is_panning:
                    # Panning canvas
                    try:
                        current_pos = event.globalPosition().toPoint()
                    except AttributeError:
                        current_pos = event.globalPos()
                    
                    # Calculate delta in screen space
                    delta = current_pos - self.pan_start_pos
                    self.pan_start_pos = current_pos
                    
                    # Try scrollbars first (when zoomed or grid is larger than view)
                    h_bar = self.graphics_view.horizontalScrollBar()
                    v_bar = self.graphics_view.verticalScrollBar()
                    
                    has_h_range = h_bar.maximum() > h_bar.minimum()
                    has_v_range = v_bar.maximum() > v_bar.minimum()
                    
                    if has_h_range or has_v_range:
                        # Use scrollbars when available
                        if has_h_range:
                            h_bar.setValue(h_bar.value() - delta.x())
                        if has_v_range:
                            v_bar.setValue(v_bar.value() - delta.y())
                    else:
                        # No scrollbars - move items directly (single or multi-file mode)
                        scene_delta = self.graphics_view.mapToScene(delta.x(), delta.y()) - self.graphics_view.mapToScene(0, 0)
                        
                        if self.pixmap_item:
                            # Single file mode - move the single pixmap
                            current_item_pos = self.pixmap_item.pos()
                            self.pixmap_item.setPos(current_item_pos + scene_delta)
                        else:
                            # Multi-file mode - move all items
                            for item in self.graphics_scene.items():
                                if hasattr(item, 'setPos'):  # QGraphicsPixmapItem has setPos
                                    current_pos = item.pos()
                                    item.setPos(current_pos + scene_delta)
                    
                    return True
                    
                elif event.buttons() == Qt.MiddleButton and self.drag_position:
                    # Moving window
                    self.move(event.globalPos() - self.drag_position)
                    return True
                    
                else:
                    # Update cursor based on position
                    direction = self.get_resize_direction(dialog_pos)
                    if direction != getattr(self, '_last_direction', None):
                        self.update_cursor(direction)
                        self._last_direction = direction
            
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self.resize_dir:
                    self.resize_dir = None
                    self.setCursor(Qt.ArrowCursor)
                    self.save_state()
                    return True
                
                elif event.button() == Qt.LeftButton and self.is_panning:
                    self.is_panning = False
                    self.pan_start_pos = None
                    self.graphics_view.setCursor(Qt.ArrowCursor)
                    return True
                    
                elif event.button() == Qt.MiddleButton and self.drag_position:
                    self.drag_position = None
                    self.setCursor(Qt.ArrowCursor)
                    self.save_state()
                    return True
        
        return super().eventFilter(obj, event)
    
    # ========== Window Resize (8-direction) & Middle-button Move ==========
    
    def mousePressEvent(self, event):
        """Start resize from edges/corners OR move with middle button"""
        if event.button() == Qt.LeftButton:
            self.resize_dir = self.get_resize_direction(event.pos())
            if self.resize_dir:
                # if DEBUG_MODE:
                #     print(f"[QuickView] Starting resize: {self.resize_dir}")
                event.accept()
                return
        elif event.button() == Qt.MiddleButton:
            # Middle button drag to move window
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(Qt.SizeAllCursor)
            # if DEBUG_MODE:
            #     print(f"[QuickView] Starting window drag")
            event.accept()
            return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle resize, window drag, and cursor updates"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'resize_dir') and self.resize_dir:
            # Left button: resize
            self.perform_resize(event.globalPos())
            event.accept()
        elif event.buttons() == Qt.MiddleButton and hasattr(self, 'drag_position') and self.drag_position:
            # Middle button: move window
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            # No button pressed - update cursor based on position
            direction = self.get_resize_direction(event.pos())
            if direction != getattr(self, '_last_direction', None):
                self.update_cursor(direction)
                self._last_direction = direction
    
    def mouseReleaseEvent(self, event):
        """End resize or drag and save state"""
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'resize_dir'):
                self.resize_dir = None
            self.setCursor(Qt.ArrowCursor)
            self.save_state()
        elif event.button() == Qt.MiddleButton:
            if hasattr(self, 'drag_position'):
                self.drag_position = None
            self.setCursor(Qt.ArrowCursor)
            self.save_state()
    
    def get_resize_direction(self, pos):
        """Detect resize direction from mouse position"""
        rect = self.rect()
        x, y = pos.x(), pos.y()
        w, h = rect.width(), rect.height()
        margin = 15  # Wider resize handle margin for easier grabbing
        
        # Corners (priority)
        if x <= margin and y <= margin:
            return 'top-left'
        elif x >= w - margin and y <= margin:
            return 'top-right'
        elif x <= margin and y >= h - margin:
            return 'bottom-left'
        elif x >= w - margin and y >= h - margin:
            return 'bottom-right'
        
        # Edges
        elif x <= margin:
            return 'left'
        elif x >= w - margin:
            return 'right'
        elif y <= margin:
            return 'top'
        elif y >= h - margin:
            return 'bottom'
        
        return None
    
    def update_cursor(self, direction):
        """Update cursor based on resize direction"""
        if direction in ['top', 'bottom']:
            self.setCursor(Qt.SizeVerCursor)
        elif direction in ['left', 'right']:
            self.setCursor(Qt.SizeHorCursor)
        elif direction in ['top-left', 'bottom-right']:
            self.setCursor(Qt.SizeFDiagCursor)
        elif direction in ['top-right', 'bottom-left']:
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    def perform_resize(self, global_pos):
        """Resize window based on direction"""
        rect = self.geometry()
        min_w, min_h = 300, 200
        
        if 'right' in self.resize_dir:
            new_w = max(min_w, global_pos.x() - rect.x())
            rect.setWidth(new_w)
        
        if 'left' in self.resize_dir:
            delta = rect.x() - global_pos.x()
            new_w = max(min_w, rect.width() + delta)
            if new_w >= min_w:
                rect.setX(global_pos.x())
                rect.setWidth(new_w)
        
        if 'bottom' in self.resize_dir:
            new_h = max(min_h, global_pos.y() - rect.y())
            rect.setHeight(new_h)
        
        if 'top' in self.resize_dir:
            delta = rect.y() - global_pos.y()
            new_h = max(min_h, rect.height() + delta)
            if new_h >= min_h:
                rect.setY(global_pos.y())
                rect.setHeight(new_h)
        
        self.setGeometry(rect)
    
    def zoom_canvas(self, zoom_in, mouse_pos):
        """Zoom canvas in/out centered on mouse cursor (like PreviewPanel)"""
        # Zoom factor increment
        zoom_step = 1.15
        
        # Get the mouse position in scene coordinates BEFORE zoom
        old_scene_pos = self.graphics_view.mapToScene(mouse_pos)
        
        # Calculate new zoom factor
        if zoom_in:
            self.zoom_factor *= zoom_step
        else:
            self.zoom_factor /= zoom_step
        
        # Clamp zoom (10% to 1000%)
        self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))
        
        # Apply zoom transform
        self.graphics_view.scale(
            zoom_step if zoom_in else 1/zoom_step,
            zoom_step if zoom_in else 1/zoom_step
        )
        
        # Get the mouse position in scene coordinates AFTER zoom
        new_scene_pos = self.graphics_view.mapToScene(mouse_pos)
        
        # Calculate offset to keep the point under mouse cursor in place
        delta = new_scene_pos - old_scene_pos
        
        # Translate view to compensate (keep zoom centered on cursor)
        self.graphics_view.translate(delta.x(), delta.y())
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Zoom: {self.zoom_factor:.2f}x")
    
    def fit_to_view(self):
        """Fit content to view - reset zoom and pan (F key)"""
        # Reset zoom factor
        self.zoom_factor = 1.0
        
        # Reset transform
        self.graphics_view.resetTransform()
        
        # Check if single image or multi-grid
        if self.pixmap_item:
            # Single image mode - fit to viewport
            viewport_rect = self.graphics_view.viewport().rect()
            pixmap = self.pixmap_item.pixmap()
            
            if not pixmap.isNull():
                pixmap_width = pixmap.width()
                pixmap_height = pixmap.height()
                
                # Calculate scale to fit
                scale_x = viewport_rect.width() / pixmap_width if pixmap_width > 0 else 1.0
                scale_y = viewport_rect.height() / pixmap_height if pixmap_height > 0 else 1.0
                fit_scale = min(scale_x, scale_y)
                
                # Apply scale
                self.graphics_view.scale(fit_scale, fit_scale)
                
                # Store fit scale for PDF navigation
                self.pdf_fit_scale = fit_scale
                
                # Center the image
                self.graphics_view.centerOn(self.pixmap_item)
        else:
            # Multi-grid mode - fit grid to viewport
            scene_rect = self.graphics_scene.sceneRect()
            
            # Get all items to calculate actual content bounds (not expanded scene rect)
            items = self.graphics_scene.items()
            if items:
                # Calculate bounding rect of all items
                content_rect = items[0].sceneBoundingRect()
                for item in items[1:]:
                    content_rect = content_rect.united(item.sceneBoundingRect())
                
                viewport_rect = self.graphics_view.viewport().rect()
                
                # Calculate scale to fit content
                scale_x = viewport_rect.width() / content_rect.width() if content_rect.width() > 0 else 1.0
                scale_y = viewport_rect.height() / content_rect.height() if content_rect.height() > 0 else 1.0
                fit_scale = min(scale_x, scale_y)
                
                # Apply scale
                self.graphics_view.scale(fit_scale, fit_scale)
                
                # Store fit scale for PDF navigation
                self.pdf_fit_scale = fit_scale
                
                # Center the grid
                self.graphics_view.centerOn(content_rect.center())
        
        # if DEBUG_MODE:
        #     print("[QuickView] Fit to view")
    
    # ========== Window Events (for state persistence) ==========
    
    def showEvent(self, event):
        """Handle first show - ensure proper viewport sizing"""
        super().showEvent(event)
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] showEvent - pixmap_item exists: {self.pixmap_item is not None}")
        
        # On first show, re-fit content after window is fully shown
        # This handles the case where viewport size wasn't final during initial load
        if not hasattr(self, '_first_show_done'):
            self._first_show_done = True
            
            # Defer fit slightly to ensure viewport geometry is final
            try:
                from PySide6.QtCore import QTimer
            except ImportError:
                from PySide2.QtCore import QTimer
            
            # Re-fit regardless (either pixmap or grid)
            QTimer.singleShot(10, self._refit_on_first_show)
            
            # if DEBUG_MODE:
            #     print("[QuickView] First show - scheduling refit")
    
    def _refit_on_first_show(self):
        """Re-fit content on first show (viewport size is now correct)"""
        # if DEBUG_MODE:
        #     viewport_rect = self.graphics_view.viewport().rect()
        #     print(f"[QuickView] _refit_on_first_show - viewport: {viewport_rect.width()}x{viewport_rect.height()}, pixmap_item: {self.pixmap_item is not None}")
        
        if self.pixmap_item is not None:
            # Re-calculate fit with correct viewport size
            viewport_rect = self.graphics_view.viewport().rect()
            pixmap = self.pixmap_item.pixmap()
            
            if not pixmap.isNull():
                pixmap_width = pixmap.width()
                pixmap_height = pixmap.height()
                
                # Clear transforms
                self.graphics_view.resetTransform()
                
                # Calculate scale to fit
                scale_x = viewport_rect.width() / pixmap_width if pixmap_width > 0 else 1.0
                scale_y = viewport_rect.height() / pixmap_height if pixmap_height > 0 else 1.0
                fit_scale = min(scale_x, scale_y)
                
                # Apply scale
                self.graphics_view.scale(fit_scale, fit_scale)
                
                # Center the image
                self.graphics_view.centerOn(self.pixmap_item)
                
                self.zoom_factor = 1.0
                
                # If PDF, recreate navigation overlay with correct scale
                if self.is_pdf and self.pdf_page_count > 1:
                    self.pdf_fit_scale = fit_scale  # Update fit scale
                    pixmap_rect = pixmap.rect()
                    self.create_pdf_navigation_overlay(pixmap_rect)
                
                # if DEBUG_MODE:
                #     print(f"[QuickView] Re-fitted on first show (scale: {fit_scale:.2f})")
        else:
            # No pixmap - might be multi-grid, try generic fit
            self.fit_to_view()
            
            # If grid has PDFs, recreate their navigation overlays with correct scale
            if self.grid_pdf_states:
                for cell_index, pdf_state in self.grid_pdf_states.items():
                    # Remove old navigation items for this cell
                    items_to_remove = [item for item in self.pdf_nav_items 
                                      if hasattr(item, 'data') and item.data(0) 
                                      and str(item.data(0)).startswith(f"grid_pdf_") 
                                      and str(item.data(0)).endswith(f"_{cell_index}")]
                    for item in items_to_remove:
                        self.graphics_scene.removeItem(item)
                        self.pdf_nav_items.remove(item)
                    
                    # Recreate navigation overlay for this cell
                    self.create_pdf_grid_navigation(
                        cell_index, 
                        pdf_state['cell_x'] + pdf_state['x_offset'], 
                        pdf_state['cell_y'] + pdf_state['y_offset'],
                        pdf_state['scaled_width'], 
                        pdf_state['scaled_height']
                    )
            
            # if DEBUG_MODE:
            #     print("[QuickView] No pixmap, called fit_to_view()")
    
    def resizeEvent(self, event):
        """Save state when window is resized"""
        super().resizeEvent(event)
        # Debounce saving - only save after resize finishes
        if not hasattr(self, '_resize_timer'):
            try:
                from PySide6.QtCore import QTimer
            except ImportError:
                from PySide2.QtCore import QTimer
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.save_state)
        self._resize_timer.start(500)  # 500ms debounce
    
    # ========== Keyboard Shortcuts ==========
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts and forward arrow keys to browser"""
        if event.key() == Qt.Key_Escape:
            self.close()
            # Restore focus to browser
            if self.browser:
                self.browser.activateWindow()
                self.browser.raise_()
        elif event.key() == Qt.Key_Space:
            self.close()
            # Restore focus to browser
            if self.browser:
                self.browser.activateWindow()
                self.browser.raise_()
        elif event.key() == Qt.Key_F:
            # F key - Fit to view (reset zoom and pan)
            self.fit_to_view()
            event.accept()
            return
        elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End):
            # Forward arrow keys and navigation keys to browser file_list for thumbnail navigation
            # This allows navigating the browser list while Quick View is active
            if self.browser and hasattr(self.browser, 'file_list'):
                try:
                    from PySide6.QtGui import QKeyEvent
                    from PySide6.QtCore import QCoreApplication
                except ImportError:
                    from PySide2.QtGui import QKeyEvent
                    from PySide2.QtCore import QCoreApplication
                
                # Create a copy of the key event and send it to browser's file_list
                key_event = QKeyEvent(event.type(), event.key(), event.modifiers(), event.text())
                QCoreApplication.sendEvent(self.browser.file_list, key_event)
                
                # Don't consume the event in Quick View
                event.accept()
                return
        else:
            super().keyPressEvent(event)
    
    # ========== Window State ==========
    
    def closeEvent(self, event):
        """Handle window close"""
        # Save window state before closing
        self.save_state()
        
        # Restore focus to browser
        if self.browser:
            self.browser.activateWindow()
            self.browser.raise_()
        
        # Emit closed signal
        self.closed.emit()
        
        # if DEBUG_MODE:
        #     print("[QuickView] Closed")
        
        super().closeEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        try:
            from PySide6.QtWidgets import QMenu
        except ImportError:
            from PySide2.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # Lock Content toggle
        lock_action = menu.addAction("📌 Lock Content" if not self.pinned else "🔓 Unlock Content")
        lock_action.setCheckable(True)
        lock_action.setChecked(self.pinned)
        
        menu.addSeparator()
        
        # Layout mode submenu (only show if multi-file mode)
        layout_submenu = None
        layout_32_action = None
        layout_23_action = None
        layout_fit_action = None
        layout_grid_action = None
        
        if self.pixmap_item is None and len(self.current_assets) > 1:
            layout_submenu = menu.addMenu("📐 Layout Mode")
            
            layout_32_action = layout_submenu.addAction("🔲 Landscape (More Columns)")
            layout_32_action.setCheckable(True)
            layout_32_action.setChecked(self.layout_mode == '3:2')
            
            layout_23_action = layout_submenu.addAction("🔳 Portrait (More Rows)")
            layout_23_action.setCheckable(True)
            layout_23_action.setChecked(self.layout_mode == '2:3')
            
            layout_fit_action = layout_submenu.addAction("↔️ Fit to Window")
            layout_fit_action.setCheckable(True)
            layout_fit_action.setChecked(self.layout_mode == 'fit')
            
            layout_submenu.addSeparator()
            
            layout_grid_action = layout_submenu.addAction("⊞ Grid")
            layout_grid_action.setCheckable(True)
            layout_grid_action.setChecked(self.layout_mode == 'grid')
            
            menu.addSeparator()
        
        # Refresh Layout (only show if multi-file mode)
        refresh_action = None
        if self.pixmap_item is None and len(self.current_assets) > 1:
            refresh_action = menu.addAction("🔄 Refresh Layout")
            menu.addSeparator()
        
        # Always on Top toggle
        always_on_top_action = menu.addAction("✓ Always on Top" if self.always_on_top else "Always on Top")
        always_on_top_action.setCheckable(True)
        always_on_top_action.setChecked(self.always_on_top)
        
        # Execute menu
        action = menu.exec_(event.globalPos())
        
        if action == lock_action:
            self.toggle_pin()
        elif action == always_on_top_action:
            self.toggle_always_on_top()
        elif refresh_action and action == refresh_action:
            self.refresh_layout()
        elif layout_32_action and action == layout_32_action:
            self.set_layout_mode('3:2')
        elif layout_23_action and action == layout_23_action:
            self.set_layout_mode('2:3')
        elif layout_fit_action and action == layout_fit_action:
            self.set_layout_mode('fit')
        elif layout_grid_action and action == layout_grid_action:
            self.set_layout_mode('grid')
    
    def toggle_pin(self):
        """Toggle pin state (lock content)"""
        self.pinned = not self.pinned
        
        if self.pinned:
            # Save current assets
            self.pinned_assets = self.current_assets.copy()
            # if DEBUG_MODE:
            #     print(f"[QuickView] Content locked - showing {len(self.pinned_assets)} asset(s)")
        else:
            # Clear pinned assets
            self.pinned_assets = []
            # if DEBUG_MODE:
            #     print("[QuickView] Content unlocked")
    
    def toggle_always_on_top(self):
        """Toggle always on top window flag"""
        self.always_on_top = not self.always_on_top
        
        # Store current state
        was_visible = self.isVisible()
        geometry = self.geometry()
        
        # Update window flags
        if self.always_on_top:
            self.setWindowFlags(
                Qt.Tool | 
                Qt.WindowStaysOnTopHint | 
                Qt.FramelessWindowHint
            )
        else:
            self.setWindowFlags(
                Qt.Tool | 
                Qt.FramelessWindowHint
            )
        
        # Restore visibility and geometry
        if was_visible:
            self.setGeometry(geometry)
            self.show()
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Always on top: {self.always_on_top}")
    
    def refresh_layout(self):
        """Refresh multi-file layout based on current viewport size"""
        if not self.current_assets or len(self.current_assets) <= 1:
            return
        
        # if DEBUG_MODE:
        #     print("[QuickView] Refreshing layout...")
        
        # Re-show multi-file grid (will recalculate layout based on current viewport)
        self.show_multi_file_grid(self.current_assets)
    
    def set_layout_mode(self, mode):
        """Set layout mode and refresh layout"""
        if mode not in ['3:2', '2:3', 'fit', 'grid']:
            return
        
        if self.layout_mode == mode:
            return  # Already in this mode
        
        self.layout_mode = mode
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Layout mode changed to: {mode}")
        
        # Refresh layout with new mode
        self.refresh_layout()
    
    def show_single_file(self, asset):
        """Show single file preview"""
        file_path = Path(asset.file_path)
        
        # Check if it's a PDF
        if file_path.suffix.lower() == '.pdf':
            self.show_pdf_preview(file_path)
            return
        
        # Check if it's an image
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tga', '.tif', '.tiff', 
                           '.exr', '.hdr', '.gif', '.webp', '.psd']
        
        if file_path.suffix.lower() in image_extensions:
            self.show_image_preview(file_path)
        else:
            # Non-image file - show icon/placeholder
            self.show_placeholder(asset)
    
    def show_image_preview(self, file_path):
        """Show image preview"""
        # if DEBUG_MODE:
        #     print(f"[QuickView] show_image_preview called for: {file_path.name}")
        
        try:
            # Reset PDF state (we're showing an image now)
            self.is_pdf = False
            self.pdf_path = None
            self.pdf_current_page = 0
            self.pdf_page_count = 0
            
            # Reset first show flag (new content needs refit)
            if hasattr(self, '_first_show_done'):
                delattr(self, '_first_show_done')
            
            # Clear PDF navigation items
            for item in self.pdf_nav_items:
                self.graphics_scene.removeItem(item)
            self.pdf_nav_items.clear()
            
            # Check if this is the same file we already have loaded
            is_same_file = (self.current_file_path == file_path)
            
            # If same file and already loaded, do nothing (preserve zoom/pan/transforms)
            if is_same_file and self.pixmap_item is not None:
                # if DEBUG_MODE:
                #     print(f"[QuickView] Same image already loaded, preserving state: {file_path.name}")
                return
            
            # Load image - use HDR/EXR loader for .exr and .hdr files
            pixmap = None
            if file_path.suffix.lower() in ['.exr', '.hdr']:
                # if DEBUG_MODE:
                #     print(f"[QuickView] Loading HDR/EXR using load_hdr_exr_image: {file_path.name}")
                # Use the same HDR/EXR loader as PreviewPanel
                # NOTE: load_hdr_exr_image returns tuple (pixmap, resolution_str)
                result = load_hdr_exr_image(str(file_path))
                if result and result[0]:
                    pixmap = result[0]  # Extract pixmap from tuple
                    # if DEBUG_MODE:
                    #     print(f"[QuickView] HDR/EXR loaded successfully: {pixmap.width()}×{pixmap.height()}")
                # else:
                #     if DEBUG_MODE:
                #         print(f"[QuickView] HDR/EXR load failed or returned None")
            else:
                # Standard image formats (JPG, PNG, etc.)
                # Try OpenCV first for large images (better memory handling for 16K+ images)
                try:
                    # Check file size - if over 50MB or JPG, use OpenCV
                    import os
                    file_size_mb = os.path.getsize(str(file_path)) / (1024 * 1024)
                    
                    if file_size_mb > 50 or str(file_path).lower().endswith(('.jpg', '.jpeg')):
                        try:
                            import cv2
                            import numpy as np
                            
                            # Read FULL resolution image with OpenCV
                            img = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
                            
                            if img is not None:
                                # Convert BGR to RGB
                                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                
                                # Convert to QPixmap
                                from PySide6.QtGui import QImage
                                height, width, channels = img.shape
                                bytes_per_line = width * channels
                                q_image = QImage(img.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                                pixmap = QPixmap.fromImage(q_image.copy())
                            else:
                                raise Exception("OpenCV could not load image")
                        except Exception as cv_error:
                            # print(f"[QuickView] OpenCV loading failed: {cv_error}, using QPixmap...")
                            pixmap = QPixmap(str(file_path))
                    else:
                        # Small files - use standard QPixmap
                        pixmap = QPixmap(str(file_path))
                except Exception as e:
                    # Fallback to standard QPixmap loading
                    # print(f"[QuickView] Error checking file size: {e}, using QPixmap...")
                    pixmap = QPixmap(str(file_path))
            
            if pixmap is None or pixmap.isNull():
                # if DEBUG_MODE:
                #     print(f"[QuickView] Failed to load image: {file_path.name}")
                return
            
            # NOTE: Quick view doesn't need apply_exif_orientation - loads correctly already
            
            # Clear scene
            self.graphics_scene.clear()
            
            # Add pixmap to scene
            self.pixmap_item = self.graphics_scene.addPixmap(pixmap)
            
            # Set scene rect LARGER than pixmap to allow free panning beyond edges
            pixmap_rect = pixmap.rect()
            expanded_rect = pixmap_rect.adjusted(
                -pixmap_rect.width() * 2,   # Left padding (2x image width)
                -pixmap_rect.height() * 2,  # Top padding (2x image height)
                pixmap_rect.width() * 2,    # Right padding (2x image width)
                pixmap_rect.height() * 2    # Bottom padding (2x image height)
            )
            self.graphics_scene.setSceneRect(expanded_rect)
            
            # Position pixmap at origin (centered in expanded scene)
            self.pixmap_item.setPos(0, 0)
            
            # Fit new image in view - calculate scale factor manually (like PreviewPanel Zoom Mode)
            self.graphics_view.resetTransform()  # Clear any pan/zoom transforms
            
            # Calculate scale to fit image in viewport
            viewport_rect = self.graphics_view.viewport().rect()
            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()
            
            # Calculate scale factors for width and height
            scale_x = viewport_rect.width() / pixmap_width if pixmap_width > 0 else 1.0
            scale_y = viewport_rect.height() / pixmap_height if pixmap_height > 0 else 1.0
            
            # Use the smaller scale to fit completely (keep aspect ratio)
            fit_scale = min(scale_x, scale_y)
            
            # Apply initial scale transform
            self.graphics_view.scale(fit_scale, fit_scale)
            
            # Center the image
            self.graphics_view.centerOn(self.pixmap_item)
            
            self.zoom_factor = 1.0  # Reset zoom factor (relative to fitted size)
            
            # Update current file path
            self.current_file_path = file_path
            
            # if DEBUG_MODE:
            #     print(f"[QuickView] Loaded NEW image: {file_path.name} ({pixmap.width()}×{pixmap.height()})")
            
            # TODO: Add text label to scene below image (later)
        
        except Exception as e:
            # if DEBUG_MODE:
            #     print(f"[QuickView] Error loading image: {e}")
            pass
    
    def show_pdf_preview(self, file_path):
        """Show PDF preview (simple version: just load first page as image)"""
        # if DEBUG_MODE:
        #     print(f"[QuickView] Loading PDF: {file_path.name}")
        
        try:
            # Load first page of PDF
            pixmap, page_count, resolution = load_pdf_page(str(file_path), 0, 2048)
            
            if pixmap is None or pixmap.isNull():
                # if DEBUG_MODE:
                #     print(f"[QuickView] Failed to load PDF: {file_path.name}")
                return
            
            # Reset first show flag (new content needs refit)
            if hasattr(self, '_first_show_done'):
                delattr(self, '_first_show_done')
            
            # Clear scene (this also removes any old PDF navigation items)
            self.graphics_scene.clear()
            self.pdf_nav_items.clear()  # Clear the reference list too
            
            # Add PDF page as image
            self.pixmap_item = self.graphics_scene.addPixmap(pixmap)
            
            # Set scene rect LARGER than pixmap to allow free panning
            pixmap_rect = pixmap.rect()
            expanded_rect = pixmap_rect.adjusted(
                -pixmap_rect.width() * 2,
                -pixmap_rect.height() * 2,
                pixmap_rect.width() * 2,
                pixmap_rect.height() * 2
            )
            self.graphics_scene.setSceneRect(expanded_rect)
            self.pixmap_item.setPos(0, 0)
            
            # Fit PDF in view
            self.graphics_view.resetTransform()
            viewport_rect = self.graphics_view.viewport().rect()
            
            scale_x = viewport_rect.width() / pixmap.width() if pixmap.width() > 0 else 1.0
            scale_y = viewport_rect.height() / pixmap.height() if pixmap.height() > 0 else 1.0
            fit_scale = min(scale_x, scale_y)
            
            self.graphics_view.scale(fit_scale, fit_scale)
            self.graphics_view.centerOn(self.pixmap_item)
            
            self.zoom_factor = 1.0
            self.current_file_path = file_path
            self.pdf_fit_scale = fit_scale  # Store fit scale for navigation buttons
            
            # Store PDF state for navigation
            self.is_pdf = True
            self.pdf_path = str(file_path)
            self.pdf_current_page = 0
            self.pdf_page_count = page_count
            
            # Create PDF navigation overlays (only if multiple pages)
            if page_count > 1:
                self.create_pdf_navigation_overlay(pixmap_rect)
            
            # if DEBUG_MODE:
            #     print(f"[QuickView] PDF loaded: page 1/{page_count}")
        
        except Exception as e:
            # if DEBUG_MODE:
            #     print(f"[QuickView] Error loading PDF: {e}")
            pass
    
    def create_pdf_navigation_overlay(self, pixmap_rect):
        """Create simple navigation arrows on PDF edges"""
        try:
            from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
            from PySide6.QtGui import QBrush, QColor, QFont
        except ImportError:
            from PySide2.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
            from PySide2.QtGui import QBrush, QColor, QFont
        
        # Clear old navigation items
        for item in self.pdf_nav_items:
            self.graphics_scene.removeItem(item)
        self.pdf_nav_items.clear()
        
        # Get current scale for zoom-independent sizing
        # Use stored fit scale if available, otherwise get from view transform
        if hasattr(self, 'pdf_fit_scale') and self.pdf_fit_scale:
            scale_factor = self.pdf_fit_scale * self.zoom_factor
        else:
            view_transform = self.graphics_view.transform()
            scale_factor = view_transform.m11()
        
        # Fixed button dimensions in screen pixels (zoom-independent)
        fixed_btn_width = 120
        fixed_btn_height = 200
        fixed_visual_width = 60
        fixed_visual_height = 100
        fixed_font_size = 28
        fixed_counter_font = 14
        
        # Convert to scene coordinates (account for zoom)
        btn_width = fixed_btn_width / scale_factor
        btn_height = fixed_btn_height / scale_factor
        visual_width = fixed_visual_width / scale_factor
        visual_height = fixed_visual_height / scale_factor
        font_size = int(fixed_font_size / scale_factor)
        counter_font_size = int(fixed_counter_font / scale_factor)
        
        pdf_width = pixmap_rect.width()
        pdf_height = pixmap_rect.height()
        
        # Left arrow (previous page) - full height clickable area
        left_btn = QGraphicsRectItem(0, 0, btn_width, pdf_height)
        left_btn.setBrush(QBrush(QColor(40, 40, 40, 0)))  # Invisible but clickable
        left_btn.setPen(Qt.NoPen)
        left_btn.setData(0, "pdf_prev")  # Store button type in data
        left_btn.setVisible(False)  # Hidden by default (shown on hover)
        self.graphics_scene.addItem(left_btn)
        self.pdf_nav_items.append(left_btn)
        
        # Visual indicator for left arrow (smaller, centered)
        left_visual = QGraphicsRectItem(10 / scale_factor, (pdf_height - visual_height) / 2, visual_width, visual_height)
        left_visual.setBrush(QBrush(QColor(40, 40, 40, 150)))
        left_visual.setPen(Qt.NoPen)
        left_visual.setData(0, "pdf_prev")
        left_visual.setVisible(False)
        self.graphics_scene.addItem(left_visual)
        self.pdf_nav_items.append(left_visual)
        
        left_text = QGraphicsTextItem("◀")
        left_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        font = QFont(UI_FONT, font_size, QFont.Bold)
        left_text.setFont(font)
        # Center text in visual indicator
        text_rect = left_text.boundingRect()
        left_text.setPos(
            10 / scale_factor + (visual_width - text_rect.width()) / 2,
            (pdf_height - visual_height) / 2 + (visual_height - text_rect.height()) / 2
        )
        left_text.setData(0, "pdf_prev")
        left_text.setVisible(False)
        self.graphics_scene.addItem(left_text)
        self.pdf_nav_items.append(left_text)
        
        # Right arrow (next page) - full height clickable area
        right_btn = QGraphicsRectItem(pdf_width - btn_width, 0, btn_width, pdf_height)
        right_btn.setBrush(QBrush(QColor(40, 40, 40, 0)))  # Invisible but clickable
        right_btn.setPen(Qt.NoPen)
        right_btn.setData(0, "pdf_next")
        right_btn.setVisible(False)
        self.graphics_scene.addItem(right_btn)
        self.pdf_nav_items.append(right_btn)
        
        # Visual indicator for right arrow (smaller, centered)
        right_visual = QGraphicsRectItem(pdf_width - 70 / scale_factor, (pdf_height - visual_height) / 2, visual_width, visual_height)
        right_visual.setBrush(QBrush(QColor(40, 40, 40, 150)))
        right_visual.setPen(Qt.NoPen)
        right_visual.setData(0, "pdf_next")
        right_visual.setVisible(False)
        self.graphics_scene.addItem(right_visual)
        self.pdf_nav_items.append(right_visual)
        
        right_text = QGraphicsTextItem("▶")
        right_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        right_text.setFont(font)
        # Center text in visual indicator
        text_rect = right_text.boundingRect()
        right_text.setPos(
            pdf_width - 70 / scale_factor + (visual_width - text_rect.width()) / 2,
            (pdf_height - visual_height) / 2 + (visual_height - text_rect.height()) / 2
        )
        right_text.setData(0, "pdf_next")
        right_text.setVisible(False)
        self.graphics_scene.addItem(right_text)
        self.pdf_nav_items.append(right_text)
        
        # Page counter (bottom center)
        page_text = QGraphicsTextItem(f"{self.pdf_current_page + 1} / {self.pdf_page_count}")
        page_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        page_font = QFont(UI_FONT, counter_font_size, QFont.Bold)
        page_text.setFont(page_font)
        text_width = page_text.boundingRect().width()
        page_text.setPos((pdf_width - text_width) / 2, pdf_height - 40 / scale_factor)
        page_text.setData(0, "pdf_counter")
        page_text.setVisible(False)
        self.graphics_scene.addItem(page_text)
        self.pdf_nav_items.append(page_text)
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Created PDF navigation overlay")
    
    def pdf_navigate_page(self, direction):
        """Navigate PDF pages (direction: -1 = prev, +1 = next)"""
        if not self.is_pdf:
            return
        
        # Calculate new page
        new_page = self.pdf_current_page + direction
        
        # Clamp to valid range
        if new_page < 0 or new_page >= self.pdf_page_count:
            return
        
        # Load directly (no flag, no async - just like Preview Panel)
        self._do_pdf_navigate(new_page)
    
    def _do_pdf_navigate(self, new_page):
        """Actually load and display PDF page"""
        # Load new page
        pixmap, _, _ = load_pdf_page(self.pdf_path, new_page, 2048)
        
        if pixmap is None or pixmap.isNull():
            return
        
        # Update pixmap
        self.pixmap_item.setPixmap(pixmap)
        
        # Update page number
        self.pdf_current_page = new_page
        
        # Update page counter text
        for item in self.pdf_nav_items:
            if hasattr(item, 'data') and item.data(0) == "pdf_counter":
                if hasattr(item, 'setPlainText'):
                    item.setPlainText(f"{new_page + 1} / {self.pdf_page_count}")
    
    def create_pdf_grid_navigation(self, cell_index, cell_x, cell_y, cell_width, cell_height):
        """Create navigation buttons for PDF in grid cell"""
        try:
            from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
            from PySide6.QtGui import QBrush, QColor, QFont
        except ImportError:
            from PySide2.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
            from PySide2.QtGui import QBrush, QColor, QFont
        
        pdf_state = self.grid_pdf_states[cell_index]
        
        # Get current scale for zoom-independent sizing
        # Use stored fit scale if available, otherwise get from view transform
        if hasattr(self, 'pdf_fit_scale') and self.pdf_fit_scale:
            scale_factor = self.pdf_fit_scale * self.zoom_factor
        else:
            view_transform = self.graphics_view.transform()
            scale_factor = view_transform.m11()
        
        # Fixed button dimensions in screen pixels (smaller for grid)
        fixed_btn_width = 40
        fixed_btn_height = 60
        fixed_visual_width = 30
        fixed_visual_height = 60
        fixed_font_size = 16
        fixed_counter_font = 10
        
        # Convert to scene coordinates
        btn_width = fixed_btn_width / scale_factor
        btn_height = fixed_btn_height / scale_factor
        visual_width = fixed_visual_width / scale_factor
        visual_height = fixed_visual_height / scale_factor
        font_size = int(fixed_font_size / scale_factor)
        counter_font_size = int(fixed_counter_font / scale_factor)
        
        # Left arrow (previous page) - clickable area covers left side
        left_btn = QGraphicsRectItem(cell_x, cell_y, btn_width, cell_height)
        left_btn.setBrush(QBrush(QColor(40, 40, 40, 0)))  # Invisible but clickable
        left_btn.setPen(Qt.NoPen)
        left_btn.setData(0, f"grid_pdf_prev_{cell_index}")
        left_btn.setVisible(False)  # Hidden by default
        self.graphics_scene.addItem(left_btn)
        self.pdf_nav_items.append(left_btn)
        
        # Visual indicator for left
        left_visual = QGraphicsRectItem(cell_x + 5 / scale_factor, cell_y + (cell_height - visual_height) / 2, visual_width, visual_height)
        left_visual.setBrush(QBrush(QColor(40, 40, 40, 150)))
        left_visual.setPen(Qt.NoPen)
        left_visual.setData(0, f"grid_pdf_prev_{cell_index}")
        left_visual.setVisible(False)
        self.graphics_scene.addItem(left_visual)
        self.pdf_nav_items.append(left_visual)
        
        left_text = QGraphicsTextItem("◀")
        left_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        font = QFont(UI_FONT, font_size, QFont.Bold)
        left_text.setFont(font)
        # Center text in visual indicator
        text_rect = left_text.boundingRect()
        left_text.setPos(
            cell_x + 5 / scale_factor + (visual_width - text_rect.width()) / 2,
            cell_y + (cell_height - visual_height) / 2 + (visual_height - text_rect.height()) / 2
        )
        left_text.setData(0, f"grid_pdf_prev_{cell_index}")
        left_text.setVisible(False)
        self.graphics_scene.addItem(left_text)
        self.pdf_nav_items.append(left_text)
        
        # Right arrow (next page)
        right_btn = QGraphicsRectItem(cell_x + cell_width - btn_width, cell_y, btn_width, cell_height)
        right_btn.setBrush(QBrush(QColor(40, 40, 40, 0)))
        right_btn.setPen(Qt.NoPen)
        right_btn.setData(0, f"grid_pdf_next_{cell_index}")
        right_btn.setVisible(False)
        self.graphics_scene.addItem(right_btn)
        self.pdf_nav_items.append(right_btn)
        
        # Visual indicator for right
        right_visual = QGraphicsRectItem(cell_x + cell_width - 35 / scale_factor, cell_y + (cell_height - visual_height) / 2, visual_width, visual_height)
        right_visual.setBrush(QBrush(QColor(40, 40, 40, 150)))
        right_visual.setPen(Qt.NoPen)
        right_visual.setData(0, f"grid_pdf_next_{cell_index}")
        right_visual.setVisible(False)
        self.graphics_scene.addItem(right_visual)
        self.pdf_nav_items.append(right_visual)
        
        right_text = QGraphicsTextItem("▶")
        right_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        right_text.setFont(font)
        # Center text in visual indicator
        text_rect = right_text.boundingRect()
        right_text.setPos(
            cell_x + cell_width - 35 / scale_factor + (visual_width - text_rect.width()) / 2,
            cell_y + (cell_height - visual_height) / 2 + (visual_height - text_rect.height()) / 2
        )
        right_text.setData(0, f"grid_pdf_next_{cell_index}")
        right_text.setVisible(False)
        self.graphics_scene.addItem(right_text)
        self.pdf_nav_items.append(right_text)
        
        # Page counter (bottom center of cell)
        page_text = QGraphicsTextItem(f"{pdf_state['page'] + 1}/{pdf_state['page_count']}")
        page_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        page_font = QFont(UI_FONT, counter_font_size, QFont.Bold)
        page_text.setFont(page_font)
        text_width = page_text.boundingRect().width()
        page_text.setPos(cell_x + (cell_width - text_width) / 2, cell_y + cell_height - 30 / scale_factor)
        page_text.setData(0, f"grid_pdf_counter_{cell_index}")
        page_text.setVisible(False)
        self.graphics_scene.addItem(page_text)
        self.pdf_nav_items.append(page_text)
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Created grid PDF navigation for cell {cell_index}")
    
    def pdf_navigate_grid_page(self, cell_index, direction):
        """Navigate PDF page in grid mode"""
        if cell_index not in self.grid_pdf_states:
            return
        
        pdf_state = self.grid_pdf_states[cell_index]
        current_page = pdf_state['page']
        page_count = pdf_state['page_count']
        
        # Calculate new page
        new_page = current_page + direction
        
        # Clamp to valid range
        if new_page < 0 or new_page >= page_count:
            return
        
        # Load directly (no flag, no async - just like Preview Panel)
        self._do_pdf_navigate_grid(cell_index, new_page)
    
    def _do_pdf_navigate_grid(self, cell_index, new_page):
        """Actually load and display grid PDF page"""
        if cell_index not in self.grid_pdf_states:
            return
        
        pdf_state = self.grid_pdf_states[cell_index]
        page_count = pdf_state['page_count']
        
        # Load new page
        pixmap, _, _ = load_pdf_page(pdf_state['path'], new_page, 2048)
        
        if pixmap is None or pixmap.isNull():
            # if DEBUG_MODE:
            #     print(f"[QuickView] Failed to load grid PDF page {new_page + 1}")
            return
        
        # Update pixmap
        pixmap_item = pdf_state['pixmap_item']
        pixmap_item.setPixmap(pixmap)
        
        # Reapply transform
        try:
            from PySide6.QtGui import QTransform
        except ImportError:
            from PySide2.QtGui import QTransform
        
        transform = QTransform()
        transform.scale(pdf_state['scale_factor'], pdf_state['scale_factor'])
        pixmap_item.setTransform(transform)
        
        # Update page number
        pdf_state['page'] = new_page
        
        # Update page counter text
        for item in self.pdf_nav_items:
            if hasattr(item, 'data') and item.data(0) == f"grid_pdf_counter_{cell_index}":
                if hasattr(item, 'setPlainText'):
                    item.setPlainText(f"{new_page + 1}/{page_count}")
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Grid PDF cell {cell_index}: page {new_page + 1}/{page_count}")
    
    def show_placeholder(self, asset):
        """Show placeholder for non-image files"""
        # Clear scene
        self.graphics_scene.clear()
        
        # TODO: Show icon/gradient like main browser
        
        # TODO: Show gradient icon like in main browser
        # TODO: Show PDF preview
        # TODO: Show text preview
    
    # ========== Multi-File Grid ==========
    
    def show_multi_file_grid(self, assets):
        """Show multiple images and PDFs in PureRef-style flowing tile layout"""
        # if DEBUG_MODE:
        #     print(f"[QuickView] show_multi_file_grid called for {len(assets)} files")
        
        try:
            # Filter to images and PDFs
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tga', '.tif', '.tiff', 
                               '.exr', '.hdr', '.gif', '.webp', '.psd']
            
            supported_assets = []
            for a in assets:
                ext = Path(a.file_path).suffix.lower()
                if ext in image_extensions or ext == '.pdf':
                    supported_assets.append(a)
            
            if not supported_assets:
                # if DEBUG_MODE:
                #     print("[QuickView] No supported files to display in grid")
                return
            
            # Reset first show flag (new content needs refit)
            if hasattr(self, '_first_show_done'):
                delattr(self, '_first_show_done')
            
            # Clear scene and PDF state (clear list first, then scene to avoid dangling references)
            self.pdf_nav_items.clear()  # Clear references BEFORE scene.clear()
            self.grid_pdf_states.clear()  # Clear grid PDF states too
            self.graphics_scene.clear()
            self.pixmap_item = None  # Multi-item mode
            self.is_pdf = False  # No single PDF navigation in grid mode
            
            # Get viewport size for layout calculation
            viewport_rect = self.graphics_view.viewport().rect()
            viewport_width = viewport_rect.width()
            viewport_height = viewport_rect.height()
            
            # PureRef-style layout parameters
            ROW_HEIGHT = 250  # Fixed height for all items
            PADDING = 10  # Padding between items
            
            # Pre-load all images to get dimensions
            loaded_items = []  # List of (asset, pixmap, is_pdf, page_count)
            
            for asset in supported_assets:
                file_path = Path(asset.file_path)
                is_pdf = file_path.suffix.lower() == '.pdf'
                
                # Load image/PDF
                pixmap = None
                page_count = 1
                
                if is_pdf:
                    pixmap, page_count, _ = load_pdf_page(str(file_path), 0, 2048)
                elif file_path.suffix.lower() in ['.exr', '.hdr']:
                    result = load_hdr_exr_image(str(file_path))
                    if result and result[0]:
                        pixmap = result[0]
                else:
                    # Try OpenCV first for large images
                    try:
                        import os
                        file_size_mb = os.path.getsize(str(file_path)) / (1024 * 1024)
                        
                        if file_size_mb > 50 or str(file_path).lower().endswith(('.jpg', '.jpeg')):
                            try:
                                import cv2
                                import numpy as np
                                
                                img = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
                                
                                if img is not None:
                                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                    
                                    from PySide6.QtGui import QImage
                                    height, width, channels = img.shape
                                    bytes_per_line = width * channels
                                    q_image = QImage(img.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                                    pixmap = QPixmap.fromImage(q_image.copy())
                                else:
                                    raise Exception("OpenCV failed")
                            except:
                                pixmap = QPixmap(str(file_path))
                        else:
                            pixmap = QPixmap(str(file_path))
                    except:
                        pixmap = QPixmap(str(file_path))
                
                if pixmap and not pixmap.isNull():
                    # NOTE: Quick view doesn't need apply_exif_orientation - loads correctly already
                    loaded_items.append((asset, pixmap, is_pdf, page_count))
            
            if not loaded_items:
                return
            
            # Calculate target width based on layout mode
            if self.layout_mode == 'grid':
                # Legacy grid mode - use simple grid calculation
                target_width = viewport_width
                use_grid_mode = True
            else:
                # Tile flow mode
                use_grid_mode = False
                
                # Calculate target aspect ratio
                if self.layout_mode == '3:2':
                    target_aspect = 3.0 / 2.0  # landscape
                elif self.layout_mode == '2:3':
                    target_aspect = 2.0 / 3.0  # portrait
                else:  # 'fit'
                    # Use window aspect ratio
                    target_aspect = viewport_width / viewport_height if viewport_height > 0 else 1.5
                
                # Simple heuristic: calculate items per row
                avg_item_aspect = 1.5
                avg_item_width = ROW_HEIGHT * avg_item_aspect
                num_items = len(loaded_items)
                
                if self.layout_mode == '3:2':
                    # Landscape: More columns than rows (wider layout)
                    # Use sqrt(N * 3.5) for strong wider bias
                    items_per_row = max(2, int((num_items * 3.5) ** 0.5 + 0.5))
                elif self.layout_mode == '2:3':
                    # Portrait: More rows than columns (taller layout)
                    # Use sqrt(N / 3.5) for strong taller bias
                    items_per_row = max(1, int((num_items / 3.5) ** 0.5 + 0.5))
                else:  # 'fit'
                    # Use target aspect ratio
                    items_per_row = max(2, int((num_items * target_aspect) ** 0.5 + 0.5))
                
                # Calculate target width based on items per row
                target_width = items_per_row * avg_item_width + (items_per_row - 1) * PADDING
            
            # GRID MODE - simple grid layout
            if use_grid_mode:
                # Calculate grid layout (simple cols×rows)
                num_files = len(loaded_items)
                if num_files <= 4:
                    cols = num_files if num_files <= 2 else 2
                    rows_count = (num_files + cols - 1) // cols
                else:
                    cols = int((num_files * 1.6) ** 0.5)
                    rows_count = (num_files + cols - 1) // cols
                
                # Calculate cell size
                cell_width = (viewport_width - PADDING * (cols + 1)) / cols if cols > 0 else viewport_width
                cell_height = (viewport_height - PADDING * (rows_count + 1)) / rows_count if rows_count > 0 else viewport_height
                
                # Place items in grid
                item_index = 0
                for idx, (asset, pixmap, is_pdf, page_count) in enumerate(loaded_items):
                    col = idx % cols
                    row = idx // cols
                    
                    cell_x = PADDING + col * (cell_width + PADDING)
                    cell_y = PADDING + row * (cell_height + PADDING)
                    
                    pixmap_item = self.graphics_scene.addPixmap(pixmap)
                    
                    # Scale to fit cell
                    scale_x = cell_width / pixmap.width() if pixmap.width() > 0 else 1.0
                    scale_y = cell_height / pixmap.height() if pixmap.height() > 0 else 1.0
                    scale_factor = min(scale_x, scale_y)
                    
                    try:
                        from PySide6.QtGui import QTransform
                    except ImportError:
                        from PySide2.QtGui import QTransform
                    
                    transform = QTransform()
                    transform.scale(scale_factor, scale_factor)
                    pixmap_item.setTransform(transform)
                    
                    scaled_width = pixmap.width() * scale_factor
                    scaled_height = pixmap.height() * scale_factor
                    x_offset = (cell_width - scaled_width) / 2
                    y_offset = (cell_height - scaled_height) / 2
                    
                    pixmap_item.setPos(cell_x + x_offset, cell_y + y_offset)
                    
                    # PDF navigation
                    if is_pdf and page_count > 1:
                        self.grid_pdf_states[item_index] = {
                            'path': str(asset.file_path),
                            'page': 0,
                            'page_count': page_count,
                            'pixmap_item': pixmap_item,
                            'cell_x': cell_x,
                            'cell_y': cell_y,
                            'cell_width': cell_width,
                            'cell_height': cell_height,
                            'x_offset': x_offset,
                            'y_offset': y_offset,
                            'scaled_width': scaled_width,
                            'scaled_height': scaled_height,
                            'scale_factor': scale_factor
                        }
                        self.create_pdf_grid_navigation(item_index, cell_x + x_offset, cell_y + y_offset, 
                                                        scaled_width, scaled_height)
                    item_index += 1
                
                # Grid scene rect
                total_width = cols * (cell_width + PADDING) + PADDING
                total_height = rows_count * (cell_height + PADDING) + PADDING
                expanded_scene_rect = (-total_width * 2, -total_height * 2, 
                                       total_width * 5, total_height * 5)
                self.graphics_scene.setSceneRect(*expanded_scene_rect)
                
                self.graphics_view.resetTransform()
                scale_x = viewport_width / total_width if total_width > 0 else 1.0
                scale_y = viewport_height / total_height if total_height > 0 else 1.0
                fit_scale = min(scale_x, scale_y)
                self.graphics_view.scale(fit_scale, fit_scale)
                self.graphics_view.centerOn(total_width / 2, total_height / 2)
                
                self.zoom_factor = 1.0
                self.pdf_fit_scale = fit_scale
                self.current_file_path = None
                return  # Exit early for grid mode
            
            # TILE FLOW MODE - Greedy row packing algorithm
            rows = []  # List of rows, each row is a list of (asset, pixmap, is_pdf, page_count, x, y, width, height)
            current_row = []
            current_row_width = 0
            current_y = PADDING
            
            for asset, pixmap, is_pdf, page_count in loaded_items:
                # Calculate item width based on aspect ratio
                aspect_ratio = pixmap.width() / pixmap.height() if pixmap.height() > 0 else 1.0
                item_width = ROW_HEIGHT * aspect_ratio
                
                # Check if item fits in current row (use target_width instead of viewport_width)
                if current_row and current_row_width + PADDING + item_width > target_width:
                    # Current row is full, start new row
                    rows.append(current_row)
                    current_row = []
                    current_row_width = 0
                    current_y += ROW_HEIGHT + PADDING
                
                # Add item to current row
                current_row.append({
                    'asset': asset,
                    'pixmap': pixmap,
                    'is_pdf': is_pdf,
                    'page_count': page_count,
                    'x': current_row_width + PADDING,
                    'y': current_y,
                    'width': item_width,
                    'height': ROW_HEIGHT
                })
                current_row_width += item_width + PADDING
            
            # Add last row
            if current_row:
                rows.append(current_row)
            
            # Place all items in scene
            item_index = 0
            for row in rows:
                for item_data in row:
                    asset = item_data['asset']
                    pixmap = item_data['pixmap']
                    is_pdf = item_data['is_pdf']
                    page_count = item_data['page_count']
                    x = item_data['x']
                    y = item_data['y']
                    width = item_data['width']
                    height = item_data['height']
                    
                    # Add pixmap to scene
                    pixmap_item = self.graphics_scene.addPixmap(pixmap)
                    
                    # Calculate scale factor
                    scale_factor = height / pixmap.height() if pixmap.height() > 0 else 1.0
                    
                    # Apply scale transform
                    try:
                        from PySide6.QtGui import QTransform
                    except ImportError:
                        from PySide2.QtGui import QTransform
                    
                    transform = QTransform()
                    transform.scale(scale_factor, scale_factor)
                    pixmap_item.setTransform(transform)
                    
                    # Position item
                    pixmap_item.setPos(x, y)
                    
                    # If PDF with multiple pages, store state and create navigation buttons
                    if is_pdf and page_count > 1:
                        self.grid_pdf_states[item_index] = {
                            'path': str(asset.file_path),
                            'page': 0,
                            'page_count': page_count,
                            'pixmap_item': pixmap_item,
                            'cell_x': x,
                            'cell_y': y,
                            'cell_width': width,
                            'cell_height': height,
                            'x_offset': 0,
                            'y_offset': 0,
                            'scaled_width': width,
                            'scaled_height': height,
                            'scale_factor': scale_factor
                        }
                        
                        # Create navigation buttons for this PDF
                        self.create_pdf_grid_navigation(item_index, x, y, width, height)
                    
                    item_index += 1
            
            # Calculate total content size
            total_width = target_width  # Use target_width instead of viewport_width
            total_height = current_y + ROW_HEIGHT + PADDING if rows else 0
            
            # Set scene rect LARGER than content to allow free panning beyond edges
            expanded_scene_rect = (-total_width * 2, -total_height * 2, 
                                   total_width * 5, total_height * 5)
            self.graphics_scene.setSceneRect(*expanded_scene_rect)
            
            # Reset transform and fit content in view
            self.graphics_view.resetTransform()
            
            # Calculate scale to fit content in viewport
            scale_x = viewport_width / total_width if total_width > 0 else 1.0
            scale_y = viewport_rect.height() / total_height if total_height > 0 else 1.0
            fit_scale = min(scale_x, scale_y, 1.0)  # Don't scale up, max 1.0
            
            # Apply scale
            self.graphics_view.scale(fit_scale, fit_scale)
            
            # Center the content
            self.graphics_view.centerOn(total_width / 2, total_height / 2)
            
            self.zoom_factor = 1.0  # Reset zoom
            self.pdf_fit_scale = fit_scale  # Store fit scale for PDF navigation buttons
            
            # Store current file paths (for same-file check)
            self.current_file_path = None  # Multi-file mode
            
            # if DEBUG_MODE:
            #     print(f"[QuickView] Tile layout displayed: {len(loaded_items)} files in {len(rows)} rows")
        
        except Exception as e:
            # if DEBUG_MODE:
            #     print(f"[QuickView] Error showing multi-file grid: {e}")
            #     import traceback
            #     traceback.print_exc()
            pass
    
    # ========== State Persistence ==========
    
    def restore_state(self):
        """Restore window state from config"""
        if not hasattr(self.browser, 'config'):
            return
        
        config = self.browser.config.config
        
        # Restore size
        if "quick_view_width" in config and "quick_view_height" in config:
            width = config["quick_view_width"]
            height = config["quick_view_height"]
            self.resize(width, height)
            # if DEBUG_MODE:
            #     print(f"[QuickView] Restored size: {width}×{height}")
        
        # Restore position
        if "quick_view_x" in config and "quick_view_y" in config:
            x = config["quick_view_x"]
            y = config["quick_view_y"]
            self.move(x, y)
            # if DEBUG_MODE:
            #     print(f"[QuickView] Restored position: ({x}, {y})")
    
    def save_state(self):
        """Save window state to config"""
        if not hasattr(self.browser, 'config'):
            return
        
        # Save size
        self.browser.config.config["quick_view_width"] = self.width()
        self.browser.config.config["quick_view_height"] = self.height()
        
        # Save position
        pos = self.pos()
        self.browser.config.config["quick_view_x"] = pos.x()
        self.browser.config.config["quick_view_y"] = pos.y()
        
        # Save to file
        self.browser.config.save_config()
        
        # if DEBUG_MODE:
        #     print(f"[QuickView] Saved state: {self.width()}×{self.height()} at ({pos.x()}, {pos.y()})")
