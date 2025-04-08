from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from home.models import Facility, UserProfile
from unittest.mock import patch, MagicMock

class ViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_model = get_user_model()
        self.test_username = 'testuser'
        self.test_password = 'testpass123'
        self.user = self.user_model.objects.create_user(username=self.test_username, password=self.test_password)
        # Ensure a UserProfile exists for the user.
        UserProfile.objects.get_or_create(user=self.user)

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    @patch('home.views.search_facilities')
    def test_search_view_no_query(self, mock_search_facilities):
        # No query provided, so search_facilities should not be called.
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_results.html')
        self.assertEqual(response.context.get('campsites'), [])
        self.assertIsNone(response.context.get('query'))
        mock_search_facilities.assert_not_called()


    @patch('home.views.return_facility_detail')
    @patch('home.views.return_facility_address')
    def test_facility_detail_view_with_addresses(self, mock_return_facility_address, mock_return_facility_detail):
        facility_id = "123"
        # Simulate valid responses from the external functions.
        mock_return_facility_detail.return_value = {'f_id': facility_id, 'name': 'Camp A'}
        mock_return_facility_address.return_value = "123 test, Denver, Colorado"
        url = reverse('facility_detail', kwargs={'facility_id': facility_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'facility_detail.html')
        self.assertEqual(response.context.get('campsite'), {'f_id': facility_id, 'name': 'Camp A'})
        self.assertEqual(response.context.get('facility_address'), "123 test, Denver, Colorado")
        mock_return_facility_detail.assert_called_once_with(facility_id)
        mock_return_facility_address.assert_called_once_with(facility_id)

    @patch('home.views.return_facility_detail')
    @patch('home.views.return_facility_address')
    def test_facility_detail_view_without_addresses(self, mock_return_facility_address, mock_return_facility_detail):
        facility_id = "456"
        mock_return_facility_detail.return_value = {'f_id': facility_id, 'name': 'Camp B'}
        mock_return_facility_address.return_value = ""
        url = reverse('facility_detail', kwargs={'facility_id': facility_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'facility_detail.html')
        self.assertEqual(response.context.get('campsite'), {'f_id': facility_id, 'name': 'Camp B'})
        self.assertEqual(response.context.get('facility_address'), "")

    @patch('home.views.return_facility_detail')
    @patch('home.views.return_facility_address')
    @patch('home.views.return_facility_url')
    def test_save_facility_view(self, mock_return_facility_address, mock_return_facility_url, mock_return_facility_detail):
        # Log in the test user.
        self.client.login(username=self.test_username, password=self.test_password)
        # Simulate mock API call
        facility_id = "123"

        # Mock the return_facility_detail response to match what the view expects
        mock_return_facility_detail.return_value = {
            "FacilityName": "Camp Save",
            "FacilityTypeDescription": "Campground",
            "FacilityAccessibilityText": "Accessible",
            "FacilityAdaAccess": "Y",
            "FacilityPhone": "123 456-78910",
            "FacilityEmail": "email@test.com",
            "FacilityDescription": "Description here",
            "Reservable": True
        }
        mock_return_facility_address.return_value = "123 test, Denver, CO"
        mock_return_facility_url.return_value = "www.url.com"


        url = reverse('save_facility', kwargs={'facility_id': facility_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile'))
        # Verify that the facility was created and added to the user's profile.
        facility = Facility.objects.get(f_id=facility_id)
        self.assertEqual(facility.name, "Camp Save")
        profile = UserProfile.objects.get(user=self.user)
        self.assertIn(facility, profile.favorited_loc.all())

    def test_register_view_get(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")
        self.assertIn("form", response.context)

    def test_register_view_post_valid(self):
        url = reverse('register')
        data = {
            "username": "newuser",
            "password1": "newpassword123",
            "password2": "newpassword123"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/")
        # Check that the new user is created.
        new_user = self.user_model.objects.get(username="newuser")
        self.assertIsNotNone(new_user)

    @patch('home.views.search_facilities')
    def test_user_profile_view_get(self, mock_search_facilities):
        self.client.login(username=self.test_username, password=self.test_password)
        mock_search_facilities.return_value = [{'name': 'Camp A'}]
        url = reverse('user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")
        # Check that context contains the expected keys.
        self.assertIn('user_profile', response.context)
        self.assertIn('favorite_loc', response.context)


    def test_logoutUser_view(self):
        self.client.login(username=self.test_username, password=self.test_password)
        url = reverse('logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))
        # After logging out, accessing a login_required view should not return 200.
        response2 = self.client.get(reverse('user_profile'))
        self.assertNotEqual(response2.status_code, 200)
