from unittest.mock import patch

from django.test import TestCase

from home.utils import check_hazards, fetch_weather


class WeatherUtilsTests(TestCase):

    @patch("home.utils.requests.get")
    def test_fetch_weather_returns_forecast(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "daily": {
                "time": ["2025-04-21", "2025-04-22"],
                "temperature_2m_max": [20.0, 22.0],
                "temperature_2m_min": [10.0, 11.0],
                "weathercode": [0, 95],  # 0 = Clear, 95 = Thunderstorm
            }
        }

        forecast = fetch_weather(39.74, -104.99, "2025-04-21", "2025-04-22")

        self.assertEqual(len(forecast), 2)
        self.assertEqual(forecast[0]["condition"], "Clear sky")
        self.assertEqual(forecast[1]["condition"], "Thunderstorm")
        self.assertTrue(any("Thunderstorm" in day["condition"] for day in forecast))

    def test_check_hazards_detects_known_conditions(self):
        sample_forecast = [
            {"date": "2025-04-21", "condition": "Clear sky"},
            {"date": "2025-04-22", "condition": "Thunderstorm"},
            {"date": "2025-04-23", "condition": "Heavy snowfall"},
        ]
        hazards = check_hazards(sample_forecast)
        self.assertEqual(len(hazards), 2)
        self.assertIn("Thunderstorm", [h["condition"] for h in hazards])
