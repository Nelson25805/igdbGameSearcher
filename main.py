import os, sys
import qdarkstyle
from PyQt5.QtWidgets import (
    QApplication, QSplashScreen, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy, 
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QTimer, Qt

# Import the other modules to load faster
import game_search
import random_game_search

# Helper function to get the resource path for PyInstaller
def resource_path(relative_path):
    try:
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
        
        self.setWindowIcon(QIcon(resource_path("images/splash.ico")))

        # Set up central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Welcome message
        title_label = QLabel("Welcome to the IGDB Game Searcher!", self)
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
               # Create a horizontal layout for the two buttons (each with its own vertical layout)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # First column: Search Games
        search_layout = QVBoxLayout()
        search_layout.setSpacing(5)  # Reduce vertical spacing between the button and its description
        search_button = QPushButton("Search Games", self)
        search_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        search_button.clicked.connect(self.launch_search)
        search_layout.addWidget(search_button)
        
        search_desc = QLabel("Click here to search for games by title and view detailed information.", self)
        search_desc.setWordWrap(True)
        search_desc.setAlignment(Qt.AlignCenter)
        search_layout.addWidget(search_desc)
        
        button_layout.addLayout(search_layout)

        # Second column: Random Game Search
        random_layout = QVBoxLayout()
        random_layout.setSpacing(5)  # Reduce spacing here as well
        random_button = QPushButton("Random Game Search", self)
        random_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        random_button.clicked.connect(self.launch_random_game_search)
        random_layout.addWidget(random_button)
        
        random_desc = QLabel("Click here to fetch and display a random game from our database.", self)
        random_desc.setWordWrap(True)
        random_desc.setAlignment(Qt.AlignCenter)
        random_layout.addWidget(random_desc)
        
        button_layout.addLayout(random_layout)

        
        layout.addLayout(button_layout)

    def launch_search(self):
        from game_search import GameSearchWindow
        global main_window
        main_window = GameSearchWindow()
        main_window.show()
        self.close()

    def launch_random_game_search(self):
        from random_game_search import RandomGameSearchWindow
        global main_window
        main_window = RandomGameSearchWindow()
        main_window.show()
        self.close()

def load_stylesheet(file_path):
    """Load external stylesheet from file."""
    with open(file_path, "r") as file:
        return file.read()

def main():
    # Enable High DPI scaling and high DPI pixmaps
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Set the application-wide icon
    icon_path = resource_path("images/splash.ico")  # Update the path if necessary
    app.setWindowIcon(QIcon(icon_path))
    
    # Load the dark theme first.
    dark_style = qdarkstyle.load_stylesheet_pyqt5()
    # Then load your size styling overrides from your external file.
    size_style = load_stylesheet(resource_path("style.qss"))
    
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
