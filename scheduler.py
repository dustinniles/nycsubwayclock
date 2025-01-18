import logging
import os
import sys
import time
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Import the LED matrix library
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Debugging statement to print the Python path
print("Python Path:", sys.path)

# Load environment variables from .env file
load_dotenv()

# Load environment variables
latitude = float(os.getenv("LATITUDE", "40.682387"))
longitude = float(os.getenv("LONGITUDE", "-73.963004"))
nyc_tz = pytz.timezone("America/New_York")

print(f"LATITUDE: {latitude}, LONGITUDE: {longitude}, NYC_TZ: {nyc_tz}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize the LED matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 32
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'
matrix = RGBMatrix(options=options)

def update_display(closest_arrival, next_arrival, line_number):
    # Add debugging statements
    logger.info(f"Updating display with closest arrival: {closest_arrival}, next arrival: {next_arrival}, line number: {line_number}")
    # Your code to update the LED matrix display
    try:
        matrix.Clear()
        # Example of displaying text
        matrix.SetText(0, 0, f"Closest: {closest_arrival}")
        matrix.SetText(0, 10, f"Next: {next_arrival}")
        matrix.SetText(0, 20, f"Line: {line_number}")
    except Exception as e:
        logger.error(f"Error updating display: {str(e)}")

def main():
    while True:
        logger.info("Checking sunrise and sunset times...")

        try:
            # Example request
            logger.info(f"Requesting sunrise and sunset times from: https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&formatted=0")
            # Simulate fetching sunrise and sunset times
            sunrise_time = "07:14:23"
            sunset_time = "16:58:24"

            logger.info(f"Sunrise (local time): {sunrise_time}")
            logger.info(f"Sunset (local time): {sunset_time}")

            current_time = datetime.now(nyc_tz)
            logger.info(f"Current time: {current_time}")

            # Example display update
            update_display("07:20 AM", "07:30 AM", 1)

            # Add a delay to prevent the script from exiting immediately
            time.sleep(300)  # Sleep for 5 minutes

        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            time.sleep(10)  # Sleep for 10 seconds before retrying

if __name__ == "__main__":
    main()
