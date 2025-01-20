import logging
import os
import time
import sys
import pytz

print("Python Path:", sys.path)

latitude = float(os.getenv("LATITUDE", "40.682387"))
longitude = float(os.getenv("LONGITUDE", "-73.963004"))
nyc_tz = "America/New_York"

print(f"LATITUDE: {latitude}, LONGITUDE: {longitude}, NYC_TZ: {nyc_tz}")

try:
    tz = pytz.timezone(nyc_tz)
    print(f"Timezone '{nyc_tz}' is valid.")
except pytz.UnknownTimeZoneError:
    print(f"Timezone '{nyc_tz}' is not valid.")
    sys.exit(1)

from train_times.fetch import fetch_train_times
from display.update import update_display
from utils.helpers import get_current_time

logger = logging.getLogger(__name__)

def main():
    trips_path = "nyct-gtfs/nyct_gtfs/gtfs_static/trips.txt"
    stops_path = "nyct-gtfs/nyct_gtfs/gtfs_static/stops.txt"

    try:
        with open(trips_path, "r") as f:
            trips_content = f.read()
            logger.info("Trips file read successfully.")
    except PermissionError as e:
        logger.error(f"PermissionError: {e}")
        return

    try:
        with open(stops_path, "r") as f:
            stops_content = f.read()
            logger.info("Stops file read successfully.")
    except PermissionError as e:
        logger.error(f"PermissionError: {e}")
        return

    while True:
        current_time_nyc = get_current_time(nyc_tz)
        train_times_data = fetch_train_times(trips_content, stops_content, nyc_tz)

        if train_times_data:
            closest_arrival = (
                train_times_data[0] if len(train_times_data) > 0 else ("No trains available", 0)
            )
            next_arrivals = train_times_data[1:4] if len(train_times_data) > 1 else []
        else:
            closest_arrival = ("No trains available", 0)
            next_arrivals = []

        secondary_index = 0

        if next_arrivals:
            next_arrival = next_arrivals[secondary_index]
            line_number = secondary_index + 2
        else:
            next_arrival = ("No trains available", 0)
            line_number = 2

        update_display(closest_arrival, next_arrival, line_number)
        time.sleep(3)

        while True:
            if secondary_index == 0:
                current_time_nyc = get_current_time(nyc_tz)
                train_times_data = fetch_train_times(trips_content, stops_content, nyc_tz)
                if train_times_data:
                    closest_arrival = (
                        train_times_data[0] if len(train_times_data) > 0 else ("No trains available", 0)
                    )
                    next_arrivals = train_times_data[1:4] if len(train_times_data) > 1 else []
                else:
                    closest_arrival = ("No trains available", 0)
                    next_arrivals = []

            if next_arrivals:
                next_arrival = next_arrivals[secondary_index]
                line_number = secondary_index + 2
            else:
                next_arrival = ("No trains available", 0)
                line_number = 2

            if next_arrivals:
                secondary_index = (secondary_index + 1) % len(next_arrivals)
            else:
                secondary_index = 0

            update_display(closest_arrival, next_arrival, line_number)
            time.sleep(5)

if __name__ == "__main__":
    main()
