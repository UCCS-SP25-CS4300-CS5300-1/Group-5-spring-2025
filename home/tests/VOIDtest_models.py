from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.auth import get_user_model
from home.models import Facility, TripDetails, UserProfile
from home.forms import CampUserCreationForm
from django.contrib.auth.models import User  # make sure this is imported




class FacilityModelTest(TestCase):
    def setUp(self):
        self.facility_data = {
            "name": "National Park Facility",
            "location": "123 Park Lane",
            "f_id": "NP123",
            "type": "Park",
            "accessibility_txt": "Fully Accessible",
            "ada_accessibility": "Y",
            "phone": "5551234567",
            "email": "info@example.com",
            "description": "A facility located in the national park."
        }

    def test_facility_creation(self):
        #Test that a Facility instance is created correctly and its __str__ method returns the facility's name.
        facility = Facility.objects.create(**self.facility_data)
        
        self.assertEqual(facility.name, self.facility_data["name"])
        self.assertEqual(str(facility), self.facility_data["name"])
        self.assertEqual(facility.location, self.facility_data["location"])
        self.assertEqual(facility.f_id, self.facility_data["f_id"])
        self.assertEqual(facility.type, self.facility_data["type"])
        self.assertEqual(facility.accessibility_txt, self.facility_data["accessibility_txt"])
        self.assertEqual(facility.ada_accessibility, self.facility_data["ada_accessibility"])
        self.assertEqual(facility.phone, self.facility_data["phone"])
        self.assertEqual(facility.email, self.facility_data["email"])
        self.assertEqual(facility.description, self.facility_data["description"])

    def test_f_id_unique_constraint(self):
        #Test that the f_id field is unique by attempting to create two facilities with the same f_id.
        Facility.objects.create(**self.facility_data)
        duplicate_data = self.facility_data.copy()
        duplicate_data["name"] = "Another Facility"
        
        with self.assertRaises(IntegrityError):
            Facility.objects.create(**duplicate_data)

    def test_email_field_validation(self):
        #Test that an invalid email format raises a ValidationError.
        invalid_data = self.facility_data.copy()
        invalid_data["email"] = "invalid-email-format"
        facility = Facility(**invalid_data)
        
        with self.assertRaises(ValidationError):
            facility.full_clean()

    def test_phone_field_accepts_valid_length(self):
        #Test that a valid phone string (within 15 characters) passes model validation.
        valid_data = self.facility_data.copy()
        valid_data["phone"] = "1234567890"  # 10 characters, within limit
        facility = Facility(**valid_data)
        
        try:
            facility.full_clean()  # Should not raise a ValidationError.
        except ValidationError:
            self.fail("Facility.full_clean() raised ValidationError unexpectedly for a valid phone number.")


class UserTests(TestCase):
    def test_create(self):
        #Test user creation and password hashing.
        test_data = {
            'username': 'Testuser',
            'password': 'Password123!'
        }
        
        CampUser = get_user_model()
        user = CampUser.objects.create_user(
            username=test_data['username'],
            password=test_data['password']
        )
        
        self.assertEqual(user.username, test_data['username'])
        self.assertTrue(user.check_password(test_data['password']))


class RegisterTests(TestCase):
    def test_form_response(self):
        #Test that the registration page returns a 200 status and contains the form.
        response = self.client.get(reverse('register'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')


class TripDetailsModelTest(TestCase):
    def setUp(self):
        # Create a User and related UserProfile
        self.user = User.objects.create_user(username='testuser', password='password')
        self.user_profile = UserProfile.objects.create(user=self.user)

        # Create a Facility
        self.facility = Facility.objects.create(
            f_id='123ABC',
            name='Test Campground',
            location='Mountains'
        )

    def test_create_trip_details(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            facility=self.facility,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 5),
            number_of_people=4,
            packing_list='Tent, Sleeping Bag, Water Bottle'
        )

        self.assertEqual(trip.user, self.user_profile)
        self.assertEqual(trip.facility, self.facility)
        self.assertEqual(trip.number_of_people, 4)
        self.assertEqual(trip.packing_list, 'Tent, Sleeping Bag, Water Bottle')

    def test_default_number_of_people(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            facility=self.facility,
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 3),
        )
        self.assertEqual(trip.number_of_people, 1)

    def test_str_representation(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            facility=self.facility,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 2),
        )
        expected_str = f"{self.user.username}'s Trip to {self.facility.name} on {trip.start_date}"
        self.assertEqual(str(trip), expected_str)
