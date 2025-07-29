"""
File carver widget for integrated file carving in main window
"""
import os
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.parsers.pytsk_parser import get_parser
from core.forensics.file_carver import SmartFileCarver
from core.forensics.file_signatures import get_supported_types


class FileCarverWidget(QWidget):
    """Widget for file carving operations integrated into main window"""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.current_image_path = None
        self.carver_thread = None
        self.carved_files = []
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Control panel
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Current Image:"))
        self.image_label = QLabel("No image selected")
        control_layout.addWidget(self.image_label)
        control_layout.addStretch()
        
        self.start_btn = QPushButton("Start Carving")
        self.start_btn.clicked.connect(self.start_carving)
        self.start_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_carving)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Select a disk image from Data Sources to begin")
        layout.addWidget(self.status_label)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # File type selection
        types_group = QGroupBox("File Types to Carve")
        types_layout = QVBoxLayout()
        
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self.toggle_all_types)
        types_layout.addWidget(self.select_all_cb)
        
        self.type_checkboxes = {}
        supported_types = get_supported_types()
        
        for file_type in supported_types:
            cb = QCheckBox(f"{file_type.upper()} files")
            cb.setChecked(file_type in ['jpg', 'pdf', 'docx'])
            self.type_checkboxes[file_type] = cb
            types_layout.addWidget(cb)
            
        types_layout.addStretch()
        types_group.setLayout(types_layout)
        splitter.addWidget(types_group)
        
        # Results table
        results_group = QGroupBox("Carved Files")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Filename", "Type", "Size", "Offset", "Status"])
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        splitter.addWidget(results_group)
        
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        
    def set_disk_image(self, image_path: str):
        """Set the disk image to carve from"""
        if os.path.exists(image_path):
            self.current_image_path = image_path
            self.image_label.setText(os.path.basename(image_path))
            self.start_btn.setEnabled(True)
            self.status_label.setText("Ready to start carving")
            
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
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "Please select a disk image from Data Sources")
            return
            
        selected_types = self.get_selected_types()
        if not selected_types:
            QMessageBox.warning(self, "No File Types", "Please select at least one file type")
            return
            
        # Get output directory
        if hasattr(self.main_window, 'current_case_path') and self.main_window.current_case_path:
            output_dir = os.path.join(self.main_window.current_case_path, "carved_files")
        else:
            output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if not output_dir:
                return
                
        # Clear previous results
        self.results_table.setRowCount(0)
        self.carved_files.clear()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Start carving thread
        from core.forensics.threads import FileCarverThread
        self.carver_thread = FileCarverThread(self.current_image_path, output_dir, selected_types)
        self.carver_thread.progress.connect(self.update_progress)
        self.carver_thread.file_carved.connect(self.add_carved_file)
        self.carver_thread.finished.connect(self.carving_finished)
        self.carver_thread.start()
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
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
        
        if success:
            self.status_label.setText(f"Carving complete! {message}")
        else:
            self.status_label.setText(f"Carving failed: {message}")
            
    def format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def update_from_data_source(self, source_path: str, source_type: str):
        """Update widget when a data source is selected"""
        if source_type == "Disk Image":
            self.set_disk_image(source_path)