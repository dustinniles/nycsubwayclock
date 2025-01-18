"""
This script fetches train arrival times from the NYC subway GTFS feed and displays
the information on an LED matrix. The script is designed to run on a Raspberry Pi
with an Adafruit RGB Matrix HAT.
"""

import os
import getpass
import stat
from nyct_gtfs import NYCTFeed
from datetime import datetime, timezone
from pytz import timezone as pytz_timezone
from PIL import ImageFont, Image, ImageDraw
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import time
import io

trips_path = "/root/nycsubwayclock/nyct-gtfs/nyct_gtfs/gtfs_static/trips.txt"
stops_path = "/root/nycsubwayclock/nyct-gtfs/nyct_gtfs/gtfs_static/stops.txt"

# Verify file access
try:
    with open(trips_path, "r") as f:
        trips_content = f.read()
        print("Trips file read successfully.")
except PermissionError as e:
    print(f"PermissionError: {e}")
    exit(1)

try:
    with open(stops_path, "r") as f:
        stops_content = f.read()
        print("Stops file read successfully.")
except PermissionError as e:
    print(f"PermissionError: {e}")
    exit(1)

print(f"Current user: {getpass.getuser()}")
print(f"Effective user ID: {os.geteuid()}")
print(f"Trips file path: {trips_path}")
print(f"Stops file path: {stops_path}")
print(f"Trips file permissions: {oct(os.stat(trips_path).st_mode)}")
print(f"Stops file permissions: {oct(os.stat(stops_path).st_mode)}")

# Convert the current time to NYC timezone
nyc_tz = pytz_timezone("America/New_York")
current_time_nyc = datetime.now(nyc_tz)
print(f"Current system time (NYC): {current_time_nyc}")


def fetch_train_times():
    """
    Fetches train arrival times from the NYC subway GTFS feed.

    This function reads the GTFS trips and stops data, initializes the NYCTFeed,
    filters trips for specific stops, calculates the arrival times, and returns
    a list of train arrival times sorted by minutes away.

    Returns:
        list of tuple: A sorted list of tuples containing the train details and minutes away.
    """
    try:
        trips_stream = io.StringIO(trips_content)
        stops_stream = io.StringIO(stops_content)
        print("Initializing NYCTFeed")
        feed = NYCTFeed("C", "C", trips_txt=trips_stream, stops_txt=stops_stream)
        print("NYCTFeed initialized successfully")

        print("Filtering trips")
        trains = feed.filter_trips(headed_for_stop_id=["A44N", "A44S"])
        print(f"Number of trains found: {len(trains)}")

        train_times = []
        for train in trains:
            print(f"Train: {train}")
            for stop_update in train.stop_time_updates:
                if stop_update.stop_id in ["A44N", "A44S"]:
                    arrival_time = stop_update.arrival
                    print(f"Original arrival time: {arrival_time}")

                    # Ensure arrival_time is timezone-aware
                    if (
                        arrival_time.tzinfo is None
                        or arrival_time.tzinfo.utcoffset(arrival_time) is None
                    ):
                        arrival_time = nyc_tz.localize(arrival_time)

                    minutes_away = (
                        arrival_time - current_time_nyc
                    ).total_seconds() // 60
                    print(f"Arrival time: {arrival_time}, Minutes away: {minutes_away}")
                    if minutes_away >= 0:
                        headsign = "".join(
                            c
                            for c in train.headsign_text.strip().replace('"', "")
                            if c.isalnum() or c.isspace()
                        )
                        if minutes_away <= 30:
                            train_times.append(
                                (
                                    f"{map_route_id(train.route_id)} {headsign} {int(minutes_away)}m",
                                    minutes_away,
                                )
                            )
                            print(f"Added train time: {train_times[-1]}")
                        else:
                            print(f"Train {train} is more than 30 minutes away.")
                    else:
                        print(f"Train {train} has a negative minutes away value.")

        # Filter out past train times
        train_times = [t for t in train_times if t[1] >= 0]
        print(f"Filtered train times: {train_times}")

        return sorted(train_times, key=lambda x: x[1])
    except PermissionError as e:
        print(f"PermissionError: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


def map_route_id(route_id):
    """
    Maps the route ID to a corresponding symbol.

    Args:
        route_id (str): The route ID to be mapped.

    Returns:
        str: The mapped symbol for the given route ID.
    """
    mapping = {"A": "!", "C": "@", "E": "#"}
    return mapping.get(route_id, route_id)


def hex_to_rgb(hex_color):
    """
    Converts a hex color string to an RGB tuple. I did this to get as close to the official ACE blue as possible (it's given in RGB)

    Args:
        hex_color (str): The hex color string (e.g., "#FFFFFF").

    Returns:
        tuple: The corresponding RGB tuple (e.g., (255, 255, 255)).
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


font_path = "/root/nycsubwayclock/MTA.ttf"
if not os.path.exists(font_path):
    raise FileNotFoundError(f"Font file not found: {font_path}")

font_size = 16
font = ImageFont.truetype(font_path, font_size)

matrix_width = 128
matrix_height = 32
image = Image.new("RGB", (matrix_width, matrix_height), color=(0, 0, 0))
draw = ImageDraw.Draw(image)

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4

matrix = RGBMatrix(options=options)


def draw_colored_text(draw, text, position, font, route_color, default_color):
    """
    Draws colored text on the image.

    Args:
        draw (ImageDraw.Draw): The drawing context.
        text (str): The text to be drawn.
        position (tuple): The (x, y) position to start drawing the text.
        font (ImageFont): The font to use for the text.
        route_color (tuple): The RGB color for route symbols.
        default_color (tuple): The default RGB color for text.
    """
    x, y = position
    for char in text:
        draw.text(
            (x, y),
            char,
            font=font,
            fill=route_color if char in "!@#" else default_color,
        )
        x += draw.textbbox((x, y), char, font=font)[2] - x


def draw_right_justified_text(draw, text, y, font, color, max_width):
    """
    Draws right-justified text on the image.

    Args:
        draw (ImageDraw.Draw): The drawing context.
        text (str): The text to be drawn.
        y (int): The y-coordinate to start drawing the text.
        font (ImageFont): The font to use for the text.
        color (tuple): The RGB color for the text.
        max_width (int): The maximum width of the text area.
    """
    text_width = draw.textbbox((0, 0), text, font=font)[2]
    x = max_width - text_width
    draw.text((x, y), text, font=font, fill=color)


def truncate_text(text, font, max_width):
    """
    Truncates the text to fit within the specified width.

    Args:
        text (str): The text to be truncated.
        font (ImageFont): The font to use for the text.
        max_width (int): The maximum width of the text area.

    Returns:
        str: The truncated text with ellipsis if necessary.
    """
    ellipsis = "..."
    while draw.textbbox((0, 0), text + ellipsis, font=font)[2] > max_width:
        if len(text) <= 1:
            return ellipsis
        text = text[:-1]
    return (
        text + ellipsis
        if draw.textbbox((0, 0), text, font=font)[2] > max_width
        else text
    )


def draw_white_circle(draw, position, size):
    """
    Draws a white circle on the image under the route bullet. That way the letter shows up in white.

    Args:
        draw (ImageDraw.Draw): The drawing context.
        position (tuple): The (x, y) position to draw the circle.
        size (int): The diameter of the circle.
    """
    x, y = position
    offset_x = 17
    offset_y = 1
    draw.ellipse(
        (x + offset_x, y + offset_y, x + offset_x + size, y + offset_y + size),
        fill=(255, 255, 255),
    )


def update_display(closest_arrival, next_arrival, line_number):
    """
    Updates the LED matrix display with train arrival information.

    Args:
        closest_arrival (tuple): The closest train arrival information.
        next_arrival (tuple): The next train arrival information to display on the second line.
        line_number (int): The line number to display the next arrival.
    """
    draw.rectangle((0, 0, matrix_width, matrix_height), fill=(0, 0, 0))
    blue_color = hex_to_rgb("#003986")
    circle_size = font_size - 6

    if closest_arrival[0] != "No trains available":
        closest_parts = closest_arrival[0].rsplit(" ", 1)
        closest_headsign = truncate_text(closest_parts[0], font, matrix_width - 30)
        arrival_time = closest_parts[1]

        draw_white_circle(draw, (0, 0), circle_size)
        draw_colored_text(
            draw, f"1. {closest_headsign}", (0, 0), font, blue_color, (255, 255, 255)
        )
        draw_right_justified_text(
            draw, arrival_time, 0, font, (255, 255, 255), matrix_width
        )

    # Display the next arrival on the second line
    if next_arrival:
        next_parts = next_arrival[0].rsplit(" ", 1)
        next_headsign = truncate_text(next_parts[0], font, matrix_width - 30)
        arrival_time = next_parts[1]

        draw_white_circle(draw, (0, 16), circle_size)
        draw_colored_text(
            draw,
            f"{line_number}. {next_headsign}",
            (0, 16),
            font,
            blue_color,
            (255, 255, 255),
        )
        draw_right_justified_text(
            draw, arrival_time, 16, font, (255, 255, 255), matrix_width
        )

    image_rgb = image.convert("RGB")
    pixels = image_rgb.load()
    for x in range(matrix_width):
        for y in range(matrix_height):
            r, g, b = pixels[x, y]
            matrix.SetPixel(x, y, r, g, b)

train_times = fetch_train_times()

if train_times:
    closest_arrival = (
        train_times[0] if len(train_times) > 0 else ("No trains available", 0)
    )
    next_arrivals = train_times[1:4] if len(train_times) > 1 else []
else:
    closest_arrival = ("No trains available", 0)
    next_arrivals = []

secondary_index = 0

# Initial display update
if next_arrivals:
    next_arrival = next_arrivals[secondary_index]
    line_number = secondary_index + 2
else:
    next_arrival = ("No trains available", 0)
    line_number = 2

update_display(closest_arrival, next_arrival, line_number)
time.sleep(3)

while True:
    # Fetch the latest train times every minute
    if secondary_index == 0:
        current_time_nyc = datetime.now(nyc_tz)  # Update current time for accurate calculations
        train_times = fetch_train_times()
        if train_times:
            closest_arrival = (
                train_times[0] if len(train_times) > 0 else ("No trains available", 0)
            )
            next_arrivals = train_times[1:4] if len(train_times) > 1 else []
        else:
            closest_arrival = ("No trains available", 0)
            next_arrivals = []

    if next_arrivals:
        next_arrival = next_arrivals[secondary_index]
        line_number = secondary_index + 2
    else:
        next_arrival = ("No trains available", 0)
        line_number = 2

    update_display(closest_arrival, next_arrival, line_number)
    secondary_index = (secondary_index + 1) % len(next_arrivals)
    time.sleep(5)
