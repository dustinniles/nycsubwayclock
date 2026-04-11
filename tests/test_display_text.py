import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pytz
from train_times import fetch_train_times
from display import route_color_rgb, ROUTE_COLORS
from utils import hex_to_rgb
from config import Config, VALID_ROUTES


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


class TestRouteColors(unittest.TestCase):
    """Tests for route color mapping."""

    def test_all_main_routes_have_colors(self):
        """Every main service route should have a color defined."""
        main_routes = {"1", "2", "3", "4", "5", "6", "7",
                       "A", "C", "E", "B", "D", "F", "M",
                       "G", "J", "Z", "L", "N", "Q", "R", "W", "S"}
        for route in main_routes:
            self.assertIn(route, ROUTE_COLORS, f"Route {route} missing from ROUTE_COLORS")

    def test_route_colors_are_valid_hex(self):
        """All color values should be valid 7-character hex strings."""
        for route, color in ROUTE_COLORS.items():
            self.assertTrue(color.startswith("#"), f"Route {route} color must start with #")
            self.assertEqual(len(color), 7, f"Route {route} color must be 7 chars (e.g., #003986)")

    def test_route_color_rgb_returns_tuple(self):
        """route_color_rgb should return an RGB tuple for known routes."""
        rgb = route_color_rgb("A")
        self.assertIsInstance(rgb, tuple)
        self.assertEqual(len(rgb), 3)
        self.assertEqual(rgb, (0, 57, 134))  # MTA blue

    def test_route_color_rgb_fallback(self):
        """Unknown routes should fall back to MTA blue."""
        rgb = route_color_rgb("UNKNOWN")
        self.assertEqual(rgb, (0, 57, 134))

    def test_ace_lines_are_blue(self):
        """A, C, E lines should all be MTA blue."""
        for route in ("A", "C", "E"):
            self.assertEqual(ROUTE_COLORS[route], "#003986")

    def test_numbered_lines_have_correct_colors(self):
        """Numbered lines should have their official colors."""
        # Red line
        for route in ("1", "2", "3"):
            self.assertEqual(ROUTE_COLORS[route], "#EE352E")
        # Green line
        for route in ("4", "5", "6"):
            self.assertEqual(ROUTE_COLORS[route], "#00933C")


class TestHexToRgb(unittest.TestCase):
    """Tests for hex color conversion."""

    def test_hex_to_rgb(self):
        """Test hex color to RGB tuple conversion."""
        self.assertEqual(hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("#003986"), (0, 57, 134))  # MTA blue


class TestConfigValidation(unittest.TestCase):
    """Tests for configuration validation."""

    def test_valid_routes_complete(self):
        """VALID_ROUTES should contain all standard NYC subway routes."""
        expected = {"1", "2", "3", "4", "5", "6", "7",
                    "A", "C", "E", "B", "D", "F", "M",
                    "G", "J", "Z", "L", "N", "Q", "R", "W", "S"}
        self.assertTrue(expected.issubset(VALID_ROUTES))

    def test_config_has_required_attributes(self):
        """Config class should have all required attributes."""
        required = [
            "SUBWAY_ROUTE", "STOP_IDS", "MAX_MINUTES_AWAY",
            "MAX_TRAINS_PER_DIRECTION", "DIRECTION_NORTH_LABEL",
            "DIRECTION_SOUTH_LABEL", "DISPLAY_REFRESH_CYCLE",
            "MATRIX_ROWS", "MATRIX_COLS", "MATRIX_CHAIN_LENGTH",
            "MATRIX_BRIGHTNESS", "FONT_SIZE", "FONT_PATH",
            "CACHE_TTL_SECONDS", "STALE_CACHE_MAX_SECONDS",
            "SIMULATE_DISPLAY",
        ]
        for attr in required:
            self.assertTrue(hasattr(Config, attr), f"Config missing attribute: {attr}")


if __name__ == "__main__":
    unittest.main()
