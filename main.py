import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt, QTimer 

# Import the SplashScreen class from the Gui sub-directory
from gui.splash_screen import SplashScreen

# Import main window class from the Gui sub-directory
from gui.main_window import MainWindow


if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    # --- Splash Screen Management ---
    splash = SplashScreen(
        logo_path=r"assets\icons\open_case.svg",
        messages=[
            "Starting up components...",
            "Loading user configurations...",
            "Preparing workspace...",
            "Almost ready!",
            "Welcome!"
        ]
    )
    splash.show() 

    main_window = MainWindow()
    
    QTimer.singleShot(3500, lambda: (
        splash.close(),
        main_window.show_and_initiate_case_dialog()
    ))


    sys.exit(app.exec())