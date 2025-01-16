import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, time as dtime
from scheduler import get_sun_times, is_time_between


class TestScheduler(unittest.TestCase):
    @patch("scheduler.requests.get")
    def test_get_sun_times(self, mock_get):
        # Mock the requests.get method
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": {
                "sunrise": "2025-01-16T12:00:00+00:00",
                "sunset": "2025-01-16T22:00:00+00:00",
            }
        }
        mock_get.return_value = mock_response

        sunrise, sunset = get_sun_times(40.682387, -73.963004)
        self.assertEqual(sunrise, dtime(7, 0))  # Local time conversion
        self.assertEqual(sunset, dtime(17, 0))  # Local time conversion

    def test_is_time_between(self):
        start_time = dtime(6, 0)
        end_time = dtime(22, 0)
        current_time = datetime.now(timezone("America/New_York")).time()
        self.assertTrue(is_time_between(start_time, end_time))


if __name__ == "__main__":
    unittest.main()
