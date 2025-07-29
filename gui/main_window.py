# NEW: Show fileimport sys
import os

from PyQt6.QtGui import QAction, QIcon, QFont 
from PyQt6.QtCore import Qt, QSize 

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
    QTabWidget,    # For multi-tab interface (Overview, Data Sources, etc.)
    QSplitter,      # For resizable panels (Recent Cases | Main Content)
    QListWidgetItem,
    QTreeWidget
)

from . import resources_rc

from gui.case_creation import CaseCreationDialog
from core.case_manager import CaseManager, CASES_BASE_DIR_NAME, APP_ROOT

# --- IMPORTS FOR DATA SOURCE ---
from gui.add_data_source_dialog import AddDataSourceDialog # Dialog for adding data sources
from gui.data_source_viewer import DataSourceViewerWidget # Widget to display data sources
from gui.widgets.file_system_viewer import FileSystemViewerWidget  # NEW: Import file system viewer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("ByteProbe")
        self.setWindowIcon(QIcon("assets\images\byteprobe_logo.svg"))

        # handles the window size
        # self.showMaximized() #- for maximized screen sized win
        # self.showFullScreen() #- for fullscreen sized window
        # self.setMinimumSize(00, 00) #- can't be minimized further below
        self.resize(1300, 700) # for initial window size
        self.setMinimumSize(1024, 768) 

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
        self.init_main_layout() # handles setting up the main layout

        # --- Call initial UI updates ---
        self._update_status_bar() # initial status bar message
        self._populate_recent_cases_menu() # Update recent cases menu

        # Set initial UI state for no case open 
        self._reset_ui_for_no_case()
        
        # Apply global stylesheet
        self._apply_global_stylesheet()


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
        self.open_case_action.triggered.connect(self._open_case_from_dialog)

        self.save_case_action = QAction(QIcon(":/icons/save_case"), "&Save Case", self)
        self.save_case_action.setShortcut("Ctrl+S")
        self.save_case_action.setStatusTip("Save the current forensics case")
        self.save_case_action.triggered.connect(self._save_case)  # MODIFIED: Connect to actual handler

        self.close_case_action = QAction(QIcon(":/icons/close_case"), "Close Case", self) 
        self.close_case_action.setStatusTip("Close the current forensic case")
        self.close_case_action.triggered.connect(self._close_current_case)
        
        self.delete_case_action = QAction(QIcon(":/icons/delete"), "Delete Case...", self)
        self.delete_case_action.setStatusTip("Delete an existing case")
        self.delete_case_action.triggered.connect(self._delete_case)

        self.exit_action = QAction("E&xit", self)
        self.exit_action.setStatusTip("Exit the application")
        self.exit_action.triggered.connect(self.close)

        # Edit Actions
        self.undo_action = QAction(QIcon(":/icons/undo"), "&Undo", self)
        self.undo_action.setStatusTip("Undo the last action")
        self.undo_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Undo not implemented yet."))  # to be implemented

        self.redo_action = QAction(QIcon(":/icons/redo"), "&Redo", self)
        self.redo_action.setStatusTip("Redo the last undone action")
        self.redo_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Redo not implemented yet.")) #to be implemented

        self.cut_action = QAction(QIcon(":/icons/cut"), "Cu&t", self)
        self.cut_action.setStatusTip("Cut the selected content")
        self.cut_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Cut not implemented yet.")) #to be implemented

        self.copy_action = QAction(QIcon(":/icons/copy"), "&Copy", self)
        self.copy_action.setStatusTip("Copy the selected content")
        self.copy_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Copy not implemented yet.")) #to be implemented

        self.paste_action = QAction(QIcon(":/icons/paste"), "&Paste", self)
        self.paste_action.setStatusTip("Paste content from the clipboard")
        self.paste_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Paste not implemented yet.")) #to be implemented

        self.find_action = QAction( "&Find...", self)
        self.find_action.setStatusTip("Find text or patterns within the current view")
        self.find_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Find not implemented yet.")) # to be implemented

        self.replace_action = QAction("Re&place...", self)
        self.replace_action.setStatusTip("Find and replace text or patterns")
        self.replace_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Replace not implemented yet.")) #to be implemented


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


        # Tools Actions
        self.hash_calc_action = QAction(QIcon(":/icons/hash_calc"), "&Hash Calculator", self)
        self.hash_calc_action.setStatusTip("Calculate MD5, SHA1, SHA256 hashes for files")
        self.hash_calc_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Hash Calculator not implemented yet.")) #to be implemented

        self.file_carver_action = QAction(QIcon(":/icons/file_carver.png"), "&File Carver", self)
        self.file_carver_action.setStatusTip("Recover deleted files by carving disk images")
        self.file_carver_action.triggered.connect(self._show_file_carver_dialog)  # MODIFIED: Connect to actual handler
        self.file_carver_action.setEnabled(False)  # ADDED: Initially disabled

        self.disk_imager_action = QAction(QIcon(":/icons/disk_reader"), "&Disk Imager", self) 
        self.disk_imager_action.setStatusTip("Create forensic images of disks or partitions")
        self.disk_imager_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Disk Imager not implemented yet.")) #to be implemented

        self.options_action = QAction( "&Options...", self)
        self.options_action.setStatusTip("Configure application settings")
        self.options_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Options not implemented yet.")) #to be implemented

        # Help Actions
        self.about_action = QAction(QIcon(":/icons/about"), "&About ByteProbe", self) 
        self.about_action.setStatusTip("Learn more about ByteProbe")
        self.about_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "About ByteProbe not implemented yet.")) # to be implemented

        self.recent_cases_menu = None 

        # --- Data Source Action ---
        self.add_data_source_action = QAction(QIcon(":/icons/add_source.svg"), "+Data Source...", self) 
        self.add_data_source_action.setStatusTip("Add a new data source to the current case")
        self.add_data_source_action.triggered.connect(self._show_add_data_source_dialog)
        self.add_data_source_action.setEnabled(False) 
        
        # --- File Carver and Timestomping Detection ---
        self.file_carver = QAction(QIcon(":/icons/add_source.svg"), "File Carver", self) 
        self.file_carver.setStatusTip("Carve Files in the current case")
        # self.file_carver.triggered.connect(self._perform_file_carving)
        self.file_carver.setEnabled(False) 

        self.timestomping_detection = QAction(QIcon(":/icons/add_source.svg"), "Timestomping Detection", self) 
        self.timestomping_detection.setStatusTip("Perform timestomping detection")
        self.timestomping_detection.triggered.connect(self._show_timestamp_analysis)  # ADDED: Connect to handler
        self.timestomping_detection.setEnabled(False)  # FIXED: Was setting file_carver instead

        # --- Analysis and Report Actions ---
        self.analyze_action = QAction(QIcon(":/icons/analyze.svg"), "Analyze Data", self) 
        self.analyze_action.setStatusTip("Start analysis on selected data sources")
        self.analyze_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Analysis not implemented yet.")) #to be implemented
        self.analyze_action.setEnabled(False) 

        self.report_action = QAction(QIcon(":/icons/report.svg"), "Generate Report", self) 
        self.report_action.setStatusTip("Generate a report for the current case")
        self.report_action.triggered.connect(self._show_report_dialog)  # MODIFIED: Connect to actual handler
        self.report_action.setEnabled(False) 


    def _createMenuBar(self):
        menu_bar = self.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_case_action)
        file_menu.addAction(self.open_case_action)
        file_menu.addAction(self.save_case_action)
        file_menu.addAction(self.close_case_action) 
        file_menu.addAction(self.delete_case_action)  # ADDED: Delete case option
        file_menu.addSeparator()
        self.recent_cases_menu = file_menu.addMenu("Recent Cases")
        self._populate_recent_cases_menu()
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

        # Toggling Toolbar Visibility
        if hasattr(self, 'main_toolbar') and isinstance(self.main_toolbar, QToolBar):
            self.toolbar_action.setChecked(self.main_toolbar.isVisible())
            self.toolbar_action.triggered.connect(self.main_toolbar.setVisible)
        else:
            self.toolbar_action.setEnabled(False)
        view_menu.addAction(self.toolbar_action)

        # Toggling Status Bar Visibility
        if self.statusBar:
            self.statusbar_action.setChecked(self.statusBar.isVisible())
            self.statusbar_action.triggered.connect(self.statusBar.setVisible)
        else:
            self.statusbar_action.setEnabled(False)
        view_menu.addAction(self.statusbar_action)

        view_menu.addSeparator()
        view_menu.addAction(self.filelist_action)

        # --- Tools Menu ---
        tools_menu = menu_bar.addMenu("&Tools")
        tools_menu.addAction(self.hash_calc_action)
        tools_menu.addAction(self.file_carver_action)
        tools_menu.addAction(self.disk_imager_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.timestomping_detection)  # ADDED: Timestomping to menu
        tools_menu.addSeparator()
        tools_menu.addAction(self.options_action)

        # --- Case Menu (for Add Data Source, Analyze, Report) ---
        case_menu = menu_bar.addMenu("&Case")
        case_menu.addAction(self.add_data_source_action) 
        case_menu.addSeparator() 
        case_menu.addAction(self.analyze_action) 
        case_menu.addAction(self.report_action) 

        # --- Help Menu ---
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(self.about_action)


    def _createToolBars(self):
        self.main_toolbar = self.addToolBar("main_toolbar")
        self.main_toolbar.setIconSize(QSize(24, 24)) 
        self.main_toolbar.addAction(self.new_case_action)
        self.main_toolbar.addAction(self.open_case_action)
        self.main_toolbar.addAction(self.save_case_action)
        self.main_toolbar.addAction(self.close_case_action) 
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.copy_action)
        self.main_toolbar.addAction(self.paste_action)
        self.main_toolbar.addSeparator()
        # Data Source, Analyze, Report actions to Toolbar
        self.main_toolbar.addAction(self.add_data_source_action) 
        self.main_toolbar.addAction(self.file_carver_action)  # ADDED: File carver to toolbar
        self.main_toolbar.addAction(self.timestomping_detection)  # ADDED: Timestomping to toolbar
        self.main_toolbar.addAction(self.analyze_action) 
        self.main_toolbar.addAction(self.report_action) 
        self.main_toolbar.addSeparator() 

    # loads the main_layouy in the central widget of main window
    def init_main_layout(self): 
        """
        Sets up the central widget and its layout for the main application content,
        including the welcome message, quick action buttons, and recent cases list,
        now incorporating the QSplitter and QTabWidget for data source integration.
        """

        self.central_widget_container = QWidget() # New container for splitter
        self.setCentralWidget(self.central_widget_container)

        # QSplitter for resizable left (file hierarchy) and right (main content) panels
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal) 
        self.central_widget_layout = QHBoxLayout(self.central_widget_container) # ADDED: Use QHBoxLayout for central widget
        self.central_widget_layout.addWidget(self.main_splitter) # ADDED

        # MODIFIED: Left Panel Container (for File Hierarchy)
        self.left_panel_container = QWidget() 
        self.left_panel_layout = QVBoxLayout(self.left_panel_container) 
        self.file_hierarchy_label = QLabel("File Explorer") # MODIFIED: Changed from Recent Cases
        self.file_hierarchy_label.setFont(QFont("Arial", 12, QFont.Weight.Bold)) 
        self.file_hierarchy_label.setStyleSheet("color: #333; margin-bottom: 5px;") 
        self.left_panel_layout.addWidget(self.file_hierarchy_label) 

        
        # MODIFIED: Create a mini file system viewer for the left panel
        from gui.widgets.file_system_viewer import FileSystemViewerWidget
        self.left_file_tree = QTreeWidget()  # Simple tree for file hierarchy
        self.left_file_tree.setHeaderLabel("No disk image loaded")
        self.left_file_tree.setMinimumWidth(180) 
        self.left_file_tree.setMaximumWidth(300) 
        
        self.left_panel_layout.addWidget(self.left_file_tree) 

        self.main_splitter.addWidget(self.left_panel_container) # Add left panel to splitter

        # Right Panel Container (for Main Content - Tabs)
        self.right_panel_container = QWidget() 
        self.right_panel_layout = QVBoxLayout(self.right_panel_container) 

        # QTabWidget for main content
        self.main_tab_widget = QTabWidget() 
        self.main_tab_widget.setFont(QFont("Arial", 10)) 

        # 1. Overview Tab (Placeholder for general information/welcome)
        self.overview_tab = QWidget() 
        overview_layout = QVBoxLayout(self.overview_tab) 
        # The welcome_label content is now part of the overview tab
        welcome_label_content = ("<h2>Welcome to ByteProbe!</h2>"
                                 "<p>Select an action from the toolbar/menu or open an existing case.</p>"
                                 "<p>To begin, create a <b>New Case</b> or <b>Open Case</b>.</p>")
        self.welcome_label = QLabel(welcome_label_content) # Re-purposed/added this label for the tab
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        overview_layout.addWidget(self.welcome_label) 
        overview_layout.addStretch(1) 
        self.main_tab_widget.addTab(self.overview_tab, "Overview") 

        # 2. Data Sources Tab - Encapsulated in DataSourceViewerWidget
        self.data_source_viewer = DataSourceViewerWidget(self.case_manager) 
        self.main_tab_widget.addTab(self.data_source_viewer, "Data Sources") 

        # 3. File System Tab with actual FileSystemViewerWidget
        self.file_system_viewer = FileSystemViewerWidget()  # Create file system viewer
        self.file_system_viewer.main_window = self  # Add reference to main window
        self.main_tab_widget.addTab(self.file_system_viewer, "File System")  
        
        # Don't create carving and timestamp tabs here - they'll be added dynamically
        
        # Make tabs closable
        self.main_tab_widget.setTabsClosable(True)
        self.main_tab_widget.tabCloseRequested.connect(self.close_tab)  

        self.right_panel_layout.addWidget(self.main_tab_widget) 
        self.main_splitter.addWidget(self.right_panel_container) # Add right panel to splitter

        # Set initial sizes for the splitter sections (e.g., left 20%, right 80%)
        self.main_splitter.setSizes([250, 800]) 

        # Connect data source selection to file system viewer
        self.data_source_viewer.data_source_table.itemSelectionChanged.connect(self._on_data_source_selected)
        
        # ADDED: Connect file system viewer to update left panel tree
        self.file_system_viewer.entry_found = self._update_left_file_tree


    # ADDED: Update left file tree when file system is parsed
    def _update_left_file_tree(self, entry):
        """Update the left panel file tree with parsed entries"""
        if hasattr(self, 'left_file_tree') and entry:
            # This will be called by the file system viewer
            # For now, just update the header to show it's loaded
            if self.left_file_tree.headerItem().text(0) == "No disk image loaded":
                self.left_file_tree.clear()
                self.left_file_tree.setHeaderLabel("File System")
                
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
            self._populate_recent_cases_menu() # Re-populate menu
            # Automatically load the newly created case and update UI
            self._load_case_and_update_ui(created_case_path)
        else:
            QMessageBox.critical(self, "Error", f"Failed to open or verify case '{case_name_for_display}'. It might have failed during creation.")


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
            self.file_carver_action.setEnabled(True)  # ADDED: Enable file carver
            self.timestomping_detection.setEnabled(True)  # ADDED: Enable timestomping
            # Add other case-specific actions to enable/disable here
            # self.plugins_action.setEnabled(True) # if you have these actions
            # self.settings_action.setEnabled(True)
            # self.help_action.setEnabled(True)


            # ADDED: Enable Data Sources tab and set current case for the viewer
            # Ensure these widgets are created in init_main_layout
            self.main_tab_widget.setTabEnabled(1, True) # Data Sources tab (index 1)
            self.main_tab_widget.setTabEnabled(2, True) # File System tab (index 2)
            self.main_tab_widget.setTabEnabled(3, True) # File Carving tab
            self.main_tab_widget.setTabEnabled(4, True) # Timestamp Analysis tab
            self.data_source_viewer.set_current_case(self.current_case_path) # ADDED: Pass the case path to the viewer
            self.main_tab_widget.setCurrentIndex(1) # ADDED: Switch to Data Sources tab by default
            
            # Update overview tab
            self._update_overview_tab(case_metadata)
        else:
            self.statusBar.showMessage("Failed to load case.")
            self._reset_ui_for_no_case() # ADDED: Call reset if loading fails


    # ADDED: Save case method
    def _save_case(self):
        """Save the current case"""
        if not self.current_case_path:
            QMessageBox.information(self, "No Case", "No case is currently open.")
            return
            
        # The case is already saved automatically in SQLite
        # This is just a confirmation
        QMessageBox.information(
            self, 
            "Case Saved", 
            f"Case data is automatically saved.\nCase location: {self.current_case_path}"
        )

    # ADDED: Delete case method
    def _delete_case(self):
        """Delete an existing case"""
        # Get list of recent cases to choose from
        recent_cases = self.case_manager.get_recent_cases()
        if not recent_cases:
            QMessageBox.information(self, "No Cases", "No cases found to delete.")
            return
            
        # Create a simple selection dialog
        from PyQt6.QtWidgets import QInputDialog
        case_names = [case['name'] for case in recent_cases]
        case_name, ok = QInputDialog.getItem(
            self, 
            "Delete Case", 
            "Select a case to delete:", 
            case_names, 
            0, 
            False
        )
        
        if ok and case_name:
            # Find the case path
            case_path = None
            for case in recent_cases:
                if case['name'] == case_name:
                    case_path = case['path']
                    break
                    
            if case_path:
                # Confirm deletion
                reply = QMessageBox.question(
                    self,
                    "Confirm Deletion",
                    f"Are you sure you want to delete the case '{case_name}'?\n\n"
                    f"Path: {case_path}\n\n"
                    "This action cannot be undone!",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        # If it's the current case, close it first
                        if self.current_case_path == case_path:
                            self._reset_ui_for_no_case()
                            
                        # Delete the case directory
                        import shutil
                        shutil.rmtree(case_path)
                        
                        # Update recent cases
                        self._populate_recent_cases_menu()
                        
                        QMessageBox.information(
                            self,
                            "Case Deleted",
                            f"Case '{case_name}' has been deleted successfully."
                        )
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Deletion Error",
                            f"Failed to delete case:\n{str(e)}"
                        )

    def _update_overview_tab(self, case_metadata):
        """Update the overview tab with case information"""
        if hasattr(self, 'case_name_label'):
            self.case_name_label.setText(case_metadata.get('case_name', 'Unknown'))
            self.case_type_label.setText(case_metadata.get('case_type', 'N/A'))
            self.investigator_label.setText(case_metadata.get('investigator_name', 'N/A'))
            
            # Format creation date
            created = case_metadata.get('created', '')
            if created:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created)
                    self.created_label.setText(dt.strftime("%Y-%m-%d %H:%M"))
                except:
                    self.created_label.setText(created)
            else:
                self.created_label.setText('N/A')
                
            # Update activity summary
            self._update_activity_summary()
            
    def _update_activity_summary(self):
        """Update the activity summary in overview tab"""
        if hasattr(self, 'activity_text') and self.current_case_path:
            activities = []
            
            # Check data sources
            sources = self.case_manager.get_data_sources(self.current_case_path)
            if sources:
                activities.append(f"• {len(sources)} data source(s) added")
                
            # Check file system parsing
            if os.path.exists(os.path.join(self.current_case_path, ".file_system_parsed")):
                activities.append("• File system parsed")
                
            # Check carved files
            carved_dir = os.path.join(self.current_case_path, "carved_files")
            if os.path.exists(carved_dir):
                file_count = len([f for f in os.listdir(carved_dir) if os.path.isfile(os.path.join(carved_dir, f))])
                if file_count > 0:
                    activities.append(f"• {file_count} files carved")
                    
            # Check timestamp analysis
            if os.path.exists(os.path.join(self.current_case_path, "timestamp_analysis.json")):
                activities.append("• Timestamp analysis performed")
                
            if activities:
                self.activity_text.setPlainText("Case Activities:\n\n" + "\n".join(activities))
            else:
                self.activity_text.setPlainText("No activities recorded yet.")

    # ADDED: Close Case Method
    def _close_current_case(self):
        if self.current_case_path:
            reply = QMessageBox.question(self, 'Close Case',
                                         f"Are you sure you want to close '{os.path.basename(self.current_case_path)}'?\n\n"
                                         "All data is automatically saved.",
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
        self.file_carver_action.setEnabled(False)  # ADDED
        self.timestomping_detection.setEnabled(False)  # ADDED
        # Add other case-specific actions to disable here
        # self.plugins_action.setEnabled(False)
        # self.settings_action.setEnabled(False)
        # self.help_action.setEnabled(False)

        # Clear data source viewer and disable its tab (and any other case-specific tabs)
        # Ensure main_tab_widget and data_source_viewer are initialized in init_main_layout
        if hasattr(self, 'data_source_viewer'): # Check if it exists before using
             self.data_source_viewer.set_current_case(None) # ADDED: Clear viewer content
        if hasattr(self, 'file_system_viewer'):  # ADDED: Clear file system viewer
            self.file_system_viewer.clear_view()
        if hasattr(self, 'left_file_tree'):  # Clear left file tree
            self.left_file_tree.clear()
            self.left_file_tree.setHeaderLabel("No disk image loaded")
        if hasattr(self, 'main_tab_widget'): # Check if it exists before using
            self.main_tab_widget.setTabEnabled(1, False) # Data Sources tab
            self.main_tab_widget.setTabEnabled(2, False) # File System tab
            # Remove any dynamically added tabs
            for i in range(self.main_tab_widget.count() - 1, 2, -1):  # Start from end, go to index 3
                self.main_tab_widget.removeTab(i)
            self.main_tab_widget.setCurrentIndex(0) # Go back to Overview tab
            
        # Reset overview tab
        if hasattr(self, 'case_name_label'):
            self.case_name_label.setText("No case loaded")
            self.case_type_label.setText("N/A")
            self.investigator_label.setText("N/A")
            self.created_label.setText("N/A")
            self.activity_text.setPlainText("No activity recorded yet.")


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

    # NEW: Handle data source selection
    def _on_data_source_selected(self):
        """Handle when a data source is selected in the data source viewer"""
        selected_items = self.data_source_viewer.data_source_table.selectedItems()
        if selected_items:
            # Get the selected row
            row = selected_items[0].row()
            # Get the path from column 2
            path_item = self.data_source_viewer.data_source_table.item(row, 2)
            if path_item:
                source_path = path_item.text()
                source_type_item = self.data_source_viewer.data_source_table.item(row, 1)
                source_type = source_type_item.text() if source_type_item else ""
                
                # If it's a disk image, update all relevant widgets
                if source_type == "Disk Image" and os.path.exists(source_path):
                    # Update file system viewer
                    self.file_system_viewer.set_disk_image(source_path)
                    
                    # Update file carver widget
                    if hasattr(self, 'file_carver_widget'):
                        self.file_carver_widget.update_from_data_source(source_path, source_type)
                    
                    # Update timestamp widget
                    if hasattr(self, 'timestamp_widget'):
                        self.timestamp_widget.update_from_data_source(source_path, source_type)
                        
                    # Update left panel label
                    if hasattr(self, 'left_file_tree'):
                        self.left_file_tree.setHeaderLabel(f"File System - {os.path.basename(source_path)}")

    # NEW: Show file carver dialog
    def _show_file_carver_dialog(self):
        """Show file carver dialog or functionality"""
        if not self.current_case_path:
            QMessageBox.warning(self, "No Case Open", "Please open a case before using file carver.")
            return
            
        # Check if tab already exists
        for i in range(self.main_tab_widget.count()):
            if self.main_tab_widget.tabText(i) == "File Carving":
                self.main_tab_widget.setCurrentIndex(i)
                return
                
        # Create and add new tab
        from gui.widgets.file_carver_widget import FileCarverWidget
        self.file_carver_widget = FileCarverWidget(self)
        
        # Get current data source if selected
        selected_items = self.data_source_viewer.data_source_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            path_item = self.data_source_viewer.data_source_table.item(row, 2)
            type_item = self.data_source_viewer.data_source_table.item(row, 1)
            
            if path_item and type_item and type_item.text() == "Disk Image":
                self.file_carver_widget.set_disk_image(path_item.text())
        
        index = self.main_tab_widget.addTab(self.file_carver_widget, "File Carving")
        self.main_tab_widget.setCurrentIndex(index)

    # NEW: Show timestamp analysis
    def _show_timestamp_analysis(self):
        """Show timestamp analysis dialog or functionality"""
        if not self.current_case_path:
            QMessageBox.warning(self, "No Case Open", "Please open a case before using timestamp analysis.")
            return
            
        # Check if tab already exists
        for i in range(self.main_tab_widget.count()):
            if self.main_tab_widget.tabText(i) == "Timestamp Analysis":
                self.main_tab_widget.setCurrentIndex(i)
                return
                
        # Create and add new tab
        from gui.widgets.timestamp_analysis_widget import TimestampAnalysisWidget
        self.timestamp_widget = TimestampAnalysisWidget(self)
        
        # Get current data source if selected
        selected_items = self.data_source_viewer.data_source_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            path_item = self.data_source_viewer.data_source_table.item(row, 2)
            type_item = self.data_source_viewer.data_source_table.item(row, 1)
            
            if path_item and type_item and type_item.text() == "Disk Image":
                self.timestamp_widget.set_disk_image(path_item.text())
        
        index = self.main_tab_widget.addTab(self.timestamp_widget, "Timestamp Analysis")
        self.main_tab_widget.setCurrentIndex(index)

    # NEW: Show report generation dialog
    def _show_report_dialog(self):
        """Show report generation dialog"""
        if not self.current_case_path:
            QMessageBox.warning(self, "No Case Open", "Please open a case before generating a report.")
            return
            
        # Import and show dialog
        from gui.dialogs.report_generation_dialog import ReportGenerationDialog
        dialog = ReportGenerationDialog(self, self.current_case_path)
        dialog.exec()

    def close_tab(self, index):
        """Close a tab if it's closable"""
        tab_text = self.main_tab_widget.tabText(index)
        
        # Don't allow closing core tabs
        if tab_text in ["Overview", "Data Sources", "File System"]:
            return
            
        # Check if any operation is running
        widget = self.main_tab_widget.widget(index)
        if hasattr(widget, 'carver_thread') and widget.carver_thread and widget.carver_thread.isRunning():
            QMessageBox.warning(self, "Operation Running", 
                              "Cannot close tab while carving is in progress.")
            return
        if hasattr(widget, 'analysis_thread') and widget.analysis_thread and widget.analysis_thread.isRunning():
            QMessageBox.warning(self, "Operation Running", 
                              "Cannot close tab while analysis is in progress.")
            return
            
        # Remove the tab
        self.main_tab_widget.removeTab(index)
        
    def _show_about_dialog(self):
        # ADDED: Basic About Dialog content (can be customized)
        QMessageBox.about(self, "About ByteProbe",
                          "<b>ByteProbe Forensic Tool</b><br>"
                          "Version 0.1<br>"
                          "A digital forensics application for disk analysis.<br>"
                          "Developed for FYP<br><br>"
                          "© 2024 All rights reserved.")


    def _apply_global_stylesheet(self):
        """Apply global stylesheet to the application"""
        stylesheet = """
        /* Global Font and Colors */
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
            color: #06202B;
            background-color: #f9f9f9;
        }
        
        /* Main Window */
        QMainWindow {
            background-color: #f9f9f9;
        }
        
        /* Central Widget Container */
        #central_widget_container {
            background-color: transparent;
        }
        
        /* Tab Widget */
        QTabWidget::pane {
            border: none;
            background-color: white;
            border-radius: 0px;
        }
        
        QTabBar::tab {
            background-color: #e8e8e8;
            color: #06202B;
            padding: 8px 20px;
            margin-right: 1px;
            border: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        
        QTabBar::tab:selected {
            background-color: #7AE2CF;
            color: #06202B;
            font-weight: bold;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #d0d0d0;
        }
        
        QTabBar::close-button {
            image: url(:/icons/close.png);
            margin-left: 4px;
            padding: 2px;
            border-radius: 2px;
        }
        
        QTabBar::close-button:hover {
            background-color: rgba(255, 107, 107, 0.3);
        }
        
        /* Tree Widget */
        QTreeWidget {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            outline: none;
            color: #06202B;
            selection-background-color: #7AE2CF;
        }
        
        QTreeWidget::item {
            padding: 5px;
            border: none;
        }
        
        QTreeWidget::item:selected {
            background-color: #7AE2CF;
            color: #06202B;
        }
        
        QTreeWidget::item:hover:!selected {
            background-color: rgba(122, 226, 207, 0.2);
        }
        
        /* Table Widget */
        QTableWidget {
            background-color: white;
            gridline-color: #f0f0f0;
            border: none;
            color: #06202B;
        }
        
        QTableWidget::item {
            padding: 8px;
            border: none;
        }
        
        QTableWidget::item:selected {
            background-color: #7AE2CF;
            color: #06202B;
        }
        
        QHeaderView::section {
            background-color: #7AE2CF;
            color: #06202B;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #077A7D;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 4px;
            font-weight: 500;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #055a5d;
        }
        
        QPushButton:pressed {
            background-color: #044244;
        }
        
        QPushButton:disabled {
            background-color: #d0d0d0;
            color: #999999;
        }
        
        /* Group Box */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: white;
            color: #06202B;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #077A7D;
            background-color: white;
        }
        
        /* Progress Bar */
        QProgressBar {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            text-align: center;
            background-color: #f5f5f5;
            color: #06202B;
            height: 20px;
        }
        
        QProgressBar::chunk {
            background-color: #7AE2CF;
            border-radius: 3px;
        }
        
        /* Text Edit */
        QTextEdit {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 6px;
            color: #06202B;
        }
        
        QTextEdit:focus {
            border: 1px solid #7AE2CF;
        }
        
        /* Line Edit */
        QLineEdit {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            color: #06202B;
        }
        
        QLineEdit:focus {
            border: 1px solid #7AE2CF;
        }
        
        /* Combo Box */
        QComboBox {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 6px;
            color: #06202B;
            min-width: 100px;
        }
        
        QComboBox:focus {
            border: 1px solid #7AE2CF;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: url(:/icons/down_arrow.png);
            width: 12px;
            height: 12px;
        }
        
        QComboBox QAbstractItemView {
            background-color: white;
            border: 1px solid #e0e0e0;
            selection-background-color: #7AE2CF;
            selection-color: #06202B;
        }
        
        /* Toolbar - Different from menubar */
        QToolBar {
            background-color: #077A7D;
            border: none;
            spacing: 3px;
            padding: 5px;
        }
        
        QToolBar QToolButton {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 8px;
            margin: 2px;
            color: white;
            font-weight: 500;
        }
        
        QToolBar QToolButton:hover:enabled {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        QToolBar QToolButton:pressed {
            background-color: rgba(255, 255, 255, 0.3);
        }
        
        QToolBar QToolButton:disabled {
            color: rgba(255, 255, 255, 0.4);
        }
        
        /* Menu Bar - Different from toolbar */
        QMenuBar {
            background-color: #06202B;
            color: white;
            border: none;
        }
        
        QMenuBar::item {
            padding: 8px 16px;
            background-color: transparent;
            color: white;
        }
        
        QMenuBar::item:selected {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        
        QMenuBar::item:pressed {
            background-color: #077A7D;
        }
        
        /* Menu dropdown */
        QMenu {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 4px 0px;
        }
        
        QMenu::item {
            padding: 8px 30px;
            color: #06202B;
            border-radius: 4px;
            margin: 2px 4px;
        }
        
        QMenu::item:selected {
            background-color: #7AE2CF;
            color: #06202B;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #e0e0e0;
            margin: 4px 10px;
        }
        
        QMenu::icon {
            margin-right: 8px;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #f5f5f5;
            border-top: 1px solid #e0e0e0;
            color: #06202B;
            padding: 4px;
        }
        
        /* Splitter */
        QSplitter::handle {
            background-color: #e0e0e0;
        }
        
        QSplitter::handle:horizontal {
            width: 2px;
        }
        
        QSplitter::handle:vertical {
            height: 2px;
        }
        
        QSplitter::handle:hover {
            background-color: #7AE2CF;
        }
        
        /* Label specific styling */
        QLabel {
            background-color: transparent;
            color: #06202B;
            border: none;
        }
        
        /* Check Box */
        QCheckBox {
            color: #06202B;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #e0e0e0;
            border-radius: 3px;
            background-color: white;
        }
        
        QCheckBox::indicator:checked {
            background-color: #077A7D;
            border-color: #077A7D;
            image: url(:/icons/check.png);
        }
        
        QCheckBox::indicator:hover {
            border-color: #7AE2CF;
        }
        
        /* Scroll bars */
        QScrollBar:vertical {
            background-color: #f5f5f5;
            width: 12px;
            border: none;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        
        QScrollBar:horizontal {
            background-color: #f5f5f5;
            height: 12px;
            border: none;
            border-radius: 6px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #a0a0a0;
        }
        
        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }
        
        /* File Explorer Panel */
        #left_panel_container {
            background-color: #f5f5f5;
            border-right: 1px solid #e0e0e0;
        }
        """
        
        self.setStyleSheet(stylesheet)

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