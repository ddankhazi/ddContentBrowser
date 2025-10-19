# -*- coding: utf-8 -*-
"""
DD Content Browser - Quick View System
macOS Quick Look-style floating preview window

Author: DankHazid
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

# Import HDR/EXR loading from widgets
from .widgets import load_hdr_exr_image

# UI Font - will be set by browser at runtime
UI_FONT = "Segoe UI"

# Debug mode
DEBUG_MODE = False


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
        
        if DEBUG_MODE:
            print("[QuickView] Initialized")
    
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
        self.graphics_view.setStyleSheet("QGraphicsView { background-color: #2a2a2a; border: none; }")
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
            if DEBUG_MODE:
                print("[QuickView] Ignoring selection change (pinned)")
            return  # Ignore if pinned
        
        if not assets:
            if DEBUG_MODE:
                print("[QuickView] No assets to preview")
            return
        
        if DEBUG_MODE:
            asset_names = [Path(a.file_path).name for a in assets]
            print(f"[QuickView] show_preview called with {len(assets)} asset(s): {asset_names}")
        
        self.current_assets = assets
        
        # Single file or multiple?
        if len(assets) == 1:
            if DEBUG_MODE:
                print(f"[QuickView] Calling show_single_file for: {Path(assets[0].file_path).name}")
            self.show_single_file(assets[0])
            self.preview_container.setCurrentWidget(self.single_preview)
        else:
            # Multi-file grid (Phase 4)
            self.show_multi_file_grid(assets)
            self.preview_container.setCurrentWidget(self.single_preview)  # Use same canvas
        
        if DEBUG_MODE:
            print(f"[QuickView] Finished showing preview for {len(assets)} asset(s)")

    
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
            if event.type() not in [QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonRelease]:
                return super().eventFilter(obj, event)
            
            # Map viewport position to dialog position
            dialog_pos = self.graphics_view.mapTo(self, event.pos())
            
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
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
                if DEBUG_MODE:
                    print(f"[QuickView] Starting resize: {self.resize_dir}")
                event.accept()
                return
        elif event.button() == Qt.MiddleButton:
            # Middle button drag to move window
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(Qt.SizeAllCursor)
            if DEBUG_MODE:
                print(f"[QuickView] Starting window drag")
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
        
        if DEBUG_MODE:
            print(f"[QuickView] Zoom: {self.zoom_factor:.2f}x")
    
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
                
                # Center the grid
                self.graphics_view.centerOn(content_rect.center())
        
        if DEBUG_MODE:
            print("[QuickView] Fit to view")
    
    # ========== Window Events (for state persistence) ==========
    
    def showEvent(self, event):
        """Handle first show - ensure proper viewport sizing"""
        super().showEvent(event)
        
        if DEBUG_MODE:
            print(f"[QuickView] showEvent - pixmap_item exists: {self.pixmap_item is not None}")
        
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
            
            if DEBUG_MODE:
                print("[QuickView] First show - scheduling refit")
    
    def _refit_on_first_show(self):
        """Re-fit content on first show (viewport size is now correct)"""
        if DEBUG_MODE:
            viewport_rect = self.graphics_view.viewport().rect()
            print(f"[QuickView] _refit_on_first_show - viewport: {viewport_rect.width()}x{viewport_rect.height()}, pixmap_item: {self.pixmap_item is not None}")
        
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
                
                if DEBUG_MODE:
                    print(f"[QuickView] Re-fitted on first show (scale: {fit_scale:.2f})")
        else:
            # No pixmap - might be multi-grid, try generic fit
            self.fit_to_view()
            if DEBUG_MODE:
                print("[QuickView] No pixmap, called fit_to_view()")
    
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
        
        if DEBUG_MODE:
            print("[QuickView] Closed")
        
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
    
    def toggle_pin(self):
        """Toggle pin state (lock content)"""
        self.pinned = not self.pinned
        
        if self.pinned:
            # Save current assets
            self.pinned_assets = self.current_assets.copy()
            if DEBUG_MODE:
                print(f"[QuickView] Content locked - showing {len(self.pinned_assets)} asset(s)")
        else:
            # Clear pinned assets
            self.pinned_assets = []
            if DEBUG_MODE:
                print("[QuickView] Content unlocked")
    
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
        
        if DEBUG_MODE:
            print(f"[QuickView] Always on top: {self.always_on_top}")
    
    def show_single_file(self, asset):
        """Show single file preview"""
        file_path = Path(asset.file_path)
        
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
        if DEBUG_MODE:
            print(f"[QuickView] show_image_preview called for: {file_path.name}")
        
        try:
            # Check if this is the same file we already have loaded
            is_same_file = (self.current_file_path == file_path)
            
            # If same file and already loaded, do nothing (preserve zoom/pan/transforms)
            if is_same_file and self.pixmap_item is not None:
                if DEBUG_MODE:
                    print(f"[QuickView] Same image already loaded, preserving state: {file_path.name}")
                return
            
            # Load image - use HDR/EXR loader for .exr and .hdr files
            pixmap = None
            if file_path.suffix.lower() in ['.exr', '.hdr']:
                if DEBUG_MODE:
                    print(f"[QuickView] Loading HDR/EXR using load_hdr_exr_image: {file_path.name}")
                # Use the same HDR/EXR loader as PreviewPanel
                # NOTE: load_hdr_exr_image returns tuple (pixmap, resolution_str)
                result = load_hdr_exr_image(str(file_path))
                if result and result[0]:
                    pixmap = result[0]  # Extract pixmap from tuple
                    if DEBUG_MODE:
                        print(f"[QuickView] HDR/EXR loaded successfully: {pixmap.width()}×{pixmap.height()}")
                else:
                    if DEBUG_MODE:
                        print(f"[QuickView] HDR/EXR load failed or returned None")
            else:
                # Standard image formats (JPG, PNG, etc.)
                pixmap = QPixmap(str(file_path))
            
            if pixmap is None or pixmap.isNull():
                if DEBUG_MODE:
                    print(f"[QuickView] Failed to load image: {file_path.name}")
                return
            
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
            
            if DEBUG_MODE:
                print(f"[QuickView] Loaded NEW image: {file_path.name} ({pixmap.width()}×{pixmap.height()})")
            
            # TODO: Add text label to scene below image (later)
        
        except Exception as e:
            if DEBUG_MODE:
                print(f"[QuickView] Error loading image: {e}")
    
    def show_placeholder(self, asset):
        """Show placeholder for non-image files"""
        # Clear scene
        self.graphics_scene.clear()
        
        # TODO: Show icon/gradient like main browser
        
        # TODO: Show gradient icon like in main browser
        # TODO: Show PDF preview
        # TODO: Show text preview
    
    # ========== Multi-File Grid ==========
    
    def calculate_grid_layout(self, num_files):
        """Calculate optimal grid layout (cols, rows) for number of files - prefer wider layouts"""
        if num_files <= 0:
            return (0, 0)
        if num_files == 1:
            return (1, 1)
        if num_files == 2:
            return (2, 1)  # 2 horizontal
        if num_files == 3:
            return (3, 1)  # 3 horizontal
        if num_files == 4:
            return (2, 2)  # 2×2 square
        if num_files == 5:
            return (3, 2)  # 3×2 (not 5×1)
        if num_files == 6:
            return (3, 2)  # 3×2
        if num_files <= 8:
            return (4, 2)  # 4×2 (7-8 files)
        if num_files == 9:
            return (5, 2)  # 5×2 (not 3×3)
        if num_files <= 10:
            return (5, 2)  # 5×2
        if num_files <= 12:
            return (4, 3)  # 4×3
        if num_files <= 15:
            return (5, 3)  # 5×3
        if num_files <= 18:
            return (6, 3)  # 6×3
        if num_files <= 20:
            return (5, 4)  # 5×4
        if num_files <= 24:
            return (6, 4)  # 6×4
        
        # For very large counts, prefer wider aspect (roughly 16:9 or 3:2)
        # Target aspect ratio around 1.5-1.7 (wider than square)
        cols = int((num_files * 1.6) ** 0.5)  # Bias towards more columns
        rows = (num_files + cols - 1) // cols  # Ceiling division
        return (cols, rows)
    
    def show_multi_file_grid(self, assets):
        """Show multiple images in a grid layout"""
        if DEBUG_MODE:
            print(f"[QuickView] show_multi_file_grid called for {len(assets)} files")
        
        try:
            # Filter to only image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tga', '.tif', '.tiff', 
                               '.exr', '.hdr', '.gif', '.webp', '.psd']
            image_assets = [a for a in assets if Path(a.file_path).suffix.lower() in image_extensions]
            
            if not image_assets:
                if DEBUG_MODE:
                    print("[QuickView] No image files to display in grid")
                return
            
            # Calculate grid layout
            cols, rows = self.calculate_grid_layout(len(image_assets))
            
            if DEBUG_MODE:
                print(f"[QuickView] Grid layout: {cols}×{rows} for {len(image_assets)} images")
            
            # Clear scene
            self.graphics_scene.clear()
            self.pixmap_item = None  # Multi-item mode, no single pixmap_item
            
            # Get viewport size to calculate cell size
            viewport_rect = self.graphics_view.viewport().rect()
            viewport_width = viewport_rect.width()
            viewport_height = viewport_rect.height()
            
            # Calculate cell size (with small padding)
            padding = 10
            cell_width = (viewport_width - padding * (cols + 1)) / cols
            cell_height = (viewport_height - padding * (rows + 1)) / rows
            
            # Load and place images in grid
            for idx, asset in enumerate(image_assets):
                file_path = Path(asset.file_path)
                
                # Load FULL RESOLUTION image - use HDR/EXR loader for .exr and .hdr files
                pixmap = None
                if file_path.suffix.lower() in ['.exr', '.hdr']:
                    if DEBUG_MODE:
                        print(f"[QuickView] Grid loading HDR/EXR: {file_path.name}")
                    # NOTE: load_hdr_exr_image returns tuple (pixmap, resolution_str)
                    result = load_hdr_exr_image(str(file_path))
                    if result and result[0]:
                        pixmap = result[0]  # Extract pixmap from tuple
                else:
                    # Standard image formats
                    pixmap = QPixmap(str(file_path))
                
                if pixmap is None or pixmap.isNull():
                    if DEBUG_MODE:
                        print(f"[QuickView] Grid skipping failed load: {file_path.name}")
                    continue
                
                # Calculate grid position
                col = idx % cols
                row = idx // cols
                
                # Calculate cell position (with padding)
                cell_x = padding + col * (cell_width + padding)
                cell_y = padding + row * (cell_height + padding)
                
                # Add FULL RES pixmap to scene (don't scale it down)
                pixmap_item = self.graphics_scene.addPixmap(pixmap)
                
                # Calculate scale to fit pixmap in cell (maintain aspect ratio)
                pixmap_width = pixmap.width()
                pixmap_height = pixmap.height()
                
                scale_x = cell_width / pixmap_width if pixmap_width > 0 else 1.0
                scale_y = cell_height / pixmap_height if pixmap_height > 0 else 1.0
                scale_factor = min(scale_x, scale_y)
                
                # Apply scale transform to item (keeps full-res pixmap, just scales visually)
                try:
                    from PySide6.QtGui import QTransform
                except ImportError:
                    from PySide2.QtGui import QTransform
                
                transform = QTransform()
                transform.scale(scale_factor, scale_factor)
                pixmap_item.setTransform(transform)
                
                # Calculate final scaled size for centering
                scaled_width = pixmap_width * scale_factor
                scaled_height = pixmap_height * scale_factor
                
                # Center scaled pixmap in cell
                x_offset = (cell_width - scaled_width) / 2
                y_offset = (cell_height - scaled_height) / 2
                
                pixmap_item.setPos(cell_x + x_offset, cell_y + y_offset)
            
            # Set scene rect LARGER than grid to allow free panning beyond edges
            total_width = cols * (cell_width + padding) + padding
            total_height = rows * (cell_height + padding) + padding
            
            # Expand scene rect by 2x in all directions
            expanded_scene_rect = (-total_width * 2, -total_height * 2, 
                                   total_width * 5, total_height * 5)
            self.graphics_scene.setSceneRect(*expanded_scene_rect)
            
            # Reset transform and fit grid in view
            self.graphics_view.resetTransform()
            
            # Calculate scale to fit grid in viewport
            scale_x = viewport_width / total_width if total_width > 0 else 1.0
            scale_y = viewport_height / total_height if total_height > 0 else 1.0
            fit_scale = min(scale_x, scale_y)
            
            # Apply scale
            self.graphics_view.scale(fit_scale, fit_scale)
            
            # Center the grid
            self.graphics_view.centerOn(total_width / 2, total_height / 2)
            
            self.zoom_factor = 1.0  # Reset zoom
            
            # Store current file paths (for same-file check)
            self.current_file_path = None  # Multi-file mode
            
            if DEBUG_MODE:
                print(f"[QuickView] Grid displayed: {len(image_assets)} images in {cols}×{rows} grid")
        
        except Exception as e:
            if DEBUG_MODE:
                print(f"[QuickView] Error showing multi-file grid: {e}")
    
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
            if DEBUG_MODE:
                print(f"[QuickView] Restored size: {width}×{height}")
        
        # Restore position
        if "quick_view_x" in config and "quick_view_y" in config:
            x = config["quick_view_x"]
            y = config["quick_view_y"]
            self.move(x, y)
            if DEBUG_MODE:
                print(f"[QuickView] Restored position: ({x}, {y})")
    
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
        
        if DEBUG_MODE:
            print(f"[QuickView] Saved state: {self.width()}×{self.height()} at ({pos.x()}, {pos.y()})")
