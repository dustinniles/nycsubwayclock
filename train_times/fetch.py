import io
import logging
from nyct_gtfs import NYCTFeed
from datetime import datetime
from pytz import timezone as pytz_timezone
import multiprocessing
from utils.helpers import get_current_time, map_route_id

logger = logging.getLogger(__name__)

def fetch_train_times(trips_content, stops_content, nyc_tz_str):
    """
    Fetches train arrival times from the NYC subway GTFS feed.
    """
    try:
        nyc_tz = pytz_timezone(nyc_tz_str)  # Convert the timezone string to a pytz timezone object
        trips_stream = io.StringIO(trips_content)
        stops_stream = io.StringIO(stops_content)
        logger.info("Initializing NYCTFeed")
        feed = NYCTFeed("C", "C", trips_txt=trips_stream, stops_txt=stops_stream)
        logger.info("NYCTFeed initialized successfully")

        logger.info("Filtering trips")
        trains = feed.filter_trips(headed_for_stop_id=["A44N", "A44S"])
        logger.info(f"Number of trains found: {len(trains)}")

        data = []
        for train in trains:
            stop_updates = [(stop_update.stop_id, stop_update.arrival) for stop_update in train.stop_time_updates if stop_update.stop_id in ["A44N", "A44S"]]
            data.append(((train.route_id, train.headsign_text, stop_updates), get_current_time(nyc_tz_str), nyc_tz))

        # Use more processes to ensure better load distribution
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            results = pool.map(process_stop_update, data)

        # Flatten the list of results
        train_times = [time for sublist in results for time in sublist]
        logger.info(f"Filtered train times: {train_times}")

        return sorted(train_times, key=lambda x: x[1])
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return []

def process_stop_update(args):
    train_info, current_time_nyc, nyc_tz = args
    train_times = []
    
    route_id, headsign_text, stop_updates = train_info
    for stop_update in stop_updates:
        stop_id, arrival_time = stop_update
        logger.debug(f"Original arrival time: {arrival_time}")

        # Ensure arrival_time is timezone-aware
        if arrival_time.tzinfo is None or arrival_time.tzinfo.utcoffset(arrival_time) is None:
            arrival_time = nyc_tz.localize(arrival_time)

        minutes_away = (arrival_time - current_time_nyc).total_seconds() // 60
        logger.debug(f"Arrival time: {arrival_time}, Minutes away: {minutes_away}")
        if minutes_away >= 0:
            headsign = "".join(
                c for c in headsign_text.strip().replace('"', "")
                if c.isalnum() or c.isspace()
            )
            if minutes_away <= 30:
                train_times.append(
                    (
                        f"{map_route_id(route_id)} {headsign} {int(minutes_away)}m",
                        minutes_away,
                    )
                )
                logger.debug(f"Added train time: {train_times[-1]}")
            else:
                logger.debug(f"Train {route_id} is more than 30 minutes away.")
        else:
            logger.debug(f"Train {route_id} has a negative minutes away value.")
    return train_times
