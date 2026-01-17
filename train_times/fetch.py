import io
import logging
import time
from nyct_gtfs import NYCTFeed
from datetime import datetime
from utils.helpers import get_current_time, map_route_to_name
from config import Config

logger = logging.getLogger(__name__)


def fetch_train_times(trips_content, stops_content, nyc_tz, config=None, max_retries=3):
    """
    Fetches train arrival times from the NYC subway GTFS feed.

    Args:
        trips_content: String content of trips.txt file
        stops_content: String content of stops.txt file
        nyc_tz: pytz timezone object (not string)
        config: Config object (defaults to global Config if not provided)
        max_retries: Maximum number of retry attempts on failure

    Returns:
        List of dicts: [{'route_id': str, 'headsign': str, 'minutes': int, 'stop_id': str}, ...]
        Returns empty list on failure after retries.
    """
    cfg = config or Config

    for attempt in range(max_retries):
        try:
            trips_stream = io.StringIO(trips_content)
            stops_stream = io.StringIO(stops_content)

            logger.info(f"Initializing NYCTFeed for route {cfg.SUBWAY_ROUTE}")
            feed = NYCTFeed(
                cfg.SUBWAY_ROUTE,
                cfg.SUBWAY_ROUTE,
                trips_txt=trips_stream,
                stops_txt=stops_stream,
            )
            logger.info("NYCTFeed initialized successfully")

            logger.info(f"Filtering trips for stops: {cfg.STOP_IDS}")
            trains = feed.filter_trips(headed_for_stop_id=cfg.STOP_IDS)
            logger.info(f"Number of trains found: {len(trains)}")

            # Get current time
            current_time_nyc = datetime.now(nyc_tz)

            # Process each train - NO MULTIPROCESSING NEEDED
            # Processing 5-10 trains is trivial and doesn't need separate processes
            train_times = []
            for train in trains:
                stop_updates = [
                    (stop_update.stop_id, stop_update.arrival)
                    for stop_update in train.stop_time_updates
                    if stop_update.stop_id in cfg.STOP_IDS
                ]

                # Process stop updates for this train
                for stop_id, arrival_time in stop_updates:
                    logger.debug(f"Original arrival time: {arrival_time}")

                    # Ensure arrival_time is timezone-aware
                    if (
                        arrival_time.tzinfo is None
                        or arrival_time.tzinfo.utcoffset(arrival_time) is None
                    ):
                        arrival_time = nyc_tz.localize(arrival_time)

                    minutes_away = (arrival_time - current_time_nyc).total_seconds() // 60
                    logger.debug(f"Arrival time: {arrival_time}, Minutes away: {minutes_away}")

                    # Only include trains that are at least 1 minute away (0m trains can't be caught)
                    if minutes_away >= 1:
                        # Clean up headsign text
                        headsign = "".join(
                            c
                            for c in train.headsign_text.strip().replace('"', "")
                            if c.isalnum() or c.isspace() or c == "-"
                        )

                        # Only include trains within MAX_MINUTES_AWAY
                        if minutes_away <= cfg.MAX_MINUTES_AWAY:
                            train_times.append({
                                'route_id': train.route_id,
                                'headsign': headsign,
                                'minutes': int(minutes_away),
                                'stop_id': stop_id
                            })
                            logger.debug(f"Added train time: {train_times[-1]}")
                        else:
                            logger.debug(
                                f"Train {train.route_id} is more than {cfg.MAX_MINUTES_AWAY} minutes away."
                            )
                    else:
                        logger.debug(f"Train {train.route_id} has a negative minutes away value.")

            logger.info(f"Filtered train times: {train_times}")
            return sorted(train_times, key=lambda x: x['minutes'])

        except Exception as e:
            logger.error(f"Error fetching train times (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Exponential backoff: wait 2, 4, 8 seconds
                wait_time = 2 ** (attempt + 1)
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("Max retries reached. Returning empty list.")
                return []

    return []
