# This python script is a GUI video game search engine interface from the IDGDB website database.
# After searching for all the video games the user searched for, you have the option to save the searches in an excel file.
# Each game has the name, release date, rating, genres, storyline, summary, platforms, cover url for its record.

# Author: Nelson McFadyen
# Last Updated: Jan, 07,2025

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Listbox, PhotoImage
import pandas as pd
import os
import requests
import time
from dotenv import load_dotenv
import threading

from datetime import datetime, timezone

import ttkbootstrap as tb
from ttkbootstrap.constants import *


from PIL import Image, ImageTk
from io import BytesIO

from api import random_game_api


# Function to fetch data requests from IGDB API for game being searched
def fetch_data(endpoint, fields):
    response = requests.post(
        f"{random_game_api.IGDB_BASE_URL}/{endpoint}",
        headers=random_game_api.HEADERS,
        data=f"fields {fields}; limit 500;"
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from {endpoint}: {response.status_code} - {response.text}")
        return []

# Function to fwtch voer image url for given cover_id
def fetch_cover_image(cover_id):
    if not cover_id:
        return "No cover available"
    
    response = requests.post(
        f"{random_game_api.IGDB_BASE_URL}/covers",
        headers=random_game_api.HEADERS,
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

# Function to convert genre id's to given names
def create_genre_map():
    genres = fetch_data('genres', 'id, name')
    return {genre['id']: genre['name'] for genre in genres}

# Function to convert platform id's to given names
def create_platform_map():
    platforms = fetch_data('platforms', 'id, name')
    return {platform['id']: platform['name'] for platform in platforms}

# Constants for genre and platform maps
GENRE_MAP = create_genre_map()
PLATFORM_MAP = create_platform_map()

# Function to fetch genre names 
def fetch_genre_names(genre_ids):
    if not genre_ids:
        return ["Not Available"]
    return [GENRE_MAP.get(genre_id, f"Unknown Genre {genre_id}") for genre_id in genre_ids]

# Function to fetch platform names
def fetch_platform_names(platform_ids):
    if not platform_ids:
        return ["Not Available"]
    return [PLATFORM_MAP.get(platform_id, f"Unknown Platform {platform_id}") for platform_id in platform_ids]

# Function to convert Unix timestamp to readable date format
def format_unix_timestamp(timestamp):
    if not timestamp:
        return "Not Available"
    return time.strftime('%Y-%m-%d', time.gmtime(timestamp))

# Function to fetch game data from the IGDB API search query
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

    
# Function to add live count label, and update it with the unique games in the list
def update_live_count_label(label, root):
    label.config(text=f"Unique Games Added: {len(existing_game_ids)}")
    # Schedule the next update in 500 milliseconds (0.5 seconds)
    root.after(500, update_live_count_label, label)

# Function to fetch all game data from the given game title from user
def get_all_game_data(game_title):
    offset = 0
    all_game_data = []
    
    while True:
        # Construct the query with offset and limit of 500
        query = f"fields name, first_release_date, rating, genres, storyline, summary, platforms, cover; search \"{game_title}\"; limit 500; offset {offset};"
        game_data = get_game_data(random_game_api.ACCESS_TOKEN, random_game_api.CLIENT_ID, query)
        
        if not game_data:
            break  # Exit loop if no more data is returned
        
        all_game_data.extend(game_data)
        offset += 500  # Increase the offset for the next batch
        
        # If the number of results is less than 500, we've reached the end
        if len(game_data) < 500:
            break
    
    return all_game_data

games_list = []  # Combined list to store game information across searches
listbox_count = 0 # Keep track of the amount of full searches done

# Maintain a set of already added game IDs to avoid duplicates
existing_game_ids = set()  # We won't store the IDs in games_list

# Function to update progress bar with length left of current task
def update_progress_bar(progress_var, step, total_steps, root):
    """Updates the progress bar based on the current step."""
    progress = (step / total_steps) * 100
    progress_var.set(progress)
    root.update_idletasks()  # Ensures the UI updates in real-time
    
    
# Function to create genre checkboxes and capture selected genres
def create_genre_checkbox_frame(parent, genre_list):
    genre_frame = ttk.Frame(parent)
    genre_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="w")

    genre_vars = {}  # Dictionary to hold the Tkinter variables for the checkboxes
    for idx, genre in enumerate(genre_list):
        genre_var = tk.BooleanVar()  # Tkinter variable to hold checkbox state (True/False)
        genre_vars[genre] = genre_var
        checkbox = ttk.Checkbutton(genre_frame, text=genre, variable=genre_var)
        checkbox.grid(row=idx // 3, column=idx % 3, sticky="w", padx=5, pady=2)  # 3 columns layout
    return genre_vars

# Fetch all available genres from the API (assuming you can get all genres in one request)
def fetch_all_genres(api_token, client_id):
    query = "fields name, id;"  # Query only genre fields (name and id)
    response = get_game_data(api_token, client_id, query, endpoint="genres")  # Specify 'genres' as the endpoint
    
    print(response)  # Debug: Check the structure of the response
    
    # Process response correctly
    if isinstance(response, list):
        genres = response
    else:
        genres = response.get('data', [])
    
    # Create a dictionary mapping genre names to IDs
    genre_name_to_id = {genre['name']: genre['id'] for genre in genres}
    print(f"Available Genres: {genre_name_to_id}")  # Debug output
    
    return genre_name_to_id



# Fetch the genres when the program starts
genre_name_to_id = fetch_all_genres(random_game_api.ACCESS_TOKEN, random_game_api.CLIENT_ID)

# Update your function to dynamically retrieve genre IDs
def get_selected_genre_ids(genre_vars):
    selected_ids = [
        genre_name_to_id[genre_name] for genre_name, var in genre_vars.items() if var.get() and genre_name in genre_name_to_id
    ]
    print(f"Selected Genre IDs: {selected_ids}")  # Debug output to check selected IDs
    return selected_ids





# Function to handle the main search thread for games user has entered
def on_search(search_button, save_button, entry, search_history_listbox, searched_titles, progress_var, live_count_label, root, genre_vars):
    def search_thread():
        global listbox_count

        # Disable buttons during the search
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
        game_data = get_game_data(random_game_api.ACCESS_TOKEN, random_game_api.CLIENT_ID, query)

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

        # Progress bar variables
        total_steps = len(filtered_game_data)
        step = 0

        listbox_count += 1
        search_history_listbox.insert(0, f"{listbox_count}) {game_title}")
        searched_titles.add(game_title)

        for game in filtered_game_data:
            step += 1

            # Progress bar update
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

            # Update the live count label
            live_count_label.config(text=f"Unique Games Added: {len(existing_game_ids)}")
            root.update_idletasks()

        progress_var.set(0)  # Reset progress bar
        messagebox.showinfo("Success", f"Game data for '{game_title}' has been fetched.")
        entry.delete(0, tk.END)

        search_button.config(state='normal')
        save_button.config(state='normal')

    threading.Thread(target=search_thread, daemon=True).start()






def save_to_excel_file(games_list):
    """
    Saves the games_list data to an Excel file.
    Asks the user for a file name and location using a save file dialog.
    """
    # Prompt the user to choose a save location and file name
    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        title="Save Game Data as Excel File"
    )
    
    if not file_path:
        # User canceled the save dialog
        return

    # Create a DataFrame from games_list (replace with your actual data structure)
    df = pd.DataFrame(games_list)

    # Save the DataFrame to the chosen file path
    try:
        df.to_excel(file_path, index=False)
        print(f"Data successfully saved to {file_path}.")
    except Exception as e:
        print(f"Error saving file: {e}")
        raise



# Function to handle excel save functionality
def on_save(progress_var, save_button, root, games_list):
    """Save games_list to an Excel file."""
    if not games_list:
        messagebox.showwarning("No Data", "There are no games to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )

    if not file_path:  # User cancelled the save dialog
        messagebox.showinfo("Cancelled", "Save operation was cancelled.")
        return

    #simulate_save_progress(progress_var, save_button, root)

    # Save games_list to Excel
    df = pd.DataFrame(games_list)
    try:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Success", f"File saved successfully to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving: {str(e)}")





        
# In the open_game_search function, pass progress_var to on_search
def open_game_search(root, previous_frame, shared_state, show_frame):
    # Create the game search frame
    game_search_frame = ttk.Frame(root, padding="5")

    # Title label
    title_label = ttk.Label(game_search_frame, text="Game Search", font=("Arial", 20, "bold"))
    title_label.grid(row=0, column=1, columnspan=2, pady=10)

    # Entry and buttons
    entry_label = ttk.Label(game_search_frame, text="Enter game title:", font=("Arial", 12, "bold"))
    entry_label.grid(row=1, column=0, padx=0, pady=5, sticky="w")  # No horizontal padding

    entry = ttk.Entry(game_search_frame, width=40)
    entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")  # No horizontal padding

    # Genre list (replace with actual genre list)
    genre_list = list(GENRE_MAP.values())  # Assuming GENRE_MAP holds genre names
    genre_vars = create_genre_checkbox_frame(game_search_frame, genre_list)

    # Search button and save button
    search_button = ttk.Button(game_search_frame, text="Search", command=lambda: on_search(
        search_button, save_button, entry, search_history_listbox, searched_titles, 
        progress_var, live_count_label, root, genre_vars))

    search_button.grid(row=3, column=0, padx=5, pady=5, sticky="e")

    save_button = ttk.Button(game_search_frame, text="Save to Excel", command=lambda: on_save(progress_var, 
                                                                                            save_button, root, games_list))
    save_button.grid(row=4, column=0, padx=5, pady=5, sticky="w")
    
    # Progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(game_search_frame, variable=progress_var, maximum=100, length=500)  # Adjusted length
    progress_bar.grid(row=3, column=2, pady=10)

    # Live count label
    live_count_label = ttk.Label(game_search_frame, text="Unique Games Added: 0")
    live_count_label.grid(row=2, column=2, columnspan=2, pady=10)

    # Search history listbox and scrollbar in the right column
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

    # Function bindings
    searched_titles = set()

    # Show the new frame
    show_frame(game_search_frame)

    # Start main program
    root.mainloop()



