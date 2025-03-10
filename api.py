import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Listbox, PhotoImage
import pandas as pd
import os, sys
import requests
import time
from dotenv import load_dotenv
import threading

import random

from datetime import datetime, timezone

import ttkbootstrap as tb
from ttkbootstrap.constants import *


from PIL import Image, ImageTk
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Enviorment variables for client, token, and url
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
    # Request a new access token
    response = requests.post(TOKEN_URL, params=params)

    if response.status_code == 200:
        ACCESS_TOKEN = response.json().get('access_token')
    else:
        # Attempt to parse the response JSON to extract error details
        try:
            error_info = response.json()
            error_message = error_info.get('message', '')

            # Handle specific error scenarios based on status codes and error message
            if response.status_code == 400:
                if 'invalid client' in error_message:
                    print('Error: Your client ID is invalid or both the client ID and client secret are incorrect. Please correct them in your .env file.')
            elif response.status_code == 403:
                if 'invalid client secret' in error_message:
                    print('Error: Your client secret is invalid. Please correct it in your .env file.')
            else:
                # General fallback for unexpected errors
                print(f"Unexpected error: {error_message}")
        except ValueError:
            # Handle cases where the response is not valid JSON
            print('Error: The server response was not in JSON format.')
            print(f"Response: {response.text}")

        print('Program terminating due to error.')
        sys.exit()

except requests.exceptions.RequestException as e:
    # Handle network-related exceptions
    print(f"Network error occurred: {e}")
    print('Please check your internet connection or API endpoint URL.')
    sys.exit()

# Authorization header for searches
HEADERS = {
    'Client-ID': CLIENT_ID,
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}