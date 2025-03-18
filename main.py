import os, sys
import qdarkstyle
from PyQt5.QtWidgets import (
    QApplication, QSplashScreen, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt

# Helper function to get the resource path for PyInstaller
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Global variable to keep a reference to the main window
main_window = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Searcher")
        self.resize(600, 400)

        # Set up central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Welcome message
        welcome_label = QLabel("Welcome to Game Searcher!", self)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("Arial", 24))
        layout.addWidget(welcome_label)
        
        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # Existing buttons (for demonstration, these launch other scripts)
        search_button = QPushButton("Search Games", self)
        search_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        search_button.setFont(QFont("Arial", 16))
        search_button.clicked.connect(self.launch_search)
        button_layout.addWidget(search_button)

        # New button for Random Game Search
        random_game_button = QPushButton("Random Game Search", self)
        random_game_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        random_game_button.setFont(QFont("Arial", 16))
        random_game_button.clicked.connect(self.launch_random_game_search)
        button_layout.addWidget(random_game_button)

        layout.addLayout(button_layout)

    def launch_search(self):
        from game_search import GameSearchWindow
        global main_window
        # Replace the current window with the new one
        main_window = GameSearchWindow()
        main_window.show()
        self.close()

    def launch_random_game_search(self):
        # Import the RandomGameSearchWindow class from random_game_search.py
        from random_game_search import RandomGameSearchWindow
        global main_window
        # Replace the current window with the new one
        main_window = RandomGameSearchWindow()
        main_window.show()
        self.close()
def load_stylesheet(file_path):
    with open(file_path, "r") as f:
        return f.read()

def main():
    # Enable High DPI scaling and high DPI pixmaps
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    # Load the dark theme first.
    dark_style = qdarkstyle.load_stylesheet_pyqt5()
    # Then load your size styling overrides.
    size_style = load_stylesheet("style.qss")
    
    # Combine them (size_style overrides where applicable)
    app.setStyleSheet(dark_style + "\n" + size_style)
    
    # Set up the splash screen using resource_path to locate the image in the bundled exe.
    splash_pix = QPixmap(resource_path("images/splash.png"))
    if splash_pix.isNull():
        print("Splash image not found. Please ensure 'splash.png' exists in the images folder.")
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.showMessage("Loading application...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    splash.show()
    
    # Process events so the splash screen displays immediately
    app.processEvents()
    
    # After a simulated loading delay, close splash and show main window
    def show_main():
        global main_window
        splash.close()
        main_window = MainWindow()
        main_window.show()
    
    QTimer.singleShot(3000, show_main)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
