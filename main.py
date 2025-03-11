import tkinter as tk
from tkinter import ttk
import sys, os
from random_game_search import open_random_game_search
from game_search import open_game_search
import ttkbootstrap as tb

# Shared state between modules
shared_state = {}

def resource_path(relative_path):
    """Get the absolute path for PyInstaller bundled files."""
    if getattr(sys, '_MEIPASS', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def show_main_screen(root, splash_frame):
    # Hide the splash screen
    splash_frame.pack_forget()

    # Create the main page frame and fill the window
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill="both", expand=True)
    
    # Create a centered container frame to hold the UI elements
    container = ttk.Frame(main_frame)
    container.place(relx=0.5, rely=0.5, anchor="center")
    
    # Title label at the top of the container
    title_label = ttk.Label(
        container, 
        text="Welcome to the IGDB Game Search Application!", 
        font=("Arial", 24, "bold")
    )
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # Random Game Search Section
    random_frame = ttk.Frame(container)
    random_frame.grid(row=1, column=0, padx=20, pady=20, sticky='n')
    
    random_game_button = ttk.Button(
        random_frame,
        text="Random Game Search",
        command=lambda: open_random_game_search(root, main_frame, shared_state, show_frame)
    )
    random_game_button.pack(pady=(0, 5))
    
    random_desc = ttk.Label(
        random_frame,
        text="Launch a search that fetches a random game from the IGDB database.",
        font=("Arial", 14),
        wraplength=800,
        justify="center"
    )
    random_desc.pack(pady=(0, 20))
    
    # Game Searcher Section (Updated to Match Random Game Search)
    search_frame = ttk.Frame(container)
    search_frame.grid(row=1, column=1, padx=20, pady=20, sticky='n')
    
    search_game_button = ttk.Button(
        search_frame,
        text="Filtered Game Search",
        command=lambda: open_game_search(root, main_frame, shared_state, show_frame)
    )
    search_game_button.pack(pady=(0, 5))
    
    search_desc = ttk.Label(
        search_frame,
        text="Search for a game by title and filter by genre. You can also save your searches to an Excel file.",
        font=("Arial", 14),
        wraplength=800,
        justify="center"
    )
    search_desc.pack(pady=(0, 20))


def create_splash_screen(root):
    splash_frame = ttk.Frame(root)
    splash_frame.pack(fill="both", expand=True)
    
    # Set a dark background color for the splash screen
    root.configure(bg="#2e3f4f")
    
    splash_label = tk.Label(
        splash_frame,
        text="Game Search Application",
        font=("Arial", 24, "bold"),
        bg="#2e3f4f",
        fg="white"
    )
    splash_label.pack(expand=True)
    
    footer_label = tk.Label(
        splash_frame,
        text="Loading, please wait...",
        font=("Arial", 12, "italic"),
        bg="#2e3f4f",
        fg="white"
    )
    footer_label.pack(pady=20)
    
    # Transition to the main screen after 3 seconds
    root.after(3000, lambda: show_main_screen(root, splash_frame))

def show_frame(frame):
    for widget in root.winfo_children():
        widget.pack_forget()
    frame.pack(fill="both", expand=True)

# Initialize the root window using ttkbootstrap
root = tb.Window(themename="cyborg")
root.title("Game Search Application")
root.iconbitmap(resource_path("images/controller.ico"))

# Dynamically adjust the window size based on screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.7)
window_height = int(screen_height * 0.7)
root.geometry(f"{window_width}x{window_height}")

# Configure button style to be larger
style = tb.Style()
style.configure('TButton', font=("Arial", 18, "bold"), padding=15)

# Create the splash screen
create_splash_screen(root)

# Start the main loop
root.mainloop()
