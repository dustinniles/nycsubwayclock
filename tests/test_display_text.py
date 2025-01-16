import unittest
from unittest.mock import patch, MagicMock
from display_text import fetch_train_times, map_route_id, hex_to_rgb


class TestDisplayText(unittest.TestCase):
    @patch("display_text.NYCTFeed")
    @patch("display_text.io.StringIO")
    def test_fetch_train_times(self, mock_stringio, mock_nyctfeed):
        # Mock the NYCTFeed and its methods
        mock_feed = MagicMock()
        mock_nyctfeed.return_value = mock_feed
        mock_feed.filter_trips.return_value = [
            MagicMock(
                headsign_text="Train A",
                route_id="A",
                stop_time_updates=[
                    MagicMock(
                        stop_id="A44N",
                        arrival=datetime(
                            2025, 1, 16, 14, 30, tzinfo=timezone("America/New_York")
                        ),
                    )
                ],
            )
        ]

        train_times = fetch_train_times()
        self.assertEqual(len(train_times), 1)
        self.assertIn("Train A", train_times[0][0])

    def test_map_route_id(self):
        self.assertEqual(map_route_id("A"), "!")
        self.assertEqual(map_route_id("B"), "B")

    def test_hex_to_rgb(self):
        self.assertEqual(hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
