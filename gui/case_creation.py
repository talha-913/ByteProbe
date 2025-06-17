import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# Import the CaseManager from core module
from core.case_manager import CaseManager, CASES_BASE_DIR_NAME, APP_ROOT

class CaseCreationDialog(QDialog):
    """
    A dialog for creating a new forensic case.
    Collects essential and optional case details.
    """
    
    case_created = pyqtSignal(dict) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Case")
        self.setGeometry(200, 200, 600, 450) 

        self.case_manager = CaseManager()
        self.selected_output_dir = os.path.join(APP_ROOT, CASES_BASE_DIR_NAME) # Default output dir

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        # --- Essential Details Group ---
        essential_group = QGroupBox("Essential Details")
        essential_layout = QFormLayout()

        self.case_name_input = QLineEdit()
        self.case_name_input.setPlaceholderText("e.g., Target Breach 2025")
        essential_layout.addRow("Case Name:", self.case_name_input)

        # Default base output directory display and selection
        self.base_output_dir_label = QLabel(f"<b>{self.selected_output_dir}</b>")
        self.browse_dir_button = QPushButton("Browse...")
        self.browse_dir_button.clicked.connect(self._browse_for_output_directory)
        dir_h_layout = QHBoxLayout()
        dir_h_layout.addWidget(self.base_output_dir_label)
        dir_h_layout.addWidget(self.browse_dir_button)
        essential_layout.addRow("Base Output Directory:", dir_h_layout)

        essential_group.setLayout(essential_layout)
        main_layout.addWidget(essential_group)

        # --- Optional Details Group ---
        optional_group = QGroupBox("Optional Details")
        optional_layout = QFormLayout()

        self.case_number_input = QLineEdit()
        self.case_number_input.setPlaceholderText("e.g., CR-2025-001")
        optional_layout.addRow("Case Number:", self.case_number_input)

        self.case_type_combo = QComboBox()
        self.case_type_combo.addItems(["", "Cybercrime", "HR Investigation", "Civil Litigation", "Criminal Investigation", "Internal Audit", "Other"])
        optional_layout.addRow("Case Type:", self.case_type_combo)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Brief description of the case objectives and scope...")
        self.description_input.setFixedHeight(70) # Limit height
        optional_layout.addRow("Description:", self.description_input)

        optional_group.setLayout(optional_layout)
        main_layout.addWidget(optional_group)

        # --- Investigator Details Group ---
        investigator_group = QGroupBox("Investigator Details")
        investigator_layout = QFormLayout()

        self.investigator_name_input = QLineEdit()
        self.investigator_name_input.setPlaceholderText("e.g., Jane Doe")
        investigator_layout.addRow("Investigator Name:", self.investigator_name_input)

        self.investigator_org_input = QLineEdit()
        self.investigator_org_input.setPlaceholderText("e.g., Forensic Solutions Inc.")
        investigator_layout.addRow("Organization/Dept:", self.investigator_org_input)

        investigator_group.setLayout(investigator_layout)
        main_layout.addWidget(investigator_group)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Case")
        self.create_button.clicked.connect(self._create_case_clicked)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject) # QDialog's reject method closes the dialog

        button_layout.addStretch(1) # Pushes buttons to the right
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _browse_for_output_directory(self):
        """Opens a directory dialog to select the base output directory."""
        initial_dir = self.selected_output_dir if os.path.exists(self.selected_output_dir) else os.path.join(APP_ROOT, CASES_BASE_DIR_NAME)
        directory = QFileDialog.getExistingDirectory(self, "Select Base Output Directory", initial_dir)
        if directory:
            self.selected_output_dir = directory
            self.base_output_dir_label.setText(f"<b>{self.selected_output_dir}</b>")


    def _create_case_clicked(self):
        """Handles the 'Create Case' button click."""
        case_name = self.case_name_input.text().strip()
        case_number = self.case_number_input.text().strip()
        case_type = self.case_type_combo.currentText().strip()
        description = self.description_input.toPlainText().strip()
        investigator_name = self.investigator_name_input.text().strip()
        investigator_organization = self.investigator_org_input.text().strip()

        if not case_name:
            QMessageBox.warning(self, "Missing Information", "Please provide a Case Name. It is essential.")
            return

        # Attempt to create the case using the CaseManager
        try:
            created_case_path = self.case_manager.create_new_case(
                case_name=case_name,
                case_number=case_number if case_number else None, # Pass None if empty
                case_type=case_type if case_type else None,
                description=description if description else None,
                investigator_name=investigator_name if investigator_name else None,
                investigator_organization=investigator_organization if investigator_organization else None,
                base_output_dir=self.selected_output_dir
            )

            if created_case_path:
                
                # MODIFIED: Emit a dictionary containing both path and name
                self.case_created.emit({
                    'path': created_case_path, 
                    'case_name': case_name, # Include case_name
                    'case_number': case_number, # Include other details if main_window uses them directly
                    'case_type': case_type,
                    'description': description,
                    'investigator_name': investigator_name,
                    'investigator_organization': investigator_organization
                }) 
                self.accept() # Close the dialog with 'Accepted' status
            else:
                # Error message already printed by CaseManager, just show a generic dialog
                QMessageBox.critical(self, "Creation Failed", "Failed to create case. Try a different case name/directory.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during case creation: {e}")

# Example of how to run this dialog independently for testing:
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = CaseCreationDialog()
    # MODIFIED: Connect to the signal to see the dictionary emitted
    dialog.case_created.connect(lambda details_dict: print(f"Signal emitted: Case created with details: {details_dict}"))

    if dialog.exec() == QDialog.Accepted:
        print("Dialog accepted (Case created).")
    else:
        print("Dialog rejected (Case creation cancelled).")
    sys.exit(app.exec())