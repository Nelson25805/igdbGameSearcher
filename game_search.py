import sys
import pandas as pd
import qdarkstyle

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QProgressBar, QListWidget,
    QMessageBox, QFileDialog, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject

import api  # Now all API logic is centralized in api.py

# Global state similar to your original code
games_list = []           # List of game records
existing_game_ids = set() # To avoid duplicate games
searched_titles = set()   # Track which titles have been searched

# -----------------------
# Worker Class for Searching
# -----------------------
class SearchWorker(QObject):
    progress = pyqtSignal(int, int)  # current step, total steps
    finished = pyqtSignal(list, str)  # list of game records, searched title
    error = pyqtSignal(str)
    
    def __init__(self, game_title, selected_genre_ids):
        super().__init__()
        self.game_title = game_title
        self.selected_genre_ids = selected_genre_ids
        
    def run(self):
        try:
            all_game_data = []
            offset = 0
            # Retrieve all game data matching the search title
            while True:
                query = (f"fields name, first_release_date, rating, genres, storyline, summary, "
                         f"platforms, cover, id; search \"{self.game_title}\"; limit 500; offset {offset};")
                game_data = api.get_game_data(query)
                if not game_data:
                    break
                all_game_data.extend(game_data)
                offset += 500
                if len(game_data) < 500:
                    break
            if not all_game_data:
                self.finished.emit([], self.game_title)
                return
            
            # Filter games by selected genres (if any)
            if self.selected_genre_ids:
                filtered_game_data = [
                    game for game in all_game_data
                    if 'genres' in game and any(genre in self.selected_genre_ids for genre in game['genres'])
                ]
            else:
                filtered_game_data = all_game_data
            
            if not filtered_game_data:
                self.error.emit("No games match the selected genres.")
                self.finished.emit([], self.game_title)
                return
            
            total = len(filtered_game_data)
            results = []
            count = 0
            for game in filtered_game_data:
                count += 1
                if game.get('id') in existing_game_ids:
                    self.progress.emit(count, total)
                    continue
                game_info = {
                    "Name": game.get('name', 'Not Available'),
                    "Release Date": api.format_unix_timestamp(game.get('first_release_date')),
                    "Rating": game.get('rating', 'Not Available'),
                    "Genres": ', '.join(api.fetch_genre_names(game.get('genres', []), api.GENRE_MAP)),
                    "Storyline": game.get('storyline', 'Not Available'),
                    "Summary": game.get('summary', 'Not Available'),
                    "Platforms": ', '.join(api.fetch_platform_names(game.get('platforms', []), api.PLATFORM_MAP)),
                    "Cover URL": api.fetch_cover_image(game.get('cover'))
                }
                results.append(game_info)
                existing_game_ids.add(game.get('id'))
                self.progress.emit(count, total)
            self.finished.emit(results, self.game_title)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit([], self.game_title)

# -----------------------
# Main Game Search Window (PyQt version)
# -----------------------
class GameSearchWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Search")
        self.resize(800, 600)
        self.games_list = []  # local storage of game records
        
        # Main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Game Search", self)
        title_label.setObjectName("title_label")
        main_layout.addWidget(title_label)
        
        # Input for game title in a horizontal layout with minimal spacing
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)  # Reduce spacing so label and QLineEdit are close
        entry_label = QLabel("Enter game title:", self)
        input_layout.addWidget(entry_label)
        self.entry = QLineEdit(self)
        self.entry.setFixedWidth(300)
        input_layout.addWidget(self.entry)
        main_layout.addLayout(input_layout)
        
        # Create a horizontal layout for the genre checkboxes and search history list
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        # Genre selection checkboxes in a grid layout (3 columns)
        self.genre_checkbox_widget = QWidget(self)
        checkbox_layout = QGridLayout(self.genre_checkbox_widget)
        checkbox_layout.setSpacing(5)
        self.genre_checkboxes = {}
        genres = list(api.GENRE_MAP.values())
        columns = 3  # adjust number of columns as needed
        for idx, genre in enumerate(genres):
            checkbox = QCheckBox(genre, self)
            self.genre_checkboxes[genre] = checkbox
            row = idx // columns
            col = idx % columns
            checkbox_layout.addWidget(checkbox, row, col)
        info_layout.addWidget(self.genre_checkbox_widget)
        
        # Search history list with fixed dimensions
        self.search_history_list = QListWidget(self)
        self.search_history_list.setMinimumWidth(150)
        self.search_history_list.setMaximumHeight(200)
        info_layout.addWidget(self.search_history_list)
        
        main_layout.addLayout(info_layout)
        
        # Progress bar and live count label
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        main_layout.addWidget(self.progress_bar)
        
        self.live_count_label = QLabel("Unique Games Added: 0", self)
        main_layout.addWidget(self.live_count_label)
        
        # Buttons: Search, Save, Back in a horizontal layout
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.on_search)
        button_layout.addWidget(self.search_button)
        
        self.save_button = QPushButton("Save to Excel", self)
        self.save_button.clicked.connect(self.on_save)
        button_layout.addWidget(self.save_button)
        
        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(self.back_to_main)
        button_layout.addWidget(self.back_button)
        
        main_layout.addLayout(button_layout)
        
    def get_selected_genre_ids(self):
        """Return a list of selected genre IDs for query filtering."""
        selected_ids = []
        for genre, checkbox in self.genre_checkboxes.items():
            if checkbox.isChecked():
                # Reverse lookup to get the id from GENRE_MAP
                for id_, name in api.GENRE_MAP.items():
                    if name == genre:
                        selected_ids.append(id_)
                        break
        return selected_ids
    
    def get_selected_genre_names(self):
        """Return a sorted list of selected genre names for display and duplicate checking."""
        selected_names = [genre for genre, checkbox in self.genre_checkboxes.items() if checkbox.isChecked()]
        selected_names.sort()
        return selected_names
    
    def on_search(self):
        game_title = self.entry.text().strip().lower()
        if not game_title:
            QMessageBox.warning(self, "Input Error", "Please enter a game title.")
            return
        
        # Build a composite search key from the game title and selected genres
        selected_genre_names = self.get_selected_genre_names()
        if selected_genre_names:
            search_key = f"{game_title} | {','.join(selected_genre_names)}"
        else:
            search_key = game_title
        
        if search_key in searched_titles:
            QMessageBox.information(self, "Duplicate Search", f"Search for '{search_key}' has already been done.")
            return
        
        # Disable buttons
        self.search_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.back_button.setEnabled(False)
        
        selected_genre_ids = self.get_selected_genre_ids()
        
        self.thread = QThread()
        self.worker = SearchWorker(game_title, selected_genre_ids)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.search_finished)
        self.worker.error.connect(self.search_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    
    def update_progress(self, current, total):
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.live_count_label.setText(f"Unique Games Added: {len(existing_game_ids)}")
    
    def search_finished(self, results, game_title):
        global searched_titles
        # Build the composite key again to store in searched_titles and display in history.
        selected_genre_names = self.get_selected_genre_names()
        if selected_genre_names:
            search_key = f"{game_title} | {','.join(selected_genre_names)}"
        else:
            search_key = game_title

        searched_titles.add(search_key)
        self.search_history_list.insertItem(0, f"{len(searched_titles)}) {search_key}")
        self.progress_bar.setValue(0)
        self.entry.clear()
        if not results:
            QMessageBox.information(self, "No Results", f"No game data found for '{search_key}'.")
        else:
            self.games_list.extend(results)
            QMessageBox.information(self, "Success", f"Game data for '{search_key}' has been fetched.")
        self.search_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.back_button.setEnabled(True)
        
    def search_error(self, error_message):
        QMessageBox.information(self, "Error", error_message)
        self.search_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.back_button.setEnabled(True)
        
    def on_save(self):
        if not self.games_list:
            QMessageBox.warning(self, "No Data", "There are no games to save.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx);;All Files (*)")
        if file_path:
            try:
                df = pd.DataFrame(self.games_list)
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Success", f"File saved successfully to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while saving: {str(e)}")
                
    def back_to_main(self):
        from main import MainWindow
        global main_window
        main_window = MainWindow()
        main_window.show()
        self.close()
        
def load_stylesheet(file_path):
    with open(file_path, "r") as f:
        return f.read()
    
def closeEvent(self, event):
    if hasattr(self, 'thread') and self.thread.isRunning():
        self.thread.quit()
        self.thread.wait()
    event.accept()


def main():
    app = QApplication(sys.argv)
    # Load the dark theme first.
    dark_style = qdarkstyle.load_stylesheet_pyqt5()
    # Then load your size styling overrides.
    size_style = load_stylesheet("style.qss")
    
    # Combine them (size_style overrides where applicable)
    app.setStyleSheet(dark_style + "\n" + size_style)
    window = GameSearchWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
