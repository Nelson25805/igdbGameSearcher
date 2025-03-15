import os, sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables for client, token, and url
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
IGDB_BASE_URL = 'https://api.igdb.com/v4'

# Check if CLIENT_ID and CLIENT_SECRET are defined
if not CLIENT_ID and not CLIENT_SECRET:
    print('Error: Both the client ID and client secret are missing. Please add them to your .env file.')
    sys.exit()
elif not CLIENT_ID:
    print('Error: The client ID is missing. Please add it to your .env file.')
    sys.exit()
elif not CLIENT_SECRET:
    print('Error: The client secret is missing. Please add it to your .env file.')
    sys.exit()

# Get a new access token
params = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'client_credentials'
}

try:
    response = requests.post(TOKEN_URL, params=params)
    if response.status_code == 200:
        ACCESS_TOKEN = response.json().get('access_token')
    else:
        try:
            error_info = response.json()
            error_message = error_info.get('message', '')
            if response.status_code == 400 and 'invalid client' in error_message:
                print('Error: Your client ID is invalid or both the client ID and client secret are incorrect. Please correct them in your .env file.')
            elif response.status_code == 403 and 'invalid client secret' in error_message:
                print('Error: Your client secret is invalid. Please correct it in your .env file.')
            else:
                print(f"Unexpected error: {error_message}")
        except ValueError:
            print('Error: The server response was not in JSON format.')
            print(f"Response: {response.text}")
        print('Program terminating due to error.')
        sys.exit()
except requests.exceptions.RequestException as e:
    print(f"Network error occurred: {e}")
    print('Please check your internet connection or API endpoint URL.')
    sys.exit()

# Authorization header for API calls
HEADERS = {
    'Client-ID': CLIENT_ID,
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}


# -----------------------
# API Helper Functions
# -----------------------

def fetch_data(endpoint, fields, limit=500, offset=0):
    """
    Fetch data from a given IGDB endpoint.
    """
    query = f"fields {fields}; limit {limit}; offset {offset};"
    response = requests.post(f"{IGDB_BASE_URL}/{endpoint}", headers=HEADERS, data=query)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from {endpoint}: {response.status_code} - {response.text}")
        return []


def get_game_data(query, endpoint="games"):
    """
    Fetch game data from the IGDB API using a custom query.
    """
    url = f"{IGDB_BASE_URL}/{endpoint}"
    response = requests.post(url, headers=HEADERS, data=query)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []
    
def get_games_count():
    """
    Returns the total number of games in the IGDB database.
    This function calls the /games/count endpoint with an empty query.
    """
    try:
        response = requests.post(f"{IGDB_BASE_URL}/games/count", headers=HEADERS, data="", timeout=10)
        if response.status_code == 200:
            return response.json().get("count", 0)
        else:
            print(f"Error fetching games count: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        print("Exception in get_games_count:", e)
        return 0



def fetch_cover_image(cover_id):
    """
    Given a cover ID (a string like "co12345"), return the URL for the cover image.
    """
    if not cover_id:
        return "No cover available"
    
    response = requests.post(
        f"{IGDB_BASE_URL}/covers",
        headers=HEADERS,
        data=f'fields image_id; where id = {cover_id};'
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


def fetch_genre_names(genre_ids, genre_map):
    if not genre_ids:
        return ["Not Available"]
    return [genre_map.get(genre_id, f"Unknown Genre {genre_id}") for genre_id in genre_ids]


def fetch_platform_names(platform_ids, platform_map):
    if not platform_ids:
        return ["Not Available"]
    return [platform_map.get(platform_id, f"Unknown Platform {platform_id}") for platform_id in platform_ids]


def format_unix_timestamp(timestamp):
    if not timestamp:
        return "Not Available"
    return time.strftime('%d-%m-%Y', time.gmtime(timestamp))


# Create global maps that can be imported and used by other modules
GENRE_MAP = create_genre_map()
PLATFORM_MAP = create_platform_map()
