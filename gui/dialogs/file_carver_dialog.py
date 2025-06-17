"""
File carver dialog for recovering deleted files
"""
import os
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QListWidget, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QListWidgetItem,
    QDialogButtonBox, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.parsers.pytsk_parser import get_parser
from core.forensics.file_carver import SmartFileCarver
from core.forensics.file_signatures import get_supported_types


class FileCarverThread(QThread):
    """Thread for file carving operation"""
    
    progress = pyqtSignal(int, str)
    file_carved = pyqtSignal(dict)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, image_path: str, output_dir: str, file_types: List[str]):
        super().__init__()
        self.image_path = image_path
        self.output_dir = output_dir
        self.file_types = file_types
        self.carver = None
        
    def run(self):
        """Run the carving process"""
        try:
            parser = get_parser()
            self.carver = SmartFileCarver(parser)
            
            def progress_callback(percent, message):
                self.progress.emit(percent, message)
                
            # Carve files
            carved_files = self.carver.carve_files(
                self.image_path,
                self.output_dir,
                self.file_types,
                progress_callback
            )
            
            # Emit each carved file
            for file_info in carved_files:
                self.file_carved.emit(file_info)
                
            self.finished.emit(True, f"Successfully carved {len(carved_files)} files")
            
        except Exception as e:
            self.finished.emit(False, str(e))
            
    def stop(self):
        """Stop the carving process"""
        if self.carver:
            self.carver.stop_carving()


class FileCarverDialog(QDialog):
    """Dialog for file carving operations"""
    
    def __init__(self, parent=None, image_path: str = None, case_path: str = None):
        super().__init__(parent)
        self.image_path = image_path
        self.case_path = case_path
        self.output_dir = None
        self.carver_thread = None
        self.carved_files = []
        
        self.setWindowTitle("File Carver")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Image selection
        image_group = QGroupBox("Disk Image")
        image_layout = QHBoxLayout()
        
        self.image_label = QLabel(self.image_path or "No image selected")
        image_layout.addWidget(self.image_label)
        
        self.browse_image_btn = QPushButton("Browse...")
        self.browse_image_btn.clicked.connect(self.browse_image)
        image_layout.addWidget(self.browse_image_btn)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # Output directory
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout()
        
        self.output_label = QLabel("Not selected")
        output_layout.addWidget(self.output_label)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(self.browse_output_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # File type selection
        types_group = QGroupBox("File Types to Carve")
        types_layout = QVBoxLayout()
        
        # Select all checkbox
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self.toggle_all_types)
        types_layout.addWidget(self.select_all_cb)
        
        # File type checkboxes
        self.type_checkboxes = {}
        supported_types = get_supported_types()
        
        for file_type in supported_types:
            cb = QCheckBox(f"{file_type.upper()} files")
            cb.setChecked(file_type in ['jpg', 'pdf', 'docx'])  # Default selection
            self.type_checkboxes[file_type] = cb
            types_layout.addWidget(cb)
            
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to start carving")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Results table
        results_group = QGroupBox("Carved Files")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Filename", "Type", "Size", "Offset", "Status"])
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Carving")
        self.start_btn.clicked.connect(self.start_carving)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_carving)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Set default output directory if case path is provided
        if self.case_path:
            default_output = os.path.join(self.case_path, "carved_files")
            self.output_dir = default_output
            self.output_label.setText(default_output)
            
    def browse_image(self):
        """Browse for disk image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Disk Image",
            "",
            "Disk Images (*.dd *.img *.raw *.e01);;All Files (*.*)"
        )
        
        if file_path:
            self.image_path = file_path
            self.image_label.setText(os.path.basename(file_path))
            
    def browse_output(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir or ""
        )
        
        if dir_path:
            self.output_dir = dir_path
            self.output_label.setText(dir_path)
            
    def toggle_all_types(self, state):
        """Toggle all file type checkboxes"""
        checked = state == Qt.CheckState.Checked.value
        for cb in self.type_checkboxes.values():
            cb.setChecked(checked)
            
    def get_selected_types(self) -> List[str]:
        """Get list of selected file types"""
        return [ft for ft, cb in self.type_checkboxes.items() if cb.isChecked()]
        
    def start_carving(self):
        """Start the carving process"""
        # Validate inputs
        if not self.image_path:
            QMessageBox.warning(self, "No Image", "Please select a disk image")
            return
            
        if not self.output_dir:
            QMessageBox.warning(self, "No Output Directory", "Please select an output directory")
            return
            
        selected_types = self.get_selected_types()
        if not selected_types:
            QMessageBox.warning(self, "No File Types", "Please select at least one file type")
            return
            
        # Clear previous results
        self.results_table.setRowCount(0)
        self.carved_files.clear()
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Start carving thread
        self.carver_thread = FileCarverThread(self.image_path, self.output_dir, selected_types)
        self.carver_thread.progress.connect(self.update_progress)
        self.carver_thread.file_carved.connect(self.add_carved_file)
        self.carver_thread.finished.connect(self.carving_finished)
        self.carver_thread.start()
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.browse_image_btn.setEnabled(False)
        self.browse_output_btn.setEnabled(False)
        
    def stop_carving(self):
        """Stop the carving process"""
        if self.carver_thread and self.carver_thread.isRunning():
            self.carver_thread.stop()
            self.status_label.setText("Stopping...")
            
    def update_progress(self, percent: int, message: str):
        """Update progress display"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        
    def add_carved_file(self, file_info: Dict[str, Any]):
        """Add a carved file to the results"""
        self.carved_files.append(file_info)
        
        # Add to table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(file_info['filename']))
        self.results_table.setItem(row, 1, QTableWidgetItem(file_info['type'].upper()))
        self.results_table.setItem(row, 2, QTableWidgetItem(self.format_size(file_info['size'])))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"0x{file_info['offset']:X}"))
        
        status = "Complete" if file_info.get('footer_found', False) else "Partial"
        self.results_table.setItem(row, 4, QTableWidgetItem(status))
        
    def carving_finished(self, success: bool, message: str):
        """Handle carving completion"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.browse_image_btn.setEnabled(True)
        self.browse_output_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Carving Complete", message)
        else:
            QMessageBox.critical(self, "Carving Error", f"Error during carving: {message}")
            
    def format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"