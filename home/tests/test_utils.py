import unittest
from unittest.mock import patch, MagicMock
from home.utils import search_facilities, return_facility_detail, return_facility_address


class TestUtils(unittest.TestCase):
    @patch('home.utils.requests.get')
    def test_search_facilities_success(self, mock_get):
        # Simulate a successful API response with RECDATA key.
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"RECDATA": [{"name": "Camp A"}]}
        mock_get.return_value = mock_response

        result = search_facilities("Denver")
        self.assertEqual(result, [{"name": "Camp A"}])

    @patch('home.utils.requests.get')
    def test_search_facilities_failure(self, mock_get):
        # Simulate a failed API response.
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        result = search_facilities("Denver")
        self.assertEqual(result, [])

    @patch('home.utils.requests.get')
    def test_return_facility_detail_success(self, mock_get):
        # Simulate a successful detail fetch.
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"name": "Camp A", "f_id": "123"}
        mock_get.return_value = mock_response

        result = return_facility_detail("123")
        self.assertEqual(result, {"name": "Camp A", "f_id": "123"})

    @patch('home.utils.requests.get')
    def test_return_facility_detail_failure(self, mock_get):
        # Simulate a failed detail fetch.
        mock_response = MagicMock(status_code=500)
        mock_get.return_value = mock_response

        result = return_facility_detail("123")
        self.assertEqual(result, {})

    @patch('home.utils.requests.get')
    def test_return_facility_address_success(self, mock_get):
        # Simulate a successful address fetch.
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"RECDATA": [{"City": "Denver"}]}
        mock_get.return_value = mock_response

        result = return_facility_address("123")
        self.assertEqual(result, [{"City": "Denver"}])

    @patch('home.utils.requests.get')
    def test_return_facility_address_failure(self, mock_get):
        # Simulate a failed address fetch.
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        result = return_facility_address("123")
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
