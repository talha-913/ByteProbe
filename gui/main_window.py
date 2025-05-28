
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
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
        self._createToolBar()
        self._createStatusBar()

        # Central Widget 
        self._createCentralWidget()

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

    def _createMenu(self):
        menu = self.menuBar()
        
    def _createToolBar(self):
        tools = QToolBar()

    def _createStatusBar(self):
        status = QStatusBar()
        

if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())