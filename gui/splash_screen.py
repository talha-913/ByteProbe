import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QRect, QSize, QTimer # QTimer is essential for dynamic updates
from PyQt6.QtGui import QPixmap, QFont # For image and font handling

class SplashScreen(QWidget):
   
    def __init__(self, logo_path, messages=None):
        super().__init__()
        self.setWindowTitle("Loading...")
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)

        # Define basic dimensions for the splash screen
        splash_width = 600
        splash_height = 400
        self.setFixedSize(QSize(splash_width, splash_height))

        # --- Splash Screen Styling (Background) ---
        # A gradient background for a modern look
        self.setStyleSheet(
            "QWidget {"
            "   background: #06202B;"
            "   border-radius: 100px;" # Rounded corners for the whole window
            "}"
        )

        # --- Layout for content ---
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center content vertically

        # --- Logo (if provided) ---
        if logo_path:
            self.logo_label = QLabel(self)
    
            pixmap = QPixmap(logo_path)

            if pixmap.isNull():
                # Fallback
                self.logo_label.setText("LOGO FAILED TO LOAD")
                self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.logo_label.setStyleSheet("color: red; font-size: 14px;")
            else:
                # Scale pixmap if it's too large, maintaining aspect ratio
                if pixmap.width() > 150 or pixmap.height() > 150:
                    pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(pixmap)
                self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            main_layout.addWidget(self.logo_label)
            main_layout.addSpacing(20)

        # --- Dynamic Message Label ---
        self.message_label = QLabel(self)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.message_label.setFont(QFont("Courier New", 16)) 
        self.message_label.setStyleSheet("color: white; margin-bottom: 5px;") 
        main_layout.addWidget(self.message_label)

        # --- Progress Bar ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100) 
        self.progress_bar.setValue(0) # Initial value
        self.progress_bar.setTextVisible(False) # Hide default percentage text
        self.progress_bar.setFixedHeight(8) # Set a fixed height
        self.progress_bar.setStyleSheet(
            "QProgressBar {"
            "   border: 2px solid black;" 
            "   border-radius: 7px;"
            "   background-color: #F5EEDD;" # Light grey background for empty part
            "   text-align: center;"
            "}"
            "QProgressBar::chunk {"
            "   background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "                                    stop:0 #7AE2CF, stop:1 #2980B9);" # Blue gradient for filled part
            "   border-radius: 5px;"
            "}"
        )
        main_layout.addWidget(self.progress_bar)
        main_layout.addSpacing(10) # Space below progress bar

        self.setLayout(main_layout)

        # --- Dynamic Text and Progress Management ---
        self.messages = messages if messages else ["Loading...", "Please wait...", "Almost done!"]
        self.current_message_index = 0
        self.message_label.setText(self.messages[self.current_message_index])

        # Calculate step for progress bar based on number of messages
        self.progress_step = 100 // len(self.messages)
        self.progress_bar.setValue(self.progress_step) # Set initial progress

        # Timer for updating messages and progress
        self.update_timer = QTimer(self)
        # Interval for each message (e.g., 800ms per message)
        self.update_interval_ms = 800
        self.update_timer.timeout.connect(self._update_splash_content)
        self.update_timer.start(self.update_interval_ms)

        # Center the splash screen on the user's primary display.
        self.center_on_screen()

    def _update_splash_content(self):

        self.current_message_index += 1
        if self.current_message_index < len(self.messages):
            self.message_label.setText(self.messages[self.current_message_index])
            # Increment progress bar
            current_progress = self.progress_bar.value() + self.progress_step
            if self.current_message_index == len(self.messages) - 1: 
                self.progress_bar.setValue(100)
            else:
                self.progress_bar.setValue(current_progress)
        else:
            # All messages displayed, stop timer and close splash
            self.update_timer.stop()
            self.close() # Close the splash screen

    def center_on_screen(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        qr = self.frameGeometry()
        qr.moveCenter(screen_geometry.center())
        self.move(qr.topLeft())


if __name__ == '__main__':
    print("SplashScreen class")