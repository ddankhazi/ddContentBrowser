# -*- coding: utf-8 -*-
"""
DD Content Browser - Collections Panel UI
UI for managing manual and smart collections

Author: ddankhazi
License: MIT
"""

from pathlib import Path

try:
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                   QListWidget, QListWidgetItem, QMenu, QInputDialog,
                                   QMessageBox, QFileDialog)
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QIcon, QColor
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                   QListWidget, QListWidgetItem, QMenu, QInputDialog,
                                   QMessageBox, QFileDialog)
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtGui import QFont, QIcon, QColor
    PYSIDE_VERSION = 2

from .asset_collections import CollectionManager, ManualCollection, SmartCollection
from .widgets import DragDropCollectionListWidget

# UI Font - Default value (can be overridden by browser at runtime)
UI_FONT = "Segoe UI"

# Debug flag
DEBUG_MODE = False


class CollectionsPanel(QWidget):
    """Collections panel widget"""
    
    # Signals
    collection_selected = Signal(str)  # collection_name
    collection_cleared = Signal()      # Clear filter (show all files)
    
    def __init__(self, collection_manager: CollectionManager, parent=None):
        super().__init__(parent)
        self.collection_manager = collection_manager
        
        self.setup_ui()
        self.refresh_collections_list()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar with buttons
        toolbar = QHBoxLayout()
        
        self.new_btn = QPushButton("+ New")
        self.new_btn.setToolTip("Create new collection")
        self.new_btn.clicked.connect(self.create_new_collection)
        toolbar.addWidget(self.new_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Collections list - with drag & drop support
        self.collections_list = DragDropCollectionListWidget()
        self.collections_list.setFont(QFont(UI_FONT, 9))
        self.collections_list.setSelectionMode(QListWidget.SingleSelection)
        self.collections_list.itemClicked.connect(self.on_collection_clicked)
        self.collections_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.collections_list.customContextMenuRequested.connect(self.show_context_menu)
        # Maya-style selection color
        self.collections_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #4b7daa;
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(75, 125, 170, 0.3);
            }
        """)
        # Connect drag & drop signal
        self.collections_list.files_dropped_on_collection.connect(self.on_files_dropped)
        layout.addWidget(self.collections_list)
        
        # Exit collection view button (only visible/enabled when in collection mode)
        self.clear_btn = QPushButton("Exit Collection View")
        self.clear_btn.setToolTip("Return to folder browsing")
        self.clear_btn.clicked.connect(self.clear_collection_filter)
        self.clear_btn.setVisible(False)  # Hidden by default
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #4b7daa;
                color: white;
                border: none;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a8dba;
            }
            QPushButton:pressed {
                background-color: #3a6d9a;
            }
        """)
        layout.addWidget(self.clear_btn)
    
    def refresh_collections_list(self):
        """Refresh collections list"""
        self.collections_list.clear()
        
        collections = self.collection_manager.get_all_collections()
        
        if not collections:
            # Show empty state
            item = QListWidgetItem("No collections yet")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self.collections_list.addItem(item)
            return
        
        # Sort: Manual first, then Smart, then alphabetically
        manual_cols = sorted([c for c in collections if c.type == 'manual'], key=lambda c: c.name.lower())
        smart_cols = sorted([c for c in collections if c.type == 'smart'], key=lambda c: c.name.lower())
        
        # Add manual collections
        if manual_cols:
            for collection in manual_cols:
                # Use a subtle gray folder symbol (▸ or ▶ or ▪)
                item_text = f"▸ {collection.name}"
                if isinstance(collection, ManualCollection):
                    file_count = len(collection.get_existing_files())
                    item_text += f" ({file_count})"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, collection.name)  # Store collection name
                # Set gray color for the icon
                item.setForeground(QColor(150, 150, 150))
                self.collections_list.addItem(item)
        
        # Add smart collections (future)
        if smart_cols:
            for collection in smart_cols:
                item_text = f"🧠 {collection.name}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, collection.name)
                self.collections_list.addItem(item)
    
    def create_new_collection(self):
        """Create new manual collection"""
        name, ok = QInputDialog.getText(
            self,
            "New Collection",
            "Collection name:",
            text="New Collection"
        )
        
        if ok and name:
            try:
                self.collection_manager.create_manual_collection(name)
                self.refresh_collections_list()
                
                if DEBUG_MODE:
                    print(f"[CollectionsPanel] Created collection: {name}")
            
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def on_collection_clicked(self, item):
        """Handle collection click"""
        collection_name = item.data(Qt.UserRole)
        if collection_name:
            self.collection_selected.emit(collection_name)
            # Show exit button when collection is active
            self.clear_btn.setVisible(True)
            
            if DEBUG_MODE:
                print(f"[CollectionsPanel] Selected collection: {collection_name}")
    
    def clear_collection_filter(self):
        """Clear collection filter"""
        self.collections_list.clearSelection()
        self.collection_cleared.emit()
        # Hide exit button when returning to folder view
        self.clear_btn.setVisible(False)
        
        if DEBUG_MODE:
            print("[CollectionsPanel] Cleared collection filter")
    
    def show_context_menu(self, position):
        """Show context menu for collections"""
        item = self.collections_list.itemAt(position)
        if not item:
            return
        
        collection_name = item.data(Qt.UserRole)
        if not collection_name:
            return
        
        collection = self.collection_manager.get_collection(collection_name)
        if not collection:
            return
        
        menu = QMenu()
        
        # Rename action
        rename_action = menu.addAction("Rename...")
        
        # Delete action
        delete_action = menu.addAction("Delete")
        
        menu.addSeparator()
        
        # Export to Folder action (manual collections only)
        if isinstance(collection, ManualCollection):
            export_action = menu.addAction("📦 Export to Folder...")
        else:
            export_action = None
        
        # Cleanup action (manual collections only)
        if isinstance(collection, ManualCollection):
            menu.addSeparator()
            cleanup_action = menu.addAction("Clean up missing files")
        else:
            cleanup_action = None
        
        # Execute menu
        action = menu.exec_(self.collections_list.mapToGlobal(position))
        
        if action == rename_action:
            self.rename_collection(collection_name)
        elif action == delete_action:
            self.delete_collection(collection_name)
        elif export_action and action == export_action:
            self.export_collection_to_folder(collection_name)
        elif cleanup_action and action == cleanup_action:
            self.cleanup_collection(collection_name)
    
    def rename_collection(self, old_name: str):
        """Rename collection"""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Collection",
            "New name:",
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            try:
                self.collection_manager.rename_collection(old_name, new_name)
                self.refresh_collections_list()
                
                if DEBUG_MODE:
                    print(f"[CollectionsPanel] Renamed: {old_name} → {new_name}")
            
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def delete_collection(self, name: str):
        """Delete collection"""
        reply = QMessageBox.question(
            self,
            "Delete Collection",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.collection_manager.delete_collection(name)
                self.refresh_collections_list()
                self.collection_cleared.emit()  # Clear filter
                
                if DEBUG_MODE:
                    print(f"[CollectionsPanel] Deleted: {name}")
            
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def cleanup_collection(self, name: str):
        """Clean up missing files from collection"""
        collection = self.collection_manager.get_collection(name)
        if not isinstance(collection, ManualCollection):
            return
        
        before_count = len(collection.files)
        collection.cleanup_missing_files()
        after_count = len(collection.files)
        removed_count = before_count - after_count
        
        if removed_count > 0:
            self.collection_manager.save()
            self.refresh_collections_list()
            QMessageBox.information(
                self,
                "Cleanup Complete",
                f"Removed {removed_count} missing file(s) from '{name}'"
            )
        else:
            QMessageBox.information(
                self,
                "Cleanup Complete",
                "No missing files found"
            )
    
    def export_collection_to_folder(self, collection_name: str):
        """Export collection files to a folder"""
        import shutil
        
        collection = self.collection_manager.get_collection(collection_name)
        if not isinstance(collection, ManualCollection):
            return
        
        # Get existing files
        files = collection.get_existing_files()
        if not files:
            QMessageBox.information(self, "Empty Collection", "This collection has no files to export")
            return
        
        # Select destination folder
        dest_folder = QFileDialog.getExistingDirectory(
            self,
            f"Export '{collection_name}' to Folder",
            str(Path.home())
        )
        
        if not dest_folder:
            return
        
        dest_path = Path(dest_folder)
        
        # Ask for conflict handling strategy
        reply = QMessageBox.question(
            self,
            "File Conflict Handling",
            f"How to handle existing files?\n\n"
            f"Yes = Overwrite existing files\n"
            f"No = Skip existing files\n"
            f"Cancel = Rename duplicates",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            conflict_mode = "overwrite"
        elif reply == QMessageBox.No:
            conflict_mode = "skip"
        else:
            conflict_mode = "rename"
        
        # Copy files with progress
        copied = 0
        skipped = 0
        errors = []
        
        for file_path in files:
            src = Path(file_path)
            dest = dest_path / src.name
            
            try:
                # Handle conflicts
                if dest.exists():
                    if conflict_mode == "skip":
                        skipped += 1
                        continue
                    elif conflict_mode == "rename":
                        # Find unique name
                        counter = 1
                        stem = dest.stem
                        suffix = dest.suffix
                        while dest.exists():
                            dest = dest_path / f"{stem}_{counter}{suffix}"
                            counter += 1
                
                # Copy file
                shutil.copy2(src, dest)
                copied += 1
                
            except Exception as e:
                errors.append(f"{src.name}: {str(e)}")
        
        # Show results
        msg = f"Export complete!\n\n"
        msg += f"Copied: {copied} file(s)\n"
        if skipped > 0:
            msg += f"Skipped: {skipped} file(s)\n"
        if errors:
            msg += f"\nErrors ({len(errors)}):\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... and {len(errors) - 5} more"
        
        QMessageBox.information(self, "Export Complete", msg)
        
        if DEBUG_MODE:
            print(f"[CollectionsPanel] Exported {copied} files from '{collection_name}' to {dest_folder}")
    
    def add_files_to_collection(self, collection_name: str, file_paths: list):
        """Add files to a collection"""
        collection = self.collection_manager.get_collection(collection_name)
        if not isinstance(collection, ManualCollection):
            QMessageBox.warning(self, "Error", "Can only add files to manual collections")
            return
        
        collection.add_files(file_paths)
        self.collection_manager.save()
        self.refresh_collections_list()
        
        if DEBUG_MODE:
            print(f"[CollectionsPanel] Added {len(file_paths)} file(s) to {collection_name}")
    
    def on_files_dropped(self, collection_name: str, file_paths: list):
        """Handle files dropped onto collection (via middle-button drag)"""
        collection = self.collection_manager.get_collection(collection_name)
        
        if not isinstance(collection, ManualCollection):
            QMessageBox.warning(self, "Error", "Can only add files to manual collections")
            return
        
        # Add files to collection
        added_count = 0
        for file_path in file_paths:
            if file_path not in collection.files:
                collection.add_file(file_path)
                added_count += 1
        
        if added_count > 0:
            self.collection_manager.save()
            self.refresh_collections_list()
            
            # Show confirmation message
            browser = self.parent()
            while browser and not hasattr(browser, 'status_bar'):
                browser = browser.parent()
            if browser and hasattr(browser, 'status_bar'):
                browser.status_bar.showMessage(
                    f"Added {added_count} file(s) to '{collection_name}'",
                    2000
                )
