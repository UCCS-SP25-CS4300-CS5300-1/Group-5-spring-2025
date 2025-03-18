"""from django.test import TestCase, Client
from django.urls import reverse
from home.models import CampUser, Facility, UserProfile

class SaveFacilityTest(TestCase):
    def setUp(self):
        # Create a test user and associated user profile
        self.password = 'testpassword'
        self.user = CampUser.objects.create_user(
            username='testuser', password=self.password, preference='camping'
        )
        UserProfile.objects.create(user=self.user)
        self.client = Client()

    def test_save_facility_creates_and_associates_facility(self):
        # Log in the test user
        self.client.login(username='testuser', password=self.password)
        
        # Define a facility id and simulate GET parameters that would be provided
        facility_id = 'facility123'
        params = {
            'name': 'Test Facility',
            'location': '123 Main St',
            'type': 'Camping',
            'a_txt': 'Accessible',
            'ada': 'Y',
            'phone': '555-1234',
            'email': 'test@example.com',
            'description': 'A place to camp'
        }
        
        # Reverse the URL for the save_facility view using the facility_id
        url = reverse('save_facility', kwargs={'facility_id': facility_id})
        
        # Simulate the GET request (as used in facility_detail.html)
        response = self.client.get(url, params)
        
        # Check that the view redirects to the user profile page
        self.assertRedirects(response, reverse('user_profile'))
        
        # Check that the facility was created with the correct attributes
        facility = Facility.objects.get(f_id=facility_id)
        self.assertEqual(facility.name, params['name'])
        self.assertEqual(facility.location, params['location'])
        self.assertEqual(facility.type, params['type'])
        self.assertEqual(facility.accessibility_txt, params['a_txt'])
        self.assertEqual(facility.ada_accessibility, params['ada'])
        self.assertEqual(facility.phone, params['phone'])
        self.assertEqual(facility.email, params['email'])
        self.assertEqual(facility.description, params['description'])
        
        # Verify that the facility is now associated with the user's profile favorites
        profile = UserProfile.objects.get(user=self.user)
        self.assertIn(facility, profile.favorited_loc.all())
"""