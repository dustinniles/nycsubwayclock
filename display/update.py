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

    def draw_colored_text_with_circles(self, text, position, route_color, default_color):
        """
        Draw text with special coloring for route bullets and white circles behind them.
        Route bullets (!@#) are colored with route_color and have white circles behind them.
        """
        x, y = position
        # Fine-tuned circle positioning to center behind route bullets
        # Positive x = right, positive y = down; negative x = left, negative y = up
        circle_offset_x = 1
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
            # Draw direction label on the left
            self.draw.text((0, 0), self.config.DIRECTION_NORTH_LABEL, font=self.font, fill=self.white_color)

            # Format and draw train listings on the right
            trains_text = self._format_trains_only(northbound_trains)
            text_width = self.draw.textbbox((0, 0), trains_text, font=self.font)[2]
            x_position = self.matrix_width - text_width
            self.draw_colored_text_with_circles(trains_text, (x_position, 0), self.blue_color, self.white_color)
        else:
            # Show direction label with no trains
            line_text = f"{self.config.DIRECTION_NORTH_LABEL}   No trains"
            self.draw.text((0, 0), line_text, font=self.font, fill=self.white_color)

        # Display southbound trains on line 2
        if southbound_trains:
            # Draw direction label on the left
            self.draw.text((0, 16), self.config.DIRECTION_SOUTH_LABEL, font=self.font, fill=self.white_color)

            # Format and draw train listings on the right
            trains_text = self._format_trains_only(southbound_trains)
            text_width = self.draw.textbbox((0, 0), trains_text, font=self.font)[2]
            x_position = self.matrix_width - text_width
            self.draw_colored_text_with_circles(trains_text, (x_position, 16), self.blue_color, self.white_color)
        else:
            # Show direction label with no trains
            line_text = f"{self.config.DIRECTION_SOUTH_LABEL}   No trains"
            self.draw.text((0, 16), line_text, font=self.font, fill=self.white_color)

        # Render to offscreen canvas then swap
        self.offscreen_canvas.SetImage(self.image.convert("RGB"))
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    def _format_trains_only(self, trains):
        """
        Format train listings without direction label.
        Dynamically fits as many trains as possible within available space.

        Args:
            trains: List of train dicts [{'route_id': str, 'minutes': int, ...}, ...]

        Returns:
            Formatted string like "A 3m C 5m E 7m"
        """
        line_text = ""

        # Add trains one at a time, checking width
        for i, train in enumerate(trains):
            bullet = map_route_to_bullet(train['route_id'])
            time_str = f"{train['minutes']}m"

            # Format this train with separator if not first
            if i == 0:
                train_text = f"{bullet} {time_str}"
            else:
                train_text = f" {bullet} {time_str}"

            # Check if adding this train would exceed display width
            test_line = line_text + train_text
            text_width = self.draw.textbbox((0, 0), test_line, font=self.font)[2]

            if text_width <= self.matrix_width:
                line_text += train_text
            else:
                # Stop adding trains - we've run out of space
                break

        return line_text
