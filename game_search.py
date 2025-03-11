# This python script is a GUI video game search engine interface from the IGDB website database.
# After searching for all the video games the user searched for, you have the option to save the searches in an excel file.
# Each game has the name, release date, rating, genres, storyline, summary, platforms, cover url for its record.
#
# Author: Nelson McFadyen
# Last Updated: Jan, 07,2025

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import requests
import time
import threading
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import api

# -----------------------
# Utility and API Functions
# -----------------------

def fetch_data(endpoint, fields):
    response = requests.post(
        f"{api.IGDB_BASE_URL}/{endpoint}",
        headers=api.HEADERS,
        data=f"fields {fields}; limit 500;"
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from {endpoint}: {response.status_code} - {response.text}")
        return []

def fetch_cover_image(cover_id):
    if not cover_id:
        return "No cover available"
    
    response = requests.post(
        f"{api.IGDB_BASE_URL}/covers",
        headers=api.HEADERS,
        data=f"fields image_id; where id = {cover_id};"
    )
    if response.status_code == 200:
        cover_data = response.json()
        if cover_data and 'image_id' in cover_data[0]:
            image_id = cover_data[0]['image_id']
            return f"https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"
        else:
            return "Cover image not found"
    else:
        print(f"Error fetching cover data: {response.status_code} - {response.text}")
        return "Error fetching cover image"

def create_genre_map():
    genres = fetch_data('genres', 'id, name')
    return {genre['id']: genre['name'] for genre in genres}

def create_platform_map():
    platforms = fetch_data('platforms', 'id, name')
    return {platform['id']: platform['name'] for platform in platforms}

# Constants for genre and platform maps
GENRE_MAP = create_genre_map()
PLATFORM_MAP = create_platform_map()

def fetch_genre_names(genre_ids):
    if not genre_ids:
        return ["Not Available"]
    return [GENRE_MAP.get(genre_id, f"Unknown Genre {genre_id}") for genre_id in genre_ids]

def fetch_platform_names(platform_ids):
    if not platform_ids:
        return ["Not Available"]
    return [PLATFORM_MAP.get(platform_id, f"Unknown Platform {platform_id}") for platform_id in platform_ids]

def format_unix_timestamp(timestamp):
    if not timestamp:
        return "Not Available"
    return time.strftime('%d-%m-%Y', time.gmtime(timestamp))

def get_game_data(api_token, client_id, query, endpoint="games"):
    url = f"https://api.igdb.com/v4/{endpoint}"  # Default to 'games' endpoint
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {api_token}",
    }
    response = requests.post(url, headers=headers, data=query)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

def update_live_count_label(label, root):
    label.config(text=f"Unique Games Added: {len(existing_game_ids)}")
    root.after(500, update_live_count_label, label, root)

def get_all_game_data(game_title):
    offset = 0
    all_game_data = []
    while True:
        query = f"fields name, first_release_date, rating, genres, storyline, summary, platforms, cover; search \"{game_title}\"; limit 500; offset {offset};"
        game_data = get_game_data(api.ACCESS_TOKEN, api.CLIENT_ID, query)
        if not game_data:
            break
        all_game_data.extend(game_data)
        offset += 500
        if len(game_data) < 500:
            break
    return all_game_data

games_list = []         # Combined list for game information
listbox_count = 0       # Count for full searches done
existing_game_ids = set()  # To avoid duplicates

def update_progress_bar(progress_var, step, total_steps, root):
    progress = (step / total_steps) * 100
    progress_var.set(progress)
    root.update_idletasks()

def create_genre_checkbox_frame(parent, genre_list):
    genre_frame = ttk.Frame(parent)
    genre_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="w")
    genre_vars = {}
    for idx, genre in enumerate(genre_list):
        genre_var = tk.BooleanVar()
        genre_vars[genre] = genre_var
        checkbox = ttk.Checkbutton(genre_frame, text=genre, variable=genre_var)
        checkbox.grid(row=idx // 3, column=idx % 3, sticky="w", padx=5, pady=2)
    return genre_vars

def fetch_all_genres(api_token, client_id):
    genre_name_to_id = {}
    offset = 0
    limit = 100
    while True:
        query = f"fields name, id; limit {limit}; offset {offset};"
        response = get_game_data(api_token, client_id, query, endpoint="genres")
        if not response:
            break
        for genre in response:
            genre_name_to_id[genre['name']] = genre['id']
        if len(response) < limit:
            break
        offset += limit
    return genre_name_to_id

genre_name_to_id = fetch_all_genres(api.ACCESS_TOKEN, api.CLIENT_ID)

def get_selected_genre_ids(genre_vars):
    selected_ids = [
        genre_name_to_id[genre_name] for genre_name, var in genre_vars.items()
        if var.get() and genre_name in genre_name_to_id
    ]
    return selected_ids

# -----------------------
# Main Search and Save Functions
# -----------------------

def on_search(search_button, save_button, entry, search_history_listbox, searched_titles, 
              progress_var, live_count_label, root, genre_vars):
    def search_thread():
        global listbox_count
        search_button.config(state='disabled')
        save_button.config(state='disabled')

        game_title = entry.get().strip().lower()
        if not game_title:
            messagebox.showwarning("Input Error", "Please enter a game title.")
            search_button.config(state='normal')
            save_button.config(state='normal')
            return

        if game_title in searched_titles:
            messagebox.showinfo("Duplicate Search", f"Search for '{game_title}' has already been done.")
            search_button.config(state='normal')
            save_button.config(state='normal')
            return

        selected_genre_ids = get_selected_genre_ids(genre_vars)
        query = f"fields name, first_release_date, rating, genres, storyline, summary, platforms, cover; search \"{game_title}\"; limit 500;"
        game_data = get_game_data(api.ACCESS_TOKEN, api.CLIENT_ID, query)

        if not game_data:
            messagebox.showinfo("No Results", "No data found for the specified game.")
            search_button.config(state='normal')
            save_button.config(state='normal')
            return

        filtered_game_data = [
            game for game in game_data
            if not selected_genre_ids or any(genre_id in selected_genre_ids for genre_id in game.get('genres', []))
        ]

        if not filtered_game_data:
            messagebox.showinfo("No Results", "No games match the selected genres.")
            search_button.config(state='normal')
            save_button.config(state='normal')
            return

        total_steps = len(filtered_game_data)
        step = 0
        listbox_count += 1
        search_history_listbox.insert(0, f"{listbox_count}) {game_title}")
        searched_titles.add(game_title)

        for game in filtered_game_data:
            step += 1
            update_progress_bar(progress_var, step, total_steps, root)
            game_id = game.get('id')
            if game_id in existing_game_ids:
                continue

            games_list.append({
                "Name": game.get('name', 'Not Available'),
                "Release Date": format_unix_timestamp(game.get('first_release_date')),
                "Rating": game.get('rating', 'Not Available'),
                "Genres": ', '.join(fetch_genre_names(game.get('genres', []))),
                "Storyline": game.get('storyline', 'Not Available'),
                "Summary": game.get('summary', 'Not Available'),
                "Platforms": ', '.join(fetch_platform_names(game.get('platforms', []))),
                "Cover URL": fetch_cover_image(game.get('cover'))
            })
            existing_game_ids.add(game_id)
            live_count_label.config(text=f"Unique Games Added: {len(existing_game_ids)}")
            root.update_idletasks()

        progress_var.set(0)
        messagebox.showinfo("Success", f"Game data for '{game_title}' has been fetched.")
        entry.delete(0, tk.END)
        search_button.config(state='normal')
        save_button.config(state='normal')

    threading.Thread(target=search_thread, daemon=True).start()

def on_save(progress_var, save_button, root, games_list):
    if not games_list:
        messagebox.showwarning("No Data", "There are no games to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )
    if not file_path:
        messagebox.showinfo("Cancelled", "Save operation was cancelled.")
        return

    df = pd.DataFrame(games_list)
    try:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Success", f"File saved successfully to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving: {str(e)}")

# -----------------------
# Main GUI for Game Search
# -----------------------

def open_game_search(root, previous_frame, shared_state, show_frame):
    game_search_frame = ttk.Frame(root, padding="5")
    
    # Configure grid columns to allow dynamic resizing
    game_search_frame.columnconfigure(0, weight=1)
    game_search_frame.columnconfigure(1, weight=2)
    game_search_frame.columnconfigure(2, weight=1)
    
    # Title label
    title_label = ttk.Label(game_search_frame, text="Game Search", font=("Arial", 20, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, pady=10)
    
    # Entry label and field
    entry_label = ttk.Label(game_search_frame, text="Enter game title:", font=("Arial", 12, "bold"))
    entry_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry = ttk.Entry(game_search_frame, width=40)
    entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    # Genre checkbox frame
    genre_list = list(GENRE_MAP.values())
    genre_vars = create_genre_checkbox_frame(game_search_frame, genre_list)
    
    # Buttons for search and save
    search_button = ttk.Button(game_search_frame, text="Search", command=lambda: on_search(
        search_button, save_button, entry, search_history_listbox, searched_titles, 
        progress_var, live_count_label, root, genre_vars))
    search_button.grid(row=3, column=0, padx=5, pady=5, sticky="e")
    
    save_button = ttk.Button(game_search_frame, text="Save to Excel", command=lambda: on_save(
        progress_var, save_button, root, games_list))
    save_button.grid(row=4, column=0, padx=5, pady=5, sticky="w")
    
    # Dynamically set progress bar length based on window width
    progress_length = int(root.winfo_width() * 0.4) if root.winfo_width() > 100 else 500
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(game_search_frame, variable=progress_var, maximum=100, length=progress_length)
    progress_bar.grid(row=3, column=2, pady=10)
    
    # Live count label
    live_count_label = ttk.Label(game_search_frame, text="Unique Games Added: 0")
    live_count_label.grid(row=2, column=2, columnspan=2, pady=10)
    
    # Search history listbox with scrollbar
    search_history_frame = ttk.Frame(game_search_frame)
    search_history_frame.grid(row=4, rowspan=5, column=2, padx=10, pady=10, sticky="nsew")
    search_history_listbox = tk.Listbox(search_history_frame, height=10, width=20)
    search_history_listbox.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(search_history_frame, orient="vertical", command=search_history_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    search_history_listbox.config(yscrollcommand=scrollbar.set)
    
    # Back button
    back_button = ttk.Button(game_search_frame, text="Back", command=lambda: show_frame(previous_frame))
    back_button.grid(row=7, column=0, columnspan=2, pady=10)
    
    searched_titles = set()
    show_frame(game_search_frame)
    
    # Note: Typically mainloop() is called once in the main file.
    # If this file is used as part of a larger application, you may not need the following line.
    root.mainloop()
