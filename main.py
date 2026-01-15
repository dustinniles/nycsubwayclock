"""
NYC Subway Clock - Main application
Displays real-time subway arrival times on an LED matrix
"""
import logging
import sys
import time
import pytz
from pathlib import Path

from config import Config
from train_times import fetch_train_times
from display import DisplayManager

# Configure logging
def setup_logging():
    """Configure logging with both file and console output."""
    log_file = Path(Config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


logger = logging.getLogger(__name__)


def cycle_display(display_manager, train_times_data):
    """
    Cycle through train arrivals on the display.

    Args:
        display_manager: DisplayManager instance
        train_times_data: List of train arrival tuples [(text, minutes), ...]

    This function displays the closest arrival and cycles through the next 2-3 arrivals.
    """
    if not train_times_data:
        no_trains = ("No trains available", 0)
        display_manager.update_display(no_trains, ("", 0), Config.SECONDARY_INDEX_BASE)
        return

    # Closest arrival stays on line 1
    closest_arrival = train_times_data[0]

    # Next arrivals to cycle through on line 2
    next_arrivals = train_times_data[1 : Config.MAX_TRAINS_DISPLAY]

    if not next_arrivals:
        # Only one train available
        display_manager.update_display(closest_arrival, ("", 0), Config.SECONDARY_INDEX_BASE)
        return

    # Display the first next arrival initially
    secondary_index = 0
    next_arrival = next_arrivals[secondary_index]
    line_number = secondary_index + Config.SECONDARY_INDEX_BASE
    display_manager.update_display(closest_arrival, next_arrival, line_number)
    time.sleep(Config.DISPLAY_REFRESH_INITIAL)

    # Cycle through remaining arrivals
    while True:
        secondary_index = (secondary_index + 1) % len(next_arrivals)
        next_arrival = next_arrivals[secondary_index]
        line_number = secondary_index + Config.SECONDARY_INDEX_BASE

        display_manager.update_display(closest_arrival, next_arrival, line_number)
        time.sleep(Config.DISPLAY_REFRESH_CYCLE)

        # If we've cycled back to the start, break to fetch fresh data
        if secondary_index == 0:
            break


def main():
    """Main application loop."""
    # Setup logging first
    setup_logging()
    logger.info("=" * 60)
    logger.info("NYC Subway Clock Starting")
    logger.info("=" * 60)

    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Log configuration
    logger.info(f"Subway Route: {Config.SUBWAY_ROUTE}")
    logger.info(f"Stop IDs: {Config.STOP_IDS}")
    logger.info(f"Timezone: {Config.TIMEZONE}")
    logger.info(f"Display: {Config.MATRIX_COLS * Config.MATRIX_CHAIN_LENGTH}x{Config.MATRIX_ROWS}")

    # Set up timezone (convert once, use everywhere)
    try:
        nyc_tz = pytz.timezone(Config.TIMEZONE)
        logger.info(f"Timezone '{Config.TIMEZONE}' loaded successfully")
    except pytz.UnknownTimeZoneError:
        logger.error(f"Invalid timezone: {Config.TIMEZONE}")
        sys.exit(1)

    # Read GTFS static files once at startup
    try:
        logger.info(f"Reading GTFS files...")
        with open(Config.TRIPS_FILE, "r") as f:
            trips_content = f.read()
            logger.info(f"Loaded {len(trips_content)} bytes from trips.txt")

        with open(Config.STOPS_FILE, "r") as f:
            stops_content = f.read()
            logger.info(f"Loaded {len(stops_content)} bytes from stops.txt")
    except FileNotFoundError as e:
        logger.error(f"GTFS file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading GTFS files: {e}")
        sys.exit(1)

    # Initialize display manager
    try:
        logger.info("Initializing display manager...")
        display_manager = DisplayManager()
        logger.info("Display manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize display: {e}")
        sys.exit(1)

    # Main loop - fetch train data and display it
    logger.info("Entering main loop")
    while True:
        try:
            # Fetch fresh train times
            logger.debug("Fetching train times...")
            train_times_data = fetch_train_times(trips_content, stops_content, nyc_tz)

            if train_times_data:
                logger.info(f"Fetched {len(train_times_data)} train arrivals")
            else:
                logger.warning("No train data available")

            # Display and cycle through arrivals
            cycle_display(display_manager, train_times_data)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            # Wait a bit before retrying to avoid tight error loops
            time.sleep(10)

    logger.info("NYC Subway Clock shutdown complete")


if __name__ == "__main__":
    main()
