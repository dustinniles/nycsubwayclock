import logging
from pytz import timezone as pytz_timezone
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/nycsubwayclock.log"),
        logging.StreamHandler()
    ]
)

def get_current_time(nyc_tz):
    return datetime.now(nyc_tz)

def map_route_id(route_id):
    mapping = {"A": "!", "C": "@", "E": "#"}
    return mapping.get(route_id, route_id)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

def truncate_text(text, font, max_width):
    ellipsis = "..."
    while font.getsize(text + ellipsis)[0] > max_width:
        if len(text) <= 1:
            return ellipsis
        text = text[:-1]
    return text + ellipsis if font.getsize(text)[0] > max_width else text
