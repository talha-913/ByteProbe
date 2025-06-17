import os
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QSizePolicy, QMessageBox,
    QGridLayout,
    QTextEdit,
    QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QGuiApplication, QPalette, QBrush, QPixmap




class AddDataSourceDialog(QDialog):
    data_source_added = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Data Source")
        self.setFixedSize(600, 400) # Consistent dialog size

        # Set an object name for QSS targeting
        self.setObjectName("AddDataSourceDialog") 

        self.init_ui()
        self._apply_styles() # New method for applying QSS
        self._center_dialog_on_parent_or_screen()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Input Fields Group Box ---
        input_group_box = QGroupBox("Data Source Details")
        # You can set object name for group box as well if you want to style it separately
        input_group_box.setObjectName("DataSourceDetailsGroupBox")
        input_grid_layout = QGridLayout()

        input_grid_layout.setColumnStretch(0, 0)
        input_grid_layout.setColumnStretch(1, 1)
        input_grid_layout.setHorizontalSpacing(10)
        input_grid_layout.setVerticalSpacing(10)

        # ---Source Type ---
        type_label = QLabel("Source Type:")
        type_label.setObjectName("DialogLabel") # Object name for label styling
        type_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["Disk Image", "Logical Drive", "Folder"])
        self.source_type_combo.currentIndexChanged.connect(self._update_path_selection)
        
        type_combo_layout = QHBoxLayout()
        type_combo_layout.addWidget(self.source_type_combo)
        type_combo_layout.addStretch()
        
        input_grid_layout.addWidget(type_label, 0, 0)
        input_grid_layout.addLayout(type_combo_layout, 0, 1)

        # --- Path Selection (Path Input + Browse Button) ---
        path_label = QLabel("Path:")
        path_label.setObjectName("DialogLabel") # Object name for label styling
        path_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select data source path...")
        
        self.browse_button = QPushButton("Browse Drive...")
        self.browse_button.clicked.connect(self._browse_path)
        

        path_input_layout = QHBoxLayout()
        path_input_layout.addWidget(self.path_input)
        path_input_layout.addWidget(self.browse_button)

        input_grid_layout.addWidget(path_label, 1, 0)
        input_grid_layout.addLayout(path_input_layout, 1, 1)

        # --- Name ---
        name_label = QLabel("Name:")
        name_label.setObjectName("DialogLabel") 
        name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a name for the source (optional)")
        
        name_input_layout = QHBoxLayout()
        name_input_layout.addWidget(self.name_input)
        name_input_layout.addStretch()

        input_grid_layout.addWidget(name_label, 2, 0)
        input_grid_layout.addLayout(name_input_layout, 2, 1)

        # --- Description ---
        description_label = QLabel("Description:")
        description_label.setObjectName("DialogLabel") 
        description_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Brief description (optional, multiple lines supported)")
        self.description_input.setFixedHeight(60)
        
        description_input_layout = QHBoxLayout()
        description_input_layout.addWidget(self.description_input)
        description_input_layout.addStretch()

        input_grid_layout.addWidget(description_label, 3, 0)
        input_grid_layout.addLayout(description_input_layout, 3, 1)
        
        input_group_box.setLayout(input_grid_layout)
        main_layout.addWidget(input_group_box)
        
        # Create a widget for the empty area with background image
        background_widget = QLabel()
        background_widget.setObjectName("BackgroundWidget")
        background_widget.setMinimumHeight(100)  # Ensure minimum space for the background
        main_layout.addWidget(background_widget, 1)  # stretch factor of 1

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Source")
        self.add_button.clicked.connect(self._add_source)
        
        self.add_button.setStyleSheet("padding: 8px 15px;")

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        # REMOVED: self.cancel_button.setFixedSize(100, 35) - now uses default size
        self.cancel_button.setStyleSheet("padding: 8px 15px;")

        button_layout.addStretch(1)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self._update_path_selection(0)

    def _apply_styles(self):
        """Applies QSS for background image and other styling."""
        style_sheet = """
            QDialog#AddDataSourceDialog {
                background-color: #f0f0f0; /* Light background for main dialog */
            }
            QLabel#BackgroundWidget {
                background-image: url("assets/images/Patterns.png"); 
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover; /* Cover the widget area */
                border: none;
            }
            QGroupBox#DataSourceDetailsGroupBox {
                border: 1px solid #cccccc; /* Light border */
                border-radius: 5px; /* Rounded corners */
                margin-top: 10px; /* Space for title */
                padding-top: 15px; /* Space inside for content */
                background-color: white; /* Clean white background */
            }
            QGroupBox#DataSourceDetailsGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* Title above the group box */
                padding: 0 3px;
                color: #333333; /* Darker text */
                font-weight: bold;
            }
            QLabel#DialogLabel {
                color: #555555; /* Slightly muted label color */
                font-size: 10pt;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
        """
        self.setStyleSheet(style_sheet)


    def _center_dialog_on_parent_or_screen(self):
        if self.parent():
            parent_rect = self.parent().geometry()
            self_rect = self.frameGeometry()
            self_rect.moveCenter(parent_rect.center())
            self.move(self_rect.topLeft())
        else:
            screen = QGuiApplication.primaryScreen().geometry()
            self_rect = self.frameGeometry()
            self_rect.moveCenter(screen.center())
            self.move(self_rect.topLeft())


    def _update_path_selection(self, index):
        source_type = self.source_type_combo.currentText()
        if source_type == "Disk Image":
            self.browse_button.setText("Browse File...")
            self.path_input.setPlaceholderText("Select disk image file (e.g., .dd, .raw)...")
        elif source_type == "Logical Drive":
            self.browse_button.setText("Browse Drive...")
            self.path_input.setPlaceholderText("Select a logical drive (e.g., C:\\, D:\\) or a raw device path...")
        elif source_type == "Folder":
            self.browse_button.setText("Browse Folder...")
            self.path_input.setPlaceholderText("Select a folder to add...")

    def _browse_path(self):
        source_type = self.source_type_combo.currentText()
        path = ""
        initial_dir = os.path.expanduser("~")

        if source_type == "Disk Image":
            filter = "Disk Images (*.dd *.img *.bin *.raw *.vhd *.vmdk *.e01);;All Files (*)"
            path, _ = QFileDialog.getOpenFileName(self, "Select Disk Image File", initial_dir, filter)
        elif source_type == "Logical Drive":
            path = QFileDialog.getExistingDirectory(self, "Select Logical Drive or Partition", initial_dir)
        elif source_type == "Folder":
            path = QFileDialog.getExistingDirectory(self, "Select Folder", initial_dir)

        if path:
            self.path_input.setText(os.path.normpath(path))


    def _add_source(self):
        source_type = self.source_type_combo.currentText()
        path = self.path_input.text().strip()
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()

        if not path:
            QMessageBox.warning(self, "Input Error", "Please select or enter a path for the data source.")
            return

        is_windows_raw_device = sys.platform.startswith('win') and path.lower().startswith("\\\\.\\")
        is_linux_raw_device = sys.platform.startswith('linux') and path.lower().startswith("/dev/")

        if not os.path.exists(path) and not is_windows_raw_device and not is_linux_raw_device:
            QMessageBox.warning(self, "Path Error", f"The specified path does not exist or is inaccessible:\n{path}\n"
                                                    "Please ensure it's a valid file, mounted drive, or raw device path.")
            return

        if not name:
            name = os.path.basename(path)

        source_info = {
            "source_type": source_type,
            "path": path,
            "name": name,
            "description": description
        }

        self._latest_source_info = source_info
        
        self.data_source_added.emit(source_info)
        self.accept()

# Example usage (for testing this dialog independently)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = AddDataSourceDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Data Source Added:", dialog._latest_source_info)
    sys.exit(app.exec())