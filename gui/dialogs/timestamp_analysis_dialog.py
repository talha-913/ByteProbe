"""
Timestamp analysis dialog for detecting NTFS timestamp manipulation
"""
import os
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QSplitter,
    QHeaderView, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.parsers.pytsk_parser import get_parser
from core.forensics.timestamp_analyzer import NTFSTimestampAnalyzer, TimestampReport


class TimestampAnalysisThread(QThread):
    """Thread for timestamp analysis"""
    
    progress = pyqtSignal(int, str)
    file_analyzed = pyqtSignal(dict)
    finished = pyqtSignal(dict)
    
    def __init__(self, image_path: str, target_path: str = "/"):
        super().__init__()
        self.image_path = image_path
        self.target_path = target_path
        self.analyzer = NTFSTimestampAnalyzer()
        
    def run(self):
        """Run the analysis"""
        try:
            parser = get_parser()
            
            self.progress.emit(10, "Opening disk image...")
            if not parser.open_image(self.image_path):
                raise Exception("Failed to open disk image")
                
            self.progress.emit(20, "Opening file system...")
            if not parser.open_file_system():
                raise Exception("Failed to open file system")
                
            self.progress.emit(30, "Collecting files...")
            
            # Collect all files
            all_files = []
            file_count = 0
            
            for entry in parser.walk_file_system():
                all_files.append(entry)
                file_count += 1
                
                if file_count % 100 == 0:
                    self.progress.emit(
                        min(30 + (file_count // 10), 70),
                        f"Found {file_count} files..."
                    )
                    
            # Analyze files
            self.progress.emit(70, "Analyzing timestamps...")
            results = self.analyzer.analyze_directory(all_files)
            
            # Emit individual suspicious files
            for suspicious_file in results['suspicious_files']:
                self.file_analyzed.emit(suspicious_file)
                
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(results)
            
        except Exception as e:
            self.finished.emit({'error': str(e)})
        finally:
            parser.close()


class TimestampAnalysisDialog(QDialog):
    """Dialog for timestamp manipulation analysis"""
    
    def __init__(self, parent=None, image_path: str = None):
        super().__init__(parent)
        self.image_path = image_path
        self.analysis_thread = None
        self.analysis_results = None
        
        self.setWindowTitle("Timestamp Analysis")
        self.setModal(True)
        self.resize(900, 700)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Image selection
        image_layout = QHBoxLayout()
        image_layout.addWidget(QLabel("Disk Image:"))
        
        self.image_label = QLabel(self.image_path or "No image selected")
        image_layout.addWidget(self.image_label)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_image)
        image_layout.addWidget(self.browse_btn)
        
        image_layout.addStretch()
        layout.addLayout(image_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to analyze")
        layout.addWidget(self.status_label)
        
        # Results splitter
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Suspicious files table
        files_group = QGroupBox("Suspicious Files")
        files_layout = QVBoxLayout()
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["File Path", "Confidence", "Anomalies", "Severity"])
        self.files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.files_table.itemSelectionChanged.connect(self.on_file_selected)
        
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        files_layout.addWidget(self.files_table)
        files_group.setLayout(files_layout)
        self.splitter.addWidget(files_group)
        
        # Details
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Courier", 9))
        
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        self.splitter.addWidget(details_group)
        
        layout.addWidget(self.splitter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("Start Analysis")
        self.analyze_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.analyze_btn)
        
        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
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
            
    def start_analysis(self):
        """Start timestamp analysis"""
        if not self.image_path:
            QMessageBox.warning(self, "No Image", "Please select a disk image")
            return
            
        # Clear previous results
        self.files_table.setRowCount(0)
        self.details_text.clear()
        
        # Start analysis thread
        self.analysis_thread = TimestampAnalysisThread(self.image_path)
        self.analysis_thread.progress.connect(self.update_progress)
        self.analysis_thread.file_analyzed.connect(self.add_suspicious_file)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.start()
        
        # Update UI
        self.analyze_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        
    def update_progress(self, value: int, message: str):
        """Update progress"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def add_suspicious_file(self, file_result: Dict[str, Any]):
        """Add a suspicious file to the table"""
        row = self.files_table.rowCount()
        self.files_table.insertRow(row)
        
        # File path
        self.files_table.setItem(row, 0, QTableWidgetItem(file_result['file_path']))
        
        # Confidence
        confidence_item = QTableWidgetItem(f"{file_result['confidence']:.1%}")
        if file_result['confidence'] >= 0.7:
            confidence_item.setForeground(QColor(255, 0, 0))  # Red for high confidence
        elif file_result['confidence'] >= 0.4:
            confidence_item.setForeground(QColor(255, 140, 0))  # Orange for medium
        self.files_table.setItem(row, 1, confidence_item)
        
        # Anomaly count
        anomaly_count = len(file_result['anomalies'])
        self.files_table.setItem(row, 2, QTableWidgetItem(str(anomaly_count)))
        
        # Max severity
        severities = [a['severity'] for a in file_result['anomalies']]
        max_severity = 'high' if 'high' in severities else 'medium' if 'medium' in severities else 'low'
        severity_item = QTableWidgetItem(max_severity.capitalize())
        
        if max_severity == 'high':
            severity_item.setForeground(QColor(255, 0, 0))
        elif max_severity == 'medium':
            severity_item.setForeground(QColor(255, 140, 0))
            
        self.files_table.setItem(row, 3, severity_item)
        
        # Store full result in item data
        self.files_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, file_result)
        
    def on_file_selected(self):
        """Handle file selection"""
        current_row = self.files_table.currentRow()
        if current_row >= 0:
            item = self.files_table.item(current_row, 0)
            file_result = item.data(Qt.ItemDataRole.UserRole)
            
            if file_result:
                self.show_file_details(file_result)
                
    def show_file_details(self, file_result: Dict[str, Any]):
        """Show detailed analysis for selected file"""
        lines = []
        lines.append(f"File: {file_result['file_path']}")
        lines.append(f"Confidence: {file_result['confidence']:.1%}")
        lines.append("")
        
        lines.append("Timestamps:")
        details = file_result['details']
        lines.append(f"  Created:  {details.get('created', 'N/A')}")
        lines.append(f"  Modified: {details.get('modified', 'N/A')}")
        lines.append(f"  Accessed: {details.get('accessed', 'N/A')}")
        
        if details.get('mft_entry'):
            lines.append(f"  MFT Entry: {details['mft_entry']}")
            
        lines.append("")
        lines.append("Detected Anomalies:")
        
        for anomaly in file_result['anomalies']:
            lines.append(f"\n{anomaly['type'].replace('_', ' ').title()}:")
            lines.append(f"  Description: {anomaly['description']}")
            lines.append(f"  Severity: {anomaly['severity'].capitalize()}")
            
        self.details_text.setPlainText('\n'.join(lines))
        
    def analysis_finished(self, results: Dict[str, Any]):
        """Handle analysis completion"""
        self.analyze_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        
        if 'error' in results:
            QMessageBox.critical(self, "Analysis Error", f"Error: {results['error']}")
            return
            
        self.analysis_results = results
        self.export_btn.setEnabled(True)
        
        # Show summary
        summary = []
        summary.append(f"Analysis complete!")
        summary.append(f"Total files analyzed: {results['total_files']}")
        summary.append(f"Suspicious files found: {len(results['suspicious_files'])}")
        
        if results['patterns']:
            summary.append(f"Suspicious patterns detected: {len(results['patterns'])}")
            
        QMessageBox.information(self, "Analysis Complete", '\n'.join(summary))
        
    def export_report(self):
        """Export analysis report"""
        if not self.analysis_results:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            "timestamp_analysis_report.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                report = TimestampReport.generate_summary(self.analysis_results)
                with open(file_path, 'w') as f:
                    f.write(report)
                QMessageBox.information(self, "Export Complete", f"Report saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export report: {str(e)}")