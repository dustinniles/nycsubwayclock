"""
Configuration management for NYC Subway Clock.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Valid Python logging levels
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Config:
    """Centralized configuration for the subway clock application."""

    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "America/New_York")

    # Subway configuration — configure the station stop IDs to watch.
    # All MTA GTFS-RT feeds are queried automatically, so any train
    # stopping at these stops (including rerouted trains) will appear.
    STOP_IDS: list = os.getenv("STOP_IDS", "A44N,A44S").split(",")
    MAX_MINUTES_AWAY: int = int(os.getenv("MAX_MINUTES_AWAY", "30"))
    MAX_TRAINS_PER_DIRECTION: int = int(os.getenv("MAX_TRAINS_PER_DIRECTION", "3"))

    # Direction labels (2-letter borough abbreviations: Ma=Manhattan, Bk=Brooklyn, Qn=Queens, Bx=Bronx, Si=Staten Island)
    # Note: Use lowercase for second letter as custom MTA font may not support all uppercase letters
    DIRECTION_NORTH_LABEL: str = os.getenv("DIRECTION_NORTH_LABEL", "Ma")
    DIRECTION_SOUTH_LABEL: str = os.getenv("DIRECTION_SOUTH_LABEL", "Bk")

    # Display timing (in seconds)
    DISPLAY_REFRESH_CYCLE: int = int(os.getenv("DISPLAY_REFRESH_CYCLE", "5"))

    # Cache configuration
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "15"))
    STALE_CACHE_MAX_SECONDS: int = int(os.getenv("STALE_CACHE_MAX_SECONDS", "300"))

    # Matrix hardware configuration
    MATRIX_ROWS: int = int(os.getenv("MATRIX_ROWS", "32"))
    MATRIX_COLS: int = int(os.getenv("MATRIX_COLS", "64"))
    MATRIX_CHAIN_LENGTH: int = int(os.getenv("MATRIX_CHAIN_LENGTH", "2"))
    MATRIX_GPIO_SLOWDOWN: int = int(os.getenv("MATRIX_GPIO_SLOWDOWN", "4"))  # Pi 4 requires 4
    MATRIX_PWM_LSB_NANOSECONDS: int = int(os.getenv("MATRIX_PWM_LSB_NANOSECONDS", "50"))
    MATRIX_PWM_BITS: int = int(os.getenv("MATRIX_PWM_BITS", "5"))
    MATRIX_HARDWARE_MAPPING: str = os.getenv("MATRIX_HARDWARE_MAPPING", "adafruit-hat")
    MATRIX_SHOW_REFRESH_RATE: bool = os.getenv("MATRIX_SHOW_REFRESH_RATE", "true").lower() == "true"
    MATRIX_BRIGHTNESS: int = int(os.getenv("MATRIX_BRIGHTNESS", "50"))  # 0-100, lower values reduce power draw
    MATRIX_LIMIT_REFRESH_HZ: int = int(os.getenv("MATRIX_LIMIT_REFRESH_HZ", "100"))  # Limit refresh rate to reduce CPU and improve stability
    MATRIX_DISABLE_HARDWARE_PULSING: bool = os.getenv("MATRIX_DISABLE_HARDWARE_PULSING", "false").lower() == "true"

    # Simulation mode (for development without LED hardware)
    SIMULATE_DISPLAY: bool = os.getenv("SIMULATE_DISPLAY", "false").lower() == "true"

    # Font configuration
    FONT_PATH: str = os.getenv("FONT_PATH", str(Path(__file__).parent / "MTA.ttf"))
    FONT_SIZE: int = int(os.getenv("FONT_SIZE", "16"))

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(Path(__file__).parent / "logs" / "subway_clock.log"))
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB default
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # Keep 5 old logs

    # GTFS static files (configurable for alternate installations)
    TRIPS_FILE: str = os.getenv("TRIPS_FILE", str(Path(__file__).parent / "nyct-gtfs" / "nyct_gtfs" / "gtfs_static" / "trips.txt"))
    STOPS_FILE: str = os.getenv("STOPS_FILE", str(Path(__file__).parent / "nyct-gtfs" / "nyct_gtfs" / "gtfs_static" / "stops.txt"))

    @classmethod
    def validate(cls):
        """Validate configuration settings. Raises ValueError with all errors found."""
        errors = []

        # File existence checks
        if not os.path.exists(cls.FONT_PATH):
            errors.append(f"Font file not found: {cls.FONT_PATH}")

        if not os.path.exists(cls.TRIPS_FILE):
            errors.append(f"Trips file not found: {cls.TRIPS_FILE}")

        if not os.path.exists(cls.STOPS_FILE):
            errors.append(f"Stops file not found: {cls.STOPS_FILE}")

        # Stop ID validation
        for stop_id in cls.STOP_IDS:
            stop_id = stop_id.strip()
            if not stop_id or len(stop_id) < 2:
                errors.append(f"Invalid STOP_ID: '{stop_id}'. Must be at least 2 characters.")

        # Numeric range validation
        if not (0 <= cls.MATRIX_BRIGHTNESS <= 100):
            errors.append(f"MATRIX_BRIGHTNESS must be 0-100, got {cls.MATRIX_BRIGHTNESS}")

        if not (1 <= cls.FONT_SIZE <= 64):
            errors.append(f"FONT_SIZE must be 1-64, got {cls.FONT_SIZE}")

        if not (1 <= cls.MATRIX_ROWS <= 128):
            errors.append(f"MATRIX_ROWS must be 1-128, got {cls.MATRIX_ROWS}")

        if not (1 <= cls.MATRIX_COLS <= 128):
            errors.append(f"MATRIX_COLS must be 1-128, got {cls.MATRIX_COLS}")

        if not (1 <= cls.MATRIX_CHAIN_LENGTH <= 16):
            errors.append(f"MATRIX_CHAIN_LENGTH must be 1-16, got {cls.MATRIX_CHAIN_LENGTH}")

        if cls.DISPLAY_REFRESH_CYCLE < 1:
            errors.append(f"DISPLAY_REFRESH_CYCLE must be >= 1, got {cls.DISPLAY_REFRESH_CYCLE}")

        if not (1 <= cls.MAX_MINUTES_AWAY <= 120):
            errors.append(f"MAX_MINUTES_AWAY must be 1-120, got {cls.MAX_MINUTES_AWAY}")

        if not (1 <= cls.MAX_TRAINS_PER_DIRECTION <= 10):
            errors.append(f"MAX_TRAINS_PER_DIRECTION must be 1-10, got {cls.MAX_TRAINS_PER_DIRECTION}")

        if cls.CACHE_TTL_SECONDS < 0:
            errors.append(f"CACHE_TTL_SECONDS must be >= 0, got {cls.CACHE_TTL_SECONDS}")

        if cls.STALE_CACHE_MAX_SECONDS < 0:
            errors.append(f"STALE_CACHE_MAX_SECONDS must be >= 0, got {cls.STALE_CACHE_MAX_SECONDS}")

        # Log level validation
        if cls.LOG_LEVEL.upper() not in VALID_LOG_LEVELS:
            errors.append(
                f"LOG_LEVEL '{cls.LOG_LEVEL}' is not valid. "
                f"Valid levels: {', '.join(sorted(VALID_LOG_LEVELS))}"
            )

        # Ensure logs directory exists
        log_dir = Path(cls.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True
