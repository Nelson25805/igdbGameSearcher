import tkinter as tk
from tkinter import ttk

def open_game_search():
    # Create a new window for game search
    game_search_window = tk.Toplevel()
    game_search_window.title("Game Search")

    # Example: Add search functionality like input fields and buttons
    search_button = ttk.Button(game_search_window, text="Search Game", command=fetch_random_game_gui)  # Replace with your actual search function
    search_button.grid(row=0, column=0, pady=10)

    # Add the labels and textboxes you already have for displaying game data
    game_name_label = ttk.Label(game_search_window, text="Game Name:", font=("Arial", 12, "bold"))
    game_name_label.grid(row=1, column=0, sticky="nw", pady=5)

    game_name_text = tk.Text(game_search_window, height=2, wrap="word")
    game_name_text.grid(row=1, column=1, sticky="ew", padx=(5, 0))

# You can import this file in `main.py` and call `open_game_search` when required
