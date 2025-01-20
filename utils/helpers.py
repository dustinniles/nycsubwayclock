import pytz
from datetime import datetime

def get_current_time(timezone_str):
    """
    Returns the current time in the specified timezone.
    """
    if isinstance(timezone_str, str):
        tz = pytz.timezone(timezone_str)
    else:
        raise ValueError("Invalid timezone format. Expected a string.")
    return datetime.now(tz)

def hex_to_rgb(hex_color):
    """
    Converts a hex color string to an RGB tuple.
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def truncate_text(text, font, max_width):
    """
    Truncate the text so that it fits within the specified width.
    """
    ellipsis = "..."
    ellipsis_width = font.getbbox(ellipsis)[2] - font.getbbox(ellipsis)[0]
    text_width = font.getbbox(text)[2] - font.getbbox(text)[0]

    while text and text_width > max_width:
        text = text[:-1]
        text_width = font.getbbox(text + ellipsis)[2] - font.getbbox(text + ellipsis)[0]

    return text + ellipsis if text else text

def map_route_id(route_id):
    """
    Maps a route_id to a human-readable name.
    """
    route_map = {
        "A": "A Train",
        "C": "C Train",
        "E": "E Train",
        # Add other route mappings as needed
    }
    return route_map.get(route_id, route_id)
