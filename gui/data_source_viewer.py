import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class DataSourceViewerWidget(QWidget):
    """
    A widget to display a list of data sources for the current case in a table.
    """
    def __init__(self, case_manager, parent=None):
        super().__init__(parent)
        self.case_manager = case_manager
        self.current_case_path = None # Stores the path of the currently loaded case
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) # Add some padding

        self.table_label = QLabel("No Case Loaded: Data Sources will appear here.")
        self.table_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_label.setFont(QFont("Arial", 10, QFont.Weight.Bold)) # Make label stand out
        self.table_label.setStyleSheet("color: #333333; margin-bottom: 5px;")
        main_layout.addWidget(self.table_label)

        self.data_source_table = QTableWidget()
        self.data_source_table.setColumnCount(5) # ID, Type, Path, Name, Description
        self.data_source_table.setHorizontalHeaderLabels(["ID", "Type", "Path", "Name", "Description"])
        
        # Make the table read-only
        self.data_source_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Allow full row selection
        self.data_source_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_source_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Styling for headers
        header_style = "::section { background-color: #f0f0f0; border-right: 1px solid #d0d0d0; padding: 4px; }"
        self.data_source_table.horizontalHeader().setStyleSheet(header_style)
        self.data_source_table.verticalHeader().setVisible(False) # Hide vertical header (row numbers)

        main_layout.addWidget(self.data_source_table)

    def set_current_case(self, case_path):
        """
        Sets the current case path and triggers a reload of data sources.
        Call this when a case is opened/created or closed (pass None).
        """
        self.current_case_path = case_path
        self.load_and_display_sources()

    def load_and_display_sources(self):
        """
        Loads data sources from the current case using CaseManager and displays them in the table.
        """
        self.data_source_table.setRowCount(0) # Clear existing rows
        self.data_source_table.clearContents() # Clear contents (important if changing column count)

        if not self.current_case_path:
            self.table_label.setText("No Case Loaded: Data Sources will appear here.")
            return

        case_name = os.path.basename(self.current_case_path)
        self.table_label.setText(f"Data Sources for Case: '{case_name}'")

        sources = self.case_manager.get_data_sources(self.current_case_path)
        
        if not sources:
            self.table_label.setText(f"No data sources added yet for case: '{case_name}'.")
            return

        self.data_source_table.setRowCount(len(sources))
        for row_idx, source in enumerate(sources):
            # QTableWidgetItem must be created for each cell
            self.data_source_table.setItem(row_idx, 0, QTableWidgetItem(str(source.get("id", ""))))
            self.data_source_table.setItem(row_idx, 1, QTableWidgetItem(source.get("source_type", "")))
            self.data_source_table.setItem(row_idx, 2, QTableWidgetItem(source.get("path", "")))
            self.data_source_table.setItem(row_idx, 3, QTableWidgetItem(source.get("name", "")))
            self.data_source_table.setItem(row_idx, 4, QTableWidgetItem(source.get("description", "")))
        
        # Adjust column widths for better fit
        self.data_source_table.resizeColumnsToContents()
        # Make the 'Path' column stretch to fill available space
        self.data_source_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        # Allow user to interactively resize other columns
        self.data_source_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Interactive
        )
        self.data_source_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Interactive
        )
        self.data_source_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Interactive
        )
        self.data_source_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Interactive
        )