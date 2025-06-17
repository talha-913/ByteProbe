"""
Report generation dialog
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QGroupBox, QTextEdit, QFileDialog,
    QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt

from core.report_generator import ReportGenerator


class ReportGenerationDialog(QDialog):
    """Dialog for generating forensic analysis reports"""
    
    def __init__(self, parent=None, case_path: str = None):
        super().__init__(parent)
        self.case_path = case_path
        self.report_generator = ReportGenerator(case_path) if case_path else None
        
        self.setWindowTitle("Generate Report")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Report format selection
        format_group = QGroupBox("Report Format")
        format_layout = QVBoxLayout()
        
        self.html_radio = QRadioButton("HTML Report (Recommended)")
        self.html_radio.setChecked(True)
        format_layout.addWidget(self.html_radio)
        
        self.text_radio = QRadioButton("Plain Text Report")
        format_layout.addWidget(self.text_radio)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Options
        options_group = QGroupBox("Report Options")
        options_layout = QVBoxLayout()
        
        self.include_details_cb = QCheckBox("Include detailed analysis results")
        self.include_details_cb.setChecked(True)
        options_layout.addWidget(self.include_details_cb)
        
        self.include_timeline_cb = QCheckBox("Include timeline visualization")
        self.include_timeline_cb.setChecked(False)
        options_layout.addWidget(self.include_timeline_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Preview
        preview_group = QGroupBox("Report Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.preview_report)
        button_layout.addWidget(self.preview_btn)
        
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generate_report)
        button_layout.addWidget(self.generate_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Generate initial preview
        self.preview_report()
        
    def preview_report(self):
        """Show report preview"""
        if not self.report_generator:
            self.preview_text.setText("No case selected for report generation")
            return
            
        try:
            report_data = self.report_generator.generate_case_report()
            
            # Format preview
            preview_lines = []
            preview_lines.append("CASE REPORT PREVIEW")
            preview_lines.append("=" * 40)
            preview_lines.append("")
            
            # Case info
            info = report_data['case_info']
            preview_lines.append("Case Information:")
            preview_lines.append(f"  Name: {info.get('case_name', 'N/A')}")
            preview_lines.append(f"  Number: {info.get('case_number', 'N/A')}")
            preview_lines.append(f"  Type: {info.get('case_type', 'N/A')}")
            preview_lines.append(f"  Investigator: {info.get('investigator_name', 'N/A')}")
            preview_lines.append("")
            
            # Data sources
            preview_lines.append(f"Data Sources: {len(report_data['data_sources'])}")
            for source in report_data['data_sources'][:3]:  # Show first 3
                preview_lines.append(f"  - {source['name']} ({source['type']})")
            if len(report_data['data_sources']) > 3:
                preview_lines.append(f"  ... and {len(report_data['data_sources']) - 3} more")
            preview_lines.append("")
            
            # Analysis summary
            summary = report_data['analysis_summary']
            preview_lines.append("Analysis Summary:")
            preview_lines.append(f"  Carved Files: {summary['carved_files']}")
            preview_lines.append(f"  File System Parsed: {'Yes' if summary['file_system_parsed'] else 'No'}")
            preview_lines.append(f"  Timestamp Analysis: {'Yes' if summary['timestamp_analysis'] else 'No'}")
            
            self.preview_text.setPlainText('\n'.join(preview_lines))
            
        except Exception as e:
            self.preview_text.setText(f"Error generating preview: {str(e)}")
            
    def generate_report(self):
        """Generate and save the report"""
        if not self.report_generator:
            QMessageBox.warning(self, "No Case", "No case selected for report generation")
            return
            
        # Determine format
        if self.html_radio.isChecked():
            extension = "HTML Files (*.html);;All Files (*.*)"
            default_name = "forensic_report.html"
        else:
            extension = "Text Files (*.txt);;All Files (*.*)"
            default_name = "forensic_report.txt"
            
        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            os.path.join(self.case_path, default_name),
            extension
        )
        
        if not file_path:
            return
            
        try:
            # Generate report
            if self.html_radio.isChecked():
                self.report_generator.export_html_report(
                    file_path,
                    include_details=self.include_details_cb.isChecked()
                )
            else:
                self.report_generator.export_text_report(file_path)
                
            QMessageBox.information(
                self,
                "Report Generated",
                f"Report successfully generated:\n{file_path}"
            )
            
            # Optionally open the report
            reply = QMessageBox.question(
                self,
                "Open Report",
                "Would you like to open the report now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(file_path) if os.name == 'nt' else os.system(f'open "{file_path}"')
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to generate report:\n{str(e)}"
            )