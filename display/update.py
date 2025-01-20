import logging
from utils.helpers import hex_to_rgb, truncate_text
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions

logger = logging.getLogger(__name__)

font_path = "/root/nycsubwayclock/MTA.ttf"
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
options.gpio_slowdown = 3
options.show_refresh_rate = True  # Use --led-show-refresh to see the refresh rate
options.pwm_lsb_nanoseconds = 50  # led-pwm-lsb-nanoseconds=50
options.pwm_bits = 5

matrix = RGBMatrix(options=options)

# Mapping for route bullets
route_mapping = {"A": "!", "C": "@", "E": "#"}

def map_route_id(route_id):
    """
    Maps the route ID to the corresponding route bullet.
    """
    return route_mapping.get(route_id, route_id)

def draw_colored_text(draw, text, position, font, route_color, default_color):
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
    text_width = draw.textbbox((0, 0), text, font=font)[2]
    x = max_width - text_width
    draw.text((x, y), text, font=font, fill=color)

def truncate_text(text, font, max_width):
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
    x, y = position
    offset_x = 17
    offset_y = 1
    draw.ellipse(
        (x + offset_x, y + offset_y, x + offset_x + size, y + offset_y + size),
        fill=(255, 255, 255),
    )

def update_display(closest_arrival, next_arrival, line_number):
    logger.debug(f"update_display called with: closest_arrival={closest_arrival}, next_arrival={next_arrival}, line_number={line_number}")

    # Print the information to be displayed
    print(f"Displaying on matrix:")
    print(f" - Closest arrival: {closest_arrival}")
    print(f" - Next arrival: {next_arrival}")
    print(f" - Line number: {line_number}")

    draw.rectangle((0, 0, matrix_width, matrix_height), fill=(0, 0, 0))
    blue_color = hex_to_rgb("#003986")
    circle_size = font_size - 6

    if closest_arrival[0] != "No trains available":
        closest_parts = closest_arrival[0].rsplit(" ", 1)
        route_id = closest_parts[0].split()[0]  # Extract route ID
        headsign_text = " ".join(closest_parts[0].split()[1:]).replace("Train", "").strip()  # Remove "Train" and extract headsign
        mapped_route = map_route_id(route_id)
        closest_headsign = truncate_text(f"{mapped_route} {headsign_text}", font, matrix_width - 30)
        arrival_time = closest_parts[1]

        draw_white_circle(draw, (0, 0), circle_size)
        draw_colored_text(
            draw, f"1. {closest_headsign}", (0, 0), font, blue_color, (255, 255, 255)
        )
        draw_right_justified_text(
            draw, arrival_time, 0, font, (255, 255, 255), matrix_width
        )

    if next_arrival[0]:
        next_parts = next_arrival[0].rsplit(" ", 1)
        route_id = next_parts[0].split()[0]  # Extract route ID
        headsign_text = " ".join(next_parts[0].split()[1:]).replace("Train", "").strip()  # Remove "Train" and extract headsign
        mapped_route = map_route_id(route_id)
        next_headsign = truncate_text(f"{mapped_route} {headsign_text}", font, matrix_width - 30)
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
