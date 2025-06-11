import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QRect, QSize, QTimer

class SplashScreen(QWidget):
    """

    Usage:
        1. Instantiate the SplashScreen:
           splash = SplashScreen(message="Starting Up...")
        2. Show the splash screen:
           splash.show()
        3. Perform application's loading/setup tasks.
        4. When done, close the splash screen:
           splash.close()
    """
    def __init__(self, message="Loading Application..."):
        super().__init__(parent=None)
        self.setWindowTitle("Loading...")
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)

        # Define a fixed size for the splash screen for consistent appearance.
        splash_width = 600
        splash_height = 400
        self.setFixedSize(QSize(splash_width, splash_height))

        # Setup the layout and content for the splash screen.
        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center the text horizontally and vertically
        # Apply basic styling for visibility and aesthetic appeal.
        # self.label.setStyleSheet("font-size: 24px; color: white; background-color: #4CAF50; border-radius: 50px;")
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Center the splash screen on the user's primary display.
        self.center_on_screen()

    def center_on_screen(self):

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        # Get the current frame geometry of this widget.
        qr = self.frameGeometry()

        qr.moveCenter(screen_geometry.center())

        self.move(qr.topLeft())    # understanding this later------------


def test_splash_screen():
        app = QApplication(sys.argv)

        # Instantiate and show the splash screen
        splash = SplashScreen()
        splash.show()

        # Set a timer to close the splash screen after 3 seconds
        QTimer.singleShot(3000, splash.close)

        # Start the application event loop
        sys.exit(app.exec())

if __name__ == '__main__':
    print("SplashScreen class.")
    test_splash_screen()