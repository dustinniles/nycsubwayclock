"""
Configuration management for NYC Subway Clock.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent


class Config:
    """Centralized configuration for the subway clock application."""

    # Geographic coordinates for sunrise/sunset calculations
    LATITUDE: float = float(os.getenv("LATITUDE", "40.682387"))
    LONGITUDE: float = float(os.getenv("LONGITUDE", "-73.963004"))

    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "America/New_York")

    # Subway configuration
    SUBWAY_ROUTE: str = os.getenv("SUBWAY_ROUTE", "C")
    STOP_IDS: List[str] = os.getenv("STOP_IDS", "A44N,A44S").split(",")
    MAX_TRAINS_DISPLAY: int = int(os.getenv("MAX_TRAINS_DISPLAY", "4"))
    MAX_MINUTES_AWAY: int = int(os.getenv("MAX_MINUTES_AWAY", "30"))
    MAX_TRAINS_PER_DIRECTION: int = int(os.getenv("MAX_TRAINS_PER_DIRECTION", "3"))

    # Direction labels (2-letter borough abbreviations: MN=Manhattan, BK=Brooklyn, QN=Queens, BX=Bronx, SI=Staten Island)
    DIRECTION_NORTH_LABEL: str = os.getenv("DIRECTION_NORTH_LABEL", "MN")
    DIRECTION_SOUTH_LABEL: str = os.getenv("DIRECTION_SOUTH_LABEL", "BK")

    # Display timing (in seconds)
    DISPLAY_REFRESH_INITIAL: int = int(os.getenv("DISPLAY_REFRESH_INITIAL", "3"))
    DISPLAY_REFRESH_CYCLE: int = int(os.getenv("DISPLAY_REFRESH_CYCLE", "5"))

    # Matrix hardware configuration
    MATRIX_ROWS: int = int(os.getenv("MATRIX_ROWS", "32"))
    MATRIX_COLS: int = int(os.getenv("MATRIX_COLS", "64"))
    MATRIX_CHAIN_LENGTH: int = int(os.getenv("MATRIX_CHAIN_LENGTH", "2"))
    MATRIX_GPIO_SLOWDOWN: int = int(os.getenv("MATRIX_GPIO_SLOWDOWN", "3"))
    MATRIX_PWM_LSB_NANOSECONDS: int = int(os.getenv("MATRIX_PWM_LSB_NANOSECONDS", "50"))
    MATRIX_PWM_BITS: int = int(os.getenv("MATRIX_PWM_BITS", "5"))
    MATRIX_HARDWARE_MAPPING: str = os.getenv("MATRIX_HARDWARE_MAPPING", "adafruit-hat")
    MATRIX_SHOW_REFRESH_RATE: bool = os.getenv("MATRIX_SHOW_REFRESH_RATE", "true").lower() == "true"

    # Font configuration
    FONT_PATH: str = os.getenv("FONT_PATH", str(PROJECT_ROOT / "MTA.ttf"))
    FONT_SIZE: int = int(os.getenv("FONT_SIZE", "16"))

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(PROJECT_ROOT / "logs" / "subway_clock.log"))
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB default
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # Keep 5 old logs

    # GTFS static files
    TRIPS_FILE: str = str(PROJECT_ROOT / "nyct-gtfs" / "nyct_gtfs" / "gtfs_static" / "trips.txt")
    STOPS_FILE: str = str(PROJECT_ROOT / "nyct-gtfs" / "nyct_gtfs" / "gtfs_static" / "stops.txt")

    # Display line numbering offset
    SECONDARY_INDEX_BASE: int = 2

    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        errors = []

        if not os.path.exists(cls.FONT_PATH):
            errors.append(f"Font file not found: {cls.FONT_PATH}")

        if not os.path.exists(cls.TRIPS_FILE):
            errors.append(f"Trips file not found: {cls.TRIPS_FILE}")

        if not os.path.exists(cls.STOPS_FILE):
            errors.append(f"Stops file not found: {cls.STOPS_FILE}")

        # Ensure logs directory exists
        log_dir = Path(cls.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True
