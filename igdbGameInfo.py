import os
import requests
import time
from dotenv import load_dotenv
import pandas as pd

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
    print(f"New Access Token: {ACCESS_TOKEN}")
else:
    print(f"Error getting access token: {response.status_code} - {response.text}")
    exit()

# Define HEADERS after getting the access token
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


# Print game info (optional)
            #print(f"Game Name: {game_name}")
            #print(f"Release Date: {release_date}")
            #print(f"Rating: {rating}")
            #print(f"Genres: {genres}")
            #print(f"Storyline: {storyline}")
            #print(f"Summary: {summary}")
            #print(f"Platforms: {platforms}")
            #print(f"Cover URL: {cover_url}")
            #print("---")

def main():
    games_list = []  # Combined list to store game information across searches

    while True:
        # Prompt the user for a game title
        game_title = input("Enter the name of the game you want to search for (or type 'exit' to finish): ")
        
        if game_title.lower() == 'exit':
            break
        
        # Fetch all game data
        game_data = get_all_game_data(game_title)
        
        if game_data:
            print(f"\nTotal results for '{game_title}': {len(game_data)}\n")
            
            for game in game_data:
                game_name = game.get('name', 'Not Available')
                release_date = format_unix_timestamp(game.get('first_release_date'))
                rating = game.get('rating', 'Not Available')
                genres = ', '.join(fetch_genre_names(game.get('genres', [])))
                storyline = game.get('storyline', 'Not Available')
                summary = game.get('summary', 'Not Available')
                platforms = ', '.join(fetch_platform_names(game.get('platforms', [])))
                cover_url = fetch_cover_image(game.get('cover'))

                # Add the data to the list
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

        else:
            print("No data found for the specified game.")

    if games_list:
        # Ask the user for the filename to save the Excel file
        filename = input("Enter the name for the Excel file (without extension): ")
        if not filename:
            filename = "game_info"  # Default filename if none is provided
        
        # Save the data to an Excel file
        df = pd.DataFrame(games_list)
        df.to_excel(f"{filename}.xlsx", index=False, engine='openpyxl')
        print(f"Game data has been saved to '{filename}.xlsx'")
    else:
        print("No data to save.")

if __name__ == "__main__":
    main()
