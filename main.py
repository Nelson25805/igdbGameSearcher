import tkinter as tk
from tkinter import ttk
from random_game_search import open_random_game_search

import ttkbootstrap as tb

# Shared state between modules
shared_state = {}

def show_main_screen(root, splash_frame):
    # Hide the splash screen
    splash_frame.pack_forget()

    # Main Page Frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill="both", expand=True)

    # Main page content
    main_label = ttk.Label(main_frame, text="Welcome to the Game Search Application!", font=("Arial", 16))
    main_label.pack(pady=10)

    random_game_button = ttk.Button(
        main_frame, text="Random Game Search",
        command=lambda: open_random_game_search(root, main_frame, shared_state, show_frame)
    )
    random_game_button.pack(padx=30, pady=10)

    state_button = ttk.Button(
        main_frame, text="Show Shared State",
        command=lambda: print(shared_state)
    )
    state_button.pack(padx=30, pady=10)

def create_splash_screen(root):
    # Splash Screen Frame
    splash_frame = ttk.Frame(root)
    splash_frame.pack(fill="both", expand=True)

    # Add a background color
    root.configure(bg="#2e3f4f")  # Example dark background color

    # Splash Screen Content
    splash_label = tk.Label(
        splash_frame,
        text="Game Search Application",
        font=("Arial", 24, "bold"),
        bg="#2e3f4f",
        fg="white"
    )
    splash_label.pack(expand=True)

    # Footer text
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

# Initialize the root window
root = tb.Window(themename="cyborg")
root.title("Game Search Application")
root.geometry("2300x1000")  # Set a consistent size for the window

# Disable maximize and minimize buttons
root.resizable(False, False)  # Disable resizing

# Create the splash screen
create_splash_screen(root)

# Start the main loop
root.mainloop()
