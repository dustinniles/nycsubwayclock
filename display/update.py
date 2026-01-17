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

        self.matrix = RGBMatrix(options=options)

        # Display colors
        self.blue_color = hex_to_rgb("#003986")  # MTA blue
        self.white_color = (255, 255, 255)
        self.circle_size = self.config.FONT_SIZE - 6

        logger.info(f"DisplayManager initialized: {self.matrix_width}x{self.matrix_height}")

    def draw_colored_text_with_circles(self, text, position, route_color, default_color):
        """
        Draw text with special coloring for route bullets and white circles behind them.
        Route bullets (!@#) are colored with route_color and have white circles behind them.
        """
        x, y = position
        circle_offset_x = -2
        circle_offset_y = 1

        for char in text:
            # Draw white circle behind route bullets
            if char in "!@#":
                self.draw.ellipse(
                    (x + circle_offset_x, y + circle_offset_y,
                     x + circle_offset_x + self.circle_size, y + circle_offset_y + self.circle_size),
                    fill=self.white_color,
                )

            # Draw the character
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

    def update_display(self, northbound_trains, southbound_trains):
        """
        Update the LED matrix display with train arrival information by direction.

        Args:
            northbound_trains: List of train dicts for northbound direction
            southbound_trains: List of train dicts for southbound direction
        """
        logger.debug(
            f"update_display: northbound={northbound_trains}, southbound={southbound_trains}"
        )

        # Print to console for debugging
        print(f"Displaying on matrix:")
        print(f" - Northbound: {northbound_trains}")
        print(f" - Southbound: {southbound_trains}")

        # Clear the display
        self.draw.rectangle((0, 0, self.matrix_width, self.matrix_height), fill=(0, 0, 0))

        # Display northbound trains on line 1
        if northbound_trains:
            line_text = self._format_direction_line(
                northbound_trains, self.config.DIRECTION_NORTH_LABEL
            )
            self.draw_colored_text_with_circles(line_text, (0, 0), self.blue_color, self.white_color)
        else:
            # Show direction label with no trains
            line_text = f"{self.config.DIRECTION_NORTH_LABEL}   No trains"
            self.draw.text((0, 0), line_text, font=self.font, fill=self.white_color)

        # Display southbound trains on line 2
        if southbound_trains:
            line_text = self._format_direction_line(
                southbound_trains, self.config.DIRECTION_SOUTH_LABEL
            )
            self.draw_colored_text_with_circles(line_text, (0, 16), self.blue_color, self.white_color)
        else:
            # Show direction label with no trains
            line_text = f"{self.config.DIRECTION_SOUTH_LABEL}   No trains"
            self.draw.text((0, 16), line_text, font=self.font, fill=self.white_color)

        # Render to matrix
        image_rgb = self.image.convert("RGB")
        pixels = image_rgb.load()
        for x in range(self.matrix_width):
            for y in range(self.matrix_height):
                r, g, b = pixels[x, y]
                self.matrix.SetPixel(x, y, r, g, b)

    def _format_direction_line(self, trains, direction_label):
        """
        Format a line showing multiple trains for a direction.

        Args:
            trains: List of train dicts [{'route_id': str, 'minutes': int, ...}, ...]
            direction_label: Label for the direction (e.g., "MN", "BK")

        Returns:
            Formatted string like "MN   A 3m, C 5m"
        """
        # Format each train as "BULLET TIMEm"
        train_parts = []
        for i, train in enumerate(trains):
            bullet = map_route_to_bullet(train['route_id'])
            time_str = f"{train['minutes']}m"
            # Add comma and space after all but the last train
            if i < len(trains) - 1:
                train_parts.append(f"{bullet} {time_str}, ")
            else:
                train_parts.append(f"{bullet} {time_str}")

        # Join without additional separators (we already added commas above)
        trains_text = "".join(train_parts)

        # Return full line with direction label (4 spaces for better visibility)
        return f"{direction_label}    {trains_text}"
