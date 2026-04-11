import io
import logging
import time
from nyct_gtfs import NYCTFeed
from nyct_gtfs.feed import NYCTFeed as _NYCTFeed
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

# All unique MTA GTFS-RT feed URLs (covers every subway line)
_ALL_FEED_URLS = list(set(_NYCTFeed._train_to_url.values()))

# Simple time-based cache to avoid hitting MTA API every display cycle
_cache = {"data": [], "timestamp": 0}

# Stale cache: kept longer than _cache so we can serve old data during API outages
_stale_cache = {"data": [], "timestamp": 0}


def fetch_train_times(trips_content, stops_content, nyc_tz, config=None, max_retries=3):
    """
    Fetches train arrival times from all MTA GTFS-RT feeds for the configured stops.

    Queries every feed and filters to trains stopping at the configured stop IDs.
    This automatically captures rerouted trains (e.g., F trains on C line tracks)
    without any manual route configuration.

    Args:
        trips_content: String content of trips.txt file
        stops_content: String content of stops.txt file
        nyc_tz: pytz timezone object (not string)
        config: Config object (defaults to global Config if not provided)
        max_retries: Maximum number of retry attempts per feed on failure

    Returns:
        List of dicts: [{'route_id': str, 'headsign': str, 'minutes': int, 'stop_id': str}, ...]
        Returns stale cached data on failure if available, otherwise empty list.
    """
    cfg = config or Config
    cache_ttl = getattr(cfg, "CACHE_TTL_SECONDS", 15)
    stale_max = getattr(cfg, "STALE_CACHE_MAX_SECONDS", 300)

    # Return cached data if still fresh
    now = time.monotonic()
    if _cache["data"] and (now - _cache["timestamp"]) < cache_ttl:
        logger.debug("Using cached train data")
        return _cache["data"]

    current_time_nyc = datetime.now(nyc_tz)
    train_times = []
    seen = set()  # deduplicate by (route_id, stop_id, minutes)
    feeds_queried = 0
    feeds_failed = 0

    for url in _ALL_FEED_URLS:
        for attempt in range(max_retries):
            try:
                trips_stream = io.StringIO(trips_content)
                stops_stream = io.StringIO(stops_content)

                feed = NYCTFeed(url, trips_txt=trips_stream, stops_txt=stops_stream)
                trains = feed.filter_trips(headed_for_stop_id=cfg.STOP_IDS)
                feeds_queried += 1
                logger.debug(f"Feed {url.split('/')[-1]}: {len(trains)} trains at stop")

                for train in trains:
                    stop_updates = [
                        (stop_update.stop_id, stop_update.arrival)
                        for stop_update in train.stop_time_updates
                        if stop_update.stop_id in cfg.STOP_IDS
                    ]

                    for stop_id, arrival_time in stop_updates:
                        if (
                            arrival_time.tzinfo is None
                            or arrival_time.tzinfo.utcoffset(arrival_time) is None
                        ):
                            arrival_time = nyc_tz.localize(arrival_time)

                        minutes_away = (arrival_time - current_time_nyc).total_seconds() // 60

                        if 1 <= minutes_away <= cfg.MAX_MINUTES_AWAY:
                            key = (train.route_id, stop_id, int(minutes_away))
                            if key in seen:
                                continue
                            seen.add(key)

                            headsign = "".join(
                                c
                                for c in train.headsign_text.strip().replace('"', "")
                                if c.isalnum() or c.isspace() or c == "-"
                            )
                            train_times.append({
                                'route_id': train.route_id,
                                'headsign': headsign,
                                'minutes': int(minutes_away),
                                'stop_id': stop_id
                            })
                break  # feed succeeded, move to next URL

            except Exception as e:
                logger.error(f"Error fetching {url.split('/')[-1]} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    time.sleep(wait_time)
                else:
                    feeds_failed += 1

    result = sorted(train_times, key=lambda x: x['minutes'])
    logger.debug(f"Fetched {len(result)} arrivals across {feeds_queried} feeds ({feeds_failed} failed)")

    if result or feeds_queried > 0:
        now = time.monotonic()
        _cache["data"] = result
        _cache["timestamp"] = now
        _stale_cache["data"] = result
        _stale_cache["timestamp"] = now
        return result

    # All feeds failed — try stale cache
    if _stale_cache["data"] and (time.monotonic() - _stale_cache["timestamp"]) < stale_max:
        stale_age = time.monotonic() - _stale_cache["timestamp"]
        logger.warning(f"All feeds failed. Serving stale cache (age: {stale_age:.0f}s)")
        return _stale_cache["data"]

    logger.error("All feeds failed and no stale cache available. Returning empty list.")
    return []
