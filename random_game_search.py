import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from io import BytesIO
import api
import requests
import random
from datetime import datetime, timezone
import threading
import webbrowser

def open_random_game_search(root, previous_frame, shared_state, show_frame):
    # Create the random game search frame
    random_game_search_frame = ttk.Frame(root, padding="5")
    random_game_search_frame.columnconfigure(0, weight=1)
    random_game_search_frame.columnconfigure(1, weight=0)
    random_game_search_frame.columnconfigure(2, weight=1)
    random_game_search_frame.rowconfigure(0, weight=0)  # Title row fixed
    random_game_search_frame.rowconfigure(1, weight=0)  # Image row fixed
    random_game_search_frame.rowconfigure(2, weight=1)  # Game link row fixed
    random_game_search_frame.rowconfigure(3, weight=0)  # Additional content row

    # Add title label at the top center
    title_label = ttk.Label(random_game_search_frame, text="Random Game Section", font=("Arial", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, sticky="n")

    # Details frame for game info
    details_frame = ttk.Frame(random_game_search_frame)
    details_frame.grid(row=1, column=0, sticky="nsew", padx=10)

    def add_detail_row(frame, row, label_text, height):
        label = ttk.Label(frame, text=label_text, font=("Arial", 12, "bold"))
        label.grid(row=row, column=0, sticky="w", pady=5)
        # Create a container for the text widget and scrollbar
        textbox_frame = ttk.Frame(frame)
        textbox_frame.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        textbox = tk.Text(textbox_frame, height=height, state="disabled", wrap="word", bd=2, relief="sunken")
        textbox.grid(row=0, column=0, sticky="ew")
        scrollbar = ttk.Scrollbar(textbox_frame, orient="vertical", command=textbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        textbox.config(yscrollcommand=scrollbar.set)
        return textbox

    game_name_text    = add_detail_row(details_frame, 0, "Game Name:", 2)
    summary_text      = add_detail_row(details_frame, 1, "Summary:", 4)
    platforms_text    = add_detail_row(details_frame, 2, "Platforms:", 2)
    genres_text       = add_detail_row(details_frame, 3, "Genres:", 2)
    release_dates_text= add_detail_row(details_frame, 4, "Release Dates:", 2)

    # Game Image Label in column 2
    game_image_label = ttk.Label(random_game_search_frame, text="No Image Available", font=("Arial", 12, "italic"))
    game_image_label.grid(row=1, column=2, sticky="nsew", padx=10, pady=(5, 10))

    # Compute dynamic image dimensions based on current window size.
    # If the window width/height are not available yet, fallback to default values.
    current_width  = root.winfo_width() if root.winfo_width() > 100 else 1200
    current_height = root.winfo_height() if root.winfo_height() > 100 else 800
    desired_image_width  = int(current_width * 0.3)
    desired_image_height = int(current_height * 0.8)

    # Display placeholder image with dynamic dimensions
    display_no_image(game_image_label, desired_image_width, desired_image_height)

    # Frame for the game URL (placed below the image)
    url_frame = ttk.Frame(random_game_search_frame)
    url_frame.grid(row=2, column=2, sticky="nsew", padx=10, pady=(0, 10))
    url_description_label = ttk.Label(url_frame, text="Game Link:", font=("Arial", 12, "bold"))
    url_description_label.pack(anchor="w")
    url_label = ttk.Label(url_frame, text="No link available", foreground="gray", cursor="arrow", font=("Arial", 12))
    url_label.pack(anchor="w")

    # Buttons frame at the bottom (in column 0)
    buttons_frame = ttk.Frame(random_game_search_frame)
    buttons_frame.grid(row=2, column=0)
    
    # Note: Pass root to fetch_random_game_gui so it can compute sizes dynamically.
    random_game_button = ttk.Button(buttons_frame, text="Fetch Random Game",
        command=lambda: fetch_random_game_gui(root, game_name_text, summary_text, platforms_text,
                                               genres_text, release_dates_text, game_image_label, 
                                               random_game_button, back_button, url_label, random_game_search_frame))
    random_game_button.pack(side="left", padx=10)

    # Back Button to return to the previous page
    back_button = ttk.Button(buttons_frame, text="Back to Main Page",
                              command=lambda: show_frame(previous_frame))
    back_button.pack(side="right", padx=10)

    # Show the new frame
    show_frame(random_game_search_frame)


def fetch_random_game_gui(root, game_name_text, summary_text, platforms_text, genres_text, release_dates_text, 
                          game_image_label, random_game_button, back_button, url_label, random_game_search_frame):
    # Disable buttons while fetching data
    random_game_button.config(state='disabled')
    back_button.config(state='disabled')

    def fetch_data():
        try:
            total_games = get_total_games_count()
            if total_games == 0:
                raise Exception("No games found in the database.")

            random_offset = random.randint(0, total_games - 1)
            response = requests.post(
                f"{api.IGDB_BASE_URL}/games",
                headers=api.HEADERS,
                data=f"fields name, summary, release_dates.date, genres.name, platforms.name, cover.image_id, slug; offset {random_offset}; limit 1;"
            )

            if response.status_code == 200:
                game_data = response.json()[0]
                populate_game_details(game_data, game_name_text, summary_text, platforms_text, 
                                      genres_text, release_dates_text, random_game_search_frame)

                # Build game URL from slug
                game_slug = game_data.get('slug')
                game_url = f"https://www.igdb.com/games/{game_slug}" if game_slug else None

                # Display game image if available
                cover_image_id = game_data.get('cover', {}).get('image_id')
                if cover_image_id:
                    image_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover_image_id}.jpg"
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        image_data = Image.open(BytesIO(image_response.content))
                        # Dynamically compute desired image size
                        current_width  = root.winfo_width() if root.winfo_width() > 100 else 1200
                        current_height = root.winfo_height() if root.winfo_height() > 100 else 800
                        desired_width  = int(current_width * 0.3)
                        desired_height = int(current_height * 0.8)
                        image_data = image_data.resize((desired_width, desired_height))
                        game_image = ImageTk.PhotoImage(image_data)
                        game_image_label.config(image=game_image, text="")
                        game_image_label.image = game_image
                    else:
                        display_no_image(game_image_label, desired_width, desired_height)
                else:
                    display_no_image(game_image_label, desired_width, desired_height)

                # Update the game URL label
                update_game_url(url_label, game_url)
            else:
                raise Exception(f"API call failed with status code {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            random_game_button.config(state='normal')
            back_button.config(state='normal')

    threading.Thread(target=fetch_data, daemon=True).start()


def update_game_url(url_label, game_url):
    """Update the game URL label with a clickable link or placeholder text."""
    if game_url:
        url_label.config(text="View Game on IGDB", foreground="blue", cursor="hand2")
        url_label.bind("<Button-1>", lambda e: open_game_url(game_url))
    else:
        url_label.config(text="No link available", foreground="gray", cursor="arrow")


def open_game_url(url):
    """Open the game URL in the default browser."""
    webbrowser.open(url)


def display_no_image(game_image_label, width=400, height=600):
    """Display a placeholder image with dynamic dimensions."""
    placeholder_image = Image.new("RGB", (width, height), color="gray")
    draw = ImageDraw.Draw(placeholder_image)
    text = "No Image Available"
    try:
        # Use a common font; ensure 'arial.ttf' is accessible or change to a default.
        font = ImageFont.truetype("arial.ttf", int(height * 0.07))
    except Exception:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    draw.text((text_x, text_y), text, fill="white", font=font)
    game_image = ImageTk.PhotoImage(placeholder_image)
    game_image_label.config(image=game_image, text="")
    game_image_label.image = game_image


def populate_game_details(game_data, game_name_text, summary_text, platforms_text, 
                          genres_text, release_dates_text, random_game_search_frame):
    # Populate text widgets with game data
    for widget in [game_name_text, summary_text, platforms_text, genres_text, release_dates_text]:
        widget.config(state="normal")
        widget.delete("1.0", "end")
    
    game_name_text.insert("1.0", game_data.get("name", "No Information"))
    summary_text.insert("1.0", game_data.get("summary", "No Information"))
    platforms_text.insert("1.0", ', '.join(platform['name'] for platform in game_data.get('platforms', [])) or "No Information")
    genres_text.insert("1.0", ', '.join(genre['name'] for genre in game_data.get('genres', [])) or "No Information")
    release_dates_raw = game_data.get('release_dates', [])
    release_dates_text.insert("1.0", ', '.join(
        datetime.fromtimestamp(date_entry['date'], timezone.utc).strftime('%d-%m-%Y')
        for date_entry in release_dates_raw if 'date' in date_entry) or "No Information"
    )

    # Optionally add a clickable URL in this frame if provided by API
    game_url = game_data.get('url')
    if game_url:
        game_url_label = ttk.Label(random_game_search_frame, text="Visit Game Page", foreground="blue", cursor="hand2")
        game_url_label.grid(row=6, column=0, columnspan=2)
        game_url_label.bind("<Button-1>", lambda e: open_game_url(game_url))
    
    for widget in [game_name_text, summary_text, platforms_text, genres_text, release_dates_text]:
        widget.config(state="disabled")


def get_total_games_count():
    response = requests.post(
        f"{api.IGDB_BASE_URL}/games/count",
        headers=api.HEADERS,
        data=""
    )
    if response.status_code == 200:
        return response.json().get('count', 0)
    return 0
