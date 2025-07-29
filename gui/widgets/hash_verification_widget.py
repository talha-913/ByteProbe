"""
Hash verification widget for file integrity checking
"""
import os
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGroupBox, QCheckBox, QProgressBar,
    QMessageBox, QFileDialog, QTextEdit, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.forensics.hash_verifier import HashVerifier


class HashCalculationThread(QThread):
    """Thread for calculating hashes in background"""
    
    progress = pyqtSignal(int, int, str)  # current, total, message
    hash_calculated = pyqtSignal(str, dict)  # file_path, hashes
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, file_paths: List[str], algorithms: List[str], hash_verifier: HashVerifier):
        super().__init__()
        self.file_paths = file_paths
        self.algorithms = algorithms
        self.hash_verifier = hash_verifier
        self._should_stop = False
        
    def run(self):
        """Run hash calculation"""
        try:
            total_files = len(self.file_paths)
            
            for i, file_path in enumerate(self.file_paths):
                if self._should_stop:
                    break
                    
                self.progress.emit(i, total_files, f"Hashing: {os.path.basename(file_path)}")
                
                try:
                    hashes = self.hash_verifier.calculate_file_hash(file_path, self.algorithms)
                    self.hash_calculated.emit(file_path, hashes)
                    
                    # Store in database
                    self.hash_verifier.store_file_hash(file_path, hashes)
                    
                except Exception as e:
                    self.hash_calculated.emit(file_path, {"error": str(e)})
                    
            if not self._should_stop:
                self.progress.emit(total_files, total_files, "Hash calculation complete")
                self.finished.emit(True, f"Successfully calculated hashes for {total_files} files")
            else:
                self.finished.emit(False, "Hash calculation cancelled")
                
        except Exception as e:
            self.finished.emit(False, f"Error during hash calculation: {str(e)}")
            
    def stop(self):
        """Stop hash calculation"""
        self._should_stop = True


class HashVerificationWidget(QWidget):
    """Widget for hash verification and integrity checking"""
    
    def __init__(self, case_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.case_path = case_path
        self.hash_verifier = HashVerifier(case_path)
        self.hash_thread = None
        self.selected_files = []
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Algorithm selection
        self.algorithms_group = QGroupBox("Hash Algorithms")
        alg_layout = QHBoxLayout()
        
        self.md5_cb = QCheckBox("MD5")
        self.md5_cb.setChecked(True)
        alg_layout.addWidget(self.md5_cb)
        
        self.sha1_cb = QCheckBox("SHA-1")
        alg_layout.addWidget(self.sha1_cb)
        
        self.sha256_cb = QCheckBox("SHA-256")
        self.sha256_cb.setChecked(True)
        alg_layout.addWidget(self.sha256_cb)
        
        self.sha512_cb = QCheckBox("SHA-512")
        alg_layout.addWidget(self.sha512_cb)
        
        self.algorithms_group.setLayout(alg_layout)
        control_layout.addWidget(self.algorithms_group)
        
        control_layout.addStretch()
        
        # Action buttons
        self.calculate_btn = QPushButton("Calculate Hashes")
        self.calculate_btn.clicked.connect(self.calculate_selected_hashes)
        control_layout.addWidget(self.calculate_btn)
        
        self.verify_btn = QPushButton("Verify Integrity")
        self.verify_btn.clicked.connect(self.verify_file_integrity)
        control_layout.addWidget(self.verify_btn)
        
        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self.export_hash_report)
        control_layout.addWidget(self.export_btn)
        
        layout.addLayout(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Select files from File System tab to calculate hashes")
        layout.addWidget(self.status_label)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # File hashes tab
        self.hash_table = QTableWidget()
        self.hash_table.setColumnCount(6)
        self.hash_table.setHorizontalHeaderLabels([
            "File Path", "Size", "MD5", "SHA-256", "Status", "Calculated"
        ])
        self.hash_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hash_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Enable text selection for copying hashes
        self.hash_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.hash_table.customContextMenuRequested.connect(self.show_hash_context_menu)
        
        self.tab_widget.addTab(self.hash_table, "File Hashes")
        
        # Verification results tab
        self.verification_text = QTextEdit()
        self.verification_text.setReadOnly(True)
        self.verification_text.setFont(QFont("Courier", 9))
        self.tab_widget.addTab(self.verification_text, "Verification Results")
        
        # Statistics tab
        self.stats_widget = self.create_statistics_widget()
        self.tab_widget.addTab(self.stats_widget, "Statistics")
        
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Load existing hashes if case is active
        if self.case_path:
            self.load_existing_hashes()
            
    def create_statistics_widget(self) -> QWidget:
        """Create statistics display widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        layout.addWidget(QLabel("Hash Database Statistics:"))
        layout.addWidget(self.stats_text)
        
        # Hash comparison
        comparison_group = QGroupBox("Hash Comparison")
        comp_layout = QVBoxLayout()
        
        comp_button_layout = QHBoxLayout()
        self.load_comparison_btn = QPushButton("Load Hash Set...")
        self.load_comparison_btn.clicked.connect(self.load_comparison_hashes)
        comp_button_layout.addWidget(self.load_comparison_btn)
        
        self.compare_btn = QPushButton("Compare")
        self.compare_btn.clicked.connect(self.compare_hash_sets)
        comp_button_layout.addWidget(self.compare_btn)
        comp_button_layout.addStretch()
        
        comp_layout.addLayout(comp_button_layout)
        
        self.comparison_results = QTextEdit()
        self.comparison_results.setReadOnly(True)
        self.comparison_results.setMaximumHeight(150)
        comp_layout.addWidget(self.comparison_results)
        
        comparison_group.setLayout(comp_layout)
        layout.addWidget(comparison_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        return widget
        
    def set_selected_files(self, file_paths: List[str]):
        """Set the list of selected files for hash calculation"""
        self.selected_files = file_paths
        if file_paths:
            self.status_label.setText(f"{len(file_paths)} file(s) selected for hashing")
            self.calculate_btn.setEnabled(True)
        else:
            self.status_label.setText("No files selected")
            self.calculate_btn.setEnabled(False)
            
    def get_selected_algorithms(self) -> List[str]:
        """Get list of selected hash algorithms"""
        algorithms = []
        if self.md5_cb.isChecked():
            algorithms.append('md5')
        if self.sha1_cb.isChecked():
            algorithms.append('sha1')
        if self.sha256_cb.isChecked():
            algorithms.append('sha256')
        if self.sha512_cb.isChecked():
            algorithms.append('sha512')
        return algorithms
        
    def calculate_selected_hashes(self):
        """Calculate hashes for selected files"""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files Selected", 
                              "Please select files from the File System tab first.")
            return
            
        algorithms = self.get_selected_algorithms()
        if not algorithms:
            QMessageBox.warning(self, "No Algorithms Selected", 
                              "Please select at least one hash algorithm.")
            return
            
        # Start hash calculation thread
        self.hash_thread = HashCalculationThread(
            self.selected_files, algorithms, self.hash_verifier
        )
        self.hash_thread.progress.connect(self.update_progress)
        self.hash_thread.hash_calculated.connect(self.add_hash_result)
        self.hash_thread.finished.connect(self.hash_calculation_finished)
        self.hash_thread.start()
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.calculate_btn.setEnabled(False)
        
    def update_progress(self, current: int, total: int, message: str):
        """Update progress display"""
        if total > 0:
            self.progress_bar.setValue(int((current / total) * 100))
        self.status_label.setText(message)
        
    def add_hash_result(self, file_path: str, hashes: Dict[str, str]):
        """Add hash result to table"""
        row = self.hash_table.rowCount()
        self.hash_table.insertRow(row)
        
        # File path
        self.hash_table.setItem(row, 0, QTableWidgetItem(file_path))
        
        # File size
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            size_text = self.format_size(size)
        else:
            size_text = "N/A"
        self.hash_table.setItem(row, 1, QTableWidgetItem(size_text))
        
        # Hashes
        if "error" in hashes:
            self.hash_table.setItem(row, 2, QTableWidgetItem("Error"))
            self.hash_table.setItem(row, 3, QTableWidgetItem("Error"))
            status_item = QTableWidgetItem("Error")
            status_item.setForeground(QColor(255, 0, 0))
            self.hash_table.setItem(row, 4, status_item)
        else:
            self.hash_table.setItem(row, 2, QTableWidgetItem(hashes.get('md5', '')))
            self.hash_table.setItem(row, 3, QTableWidgetItem(hashes.get('sha256', '')))
            status_item = QTableWidgetItem("Complete")
            status_item.setForeground(QColor(0, 150, 0))
            self.hash_table.setItem(row, 4, status_item)
            
        # Timestamp
        from datetime import datetime
        self.hash_table.setItem(row, 5, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Auto-resize columns
        self.hash_table.resizeColumnsToContents()
        
    def hash_calculation_finished(self, success: bool, message: str):
        """Handle hash calculation completion"""
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(message)
            self.update_statistics()
        else:
            QMessageBox.critical(self, "Hash Calculation Error", message)
            
    def verify_file_integrity(self):
        """Verify integrity of selected files against stored hashes"""
        # This would implement integrity verification
        QMessageBox.information(self, "Verification", 
                              "Integrity verification functionality will be implemented.")
        
    def export_hash_report(self):
        """Export hash report"""
        if not self.case_path:
            QMessageBox.warning(self, "No Case", "No active case for hash export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Hash Report", 
            os.path.join(self.case_path, "hash_report.csv"),
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)"
        )
        
        if file_path:
            format_type = 'json' if file_path.lower().endswith('.json') else 'csv'
            success = self.hash_verifier.export_hash_report(file_path, format_type)
            
            if success:
                QMessageBox.information(self, "Export Complete", 
                                      f"Hash report exported to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Export Error", "Failed to export hash report.")
                
    def load_existing_hashes(self):
        """Load existing hashes from database"""
        # This would load and display existing hashes
        self.update_statistics()
        
    def update_statistics(self):
        """Update hash statistics display"""
        if not self.hash_verifier.hash_db_path:
            return
            
        try:
            import sqlite3
            conn = sqlite3.connect(self.hash_verifier.hash_db_path)
            cursor = conn.cursor()
            
            # Get basic statistics
            cursor.execute("SELECT COUNT(*) FROM file_hashes")
            total_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM file_hashes WHERE source_type = 'carved'")
            carved_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM file_hashes WHERE source_type = 'file_system'")
            fs_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(file_size) FROM file_hashes WHERE file_size IS NOT NULL")
            total_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            stats_text = f"""Total Hashed Files: {total_files}
File System Files: {fs_files}
Carved Files: {carved_files}
Total Data Size: {self.format_size(total_size)}

Hash Distribution:
- Files with MD5: {total_files}
- Files with SHA-256: {total_files}
"""
            
            self.stats_text.setPlainText(stats_text)
            
        except Exception as e:
            self.stats_text.setPlainText(f"Error loading statistics: {e}")
            
    def format_size(self, size: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
        
    def show_hash_context_menu(self, position):
        """Show context menu for hash table"""
        # Implementation for copying hashes, etc.
        pass
        
    def load_comparison_hashes(self):
        """Load external hash set for comparison"""
        # Implementation for loading external hash files
        pass
        
    def compare_hash_sets(self):
        """Compare current hashes with loaded set"""
        # Implementation for hash set comparison
        pass
        
    def update_case_path(self, case_path: Optional[str]):
        """Update the case path and reinitialize hash verifier"""
        self.case_path = case_path
        self.hash_verifier = HashVerifier(case_path)
        if case_path:
            self.load_existing_hashes()