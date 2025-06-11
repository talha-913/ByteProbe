
import sys
import os

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMenu,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QStatusBar,
    QToolBar,
)

import resources_rc

class Window(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("ByteProbe")
        

        # handles the window size
        # self.showMaximized()  #- for maximized screen sized win
        # self.showFullScreen() #- for fullscreen sized window
        # self.setMinimumSize(00, 00) #- can't be minimized further below
        self.resize(1300, 700) # for initial window size

        self._createActions()
        self._createToolBars()
        self._createMenuBar()
        
        # self._createStatusBar()

        # Central Widget 
        self._createCentralWidget()

    def _createActions(self):
        # hosts all the actions of req. for menubar&toolbar
        # File Actions
        self.new_case_action = QAction(QIcon(":/icons/new_case"), "&New Case", self) 
        self.new_case_action.setShortcut("Ctrl+N")
        self.new_case_action.setStatusTip("Create a new forensics case")

        self.open_case_action = QAction(QIcon(":/icons/open_case"), "&Open Case...", self)
        self.open_case_action.setShortcut("Ctrl+O")
        self.open_case_action.setStatusTip("Open an existing forensics case")

        self.save_case_action = QAction(QIcon(":/icons/save_case"), "&Save Case", self)
        self.save_case_action.setShortcut("Ctrl+S")
        self.save_case_action.setStatusTip("Save the current forensics case")

        self.exit_action = QAction("E&xit", self)
        self.exit_action.setStatusTip("Exit the ByteProbe application")

        # Edit Actions
        self.undo_action = QAction(QIcon(":/icons/undo"), "&Undo", self)
        self.undo_action.setStatusTip("Undo the last action")

        self.redo_action = QAction(QIcon(":/icons/redo"), "&Redo", self)
        self.redo_action.setStatusTip("Redo the last undone action")

        self.cut_action = QAction(QIcon(":/icons/cut"), "Cu&t", self)
        self.cut_action.setStatusTip("Cut the selected content")

        self.copy_action = QAction(QIcon(":/icons/copy"), "&Copy", self)
        self.copy_action.setStatusTip("Copy the selected content")

        self.paste_action = QAction(QIcon(":/icons/paste"), "&Paste", self)
        self.paste_action.setStatusTip("Paste content from the clipboard")

        self.find_action = QAction( "&Find...", self)
        self.find_action.setStatusTip("Find text or patterns within the current view")

        self.replace_action = QAction("Re&place...", self)
        self.replace_action.setStatusTip("Find and replace text or patterns")


        # View Actions
        self.toolbar_action = QAction( "&Toolbar", self)
        self.toolbar_action.setStatusTip("Toggle visibility of the main toolbar")

        self.statusbar_action = QAction( "&Status Bar", self)
        self.statusbar_action.setStatusTip("Toggle visibility of the status bar")

        self.filelist_action = QAction(QIcon(":/icons/folder_tree"), "&File List", self)
        self.filelist_action.setStatusTip("Toggle visibility of the file list pane")

        # Tools Actions
        self.hash_calc_action = QAction(QIcon(":/icons/hash_calc"), "&Hash Calculator", self)
        self.hash_calc_action.setStatusTip("Calculate MD5, SHA1, SHA256 hashes for files")

        self.file_carver_action = QAction(QIcon(":/icons/file_carver.png"), "&File Carver", self)
        self.file_carver_action.setStatusTip("Recover deleted files by carving disk images")

        self.options_action = QAction( "&Options...", self)
        self.options_action.setStatusTip("Configure application settings")

        # Help Actions
        self.about_action = QAction(QIcon(":/icons/about"), "&About ByteProbe", self)
        self.about_action.setStatusTip("Learn more about ByteProbe")


    def _createMenuBar(self):
        menu_bar = self.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File") # & makes the next character an accelerator key (Alt+F)        
        # self.new_case_action.triggered.connect(self._newCase)
        file_menu.addAction(self.new_case_action)
        # self.open_case_action.triggered.connect(self._openCase)
        file_menu.addAction(self.open_case_action)
        # self.save_case_action.triggered.connect(self._saveCase)
        file_menu.addAction(self.save_case_action)
        file_menu.addSeparator()
        # self.exit_action.triggered.connect(self.close) # Connects to QMainWindow's close method
        file_menu.addAction(self.exit_action)


        # --- Edit Menu ---
        edit_menu = menu_bar.addMenu("&Edit")
        # self.undo_action.triggered.connect(lambda: self._editOption("Undo"))
        edit_menu.addAction(self.undo_action)
        # self.redo_action.triggered.connect(lambda: self._editOption("Redo"))
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        # self.cut_action.triggered.connect(lambda: self._editOption("Cut"))
        edit_menu.addAction(self.cut_action)
        # self.copy_action.triggered.connect(lambda: self._editOption("Copy"))
        edit_menu.addAction(self.copy_action)
        # self.paste_action.triggered.connect(lambda: self._editOption("Paste"))
        edit_menu.addAction(self.paste_action)
        edit_menu.addSeparator()
        find_replace_menu = edit_menu.addMenu(QIcon(":/icons/find"), "Find & Replace")        
        # self.find_action.triggered.connect(lambda: self._editOption("Find"))
        find_replace_menu.addAction(self.find_action)
        # self.replace_action.triggered.connect(lambda: self._editOption("Replace"))
        find_replace_menu.addAction(self.replace_action)

         # --- View Menu ---
        view_menu = menu_bar.addMenu("&View")

        # Action for Toggling Toolbar Visibility
        self.toolbar_action.setCheckable(True)
        # Assuming self.toolbar exists and is initially visible
        if hasattr(self, 'main_toolbar') and isinstance(self.main_toolbar, QToolBar):
            print("YES EXISTS")
            self.toolbar_action.setChecked(self.main_toolbar.isVisible())
            self.toolbar_action.triggered.connect(self.main_toolbar.setVisible)
        else:
            self.toolbar_action.setEnabled(False) # Disable if toolbar is not available
        view_menu.addAction(self.toolbar_action)

        # Action for Toggling Status Bar Visibility
        self.statusbar_action.setCheckable(True)
        # Assuming self.statusBar() returns a QStatusBar object
        if self.statusBar():
            self.statusbar_action.setChecked(self.statusBar().isVisible())
            self.statusbar_action.triggered.connect(self.statusBar().setVisible)
        else:
            self.statusbar_action.setEnabled(False) # Disable if status bar is not available
        view_menu.addAction(self.statusbar_action)

        view_menu.addSeparator()
        # Action for Toggling File List Visibility
        self.filelist_action.setCheckable(True)
        # Assuming self.file_list_widget exists
        if hasattr(self, 'file_list_widget') and isinstance(self.file_list_widget, QWidget):
            self.filelist_action.setChecked(self.file_list_widget.isVisible())
            self.filelist_action.triggered.connect(self.file_list_widget.setVisible)
        else:
            self.filelist_action.setEnabled(False) # Disable if widget is not available
        view_menu.addAction(self.filelist_action)

        # --- Tools Menu ---
        tools_menu = menu_bar.addMenu("&Tools")
        # self.hash_calc_action.triggered.connect(self._hashCalculator)
        tools_menu.addAction(self.hash_calc_action)
        # self.file_carver_action.triggered.connect(self._fileCarver)
        tools_menu.addAction(self.file_carver_action)
        self.disk_imager_action = QAction(QIcon(":/icons/disk_reader"), "&Disk Imager", self)
        self.disk_imager_action.setStatusTip("Create forensic images of disks or partitions")
        # self.disk_imager_action.triggered.connect(self._diskImager)
        tools_menu.addAction(self.disk_imager_action)
        tools_menu.addSeparator()
        # self.options_action.triggered.connect(self._options)
        tools_menu.addAction(self.options_action)

        # --- Help Menu ---
        help_menu = menu_bar.addMenu("&Help")
        # self.about_action.triggered.connect(self._about)
        help_menu.addAction(self.about_action)



    def _createToolBars(self):
        self.main_toolbar = self.addToolBar("main_toolbar")
        self.main_toolbar.addAction(self.new_case_action)
        self.main_toolbar.addAction(self.open_case_action)
        self.main_toolbar.addAction(self.save_case_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.undo_action)
        self.main_toolbar.addAction(self.redo_action)
        self.main_toolbar.addAction(self.copy_action)
        self.main_toolbar.addAction(self.paste_action)




        

    def _createCentralWidget(self):
        # Create a central widget to hold main application content
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Placeholder for main forensics content
        self.content_label = QLabel("Welcome to ByteProbe!")
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("font-size: 18px; color: #333; padding: 20px;")
        layout.addWidget(self.content_label)
        layout.addStretch() # Pushes the label to the top    


     

if __name__ == "__main__":
    app = QApplication([])
    # app.setStyle('Windows')
    window = Window()
    window.show()
    sys.exit(app.exec())