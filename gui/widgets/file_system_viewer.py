"""
File system viewer widget for displaying parsed disk contents
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QLabel, QPushButton, QMessageBox, QProgressDialog,
    QMenu, QFileDialog, QTextEdit, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QFont

from core.parsers.pytsk_parser import get_parser, FileEntry


class FileSystemParseThread(QThread):
    """Thread for parsing file system in background"""
    
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(bool, str)  # success, error message
    entry_found = pyqtSignal(object)  # FileEntry object
    
    def __init__(self, image_path: str, partition_offset: int = 0):
        super().__init__()
        self.image_path = image_path
        self.partition_offset = partition_offset
        self.parser = None
        self._should_stop = False
        
    def run(self):
        """Run the parsing in background"""
        try:
            self.parser = get_parser()
            
            # Open image
            self.progress.emit(10, "Opening disk image...")
            if not self.parser.open_image(self.image_path):
                self.finished.emit(False, "Failed to open disk image")
                return
                
            # Open file system
            self.progress.emit(20, "Opening file system...")
            if not self.parser.open_file_system(self.partition_offset):
                self.finished.emit(False, "Failed to open file system")
                return
                
            # Walk file system
            self.progress.emit(30, "Scanning file system...")
            total_files = 0
            
            for entry in self.parser.walk_file_system():
                if self._should_stop:
                    break
                    
                self.entry_found.emit(entry)
                total_files += 1
                
                # Update progress periodically
                if total_files % 100 == 0:
                    self.progress.emit(
                        min(30 + (total_files // 10), 90),
                        f"Found {total_files} files/directories..."
                    )
                    
            if not self._should_stop:
                self.progress.emit(100, f"Complete! Found {total_files} items")
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, "Parsing cancelled")
                
        except Exception as e:
            logging.error(f"Error in parsing thread: {e}")
            self.finished.emit(False, str(e))
            
        finally:
            if self.parser:
                self.parser.close()
                
    def stop(self):
        """Stop the parsing thread"""
        self._should_stop = True


class FileSystemViewerWidget(QWidget):
    """Widget for viewing file system structure from disk images"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image_path = None
        self.parser = None
        self.parse_thread = None
        self.file_entries = {}  # Path -> FileEntry mapping
        self.tree_items = {}    # Path -> QTreeWidgetItem mapping
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        self.status_label = QLabel("No disk image loaded")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        self.parse_button = QPushButton("Parse Image")
        self.parse_button.clicked.connect(self.parse_current_image)
        self.parse_button.setEnabled(False)
        header_layout.addWidget(self.parse_button)
        
        self.export_button = QPushButton("Export File List")
        self.export_button.clicked.connect(self.export_file_list)
        self.export_button.setEnabled(False)
        header_layout.addWidget(self.export_button)
        
        main_layout.addLayout(header_layout)
        
        # Search and filter controls
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self.filter_tree)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Files", "Deleted Only", "Images", "Documents", "Archives"])
        self.filter_combo.currentTextChanged.connect(self.filter_tree)
        search_layout.addWidget(QLabel("Filter:"))
        search_layout.addWidget(self.filter_combo)
        
        self.size_filter = QComboBox()
        self.size_filter.addItems(["Any Size", "> 1MB", "> 10MB", "> 100MB", "< 1MB"])
        self.size_filter.currentTextChanged.connect(self.filter_tree)
        search_layout.addWidget(QLabel("Size:"))
        search_layout.addWidget(self.size_filter)
        
        search_layout.addStretch()
        
        main_layout.addLayout(search_layout)
        
        # Splitter for tree and details
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # File system tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Size", "Modified", "Type"])
        self.file_tree.itemClicked.connect(self.on_item_selected)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Style deleted files differently
        self.file_tree.setStyleSheet("""
            QTreeWidget::item {
                padding: 2px;
            }
        """)
        
        self.splitter.addWidget(self.file_tree)
        
        # Details panel
        self.details_panel = QWidget()
        details_layout = QVBoxLayout(self.details_panel)
        
        # File info table
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.info_table.horizontalHeader().setStretchLastSection(True)
        self.info_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        details_layout.addWidget(QLabel("File Information:"))
        details_layout.addWidget(self.info_table)
        
        # Hex preview
        self.hex_preview = QTextEdit()
        self.hex_preview.setReadOnly(True)
        self.hex_preview.setFont(QFont("Courier", 9))
        self.hex_preview.setMaximumHeight(200)
        details_layout.addWidget(QLabel("Content Preview (Hex):"))
        details_layout.addWidget(self.hex_preview)
        
        self.splitter.addWidget(self.details_panel)
        self.splitter.setSizes([600, 400])
        
        main_layout.addWidget(self.splitter)
        
    def set_disk_image(self, image_path: str):
        """Set the disk image to parse"""
        self.current_image_path = image_path
        self.status_label.setText(f"Image: {os.path.basename(image_path)}")
        self.parse_button.setEnabled(True)
        self.clear_view()
        
    def clear_view(self):
        """Clear the current view"""
        self.file_tree.clear()
        self.info_table.setRowCount(0)
        self.hex_preview.clear()
        self.file_entries.clear()
        self.tree_items.clear()
        self.export_button.setEnabled(False)
        
    def parse_current_image(self):
        """Parse the current disk image"""
        if not self.current_image_path:
            return
            
        # Stop any existing parsing
        if self.parse_thread and self.parse_thread.isRunning():
            self.parse_thread.stop()
            self.parse_thread.wait()
            
        # Clear current view
        self.clear_view()
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Parsing disk image...", 
            "Cancel", 
            0, 100, 
            self
        )
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.canceled.connect(self.cancel_parsing)
        
        # Start parsing thread
        self.parse_thread = FileSystemParseThread(self.current_image_path)
        self.parse_thread.progress.connect(self.update_progress)
        self.parse_thread.finished.connect(self.parsing_finished)
        self.parse_thread.entry_found.connect(self.add_file_entry)
        self.parse_thread.start()
        
        self.parse_button.setEnabled(False)
        
    def cancel_parsing(self):
        """Cancel the current parsing operation"""
        if self.parse_thread and self.parse_thread.isRunning():
            self.parse_thread.stop()
            
    def update_progress(self, value: int, message: str):
        """Update progress dialog"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(message)
            
    def parsing_finished(self, success: bool, error_message: str):
        """Handle parsing completion"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            
        self.parse_button.setEnabled(True)
        
        if success:
            self.status_label.setText(
                f"Parsed: {os.path.basename(self.current_image_path)} "
                f"({len(self.file_entries)} items)"
            )
            self.export_button.setEnabled(True)
        else:
            QMessageBox.critical(self, "Parsing Error", f"Failed to parse image:\n{error_message}")
            self.status_label.setText("Parsing failed")
            
    def add_file_entry(self, entry: FileEntry):
        """Add a file entry to the tree"""
        self.file_entries[entry.path] = entry
        
        # Get parent path
        parent_path = os.path.dirname(entry.path)
        if parent_path == entry.path:  # Root
            parent_item = None
        else:
            parent_item = self.tree_items.get(parent_path)
            
        # Create tree item
        item = QTreeWidgetItem()
        item.setText(0, entry.name)
        
        # Format size
        if entry.is_directory:
            item.setText(1, "")
            item.setText(3, "Directory")
        else:
            item.setText(1, self.format_size(entry.size))
            item.setText(3, "File")
            
        # Format modified time
        if entry.modified_time:
            item.setText(2, entry.modified_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            item.setText(2, "")
            
        # Style deleted items
        if entry.is_deleted:
            for col in range(4):
                item.setForeground(col, Qt.GlobalColor.red)
            item.setText(3, item.text(3) + " (Deleted)")
            
        # Add icon
        if entry.is_directory:
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        else:
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
            
        # Add to tree
        if parent_item:
            parent_item.addChild(item)
        else:
            self.file_tree.addTopLevelItem(item)
            
        self.tree_items[entry.path] = item
        
    def on_item_selected(self, item: QTreeWidgetItem, column: int):
        """Handle item selection"""
        # Find the file entry
        path = self.get_item_path(item)
        entry = self.file_entries.get(path)
        
        if entry:
            self.show_file_details(entry)
            
    def get_item_path(self, item: QTreeWidgetItem) -> str:
        """Get full path for a tree item"""
        parts = []
        current = item
        
        while current:
            parts.insert(0, current.text(0))
            current = current.parent()
            
        return "/" + "/".join(parts)
        
    def show_file_details(self, entry: FileEntry):
        """Show details for selected file"""
        # Clear current details
        self.info_table.setRowCount(0)
        self.hex_preview.clear()
        
        # Populate info table
        info_data = [
            ("Name", entry.name),
            ("Path", entry.path),
            ("Size", self.format_size(entry.size) if not entry.is_directory else "N/A"),
            ("Type", "Directory" if entry.is_directory else "File"),
            ("Deleted", "Yes" if entry.is_deleted else "No"),
            ("Created", entry.created_time.strftime("%Y-%m-%d %H:%M:%S") if entry.created_time else "N/A"),
            ("Modified", entry.modified_time.strftime("%Y-%m-%d %H:%M:%S") if entry.modified_time else "N/A"),
            ("Accessed", entry.accessed_time.strftime("%Y-%m-%d %H:%M:%S") if entry.accessed_time else "N/A"),
        ]
        
        if entry.mft_entry is not None:
            info_data.append(("MFT Entry", str(entry.mft_entry)))
            
        self.info_table.setRowCount(len(info_data))
        for i, (prop, value) in enumerate(info_data):
            self.info_table.setItem(i, 0, QTableWidgetItem(prop))
            self.info_table.setItem(i, 1, QTableWidgetItem(value))
            
        # Show hex preview for small files
        if not entry.is_directory and entry.size < 1024 * 1024:  # 1MB limit
            self.load_file_preview(entry)
            
    def load_file_preview(self, entry: FileEntry):
        """Load hex preview of file content"""
        if self.parse_thread and self.parse_thread.parser:
            content = self.parse_thread.parser.get_file_content(entry.path)
            if content:
                # Show first 512 bytes as hex
                hex_lines = []
                for i in range(0, min(len(content), 512), 16):
                    # Hex values
                    hex_part = " ".join(f"{b:02x}" for b in content[i:i+16])
                    # ASCII representation
                    ascii_part = "".join(
                        chr(b) if 32 <= b < 127 else "." 
                        for b in content[i:i+16]
                    )
                    hex_lines.append(f"{i:08x}  {hex_part:<48}  {ascii_part}")
                    
                self.hex_preview.setPlainText("\n".join(hex_lines))
                
    def show_context_menu(self, position):
        """Show context menu for tree items"""
        item = self.file_tree.itemAt(position)
        if not item:
            return
            
        path = self.get_item_path(item)
        entry = self.file_entries.get(path)
        
        if not entry:
            return
            
        menu = QMenu(self)
        
        # Export file action
        if not entry.is_directory:
            export_action = menu.addAction("Export File...")
            export_action.triggered.connect(lambda: self.export_file(entry))
            
        # Show properties
        props_action = menu.addAction("Properties")
        props_action.triggered.connect(lambda: self.show_file_details(entry))
        
        menu.exec(self.file_tree.mapToGlobal(position))
        
    def export_file(self, entry: FileEntry):
        """Export a single file"""
        if not self.parse_thread or not self.parse_thread.parser:
            QMessageBox.warning(self, "Export Error", "Parser not available")
            return
            
        # Get save location
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export File", 
            entry.name,
            "All Files (*.*)"
        )
        
        if save_path:
            try:
                content = self.parse_thread.parser.get_file_content(entry.path)
                if content is not None:
                    with open(save_path, 'wb') as f:
                        f.write(content)
                    QMessageBox.information(self, "Export Complete", f"File exported to:\n{save_path}")
                else:
                    QMessageBox.warning(self, "Export Error", "Failed to read file content")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export file:\n{str(e)}")
                
    def export_file_list(self):
        """Export the entire file list to CSV"""
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export File List",
            "file_list.csv",
            "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    # Write header
                    f.write("Path,Name,Size,Type,Deleted,Created,Modified,Accessed,MFT Entry\n")
                    
                    # Write entries
                    for path, entry in sorted(self.file_entries.items()):
                        f.write(f'"{entry.path}",')
                        f.write(f'"{entry.name}",')
                        f.write(f'{entry.size},')
                        f.write(f'{"Directory" if entry.is_directory else "File"},')
                        f.write(f'{"Yes" if entry.is_deleted else "No"},')
                        f.write(f'{entry.created_time.strftime("%Y-%m-%d %H:%M:%S") if entry.created_time else ""},')
                        f.write(f'{entry.modified_time.strftime("%Y-%m-%d %H:%M:%S") if entry.modified_time else ""},')
                        f.write(f'{entry.accessed_time.strftime("%Y-%m-%d %H:%M:%S") if entry.accessed_time else ""},')
                        f.write(f'{entry.mft_entry if entry.mft_entry is not None else ""}\n')
                        
                QMessageBox.information(self, "Export Complete", f"File list exported to:\n{save_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export file list:\n{str(e)}")

    def format_size(self, size: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
                
    def filter_tree(self):
        """Filter the tree based on search and filter criteria"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        size_filter = self.size_filter.currentText()
        
        # Define file type extensions
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico'}
        doc_exts = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx'}
        archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
        
        def should_show_item(item: QTreeWidgetItem, entry: FileEntry) -> bool:
            # Search filter
            if search_text and search_text not in entry.name.lower():
                return False
                
            # Type filter
            if filter_type == "Deleted Only" and not entry.is_deleted:
                return False
            elif filter_type == "Images" and not any(entry.name.lower().endswith(ext) for ext in image_exts):
                return False
            elif filter_type == "Documents" and not any(entry.name.lower().endswith(ext) for ext in doc_exts):
                return False
            elif filter_type == "Archives" and not any(entry.name.lower().endswith(ext) for ext in archive_exts):
                return False
                
            # Size filter
            if not entry.is_directory:
                if size_filter == "> 1MB" and entry.size <= 1024 * 1024:
                    return False
                elif size_filter == "> 10MB" and entry.size <= 10 * 1024 * 1024:
                    return False
                elif size_filter == "> 100MB" and entry.size <= 100 * 1024 * 1024:
                    return False
                elif size_filter == "< 1MB" and entry.size >= 1024 * 1024:
                    return False
                    
            return True
            
        def filter_item_recursive(item: QTreeWidgetItem) -> bool:
            path = self.get_item_path(item)
            entry = self.file_entries.get(path)
            
            if not entry:
                return False
                
            # Check if this item should be shown
            show_this = should_show_item(item, entry)
            
            # Check children
            child_visible = False
            for i in range(item.childCount()):
                child = item.child(i)
                if filter_item_recursive(child):
                    child_visible = True
                    
            # Show if this item matches or any child is visible
            visible = show_this or child_visible
            item.setHidden(not visible)
            
            return visible
            
        # Apply filter to all top level items
        for i in range(self.file_tree.topLevelItemCount()):
            filter_item_recursive(self.file_tree.topLevelItem(i))