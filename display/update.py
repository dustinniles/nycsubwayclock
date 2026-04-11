import logging
from utils.helpers import hex_to_rgb
from PIL import Image, ImageDraw, ImageFont
from config import Config

logger = logging.getLogger(__name__)

# Try to import rgbmatrix; allow simulation mode on non-Pi machines
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False
    logger.warning("rgbmatrix not available - running in simulation mode")


# Official MTA route colors (hex)
ROUTE_COLORS = {
    "A": "#003986", "C": "#003986", "E": "#003986",                          # Blue
    "B": "#FF6319", "D": "#FF6319", "F": "#FF6319", "M": "#FF6319",          # Orange
    "1": "#EE352E", "2": "#EE352E", "3": "#EE352E",                          # Red
    "4": "#00933C", "5": "#00933C", "6": "#00933C",                           # Green
    "7": "#B933AD",                                                            # Purple
    "N": "#FCCC0A", "Q": "#FCCC0A", "R": "#FCCC0A", "W": "#FCCC0A",          # Yellow
    "L": "#A7A9AC",                                                            # Gray
    "G": "#6CBE45",                                                            # Light green
    "J": "#996633", "Z": "#996633",                                            # Brown
    "S": "#808183", "GS": "#808183", "FS": "#808183", "SR": "#808183",        # Shuttles
    "SI": "#003986",                                                           # Staten Island Railway
}


def route_color_rgb(route_id):
    """Return the official MTA color for a route as an RGB tuple."""
    return hex_to_rgb(ROUTE_COLORS.get(route_id, "#003986"))


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
        # Smaller font for route bullet glyphs — sized to fit inside the circle with 1px padding
        bullet_font_size = int(self.config.FONT_SIZE * 0.7)
        self.bullet_font = ImageFont.truetype(self.config.FONT_PATH, bullet_font_size)

        # Matrix dimensions
        self.matrix_width = self.config.MATRIX_COLS * self.config.MATRIX_CHAIN_LENGTH
        self.matrix_height = self.config.MATRIX_ROWS

        # Display layout (derived from font size, no magic numbers)
        self.line_height = self.config.FONT_SIZE
        self.line1_y = 0
        self.line2_y = self.line_height
        self.circle_size = int(self.config.FONT_SIZE * 0.625)
        self.circle_offset_x = max(1, self.config.FONT_SIZE // 16)
        self.circle_offset_y = max(1, self.config.FONT_SIZE // 16)

        # Image and draw objects
        self.image = Image.new("RGB", (self.matrix_width, self.matrix_height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        # Display colors
        self.white_color = (255, 255, 255)

        # Matrix setup (or simulation mode)
        self.simulate = getattr(self.config, "SIMULATE_DISPLAY", False)
        if HAS_MATRIX and not self.simulate:
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
            self.offscreen_canvas = self.matrix.CreateFrameCanvas()
        else:
            self.matrix = None
            self.offscreen_canvas = None
            if self.simulate:
                logger.info("Running in simulation mode (SIMULATE_DISPLAY=true)")
            else:
                logger.info("Running in simulation mode (rgbmatrix not available)")

        # Pre-compute character widths for the fixed font
        self._char_widths = {}
        for char in " 0123456789mABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
            bbox = self.draw.textbbox((0, 0), char, font=self.font)
            self._char_widths[char] = bbox[2] - bbox[0]

        logger.info(f"DisplayManager initialized: {self.matrix_width}x{self.matrix_height}")

    def _text_width(self, text):
        """Calculate text width using cached character widths."""
        width = 0
        for char in text:
            if char in self._char_widths:
                width += self._char_widths[char]
            else:
                bbox = self.draw.textbbox((0, 0), char, font=self.font)
                self._char_widths[char] = bbox[2] - bbox[0]
                width += self._char_widths[char]
        return width

    def _bullet_width(self):
        """Width of a single route bullet (circle + padding)."""
        return self.circle_size + self.circle_offset_x + 1

    def _draw_bullet(self, x, y, route_id):
        """
        Draw a route bullet: colored circle with white route letter centered inside.
        Works for all NYC subway routes.
        """
        color = route_color_rgb(route_id)

        # Draw filled circle in the route's official color
        self.draw.ellipse(
            (x + self.circle_offset_x, y + self.circle_offset_y,
             x + self.circle_offset_x + self.circle_size,
             y + self.circle_offset_y + self.circle_size),
            fill=color,
        )

        # Draw route letter centered in white on top of the circle
        letter = route_id[0]  # Use first character for multi-char routes (SI, GS)
        circle_center_x = x + self.circle_offset_x + self.circle_size // 2
        circle_center_y = y + self.circle_offset_y + self.circle_size // 2
        letter_bbox = self.draw.textbbox((0, 0), letter, font=self.bullet_font)
        letter_x = circle_center_x - (letter_bbox[0] + letter_bbox[2]) // 2
        letter_y = circle_center_y - (letter_bbox[1] + letter_bbox[3]) // 2
        self.draw.text((letter_x, letter_y), letter, font=self.bullet_font, fill=self.white_color)

    def _measure_train_segment(self, train, is_first):
        """Measure the pixel width of a single train entry (bullet + time)."""
        time_str = f" {train['minutes']}m"
        bullet_w = self._bullet_width()
        time_w = self._text_width(time_str)
        separator_w = 0 if is_first else self._text_width(" ")
        return separator_w + bullet_w + time_w

    def _draw_train_line(self, trains, y, direction_label):
        """
        Draw a complete line: direction label on the left, train bullets+times on the right.
        Each bullet is drawn in its route's official MTA color.
        """
        # Draw direction label on the left
        self.draw.text((0, y), direction_label, font=self.font, fill=self.white_color)

        if not trains:
            no_trains_text = f"{direction_label}   No trains"
            self.draw.text((0, y), no_trains_text, font=self.font, fill=self.white_color)
            return

        # Determine which trains fit in the available width
        visible_trains = []
        total_width = 0
        for i, train in enumerate(trains):
            seg_width = self._measure_train_segment(train, i == 0)
            if total_width + seg_width <= self.matrix_width:
                visible_trains.append(train)
                total_width += seg_width
            else:
                break

        # Draw trains right-justified
        x = self.matrix_width - total_width
        for i, train in enumerate(visible_trains):
            if i > 0:
                space_w = self._text_width(" ")
                x += space_w

            # Draw bullet
            self._draw_bullet(x, y, train['route_id'])
            x += self._bullet_width()

            # Draw time
            time_str = f" {train['minutes']}m"
            self.draw.text((x, y), time_str, font=self.font, fill=self.white_color)
            x += self._text_width(time_str)

    def update_display(self, northbound_trains, southbound_trains):
        """
        Update the LED matrix display with train arrival information by direction.

        Args:
            northbound_trains: List of train dicts for northbound direction
            southbound_trains: List of train dicts for southbound direction
        """
        logger.debug(f"Displaying: N={northbound_trains}, S={southbound_trains}")

        # Clear the display
        self.draw.rectangle((0, 0, self.matrix_width, self.matrix_height), fill=(0, 0, 0))

        # Draw northbound trains on line 1
        self._draw_train_line(northbound_trains, self.line1_y, self.config.DIRECTION_NORTH_LABEL)

        # Draw southbound trains on line 2
        self._draw_train_line(southbound_trains, self.line2_y, self.config.DIRECTION_SOUTH_LABEL)

        # Render to hardware or log in simulation mode
        if self.matrix is not None:
            self.offscreen_canvas.SetImage(self.image)
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
        else:
            n_desc = ", ".join(f"{t['route_id']}={t['minutes']}m" for t in northbound_trains) or "none"
            s_desc = ", ".join(f"{t['route_id']}={t['minutes']}m" for t in southbound_trains) or "none"
            logger.info(f"[SIM] {self.config.DIRECTION_NORTH_LABEL}: {n_desc} | {self.config.DIRECTION_SOUTH_LABEL}: {s_desc}")

    def cleanup(self):
        """Clear the display and release hardware resources."""
        self.draw.rectangle((0, 0, self.matrix_width, self.matrix_height), fill=(0, 0, 0))
        if self.matrix is not None:
            self.offscreen_canvas.SetImage(self.image)
            self.matrix.SwapOnVSync(self.offscreen_canvas)
        logger.info("Display cleaned up")
