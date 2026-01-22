import logging
from utils.helpers import hex_to_rgb, truncate_text
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from config import Config

logger = logging.getLogger(__name__)


# Mapping for route bullets (used with custom MTA font)
ROUTE_TO_BULLET = {"A": "!", "C": "@", "E": "#"}


def map_route_to_bullet(route_id):
    """
    Maps the route ID to the corresponding bullet character for the MTA font.
    The MTA.ttf font uses special characters for route bullets:
    ! = A train, @ = C train, # = E train
    """
    return ROUTE_TO_BULLET.get(route_id, route_id)


def is_valid_train_data(arrival_tuple):
    """
    Check if arrival data represents actual train info (not error message).

    Args:
        arrival_tuple: Tuple of (arrival_text, minutes_away)

    Returns:
        bool: True if valid train data, False if error message or invalid
    """
    if not arrival_tuple or not arrival_tuple[0]:
        return False
    text = arrival_tuple[0]
    # Check for known error messages
    if text in ["No trains available", "Error", ""]:
        return False
    # Valid train data should have route ID and arrival time
    return " " in text and len(text.split()) >= 2


class DisplayManager:
    """
    Manages the LED matrix display for subway arrival times.
    Encapsulates all display state and configuration.
    """

    def __init__(self, config=None):
        """
        Initialize the DisplayManager with configuration.

        Args:
            config: Config object (defaults to global Config if not provided)
        """
        self.config = config or Config

        # Font setup
        self.font = ImageFont.truetype(self.config.FONT_PATH, self.config.FONT_SIZE)

        # Matrix dimensions
        self.matrix_width = self.config.MATRIX_COLS * self.config.MATRIX_CHAIN_LENGTH
        self.matrix_height = self.config.MATRIX_ROWS

        # Image and draw objects
        self.image = Image.new("RGB", (self.matrix_width, self.matrix_height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        # Matrix setup
        options = RGBMatrixOptions()
        options.rows = self.config.MATRIX_ROWS
        options.cols = self.config.MATRIX_COLS
        options.chain_length = self.config.MATRIX_CHAIN_LENGTH
        options.parallel = 1
        options.hardware_mapping = self.config.MATRIX_HARDWARE_MAPPING
        options.gpio_slowdown = self.config.MATRIX_GPIO_SLOWDOWN
        options.show_refresh_rate = self.config.MATRIX_SHOW_REFRESH_RATE
        options.pwm_lsb_nanoseconds = self.config.MATRIX_PWM_LSB_NANOSECONDS
        options.pwm_bits = self.config.MATRIX_PWM_BITS
        options.brightness = self.config.MATRIX_BRIGHTNESS

        self.matrix = RGBMatrix(options=options)

        # Create offscreen canvas for double buffering
        self.offscreen_canvas = self.matrix.CreateFrameCanvas()

        # Display colors
        self.blue_color = hex_to_rgb("#003986")  # MTA blue
        self.white_color = (255, 255, 255)
        self.circle_size = self.config.FONT_SIZE - 6

        logger.info(f"DisplayManager initialized: {self.matrix_width}x{self.matrix_height}")

    def draw_colored_text(self, text, position, route_color, default_color):
        """
        Draw text with special coloring for route bullets.
        Route bullets (!@#) are colored with route_color, other text with default_color.
        """
        x, y = position
        for char in text:
            self.draw.text(
                (x, y),
                char,
                font=self.font,
                fill=route_color if char in "!@#" else default_color,
            )
            x += self.draw.textbbox((x, y), char, font=self.font)[2] - x

    def draw_right_justified_text(self, text, y, color, max_width):
        """Draw text right-justified within max_width."""
        text_width = self.draw.textbbox((0, 0), text, font=self.font)[2]
        x = max_width - text_width
        self.draw.text((x, y), text, font=self.font, fill=color)

    def draw_white_circle(self, position, size):
        """Draw a white circle at the given position."""
        x, y = position
        offset_x = 17
        offset_y = 1
        self.draw.ellipse(
            (x + offset_x, y + offset_y, x + offset_x + size, y + offset_y + size),
            fill=self.white_color,
        )

    def update_display(self, closest_arrival, next_arrival, line_number):
        """
        Update the LED matrix display with train arrival information.

        Args:
            closest_arrival: Tuple of (arrival_text, minutes_away) for the closest train
            next_arrival: Tuple of (arrival_text, minutes_away) for the next train
            line_number: Line number to display for the next train (2, 3, or 4)
        """
        logger.debug(
            f"update_display: closest={closest_arrival}, next={next_arrival}, line={line_number}"
        )

        # Print to console for debugging
        print(f"Displaying on matrix:")
        print(f" - Closest arrival: {closest_arrival}")
        print(f" - Next arrival: {next_arrival}")
        print(f" - Line number: {line_number}")

        # Clear the display
        self.draw.rectangle((0, 0, self.matrix_width, self.matrix_height), fill=(0, 0, 0))

        # Display closest arrival on line 1
        if is_valid_train_data(closest_arrival):
            closest_parts = closest_arrival[0].rsplit(" ", 1)
            route_id = closest_parts[0].split()[0]  # Extract route ID
            headsign_text = (
                " ".join(closest_parts[0].split()[1:]).replace("Train", "").strip()
            )
            mapped_route = map_route_to_bullet(route_id)
            arrival_time = closest_parts[1]
            
            # Calculate time width to determine available space for headsign
            time_width = self.draw.textbbox((0, 0), arrival_time, font=self.font)[2]
            available_width = self.matrix_width - time_width - 10  # 10px padding between text and time
            
            closest_headsign = truncate_text(
                f"{mapped_route} {headsign_text}", self.font, available_width
            )

            self.draw_white_circle((0, 0), self.circle_size)
            self.draw_colored_text(
                f"1. {closest_headsign}", (0, 0), self.blue_color, self.white_color
            )
            self.draw_right_justified_text(
                arrival_time, 0, self.white_color, self.matrix_width
            )

        # Display next arrival on line 2
        if is_valid_train_data(next_arrival):
            next_parts = next_arrival[0].rsplit(" ", 1)
            route_id = next_parts[0].split()[0]  # Extract route ID
            headsign_text = (
                " ".join(next_parts[0].split()[1:]).replace("Train", "").strip()
            )
            mapped_route = map_route_to_bullet(route_id)
            arrival_time = next_parts[1]
            
            # Calculate time width to determine available space for headsign
            time_width = self.draw.textbbox((0, 0), arrival_time, font=self.font)[2]
            available_width = self.matrix_width - time_width - 10  # 10px padding between text and time
            
            next_headsign = truncate_text(
                f"{mapped_route} {headsign_text}", self.font, available_width
            )

            self.draw_white_circle((0, 16), self.circle_size)
            self.draw_colored_text(
                f"{line_number}. {next_headsign}",
                (0, 16),
                self.blue_color,
                self.white_color,
            )
            self.draw_right_justified_text(
                arrival_time, 16, self.white_color, self.matrix_width
            )

        # Render to offscreen canvas then swap
        self.offscreen_canvas.SetImage(self.image.convert("RGB"))
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
