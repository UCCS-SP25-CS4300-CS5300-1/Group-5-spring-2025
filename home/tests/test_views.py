from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from home.models import Facility, UserProfile, TripDetails
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User  
from datetime import date


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
        mock_return_facility_address.return_value = [{
            "City": "Denver",
            "AddressStateCode": "CO",
            "FacilityStreetAddress1": "123 Main St"
        }]
        url = reverse('facility_detail', kwargs={'facility_id': facility_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'facility_detail.html')
        self.assertEqual(response.context.get('campsite'), {'f_id': facility_id, 'name': 'Camp A'})
        self.assertEqual(response.context.get('city'), "Denver")
        self.assertEqual(response.context.get('state'), "CO")
        self.assertEqual(response.context.get('address'), "123 Main St")
        mock_return_facility_detail.assert_called_once_with(facility_id)
        mock_return_facility_address.assert_called_once_with(facility_id)

    @patch('home.views.return_facility_detail')
    @patch('home.views.return_facility_address')
    def test_facility_detail_view_without_addresses(self, mock_return_facility_address, mock_return_facility_detail):
        facility_id = "456"
        mock_return_facility_detail.return_value = {'f_id': facility_id, 'name': 'Camp B'}
        mock_return_facility_address.return_value = []
        url = reverse('facility_detail', kwargs={'facility_id': facility_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'facility_detail.html')
        self.assertEqual(response.context.get('campsite'), {'f_id': facility_id, 'name': 'Camp B'})
        self.assertEqual(response.context.get('city'), "N/A")
        self.assertEqual(response.context.get('state'), "N/A")
        self.assertEqual(response.context.get('address'), "N/A")

    def test_save_facility_view(self):
        # Log in the test user.
        self.client.login(username=self.test_username, password=self.test_password)
        facility_id = "789"
        # Simulate GET parameters from the facility_detail template.
        get_params = {
            "name": "Camp Save",
            "location": "Denver",
            "type": "Campground",
            "a_txt": "Accessible",
            "ada": "Yes",
            "phone": "1234567890",
            "email": "camp@example.com",
            "description": "A nice camp."
        }
        url = reverse('save_facility', kwargs={'facility_id': facility_id})
        response = self.client.get(url, data=get_params)
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
        self.assertIn('available_loc', response.context)
        self.assertEqual(response.context.get('available_loc'), [{'name': 'Camp A'}])
        mock_search_facilities.assert_called_once_with('denver')

    def test_user_profile_view_post_add_favorite(self):
        self.client.login(username=self.test_username, password=self.test_password)
        # Create a facility in the DB so it exists.
        facility = Facility.objects.create(
            f_id="999",
            name="Favorite Camp",
            location="Denver",
            type="Campground",
            accessibility_txt="Accessible",
            ada_accessibility="Yes",
            phone="1234567890",
            email="fav@example.com",
            description="A favorite camp."
        )
        profile = UserProfile.objects.get(user=self.user)
        self.assertNotIn(facility, profile.favorited_loc.all())
        url = reverse('user_profile')
        # Simulate POST with favorite_loc list.
        response = self.client.post(url, data={'favorite_loc': ["999"]})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile'))
        profile.refresh_from_db()
        self.assertIn(facility, profile.favorited_loc.all())

    def test_logoutUser_view(self):
        self.client.login(username=self.test_username, password=self.test_password)
        url = reverse('logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))
        # After logging out, accessing a login_required view should not return 200.
        response2 = self.client.get(reverse('user_profile'))
        self.assertNotEqual(response2.status_code, 200)





class TripViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        CampUser = get_user_model()
        self.user = CampUser.objects.create_user(username='testuser', password='testpass')
        self.user_profile = self.user.userprofile
        self.facility = Facility.objects.create(
            name='Camp Alpha',
            location='Hills',
            f_id='ALPHA1',
            type='Park',
            description='Testing facility',
        )
        self.client.login(username='testuser', password='testpass')


    @patch('home.views.openai.ChatCompletion.create')
    def test_create_trip_async_success(self, mock_openai):
        # Properly mock OpenAI API response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Tent, Sleeping Bag, Flashlight"
        mock_response.choices = [mock_choice]
        mock_openai.return_value = mock_response

        url = reverse('create_trip_async', kwargs={'facility_id': self.facility.id})
        response = self.client.post(url, {
            'start_date': '2025-06-01',
            'end_date': '2025-06-03',
            'number_of_people': 2,
        })

        # Redirects to preview page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('trip_preview'))

        # Trip should exist
        trip = TripDetails.objects.latest('id')
        self.assertEqual(trip.user, self.user_profile)
        self.assertEqual(trip.number_of_people, 2)
        self.assertIn('Tent', trip.packing_list)

        # Session should hold preview ID
        session = self.client.session
        self.assertEqual(session['trip_preview_id'], trip.id)


    def test_create_trip_async_invalid_method(self,):
        url = reverse('create_trip_async', kwargs={'facility_id': self.facility.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'Invalid request'})

    def test_trip_preview_view(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            facility=self.facility,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
            number_of_people=2,
            packing_list='Tent, Flashlight'
        )
        session = self.client.session
        session['trip_preview_id'] = trip.id
        session.save()

        response = self.client.get(reverse('trip_preview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tent')

    def test_confirm_trip_clears_session(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            facility=self.facility,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
        )
        session = self.client.session
        session['trip_preview_id'] = trip.id
        session.save()

        response = self.client.get(reverse('confirm_trip'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile'))

        self.assertNotIn('trip_preview_id', self.client.session)

    def test_cancel_trip_deletes_and_redirects(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            facility=self.facility,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
        )
        session = self.client.session
        session['trip_preview_id'] = trip.id
        session.save()

        response = self.client.get(reverse('cancel_trip'))
        self.assertRedirects(response, reverse('user_profile'))
        self.assertFalse(TripDetails.objects.filter(id=trip.id).exists())
        self.assertNotIn('trip_preview_id', self.client.session)

    def test_trip_detail_view(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            facility=self.facility,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
            packing_list="Tent, Flashlight"
        )
        response = self.client.get(reverse('trip_detail', kwargs={'trip_id': trip.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.facility.name)
        self.assertContains(response, "Tent")
