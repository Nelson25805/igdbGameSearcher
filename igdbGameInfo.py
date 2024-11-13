import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Listbox
import pandas as pd
import os
import requests
import time
from dotenv import load_dotenv
import threading

# Load environment variables from .env file
load_dotenv()

# Replace with environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
IGDB_BASE_URL = 'https://api.igdb.com/v4'

# Get a new access token
params = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'client_credentials'
}

response = requests.post(TOKEN_URL, params=params)
if response.status_code == 200:
    ACCESS_TOKEN = response.json().get('access_token')
else:
    print(f"Error getting access token: {response.status_code} - {response.text}")
    exit()

HEADERS = {
    'Client-ID': CLIENT_ID,
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

def fetch_data(endpoint, fields):
    """Fetch data from the IGDB API for the given endpoint."""
    response = requests.post(
        f"{IGDB_BASE_URL}/{endpoint}",
        headers=HEADERS,
        data=f"fields {fields}; limit 500;"
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from {endpoint}: {response.status_code} - {response.text}")
        return []

def fetch_cover_image(cover_id):
    """Fetch the cover image URL for a given cover ID."""
    if not cover_id:
        return "No cover available"
    
    response = requests.post(
        f"{IGDB_BASE_URL}/covers",
        headers=HEADERS,
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

GENRE_MAP = create_genre_map()
PLATFORM_MAP = create_platform_map()

def fetch_genre_names(genre_ids):
    """Convert genre IDs to human-readable names using the fetched GENRE_MAP."""
    if not genre_ids:
        return ["Not Available"]
    return [GENRE_MAP.get(genre_id, f"Unknown Genre {genre_id}") for genre_id in genre_ids]

def fetch_platform_names(platform_ids):
    """Convert platform IDs to human-readable names using the fetched PLATFORM_MAP."""
    if not platform_ids:
        return ["Not Available"]
    return [PLATFORM_MAP.get(platform_id, f"Unknown Platform {platform_id}") for platform_id in platform_ids]

def format_unix_timestamp(timestamp):
    """Convert a Unix timestamp to a human-readable date format."""
    if not timestamp:
        return "Not Available"
    return time.strftime('%Y-%m-%d', time.gmtime(timestamp))

def get_game_data(access_token, client_id, query):
    """Fetch game data from the IGDB API based on the search query."""
    response = requests.post(
        f"{IGDB_BASE_URL}/games",
        headers=HEADERS,
        data=query
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching game data: {response.status_code} - {response.text}")
        return []
    

# Add a label for live count in the GUI
def update_live_count_label(label):
    """Continuously update the live count of unique games in a separate thread."""
    while True:
        # Update the live count label every 0.5 seconds
        label.config(text=f"Unique Games Added: {len(existing_game_ids)}")
        time.sleep(0.5)  # Update the label every half second

def get_all_game_data(game_title):
    """Fetch all game data for the given game title, handling pagination if necessary."""
    offset = 0
    all_game_data = []
    
    while True:
        # Construct the query with offset and limit of 500
        query = f"fields name, first_release_date, rating, genres, storyline, summary, platforms, cover; search \"{game_title}\"; limit 500; offset {offset};"
        game_data = get_game_data(ACCESS_TOKEN, CLIENT_ID, query)
        
        if not game_data:
            break  # Exit loop if no more data is returned
        
        all_game_data.extend(game_data)
        offset += 500  # Increase the offset for the next batch
        
        # If the number of results is less than 500, we've reached the end
        if len(game_data) < 500:
            break
    
    return all_game_data

games_list = []  # Combined list to store game information across searches

# Maintain a set of already added game IDs to avoid duplicates
existing_game_ids = set()  # We won't store the IDs in games_list

def update_progress_bar(progress_var, current, total):
    progress_var.set((current / total) * 100)
    root.update_idletasks()

def on_search():
    def search_thread():
        # Disable the buttons during the search
        search_button.config(state='disabled')
        save_button.config(state='disabled')

        game_title = entry.get().strip().lower()  # Normalize case for consistency
        if not game_title:
            messagebox.showwarning("Input Error", "Please enter a game title.")
            search_button.config(state='normal')  # Re-enable buttons if input is invalid
            save_button.config(state='normal')
            return

        # Check if the game title has already been searched
        if game_title in searched_titles:
            messagebox.showinfo("Duplicate Search", f"Search for '{game_title}' has already been done.")
            search_button.config(state='normal')
            save_button.config(state='normal')
            return

        # Add the game title to the Listbox and the set of searched titles
        search_history_listbox.insert(tk.END, game_title)
        searched_titles.add(game_title)

        # Fetch the game data
        game_data = get_all_game_data(game_title)
        if game_data:
            for i, game in enumerate(game_data):
                game_id = game.get('id')  # Get the game ID for uniqueness check

                # Skip if the game ID is already in the list
                if game_id in existing_game_ids:
                    continue

                game_name = game.get('name', 'Not Available')
                release_date = format_unix_timestamp(game.get('first_release_date'))
                rating = game.get('rating', 'Not Available')
                genres = ', '.join(fetch_genre_names(game.get('genres', [])))
                storyline = game.get('storyline', 'Not Available')
                summary = game.get('summary', 'Not Available')
                platforms = ', '.join(fetch_platform_names(game.get('platforms', [])))
                cover_url = fetch_cover_image(game.get('cover'))

                # Add the game to the list (without the ID)
                games_list.append({
                    "Name": game_name,
                    "Release Date": release_date,
                    "Rating": rating,
                    "Genres": genres,
                    "Storyline": storyline,
                    "Summary": summary,
                    "Platforms": platforms,
                    "Cover URL": cover_url
                })

                # Update the set of existing game IDs
                existing_game_ids.add(game_id)

                update_progress_bar(progress_var, i + 1, len(game_data))

            messagebox.showinfo("Success", f"Game data for '{game_title}' has been fetched.")
        else:
            messagebox.showinfo("No Results", "No data found for the specified game.")

        progress_var.set(0)  # Reset progress bar after completion

        # Re-enable the buttons after the search completes
        search_button.config(state='normal')
        save_button.config(state='normal')

    # Run the search in a new thread
    threading.Thread(target=search_thread, daemon=True).start()




def on_save():
    # Disable the save button while saving
    save_button.config(state='disabled')

    if not games_list:
        messagebox.showwarning("Save Error", "No data available to save.")
        save_button.config(state='normal')  # Re-enable the button if nothing to save
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        df = pd.DataFrame(games_list)
        for i in range(100):  # Simulate saving process with progress updates
            update_progress_bar(progress_var, i + 1, 100)
            time.sleep(0.01)  # Simulate processing delay
        df.to_excel(file_path, index=False, engine='openpyxl')
        messagebox.showinfo("Saved", f"Data has been saved to {file_path}")
        progress_var.set(0)  # Reset progress bar

    # Re-enable the save button after saving
    save_button.config(state='normal')


# Initialize the GUI
root = tk.Tk()
root.title("Game Search Interface")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Create and place a Listbox widget to display search history
search_history_listbox = Listbox(root, height=10, width=50)
search_history_listbox.grid(pady=10)

# Set to keep track of searched game titles to avoid duplicates
searched_titles = set()

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
progress_bar.grid(row=2, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

# Widgets
entry_label = ttk.Label(frame, text="Enter game title:")
entry_label.grid(row=0, column=0, padx=5, pady=5)
entry = ttk.Entry(frame, width=30)
entry.grid(row=0, column=1, padx=5, pady=5)
search_button = ttk.Button(frame, text="Search", command=on_search)
search_button.grid(row=0, column=2, padx=5, pady=5)
save_button = ttk.Button(frame, text="Save to Excel", command=on_save)
save_button.grid(row=1, column=0, columnspan=3, pady=10)

# Live count label
live_count_label = ttk.Label(frame, text="Unique Games Added: 0")
live_count_label.grid(row=3, column=0, columnspan=3, pady=10)

# Start the live count update in a separate thread
threading.Thread(target=update_live_count_label, args=(live_count_label,), daemon=True).start()

root.mainloop()
