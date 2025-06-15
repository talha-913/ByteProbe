import sys
import os

from PyQt6.QtGui import QAction, QIcon
# ADDED: QFont, QSize for new UI elements
from PyQt6.QtGui import QFont # ADDED
from PyQt6.QtCore import Qt, QSize # MODIFIED: QSize already there, but ensuring QFont is added

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QStatusBar,
    QToolBar,
    QHBoxLayout,
    QMessageBox,
    QListWidget,
    QFileDialog,
    QPushButton,
    # --- ADDED WIDGETS FOR DATA SOURCE INTEGRATION ---
    QTabWidget,    # For multi-tab interface (Overview, Data Sources, etc.)
    QSplitter,      # For resizable panels (Recent Cases | Main Content)
    QListWidgetItem
)

from . import resources_rc

from gui.case_creation import CaseCreationDialog
from core.case_manager import CaseManager, CASES_BASE_DIR_NAME, APP_ROOT

# --- ADDED IMPORTS FOR DATA SOURCE ---
from gui.add_data_source_dialog import AddDataSourceDialog # New: Dialog for adding data sources
from gui.data_source_viewer import DataSourceViewerWidget # New: Widget to display data sources


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("ByteProbe")

        # handles the window size
        # self.showMaximized() #- for maximized screen sized win
        # self.showFullScreen() #- for fullscreen sized window
        # self.setMinimumSize(00, 00) #- can't be minimized further below
        self.resize(1300, 700) # for initial window size
        # ADDED: Minimum size for better layout with new elements
        self.setMinimumSize(1024, 768) # ADDED

        # --- Initialize CaseManager and current_case_path ---
        self.case_manager = CaseManager()
        self.current_case_path = None # To store the path of the currently open case

        # --- Initialize Status Bar ---
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self._createActions()
        self._createToolBars()
        self._createMenuBar()


        # Central Widget & Initial UI Layout
        # MODIFIED: Call the *new* init_main_layout that incorporates tabs/splitter
        self.init_main_layout() # This method will now handle setting up the main layout

        # --- NEW: Call initial UI updates ---
        self._update_status_bar() # Set initial status bar message
        self._load_recent_cases_display() # Load and display recent cases on startup
        # _populate_recent_cases_menu is called from _createMenuBar already

        # ADDED: Set initial UI state for no case open (important for new actions/tabs)
        self._reset_ui_for_no_case()


    def _createActions(self):
        # hosts all the actions req. for menubar&toolbar
        # File Actions
        self.new_case_action = QAction(QIcon(":/icons/new_case"), "&New Case", self)
        self.new_case_action.setShortcut("Ctrl+N")
        self.new_case_action.setStatusTip("Create a new forensics investigation case")
        self.new_case_action.triggered.connect(self._open_new_case_dialog)


        self.open_case_action = QAction(QIcon(":/icons/open_case"), "&Open Case...", self)
        self.open_case_action.setShortcut("Ctrl+O")
        self.open_case_action.setStatusTip("Open an existing forensics case")
        # MODIFIED: Connect to the new _open_case_from_dialog method
        self.open_case_action.triggered.connect(self._open_case_from_dialog)


        self.save_case_action = QAction(QIcon(":/icons/save_case"), "&Save Case", self)
        self.save_case_action.setShortcut("Ctrl+S")
        self.save_case_action.setStatusTip("Save the current forensics case")
        # --- Placeholder for Save Case action ---
        self.save_case_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Save Case not implemented yet."))

        # ADDED: Close Case Action
        self.close_case_action = QAction(QIcon(":/icons/close_case"), "Close Case", self) # Assuming close_case icon
        self.close_case_action.setStatusTip("Close the current forensic case")
        self.close_case_action.triggered.connect(self._close_current_case)
        # Initially disabled, enabled when a case is open

        self.exit_action = QAction("E&xit", self)
        self.exit_action.setStatusTip("Exit the application")
        self.exit_action.triggered.connect(self.close)

        # Edit Actions
        self.undo_action = QAction(QIcon(":/icons/undo"), "&Undo", self)
        self.undo_action.setStatusTip("Undo the last action")
        self.undo_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Undo not implemented yet."))

        self.redo_action = QAction(QIcon(":/icons/redo"), "&Redo", self)
        self.redo_action.setStatusTip("Redo the last undone action")
        self.redo_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Redo not implemented yet."))

        self.cut_action = QAction(QIcon(":/icons/cut"), "Cu&t", self)
        self.cut_action.setStatusTip("Cut the selected content")
        self.cut_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Cut not implemented yet."))

        self.copy_action = QAction(QIcon(":/icons/copy"), "&Copy", self)
        self.copy_action.setStatusTip("Copy the selected content")
        self.copy_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Copy not implemented yet."))

        self.paste_action = QAction(QIcon(":/icons/paste"), "&Paste", self)
        self.paste_action.setStatusTip("Paste content from the clipboard")
        self.paste_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Paste not implemented yet."))

        self.find_action = QAction( "&Find...", self)
        self.find_action.setStatusTip("Find text or patterns within the current view")
        self.find_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Find not implemented yet."))

        self.replace_action = QAction("Re&place...", self)
        self.replace_action.setStatusTip("Find and replace text or patterns")
        self.replace_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Replace not implemented yet."))


        # View Actions
        self.toolbar_action = QAction( "&Toolbar", self)
        self.toolbar_action.setStatusTip("Toggle visibility of the main toolbar")
        self.toolbar_action.setCheckable(True)

        self.statusbar_action = QAction( "&Status Bar", self)
        self.statusbar_action.setStatusTip("Toggle visibility of the status bar")
        self.statusbar_action.setCheckable(True)

        self.filelist_action = QAction(QIcon(":/icons/folder_tree"), "&File List", self)
        self.filelist_action.setStatusTip("Toggle visibility of the file list pane")
        self.filelist_action.setCheckable(True)
        # Connection for file list action will be done in _init_ui after widget creation


        # Tools Actions
        self.hash_calc_action = QAction(QIcon(":/icons/hash_calc"), "&Hash Calculator", self)
        self.hash_calc_action.setStatusTip("Calculate MD5, SHA1, SHA256 hashes for files")
        self.hash_calc_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Hash Calculator not implemented yet."))

        self.file_carver_action = QAction(QIcon(":/icons/file_carver.png"), "&File Carver", self)
        self.file_carver_action.setStatusTip("Recover deleted files by carving disk images")
        self.file_carver_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "File Carver not implemented yet."))

        self.disk_imager_action = QAction(QIcon(":/icons/disk_reader"), "&Disk Imager", self) # Moved from _createMenuBar
        self.disk_imager_action.setStatusTip("Create forensic images of disks or partitions")
        self.disk_imager_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Disk Imager not implemented yet."))

        self.options_action = QAction( "&Options...", self)
        self.options_action.setStatusTip("Configure application settings")
        self.options_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Options not implemented yet."))

        # Help Actions
        self.about_action = QAction(QIcon(":/icons/about"), "&About ByteProbe", self)
        self.about_action.setStatusTip("Learn more about ByteProbe")
        self.about_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "About ByteProbe not implemented yet."))

        # --- NEW: Placeholder for Recent Cases Menu Action ---
        self.recent_cases_menu = None # Will be a QMenu instance, initialized in _createMenuBar

        # --- ADDED: Data Source Action ---
        self.add_data_source_action = QAction(QIcon(":/icons/add_source.svg"), "Add Data Source...", self) # Assuming you have add_source.svg
        self.add_data_source_action.setStatusTip("Add a new data source to the current case")
        self.add_data_source_action.triggered.connect(self._show_add_data_source_dialog)
        self.add_data_source_action.setEnabled(False) # Initially disabled

        # --- ADDED: Placeholder Analysis and Report Actions (for later stages) ---
        self.analyze_action = QAction(QIcon(":/icons/analyze.svg"), "Analyze Data", self) # Assuming analyze.svg
        self.analyze_action.setStatusTip("Start analysis on selected data sources")
        self.analyze_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Analysis not implemented yet."))
        self.analyze_action.setEnabled(False) # Initially disabled

        self.report_action = QAction(QIcon(":/icons/report.svg"), "Generate Report", self) # Assuming report.svg
        self.report_action.setStatusTip("Generate a report for the current case")
        self.report_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Report generation not implemented yet."))
        self.report_action.setEnabled(False) # Initially disabled


    def _createMenuBar(self):
        menu_bar = self.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_case_action)
        # MODIFIED: Add close_case_action to File menu
        file_menu.addAction(self.open_case_action)
        file_menu.addAction(self.save_case_action)
        # ADDED: Close Case Action
        file_menu.addAction(self.close_case_action) # ADDED
        file_menu.addSeparator()

        # --- NEW: Add recent cases submenu here ---
        self.recent_cases_menu = file_menu.addMenu("Recent Cases")
        self._populate_recent_cases_menu() # Populate it immediately

        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)


        # --- Edit Menu ---
        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addSeparator()
        find_replace_menu = edit_menu.addMenu(QIcon(":/icons/find"), "Find & Replace")
        find_replace_menu.addAction(self.find_action)
        find_replace_menu.addAction(self.replace_action)

        # --- View Menu ---
        view_menu = menu_bar.addMenu("&View")

        # Action for Toggling Toolbar Visibility
        if hasattr(self, 'main_toolbar') and isinstance(self.main_toolbar, QToolBar):
            self.toolbar_action.setChecked(self.main_toolbar.isVisible())
            self.toolbar_action.triggered.connect(self.main_toolbar.setVisible)
        else:
            self.toolbar_action.setEnabled(False)
        view_menu.addAction(self.toolbar_action)

        # Action for Toggling Status Bar Visibility
        # Using self.statusBar instead of self.statusBar()
        if self.statusBar:
            self.statusbar_action.setChecked(self.statusBar.isVisible())
            self.statusbar_action.triggered.connect(self.statusBar.setVisible)
        else:
            self.statusbar_action.setEnabled(False)
        view_menu.addAction(self.statusbar_action)

        view_menu.addSeparator()
        # Action for Toggling File List Visibility
        # will be connected in _init_ui after self.file_list_widget is created
        view_menu.addAction(self.filelist_action)


        # --- Tools Menu ---
        tools_menu = menu_bar.addMenu("&Tools")
        tools_menu.addAction(self.hash_calc_action)
        tools_menu.addAction(self.file_carver_action)
        tools_menu.addAction(self.disk_imager_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.options_action)

        # --- ADDED: Case Menu (for Add Data Source, Analyze, Report) ---
        case_menu = menu_bar.addMenu("&Case")
        case_menu.addAction(self.add_data_source_action) # ADDED
        case_menu.addSeparator() # ADDED
        case_menu.addAction(self.analyze_action) # ADDED
        case_menu.addAction(self.report_action) # ADDED

        # --- Help Menu ---
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(self.about_action)


    def _createToolBars(self):
        self.main_toolbar = self.addToolBar("main_toolbar")
        # ADDED: Set icon size for toolbar
        self.main_toolbar.setIconSize(QSize(32, 32)) # ADDED
        self.main_toolbar.addAction(self.new_case_action)
        self.main_toolbar.addAction(self.open_case_action)
        self.main_toolbar.addAction(self.save_case_action)
        # ADDED: Close Case Action to Toolbar
        self.main_toolbar.addAction(self.close_case_action) # ADDED
        self.main_toolbar.addSeparator()

        # ADDED: Data Source, Analyze, Report actions to Toolbar
        self.main_toolbar.addAction(self.add_data_source_action) # ADDED
        self.main_toolbar.addAction(self.analyze_action) # ADDED
        self.main_toolbar.addAction(self.report_action) # ADDED
        self.main_toolbar.addSeparator() # ADDED

        self.main_toolbar.addAction(self.undo_action)
        self.main_toolbar.addAction(self.redo_action)
        self.main_toolbar.addAction(self.copy_action)
        self.main_toolbar.addAction(self.paste_action)

    # --- REPLACED _createCentralWidget with init_main_layout for comprehensive setup ---
    # MODIFIED: Renamed to init_main_layout (was _init_ui in previous complete example)
    # The original method was `_init_ui`. I'm replacing its content with the new layout.
    def init_main_layout(self): # MODIFIED: Renamed from _init_ui or _createCentralWidget
        """
        Sets up the central widget and its layout for the main application content,
        including the welcome message, quick action buttons, and recent cases list,
        now incorporating the QSplitter and QTabWidget for data source integration.
        """
        # MODIFIED: The central widget structure is now based on a splitter and tabs.
        # This replaces the simple QVBoxLayout directly on central_widget.

        self.central_widget_container = QWidget() # ADDED: New container for splitter
        self.setCentralWidget(self.central_widget_container) # ADDED

        # ADDED: QSplitter for resizable left (recent cases) and right (main content) panels
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal) # ADDED
        self.central_widget_layout = QHBoxLayout(self.central_widget_container) # ADDED: Use QHBoxLayout for central widget
        self.central_widget_layout.addWidget(self.main_splitter) # ADDED

        # ADDED: Left Panel Container (for Recent Cases)
        self.left_panel_container = QWidget() # ADDED
        self.left_panel_layout = QVBoxLayout(self.left_panel_container) # ADDED
        self.recent_cases_list_label = QLabel("Recent Cases") # ADDED
        self.recent_cases_list_label.setFont(QFont("Arial", 12, QFont.Weight.Bold)) # ADDED FONT
        self.recent_cases_list_label.setStyleSheet("color: #333; margin-bottom: 5px;") # ADDED
        self.left_panel_layout.addWidget(self.recent_cases_list_label) # ADDED

        # MODIFIED: Your existing recent_cases_list_widget is now placed here
        self.recent_cases_list_widget = QListWidget() # Original
        self.recent_cases_list_widget.setMinimumWidth(180) # ADDED
        self.recent_cases_list_widget.setMaximumWidth(250) # ADDED
        # MODIFIED: Connect to the new _open_case_from_recent_list method
        self.recent_cases_list_widget.itemDoubleClicked.connect(self._load_selected_recent_case) # Original connection (can coexist)
        self.recent_cases_list_widget.itemClicked.connect(self._open_case_from_recent_list) # ADDED: For single click to load case
        self.left_panel_layout.addWidget(self.recent_cases_list_widget) # ADDED

        self.main_splitter.addWidget(self.left_panel_container) # ADDED: Add left panel to splitter

        # ADDED: Right Panel Container (for Main Content - Tabs)
        self.right_panel_container = QWidget() # ADDED
        self.right_panel_layout = QVBoxLayout(self.right_panel_container) # ADDED

        # ADDED: QTabWidget for main content
        self.main_tab_widget = QTabWidget() # ADDED
        self.main_tab_widget.setFont(QFont("Arial", 10)) # ADDED FONT

        # ADDED: 1. Overview Tab (Placeholder for general information/welcome)
        self.overview_tab = QWidget() # ADDED
        overview_layout = QVBoxLayout(self.overview_tab) # ADDED
        # MODIFIED: The welcome_label content is now part of the overview tab
        welcome_label_content = ("<h2>Welcome to ByteProbe!</h2>"
                                 "<p>Select an action from the toolbar/menu or open an existing case from the left panel.</p>"
                                 "<p>To begin, create a <b>New Case</b> or <b>Open Case</b>.</p>")
        self.welcome_label = QLabel(welcome_label_content) # Re-purposed/added this label for the tab
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # ADDED
        # self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;") # Original style, might need adjustment
        overview_layout.addWidget(self.welcome_label) # ADDED
        overview_layout.addStretch(1) # ADDED
        self.main_tab_widget.addTab(self.overview_tab, "Overview") # ADDED

        # ADDED: 2. Data Sources Tab - Encapsulated in DataSourceViewerWidget
        self.data_source_viewer = DataSourceViewerWidget(self.case_manager) # ADDED
        self.main_tab_widget.addTab(self.data_source_viewer, "Data Sources") # ADDED

        # ADDED: 3. Placeholder for future tabs (e.g., File System, Registry, Reports, Timeline)
        self.file_system_tab = QWidget() # ADDED
        self.file_system_tab_layout = QVBoxLayout(self.file_system_tab) # ADDED
        self.file_system_tab_layout.addWidget(QLabel("File System View (Coming Soon)")) # ADDED
        self.file_system_tab_layout.addStretch(1) # ADDED
        self.main_tab_widget.addTab(self.file_system_tab, "File System") # ADDED

        self.right_panel_layout.addWidget(self.main_tab_widget) # ADDED
        self.main_splitter.addWidget(self.right_panel_container) # ADDED: Add right panel to splitter

        # ADDED: Set initial sizes for the splitter sections (e.g., left 20%, right 80%)
        self.main_splitter.setSizes([200, 800]) # ADDED


    # --- Case Management and UI Update Methods ---
    def _update_status_bar(self):
        """Updates the status bar and the central welcome label based on the current case."""
        if self.current_case_path:
            # ADDED: Get case metadata to display actual case name in title
            case_metadata = self.case_manager.get_case_metadata(self.current_case_path)
            case_name = case_metadata.get('case_name', os.path.basename(self.current_case_path)) if case_metadata else os.path.basename(self.current_case_path)
            self.statusBar.showMessage(f"Current Case: {case_name}")
            # MODIFIED: Update window title instead of welcome_label directly
            self.setWindowTitle(f"ByteProbe - {case_name}") # ADDED: Update window title
            # The welcome_label in the Overview tab can remain static or be dynamically updated if desired.
        else:
            self.statusBar.showMessage("No case open.")
            # MODIFIED: Reset window title
            self.setWindowTitle("ByteProbe") # ADDED: Reset window title
            # The welcome_label is now inside the overview tab and not directly updated by this method
            # self.welcome_label.setText("Welcome to ByteProbe! No case currently open.") # ORIGINAL - this is now handled by the Overview tab's static text.


    def _open_new_case_dialog(self):
        """Opens the Case Creation Dialog (modally for user-triggered menu/button actions)."""
        dialog = CaseCreationDialog(self)
        # MODIFIED: Connect to _handle_case_created with dictionary argument
        dialog.case_created.connect(self._handle_case_created) # Make sure dialog emits dict
        dialog.exec() # Use exec() for modal behavior when user explicitly clicks

    def _handle_case_created(self, case_details_dict): # MODIFIED: Parameter name for clarity (was case_path)
        """
        Slot to handle the signal emitted when a new case is successfully created by the CaseCreationDialog.
        This method is responsible for updating the UI based on the *already created* case.
        """
        created_case_path = case_details_dict.get('path')
        case_name_for_display = case_details_dict.get('case_name', 'Unnamed Case') # Use a fallback name

        if created_case_path and os.path.exists(created_case_path): # Added os.path.exists check as a safeguard
            QMessageBox.information(self, "Case Created", f"Case '{case_name_for_display}' created successfully!")
            self._update_status_bar() # Update status bar based on case details
            self._load_recent_cases_display() # Update recent cases list
            self._populate_recent_cases_menu() # Re-populate menu
            # Automatically load the newly created case and update UI
            self._load_case_and_update_ui(created_case_path)
        else:
            QMessageBox.critical(self, "Error", f"Failed to open or verify case '{case_name_for_display}'. It might have failed during creation.")


    def _load_recent_cases_display(self):
        """Loads recent cases from CaseManager and populates the QListWidget."""
        self.recent_cases_list_widget.clear()
        recent_cases = self.case_manager.get_recent_cases()
        if not recent_cases:
            self.recent_cases_list_widget.addItem("No recent cases found.")
            # Make the placeholder item unselectable
            self.recent_cases_list_widget.item(0).setFlags(Qt.ItemFlag.NoItemFlags)
            return

        for case in recent_cases:
            # MODIFIED: Store path in UserRole for easier retrieval
            item = QListWidgetItem(case['name']) # Display case name
            item.setData(Qt.ItemDataRole.UserRole, case['path']) # Store actual path
            self.recent_cases_list_widget.addItem(item)

    # ADDED: Method to handle clicking on a recent case list item
    def _open_case_from_recent_list(self, item):
        case_path = item.data(Qt.ItemDataRole.UserRole)
        if case_path: # Ensure an actual path was stored
            self._load_case_and_update_ui(case_path) # ADDED: Use the new centralized load method


    def _populate_recent_cases_menu(self):
        """Populates the 'Recent Cases' submenu in the File menu."""
        if self.recent_cases_menu:
            self.recent_cases_menu.clear() # Clear existing actions
            recent_cases = self.case_manager.get_recent_cases()
            if not recent_cases:
                self.recent_cases_menu.addAction("No Recent Cases").setEnabled(False)
                return

            for case_info in recent_cases:
                action = self.recent_cases_menu.addAction(case_info['name'])
                action.triggered.connect(lambda checked, path=case_info['path']: self._load_case_and_update_ui(path)) # MODIFIED: Use the new centralized load method
        else:
            print("Warning: Recent Cases menu not initialized. Cannot populate.")


    def _load_selected_recent_case(self, item):
        """Handles double-clicking an item in the recent cases list."""
        # This method can technically coexist with _open_case_from_recent_list,
        # but _open_case_from_recent_list is now the primary single-click handler.
        # Keeping this for minimal modification, but consider if both are needed.
        text = item.text()
        if "No recent cases found" in text:
            return # Do nothing if the placeholder is clicked

        try:
            # Extract path from the item's text (e.g., "Case Name (C:/path/to/case)")
            # This extraction might be less reliable if 'name' itself contains parentheses.
            # Using item.data(Qt.ItemDataRole.UserRole) as done in _open_case_from_recent_list is better.
            case_path = item.data(Qt.ItemDataRole.UserRole) # MODIFIED: Use UserRole data
            if case_path:
                self._load_case_and_update_ui(case_path) # ADDED: Use the new centralized load method
            else:
                 QMessageBox.warning(self, "Invalid Path", "Could not retrieve case path from selected item.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading recent case: {e}")

    # MODIFIED: Renamed _open_existing_case to _open_case_from_dialog
    def _open_case_from_dialog(self): # MODIFIED: Renamed method
        """Opens a file dialog to select an existing case directory."""
        # Suggest the default cases directory as starting point
        initial_dir = os.path.join(APP_ROOT, CASES_BASE_DIR_NAME)
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir, exist_ok=True) # Ensure it exists for the dialog

        # QFileDialog.getExistingDirectory returns the selected directory path
        case_directory = QFileDialog.getExistingDirectory(self, "Open Existing Case", initial_dir)

        if case_directory:
            # Validate if it's a ByteProbe case directory (e.g., check for case_metadata.db)
            metadata_db_path = os.path.join(case_directory, "case_metadata.db")
            if not os.path.exists(metadata_db_path):
                QMessageBox.warning(self, "Invalid Case",
                                    f"The selected directory '{case_directory}' does not appear to be a valid ByteProbe case directory (missing 'case_metadata.db').")
                return

            self._load_case_and_update_ui(case_directory) # MODIFIED: Use the new centralized load method


    # MODIFIED: Renamed _open_case_by_path to _load_case_and_update_ui
    # This is the central method for loading a case and updating ALL related UI
    def _load_case_and_update_ui(self, case_path): # MODIFIED: Renamed and expanded method
        """
        Loads a case, updates UI elements (window title, actions, tabs),
        and passes the case path to the data source viewer.
        """
        loaded_path = self.case_manager.load_case(case_path)
        if loaded_path:
            self.current_case_path = loaded_path
            # ADDED: Get case metadata for display name in title
            case_metadata = self.case_manager.get_case_metadata(loaded_path)
            case_name = case_metadata.get('case_name', os.path.basename(loaded_path)) if case_metadata else os.path.basename(loaded_path)

            self.statusBar.showMessage(f"Case '{case_name}' loaded successfully.")
            self.setWindowTitle(f"ByteProbe - {case_name}") # ADDED: Update window title

            # ADDED: Enable actions relevant to an open case
            self.add_data_source_action.setEnabled(True) # ADDED
            self.close_case_action.setEnabled(True) # ADDED
            self.analyze_action.setEnabled(True) # ADDED
            self.report_action.setEnabled(True) # ADDED
            # Add other case-specific actions to enable/disable here
            # self.plugins_action.setEnabled(True) # if you have these actions
            # self.settings_action.setEnabled(True)
            # self.help_action.setEnabled(True)


            # ADDED: Enable Data Sources tab and set current case for the viewer
            # Ensure these widgets are created in init_main_layout
            self.main_tab_widget.setTabEnabled(1, True) # Data Sources tab (index 1)
            self.main_tab_widget.setTabEnabled(2, True) # File System tab (index 2, placeholder)
            self.data_source_viewer.set_current_case(self.current_case_path) # ADDED: Pass the case path to the viewer
            self.main_tab_widget.setCurrentIndex(1) # ADDED: Switch to Data Sources tab by default
        else:
            self.statusBar.showMessage("Failed to load case.")
            self._reset_ui_for_no_case() # ADDED: Call reset if loading fails


    # ADDED: Close Case Method
    def _close_current_case(self):
        if self.current_case_path:
            reply = QMessageBox.question(self, 'Close Case',
                                         f"Are you sure you want to close '{os.path.basename(self.current_case_path)}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._reset_ui_for_no_case() # ADDED: Reset UI elements
                self.statusBar.showMessage("Case closed.")

    # ADDED: Reset UI for No Case
    def _reset_ui_for_no_case(self):
        """Resets UI elements when no case is loaded/closed."""
        self.current_case_path = None
        self.setWindowTitle("ByteProbe")
        self.statusBar.showMessage("Ready.")

        # Disable actions requiring an open case
        self.add_data_source_action.setEnabled(False) # ADDED
        self.close_case_action.setEnabled(False) # ADDED
        self.analyze_action.setEnabled(False) # ADDED
        self.report_action.setEnabled(False) # ADDED
        # Add other case-specific actions to disable here
        # self.plugins_action.setEnabled(False)
        # self.settings_action.setEnabled(False)
        # self.help_action.setEnabled(False)

        # Clear data source viewer and disable its tab (and any other case-specific tabs)
        # Ensure main_tab_widget and data_source_viewer are initialized in init_main_layout
        if hasattr(self, 'data_source_viewer'): # Check if it exists before using
             self.data_source_viewer.set_current_case(None) # ADDED: Clear viewer content
        if hasattr(self, 'main_tab_widget'): # Check if it exists before using
            self.main_tab_widget.setTabEnabled(1, False) # ADDED: Data Sources tab
            self.main_tab_widget.setTabEnabled(2, False) # ADDED: File System tab (and any others)
            self.main_tab_widget.setCurrentIndex(0) # ADDED: Go back to Overview tab


    # ADDED: Show Add Data Source Dialog
    def _show_add_data_source_dialog(self):
        if not self.current_case_path:
            QMessageBox.warning(self, "No Case Open", "Please open or create a case before adding data sources.")
            return

        dialog = AddDataSourceDialog(self)
        dialog.data_source_added.connect(self._handle_data_source_added) # Connect signal to slot
        dialog.exec() # Show dialog modally

    # ADDED: Handle Data Source Added
    def _handle_data_source_added(self, source_info):
        """Slot to receive data source info from the dialog and add to case."""
        if self.current_case_path:
            success = self.case_manager.add_data_source(self.current_case_path, source_info)
            if success:
                QMessageBox.information(self, "Success", "Data source added successfully!")
                self.data_source_viewer.load_and_display_sources() # ADDED: Refresh the viewer's table
                self.main_tab_widget.setCurrentIndex(1) # ADDED: Ensure Data Sources tab is active
            else:
                QMessageBox.critical(self, "Error", "Failed to add data source. Check console for details (e.g., duplicate path).")
        else:
            QMessageBox.critical(self, "Error", "No case is currently open to add data source.")


    def _show_about_dialog(self):
        # ADDED: Basic About Dialog content (can be customized)
        QMessageBox.about(self, "About ByteProbe",
                          "<b>ByteProbe Forensic Tool</b><br>"
                          "Version 0.1<br>"
                          "A simple digital forensics application.<br>"
                          "Developed by [Your Name/Team Name]<br><br>"
                          "© 2024 All rights reserved.")


    # --- Keep this method as it's called by main.py after splash screen ---
    def show_and_initiate_case_dialog(self):
        """
        Shows the main window and then initiates the initial modeless
        case creation dialog. This is called after the splash screen finishes.
        """
        self.show()

        initial_case_dialog = CaseCreationDialog(self)
        # MODIFIED: Connect to a new handler that expects the dictionary
        initial_case_dialog.case_created.connect(self._handle_case_created_from_initial_dialog) # ADDED
        initial_case_dialog.show()

    # ADDED: New handler for the initial case creation dialog, which passes a dictionary
    def _handle_case_created_from_initial_dialog(self, case_details_dict): # ADDED
        """Handler for case creation from the initial modeless dialog."""
        # This will call the main _handle_case_created, which now expects a dictionary
        self._handle_case_created(case_details_dict) # ADDED


# if __name__ == "__main__":
#     app = QApplication([])
#     # app.setStyle('Windows')
# #     window = MainWindow()
# #     window.show()
# #     sys.exit(app.exec())