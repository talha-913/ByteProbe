"""
File system viewer widget for displaying parsed disk contents with hash integration
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QLabel, QPushButton, QMessageBox, QProgressDialog,
    QMenu, QFileDialog, QTextEdit, QLineEdit, QComboBox,
    QDialog, QCheckBox  # Add QDialog and QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QFont

from core.parsers.pytsk_parser import get_parser, FileEntry
from core.forensics.hash_verifier import HashVerifier  # Add this import


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


class HashCalculationThread(QThread):
    """Thread for calculating hashes from disk image files"""
    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(dict)  # file_path -> hashes
    error = pyqtSignal(str)  # error message
    
    def __init__(self, file_entries: list, case_path: str, algorithms: list, parser):
        super().__init__()
        self.file_entries = file_entries
        self.case_path = case_path
        self.algorithms = algorithms
        self.parser = parser
        self._should_stop = False
        
    def run(self):
        """Calculate hashes for files using parser"""
        try:
            from core.forensics.hash_verifier import HashVerifier
            hash_verifier = HashVerifier(self.case_path)
            results = {}
            
            for i, entry in enumerate(self.file_entries):
                if self._should_stop:
                    break
                    
                self.progress.emit(f"Hashing {entry.name}... ({i+1}/{len(self.file_entries)})")
                
                try:
                    # Read file content through parser
                    file_content = self.parser.get_file_content(entry.path)
                    if file_content is not None:
                        # Calculate hash from file content
                        hashes = hash_verifier.calculate_data_hash(file_content, self.algorithms)
                        # Store hash with disk image path as identifier
                        hash_verifier.store_file_hash(entry.path, hashes, 'file_system')
                        results[entry.path] = hashes
                    else:
                        results[entry.path] = {"error": "Could not read file content"}
                        
                except Exception as e:
                    results[entry.path] = {"error": str(e)}
                    
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Hash calculation failed: {str(e)}")
            
    def stop(self):
        """Stop the hash calculation"""
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
        self.current_parser = None  # Store parser for file reading
        
        # Add hash-related attributes
        self.hash_verifier = None
        self.hash_thread = None
        
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
        
        # Initialize hash verifier when image is set
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'current_case_path'):
            self.hash_verifier = HashVerifier(self.main_window.current_case_path)
        
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
            # Store parser for file reading
            if self.parse_thread and hasattr(self.parse_thread, 'parser'):
                self.current_parser = self.parse_thread.parser
                
            # Create parsing marker for report generation
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'current_case_path'):
                case_path = self.main_window.current_case_path
                if case_path:
                    marker_path = os.path.join(case_path, ".file_system_parsed")
                    try:
                        with open(marker_path, 'w') as f:
                            f.write(f"Parsed: {self.current_image_path}\n")
                            f.write(f"Date: {datetime.now().isoformat()}\n")
                            f.write(f"Files: {len(self.file_entries)}\n")
                    except:
                        pass
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
        
        # Update left panel if main window reference exists
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'left_file_tree'):
            self._update_left_panel_tree(entry)
        
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
            
        # Add hash information if available
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'current_case_path') and self.main_window.current_case_path:
            hash_verifier = HashVerifier(self.main_window.current_case_path)
            stored_hashes = hash_verifier.get_file_hash(entry.path)
            
            if stored_hashes:
                info_data.extend([
                    ("", ""),  # Separator
                    ("--- Hash Information ---", ""),
                    ("MD5 Hash", stored_hashes.get('md5', 'N/A')),
                    ("SHA-1 Hash", stored_hashes.get('sha1', 'N/A')),
                    ("SHA-256 Hash", stored_hashes.get('sha256', 'N/A')),
                    ("SHA-512 Hash", stored_hashes.get('sha512', 'N/A')),
                    ("Hash Calculated", stored_hashes.get('calculated_at', 'N/A'))
                ])
            else:
                info_data.extend([
                    ("", ""),  # Separator  
                    ("Hash Status", "Not calculated - Right-click to calculate")
                ])
            
        self.info_table.setRowCount(len(info_data))
        for i, (prop, value) in enumerate(info_data):
            self.info_table.setItem(i, 0, QTableWidgetItem(prop))
            self.info_table.setItem(i, 1, QTableWidgetItem(value))
            
        # Show hex preview for small files
        if not entry.is_directory and entry.size < 1024 * 1024:  # 1MB limit
            self.load_file_preview(entry)
            
    def load_file_preview(self, entry: FileEntry):
        """Load hex preview of file content"""
        # Use stored parser or create new one
        if self.current_parser:
            try:
                # Reopen image if needed
                if not hasattr(self.current_parser, 'img_info') or self.current_parser.img_info is None:
                    self.current_parser.open_image(self.current_image_path)
                    self.current_parser.open_file_system()
                
                content = self.current_parser.get_file_content(entry.path)
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
                else:
                    self.hex_preview.setPlainText("Unable to read file content")
            except Exception as e:
                self.hex_preview.setPlainText(f"Error reading file: {str(e)}")
        else:
            self.hex_preview.setPlainText("Parser not available for file reading")
                
    def show_context_menu(self, position):
        """Show context menu for tree items"""
        try:
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
                export_action.triggered.connect(lambda checked, e=entry: self.export_file(e))
                
                # HASH ACTIONS
                menu.addSeparator()
                
                # Single file hash
                hash_action = menu.addAction("Calculate Hash (MD5 + SHA-256)")
                hash_action.triggered.connect(lambda checked, e=entry: self.calculate_file_hash(e))
                
                # Advanced hash options
                advanced_hash_action = menu.addAction("Advanced Hash Options...")
                advanced_hash_action.triggered.connect(lambda checked, e=entry: self.show_hash_options(e))
                
                # Verify integrity (if hash exists)
                if self.has_stored_hash(entry.path):
                    verify_action = menu.addAction("Verify File Integrity")
                    verify_action.triggered.connect(lambda checked, e=entry: self.verify_file_integrity(e))
            
            # Batch operations for multiple selections
            selected_items = self.file_tree.selectedItems()
            if len(selected_items) > 1:
                menu.addSeparator()
                batch_hash_action = menu.addAction(f"Calculate Hashes for {len(selected_items)} files")
                batch_hash_action.triggered.connect(self.calculate_batch_hashes)
                
            # Show properties
            menu.addSeparator()
            props_action = menu.addAction("Properties")
            props_action.triggered.connect(lambda checked, e=entry: self.show_file_details(e))
            
            menu.exec(self.file_tree.mapToGlobal(position))
            
        except Exception as e:
            print(f"Error in context menu: {e}")
            QMessageBox.critical(self, "Context Menu Error", f"Error showing context menu: {str(e)}")

    # HASH-RELATED METHODS
    def calculate_file_hash(self, entry):
        """Calculate hash for a single file"""
        try:
            # Validation checks
            if not hasattr(self, 'main_window') or not self.main_window.current_case_path:
                QMessageBox.warning(self, "No Case", "No active case for hash storage.")
                return
                
            if not self.current_parser:
                QMessageBox.warning(self, "Parser Error", "No active parser for reading disk image.")
                return
            
            # Start hash calculation with progress dialog
            self.start_hash_calculation([entry], ['md5', 'sha256'])
            
        except Exception as e:
            QMessageBox.critical(self, "Hash Error", f"Error starting hash calculation: {str(e)}")

    def show_hash_options(self, entry):
        """Show advanced hash options dialog"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Hash Options")
            dialog.setFixedSize(300, 250)
            
            layout = QVBoxLayout()
            
            layout.addWidget(QLabel(f"File: {entry.name}"))
            layout.addWidget(QLabel("Select hash algorithms:"))
            
            # Algorithm checkboxes
            md5_cb = QCheckBox("MD5")
            md5_cb.setChecked(True)
            sha1_cb = QCheckBox("SHA-1")
            sha256_cb = QCheckBox("SHA-256")
            sha256_cb.setChecked(True)
            sha512_cb = QCheckBox("SHA-512")
            
            layout.addWidget(md5_cb)
            layout.addWidget(sha1_cb)
            layout.addWidget(sha256_cb)
            layout.addWidget(sha512_cb)
            
            # Buttons
            button_layout = QHBoxLayout()
            calculate_btn = QPushButton("Calculate")
            cancel_btn = QPushButton("Cancel")
            
            def on_calculate():
                algorithms = []
                if md5_cb.isChecked(): algorithms.append('md5')
                if sha1_cb.isChecked(): algorithms.append('sha1')
                if sha256_cb.isChecked(): algorithms.append('sha256')
                if sha512_cb.isChecked(): algorithms.append('sha512')
                
                if algorithms:
                    dialog.accept()
                    self.start_hash_calculation([entry], algorithms)
                else:
                    QMessageBox.warning(dialog, "No Algorithms", "Please select at least one algorithm.")
                    
            calculate_btn.clicked.connect(on_calculate)
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(calculate_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Dialog Error", f"Error showing hash options: {str(e)}")

    def calculate_batch_hashes(self):
        """Calculate hashes for multiple selected files"""
        try:
            selected_items = self.file_tree.selectedItems()
            file_entries = []
            
            for item in selected_items:
                path = self.get_item_path(item)
                entry = self.file_entries.get(path)
                if entry and not entry.is_directory:
                    file_entries.append(entry)
            
            if not file_entries:
                QMessageBox.information(self, "No Files", "No valid files selected for hashing.")
                return
                
            if not hasattr(self, 'main_window') or not self.main_window.current_case_path:
                QMessageBox.warning(self, "No Case", "No active case for hash storage.")
                return
            
            if not self.current_parser:
                QMessageBox.warning(self, "Parser Error", "No active parser for reading disk image.")
                return
            
            # Confirm batch operation
            reply = QMessageBox.question(
                self, "Batch Hash Calculation",
                f"Calculate MD5 and SHA-256 hashes for {len(file_entries)} files?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.start_hash_calculation(file_entries, ['md5', 'sha256'])
                
        except Exception as e:
            QMessageBox.critical(self, "Batch Hash Error", f"Error in batch hash calculation: {str(e)}")

    def start_hash_calculation(self, file_entries, algorithms):
        """Start hash calculation with progress dialog"""
        try:
            # Create and start hash thread
            self.hash_thread = HashCalculationThread(
                file_entries,
                self.main_window.current_case_path,
                algorithms,
                self.current_parser
            )
            
            # Create progress dialog
            self.hash_progress_dialog = QProgressDialog("Calculating hashes...", "Cancel", 0, 0, self)
            self.hash_progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.hash_progress_dialog.setMinimumDuration(0)
            self.hash_progress_dialog.canceled.connect(self.hash_thread.stop)
            
            # Connect signals
            self.hash_thread.progress.connect(self.hash_progress_dialog.setLabelText)
            self.hash_thread.finished.connect(self.on_hash_complete)
            self.hash_thread.error.connect(self.on_hash_error)
            
            # Start thread
            self.hash_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Thread Error", f"Error starting hash thread: {str(e)}")

    def on_hash_complete(self, results):
        """Handle hash calculation completion"""
        try:
            if hasattr(self, 'hash_progress_dialog'):
                self.hash_progress_dialog.close()
            
            successful = []
            errors = []
            
            for file_path, hashes in results.items():
                if "error" in hashes:
                    errors.append(f"{os.path.basename(file_path)}: {hashes['error']}")
                else:
                    successful.append(file_path)
            
            # Show results
            if successful:
                if len(successful) == 1:
                    # Single file - show detailed hash info
                    file_path = successful[0]
                    hashes = results[file_path]
                    hash_info = f"File: {os.path.basename(file_path)}\n\n"
                    for alg, hash_value in hashes.items():
                        hash_info += f"{alg.upper()}: {hash_value}\n"
                    QMessageBox.information(self, "Hash Complete", hash_info)
                else:
                    # Multiple files - show summary
                    QMessageBox.information(self, "Batch Hash Complete", 
                                        f"Successfully hashed {len(successful)} files.")
            
            if errors:
                error_msg = "Errors occurred:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... and {len(errors) - 5} more errors"
                QMessageBox.warning(self, "Hash Errors", error_msg)
            
            # Refresh file details if currently selected file was hashed
            selected_item = self.file_tree.currentItem()
            if selected_item:
                selected_path = self.get_item_path(selected_item)
                if selected_path in successful:
                    entry = self.file_entries.get(selected_path)
                    if entry:
                        self.show_file_details(entry)
                        
        except Exception as e:
            QMessageBox.critical(self, "Result Error", f"Error processing hash results: {str(e)}")

    def on_hash_error(self, error_message):
        """Handle hash calculation error"""
        try:
            if hasattr(self, 'hash_progress_dialog'):
                self.hash_progress_dialog.close()
            QMessageBox.critical(self, "Hash Calculation Error", error_message)
        except Exception as e:
            print(f"Error in hash error handler: {e}")

    def has_stored_hash(self, file_path: str) -> bool:
        """Check if file has stored hash"""
        try:
            if not hasattr(self, 'main_window') or not self.main_window.current_case_path:
                return False
                
            from core.forensics.hash_verifier import HashVerifier
            hash_verifier = HashVerifier(self.main_window.current_case_path)
            stored_hash = hash_verifier.get_file_hash(file_path)
            return stored_hash is not None
        except:
            return False

    def verify_file_integrity(self, entry):
        """Verify file integrity against stored hash"""
        try:
            if not hasattr(self, 'main_window') or not self.main_window.current_case_path:
                QMessageBox.warning(self, "No Case", "No active case for verification.")
                return
                
            if not self.current_parser:
                QMessageBox.warning(self, "Parser Error", "No active parser for reading disk image.")
                return
                
            from core.forensics.hash_verifier import HashVerifier
            hash_verifier = HashVerifier(self.main_window.current_case_path)
            stored_hashes = hash_verifier.get_file_hash(entry.path)
            
            if not stored_hashes:
                QMessageBox.information(self, "No Hash Found", "No stored hash found for this file.")
                return
            
            # Read file content and calculate current hash
            file_content = self.current_parser.get_file_content(entry.path)
            if file_content is None:
                QMessageBox.warning(self, "Read Error", "Cannot read file content from disk image.")
                return
                
            current_hashes = hash_verifier.calculate_data_hash(file_content, ['md5', 'sha256'])
            
            # Compare hashes
            results = []
            for alg in ['md5', 'sha256']:
                if stored_hashes.get(alg) and current_hashes.get(alg):
                    match = stored_hashes[alg].lower() == current_hashes[alg].lower()
                    results.append(f"{alg.upper()}: {'✓ MATCH' if match else '✗ MISMATCH'}")
            
            if results:
                QMessageBox.information(self, "Integrity Verification", 
                                    f"File: {entry.name}\n\n" + "\n".join(results))
            else:
                QMessageBox.warning(self, "Verification Error", "No matching hash algorithms found.")
                
        except Exception as e:
            QMessageBox.critical(self, "Verification Error", f"Error verifying file integrity: {str(e)}")
            
        def export_file(self, entry: FileEntry):
            """Export a single file"""
            if not self.current_parser:
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
                    # Reopen image if needed
                    if not hasattr(self.current_parser, 'img_info') or self.current_parser.img_info is None:
                        self.current_parser.open_image(self.current_image_path)
                        self.current_parser.open_file_system()
                        
                    content = self.current_parser.get_file_content(entry.path)
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
        
    def _update_left_panel_tree(self, entry: FileEntry):
        """Update the left panel file tree"""
        if not hasattr(self, 'main_window') or not hasattr(self.main_window, 'left_file_tree'):
            return
            
        # Only add directories to left panel for cleaner view
        if not entry.is_directory:
            return
            
        # Find parent
        parent_path = os.path.dirname(entry.path)
        parent_item = None
        
        if parent_path != entry.path:
            # Search for parent item
            for i in range(self.main_window.left_file_tree.topLevelItemCount()):
                parent_item = self._find_tree_item(self.main_window.left_file_tree.topLevelItem(i), parent_path)
                if parent_item:
                    break
                    
        # Create new item
        item = QTreeWidgetItem()
        item.setText(0, entry.name)
        item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        item.setData(0, Qt.ItemDataRole.UserRole, entry.path)
        
        if entry.is_deleted:
            item.setForeground(0, Qt.GlobalColor.red)
            
        # Add to tree
        if parent_item:
            parent_item.addChild(item)
        else:
            self.main_window.left_file_tree.addTopLevelItem(item)
            
    def _find_tree_item(self, item: QTreeWidgetItem, path: str) -> Optional[QTreeWidgetItem]:
        """Find a tree item by path"""
        if item.data(0, Qt.ItemDataRole.UserRole) == path:
            return item
            
        for i in range(item.childCount()):
            result = self._find_tree_item(item.child(i), path)
            if result:
                return result
                
        return None
                
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