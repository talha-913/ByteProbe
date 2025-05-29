
import sys

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

class Window(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("ByteProbe")
        

        # handles the window size
        # self.showMaximized()  #- for maximized screen sized win
        # self.showFullScreen() #- for fullscreen sized window
        # self.setMinimumSize(00, 00) #- can't be minimized further below
        self.resize(1300, 700) # for initial window size


        self._createMenu()
        # self._createToolBar()
        # self._createStatusBar()

        # Central Widget 
        self._createCentralWidget()


    def _createMenu(self):
        menu_bar = self.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File") # & makes the next character an accelerator key (Alt+F)

        # File Actions
        self.new_case_action = QAction("&New Case", self) # Placeholder icon
        self.new_case_action.setShortcut("Ctrl+N")
        self.new_case_action.setStatusTip("Create a new forensics case")
        # self.new_case_action.triggered.connect(self._newCase)
        file_menu.addAction(self.new_case_action)

        self.open_case_action = QAction("&Open Case...", self)
        self.open_case_action.setShortcut("Ctrl+O")
        self.open_case_action.setStatusTip("Open an existing forensics case")
        # self.open_case_action.triggered.connect(self._openCase)
        file_menu.addAction(self.open_case_action)

        self.save_case_action = QAction("&Save Case", self)
        self.save_case_action.setShortcut("Ctrl+S")
        self.save_case_action.setStatusTip("Save the current forensics case")
        # self.save_case_action.triggered.connect(self._saveCase)
        file_menu.addAction(self.save_case_action)

        file_menu.addSeparator()

        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Exit the ByteProbe application")
        # self.exit_action.triggered.connect(self.close) # Connects to QMainWindow's close method
        file_menu.addAction(self.exit_action)

        

    def _createCentralWidget(self):
        # Create a central widget to hold your main application content
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Placeholder for your main forensics content
        self.content_label = QLabel("Welcome to ByteProbe!")
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("font-size: 18px; color: #333; padding: 20px;")
        layout.addWidget(self.content_label)
        layout.addStretch() # Pushes the label to the top    


     

if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())