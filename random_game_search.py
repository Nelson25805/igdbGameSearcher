import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from io import BytesIO
from api import random_game_api
import requests
import random
from datetime import datetime, timezone

import threading


def open_random_game_search(root, previous_frame, shared_state, show_frame):
    # Create the random game search frame
    random_game_search_frame = ttk.Frame(root, padding="10")

    # Configure grid for layout
    random_game_search_frame.columnconfigure(0, weight=1)
    random_game_search_frame.columnconfigure(1, weight=1)
    random_game_search_frame.rowconfigure(0, weight=0)  # Make sure row 0 (title row) doesn't stretch
    random_game_search_frame.rowconfigure(1, weight=1)  # Other rows should be expandable

    # Add title label at the top center
    title_label = ttk.Label(random_game_search_frame, text="Random Game Section", font=("Arial", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")

    # Add components (e.g., details, image, buttons)
    details_frame = ttk.Frame(random_game_search_frame)
    details_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    def add_detail_row(frame, row, label_text, height):
        label = ttk.Label(frame, text=label_text, font=("Arial", 12, "bold"))
        label.grid(row=row, column=0, sticky="w", pady=5)

        # Create a Text widget with padding, border, and a scrollbar
        textbox_frame = ttk.Frame(frame)  # Container for text box and scrollbar
        textbox_frame.grid(row=row, column=1, sticky="ew", padx=10, pady=5)

        textbox = tk.Text(textbox_frame, height=height, state="disabled", wrap="word", bd=2, relief="sunken")
        textbox.grid(row=0, column=0, sticky="ew")

        # Adding scrollbar
        scrollbar = ttk.Scrollbar(textbox_frame, orient="vertical", command=textbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        textbox.config(yscrollcommand=scrollbar.set)

        return textbox

    # Adjusting height of textboxes to make them smaller
    game_name_text = add_detail_row(details_frame, 0, "Game Name:", 2)
    summary_text = add_detail_row(details_frame, 1, "Summary:", 4)  # Reduced height
    platforms_text = add_detail_row(details_frame, 2, "Platforms:", 2)  # Reduced height
    genres_text = add_detail_row(details_frame, 3, "Genres:", 2)  # Reduced height
    release_dates_text = add_detail_row(details_frame, 4, "Release Dates:", 2)  # Reduced height

    # Game Image
    game_image_label = ttk.Label(random_game_search_frame, text="No Image Available", font=("Arial", 12, "italic"))
    game_image_label.grid(row=1, column=1, rowspan=5, sticky="nsew", padx=10, pady=10)

    # Display placeholder image
    display_no_image(game_image_label)

    # Buttons at the bottom
    buttons_frame = ttk.Frame(random_game_search_frame)
    buttons_frame.grid(row=6, column=0, columnspan=2, pady=10)

    random_game_button = ttk.Button(buttons_frame, text="Fetch Random Game",
                                    command=lambda: fetch_random_game_gui(
                                        game_name_text, summary_text, platforms_text,
                                        genres_text, release_dates_text, game_image_label, 
                                        random_game_button, back_button
                                    ))
    random_game_button.pack(side="left", padx=10)

    # Back Button to return to the previous page
    back_button = ttk.Button(buttons_frame, text="Back to Main Page",
                             command=lambda: show_frame(previous_frame))
    back_button.pack(side="right", padx=10)

    # Show the new frame
    show_frame(random_game_search_frame)



def fetch_random_game_gui(game_name_text, summary_text, platforms_text, genres_text, release_dates_text, 
                          game_image_label, random_game_button, back_button):
    # Disable both buttons
    random_game_button.config(state='disabled')
    back_button.config(state='disabled')

    # Function to run in a separate thread
    def fetch_data():
        try:
            print("Random Game Button has been pressed.")
            
            total_games = get_total_games_count()
            if total_games == 0:
                raise Exception("No games found in the database.")

            random_offset = random.randint(0, total_games - 1)
            response = requests.post(
                f"{random_game_api.IGDB_BASE_URL}/games",
                headers=random_game_api.HEADERS,
                data=f"fields name, summary, release_dates.date, genres.name, platforms.name, cover.image_id; offset {random_offset}; limit 1;"
            )

            if response.status_code == 200:
                game_data = response.json()[0]
                populate_game_details(game_data, game_name_text, summary_text, platforms_text, genres_text, release_dates_text)

                cover_image_id = game_data.get('cover', {}).get('image_id')
                if cover_image_id:
                    image_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover_image_id}.jpg"
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        image_data = Image.open(BytesIO(image_response.content))
                        image_data = image_data.resize((400, 600))  # Increased image size
                        game_image = ImageTk.PhotoImage(image_data)
                        game_image_label.config(image=game_image, text="")  # Clear text and set image
                        game_image_label.image = game_image
                    else:
                        display_no_image(game_image_label)
                else:
                    display_no_image(game_image_label)
            else:
                raise Exception(f"API call failed with status code {response.status_code}")

        except Exception as e:
            # Display an error message or handle it
            print(f"Error: {e}")

        finally:
            # Re-enable both buttons on the main thread
            random_game_button.config(state='normal')
            back_button.config(state='normal')

    # Start the fetch_data function in a new thread
    threading.Thread(target=fetch_data, daemon=True).start()



    

def set_buttons_state(frame, state):
    """Enable or disable all buttons in the given frame."""
    for widget in frame.winfo_children():
        if isinstance(widget, ttk.Button):
            widget.config(state=state)
  



def display_no_image(game_image_label):
    # Create a blank placeholder image
    placeholder_image = Image.new("RGB", (400, 600), color="gray")

    # Draw "No Image Available" text
    draw = ImageDraw.Draw(placeholder_image)
    text = "No Image Available"
    font = ImageFont.load_default()  # Default font

    # Calculate text position for centering
    text_bbox = draw.textbbox((0, 0), text, font=font)  # Get text dimensions
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (placeholder_image.width - text_width) // 2
    text_y = (placeholder_image.height - text_height) // 2

    # Draw the text onto the image
    draw.text((text_x, text_y), text, fill="white", font=font)

    # Convert to PhotoImage for Tkinter
    game_image = ImageTk.PhotoImage(placeholder_image)
    game_image_label.config(image=game_image, text="")  # Clear text and set placeholder image
    game_image_label.image = game_image


def populate_game_details(game_data, game_name_text, summary_text, platforms_text, genres_text, release_dates_text):
    # Helper function to populate textboxes with data
    game_name_text.config(state="normal")
    summary_text.config(state="normal")
    platforms_text.config(state="normal")
    genres_text.config(state="normal")
    release_dates_text.config(state="normal")

    game_name_text.delete("1.0", "end")
    summary_text.delete("1.0", "end")
    platforms_text.delete("1.0", "end")
    genres_text.delete("1.0", "end")
    release_dates_text.delete("1.0", "end")

    game_name_text.insert("1.0", game_data.get("name", "No Information"))
    summary_text.insert("1.0", game_data.get("summary", "No Information"))
    platforms_text.insert("1.0", ', '.join(platform['name'] for platform in game_data.get('platforms', [])) or "No Information")
    genres_text.insert("1.0", ', '.join(genre['name'] for genre in game_data.get('genres', [])) or "No Information")

    release_dates_raw = game_data.get('release_dates', [])
    release_dates_text.insert("1.0", ', '.join(
        datetime.fromtimestamp(date_entry['date'], timezone.utc).strftime('%Y-%m-%d')
        for date_entry in release_dates_raw if 'date' in date_entry) or "No Information"
    )

    for textbox in [game_name_text, summary_text, platforms_text, genres_text, release_dates_text]:
        textbox.config(state="disabled")


def get_total_games_count():
    response = requests.post(
        f"{random_game_api.IGDB_BASE_URL}/games/count",
        headers=random_game_api.HEADERS,
        data=""
    )
    if response.status_code == 200:
        return response.json().get('count', 0)
    return 0
