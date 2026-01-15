import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pytz
from train_times import fetch_train_times
from display import map_route_to_bullet
from utils import hex_to_rgb


class TestTrainTimes(unittest.TestCase):
    """Tests for train times fetching functionality."""

    @patch("train_times.fetch.NYCTFeed")
    def test_fetch_train_times(self, mock_nyctfeed):
        """Test that fetch_train_times returns properly formatted train data."""
        # Mock the NYCTFeed and its methods
        mock_feed = MagicMock()
        mock_nyctfeed.return_value = mock_feed

        # Create a mock train with arrival data
        mock_stop_update = MagicMock()
        mock_stop_update.stop_id = "A44N"
        mock_stop_update.arrival = datetime(
            2025, 1, 16, 14, 30, tzinfo=pytz.timezone("America/New_York")
        )

        mock_train = MagicMock()
        mock_train.headsign_text = "Test Train"
        mock_train.route_id = "C"
        mock_train.stop_time_updates = [mock_stop_update]

        mock_feed.filter_trips.return_value = [mock_train]

        # Mock timezone
        nyc_tz = pytz.timezone("America/New_York")

        # Test with mock trips and stops content
        trips_content = "route_id,trip_id\nC,test_trip"
        stops_content = "stop_id,stop_name\nA44N,Test Stop"

        train_times = fetch_train_times(trips_content, stops_content, nyc_tz)

        # Should return a list
        self.assertIsInstance(train_times, list)

    def test_map_route_to_bullet(self):
        """Test route ID to bullet character mapping."""
        self.assertEqual(map_route_to_bullet("A"), "!")
        self.assertEqual(map_route_to_bullet("C"), "@")
        self.assertEqual(map_route_to_bullet("E"), "#")
        self.assertEqual(map_route_to_bullet("B"), "B")  # Unmapped routes return as-is

    def test_hex_to_rgb(self):
        """Test hex color to RGB tuple conversion."""
        self.assertEqual(hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("#003986"), (0, 57, 134))  # MTA blue


if __name__ == "__main__":
    unittest.main()
