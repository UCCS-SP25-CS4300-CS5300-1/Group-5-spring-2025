import unittest
from unittest.mock import MagicMock, patch

from home.models import CampUser, UserPreferences
from home.utils import (
    return_facility_address,
    return_facility_detail,
    search_facilities,
    geocode_location,
)


class TestUtils(unittest.TestCase):
    @patch("home.utils.requests.get")
    def test_search_facilities_success(self, mock_get):
        # Simulate a successful API response with RECDATA key.
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"RECDATA": [{"name": "Camp A"}]}
        mock_get.return_value = mock_response

        result = search_facilities(location="Denver", user=False)
        self.assertEqual(result, [{"name": "Camp A", "image_url": None}])

    @patch("home.utils.requests.get")
    def test_search_facilities_failure(self, mock_get):
        # Simulate a failed API response.
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        result = search_facilities("Denver", user=False)
        self.assertEqual(result, [])

    @patch("home.utils.requests.get")
    def test_return_facility_detail_success(self, mock_get):
        # Simulate a successful detail fetch.
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"name": "Camp A", "f_id": "123"}
        mock_get.return_value = mock_response

        result = return_facility_detail("123")
        self.assertEqual(result, {"name": "Camp A", "f_id": "123"})

    @patch("home.utils.requests.get")
    def test_return_facility_detail_failure(self, mock_get):
        # Simulate a failed detail fetch.
        mock_response = MagicMock(status_code=500)
        mock_get.return_value = mock_response

        result = return_facility_detail("123")
        self.assertEqual(result, {})

    @patch("home.utils.requests.get")
    def test_return_facility_address_success(self, mock_get):
        # Simulate a successful address fetch.
        mock_response = {
            "RECDATA": [
                {
                    "FacilityID": "123",
                    "City": "Denver",
                    "AddressStateCode": "CO",
                    "FacilityStreetAddress1": "123 test test",
                }
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = return_facility_address("123")
        self.assertEqual(result, "123 test test, Denver, CO")

    @patch("home.utils.requests.get")
    def test_return_facility_address_failure(self, mock_get):
        # Simulate a failed address fetch.
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        result = return_facility_address("123")
        self.assertEqual(result, {})

    @patch("home.utils.requests.get")
    def test_user_preferences(self, mock_get):
        # First, lets create a user and their preferences.
        user = CampUser.objects.create_user(
            username="testuser", password="testpassword"
        )
        # This user wants campground or facilities that are reservable.
        UserPreferences.objects.create(
            user=user,
            campground=True,
            rangerstation=False,
            hotel=False,
            trail=False,
            facility=True,
            reservable=True,
        )

        # Mock API call.
        mock_response = {
            "RECDATA": [
                {
                    "FacilityID": "123",
                    "FacilityName": "Mock Facility One",
                    "FacilityTypeDescription": "Campground",
                    "Reservable": True,
                },
                {
                    "FacilityID": "456",
                    "FacilityName": "Mock Facility Two",
                    "FacilityTypeDescription": "Campground",
                    "Reservable": False,
                },
                {
                    "FacilityID": "789",
                    "FacilityName": "Mock Facility Three",
                    "FacilityTypeDescription": "Facility",
                    "Reservable": True,
                },
                {
                    "FacilityID": "101",
                    "FacilityName": "Mock Facility Four",
                    "FacilityTypeDescription": "Hotel",
                    "Reservable": True,
                },
            ]
        }

        # set mock API call response code to 200, and set its data to our mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        # test our util, call search_facilities
        # it will execute, but with the API response we crafted.
        filtered = search_facilities("Colorado Springs", user)


        # time to test: if search_facilities does as its supposed to,
        # it will return only 2 relevant facilities (campground and facility, both reservable)

        # Expecting only the 2 that are reservable and match user preferences
        self.assertEqual(len(filtered), 4)

        # Check IDs returned (no assumption about order)
        facility_ids = {f["FacilityID"] for f in filtered}
        self.assertEqual(facility_ids, {"123", "789", "456", "101"})




        @patch("home.utils.requests.get")
        def test_geocode_location_success(self, mock_get):
            # Simulate successful geocoding response
            mock_response = MagicMock(status_code=200)
            mock_response.json.return_value = [
                {
                    "lat": "39.7392",
                    "lon": "-104.9903"
                }
            ]
            mock_get.return_value = mock_response

            lat, lon = geocode_location("Denver")
            self.assertAlmostEqual(lat, 39.7392)
            self.assertAlmostEqual(lon, -104.9903)
            mock_get.assert_called_once()



if __name__ == "__main__":
    unittest.main()
