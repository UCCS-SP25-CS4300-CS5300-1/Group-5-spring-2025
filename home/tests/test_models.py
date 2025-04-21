from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from home.forms import CampUserCreationForm
from home.models import *


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
            "description": "A facility located in the national park.",
        }

    def test_facility_creation(self):
        # Test that a Facility instance is created correctly and its __str__ method returns the facility's name.
        facility = Facility.objects.create(**self.facility_data)

        self.assertEqual(facility.name, self.facility_data["name"])
        self.assertEqual(str(facility), self.facility_data["name"])
        self.assertEqual(facility.location, self.facility_data["location"])
        self.assertEqual(facility.f_id, self.facility_data["f_id"])
        self.assertEqual(facility.type, self.facility_data["type"])
        self.assertEqual(
            facility.accessibility_txt, self.facility_data["accessibility_txt"]
        )
        self.assertEqual(
            facility.ada_accessibility, self.facility_data["ada_accessibility"]
        )
        self.assertEqual(facility.phone, self.facility_data["phone"])
        self.assertEqual(facility.email, self.facility_data["email"])
        self.assertEqual(facility.description, self.facility_data["description"])

    def test_f_id_unique_constraint(self):
        # Test that the f_id field is unique by attempting to create two facilities with the same f_id.
        Facility.objects.create(**self.facility_data)
        duplicate_data = self.facility_data.copy()
        duplicate_data["name"] = "Another Facility"

        with self.assertRaises(IntegrityError):
            Facility.objects.create(**duplicate_data)

    def test_email_field_validation(self):
        # Test that an invalid email format raises a ValidationError.
        invalid_data = self.facility_data.copy()
        invalid_data["email"] = "invalid-email-format"
        facility = Facility(**invalid_data)

        with self.assertRaises(ValidationError):
            facility.full_clean()

    def test_phone_field_accepts_valid_length(self):
        # Test that a valid phone string (within 15 characters) passes model validation.
        valid_data = self.facility_data.copy()
        valid_data["phone"] = "1234567890"  # 10 characters, within limit
        facility = Facility(**valid_data)

        try:
            facility.full_clean()  # Should not raise a ValidationError.
        except ValidationError:
            self.fail(
                "Facility.full_clean() raised ValidationError unexpectedly for a valid phone number."
            )


class UserTests(TestCase):
    def test_create(self):
        # Test user creation and password hashing.
        test_data = {"username": "Testuser", "password": "Password123!"}

        CampUser = get_user_model()
        user = CampUser.objects.create_user(
            username=test_data["username"], password=test_data["password"]
        )

        self.assertEqual(user.username, test_data["username"])
        self.assertTrue(user.check_password(test_data["password"]))


class RegisterTests(TestCase):
    def test_form_response(self):
        # Test that the registration page returns a 200 status and contains the form.
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")


class UserPreferencesModelTest(TestCase):
    def setUp(self):
        # create user
        self.user = CampUser.objects.create_user(
            username="testuser", password="testpassword"
        )
        # create preferences (default is all True for pref attr)
        self.preferences = UserPreferences.objects.create(user=self.user)

    def test_preferences_defaults(self):
        # test to make sure preferences are as expected when first setting up (default = all true)
        self.assertTrue(self.preferences.campground)
        self.assertTrue(self.preferences.rangerstation)
        self.assertTrue(self.preferences.hotel)
        self.assertTrue(self.preferences.trail)
        self.assertTrue(self.preferences.reservable)

    def test_update_preferences(self):
        # test to make sure update works
        self.preferences.hotel = False
        self.preferences.rangerstation = False
        self.preferences.save()

        self.assertTrue(self.preferences.campground)
        self.assertFalse(self.preferences.rangerstation)
        self.assertFalse(self.preferences.hotel)
        self.assertTrue(self.preferences.trail)
        self.assertTrue(self.preferences.reservable)


class TripDetailsModelTests(TestCase):
    def setUp(self):
        # Use custom user model
        CampUser = get_user_model()
        self.user = CampUser.objects.create_user(
            username="testuser", password="password"
        )
        self.profile = (
            self.user.userprofile
        )  # UserProfile is created automatically by signal

        # Create facility
        self.facility = Facility.objects.create(
            name="Test Campground",
            location="Forest Hill",
            f_id="TST001",
            type="Campground",
            accessibility_txt="Fully Accessible",
            ada_accessibility="Y",
            phone="1234567890",
            email="camp@test.com",
            description="A test campground for unit testing.",
        )

    def test_tripdetails_creation(self):
        """Test basic creation of a TripDetails instance"""
        trip = TripDetails.objects.create(
            user=self.profile,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
            number_of_people=2,
            packing_list="Tent, Sleeping Bag, Flashlight",
        )
        trip.facility.set([self.facility])

        self.assertEqual(trip.user, self.profile)
        self.assertIn(self.facility, trip.facility.all())
        self.assertEqual(trip.number_of_people, 2)
        self.assertEqual(trip.packing_list, "Tent, Sleeping Bag, Flashlight")

    def test_tripdetails_str(self):
        """Test string representation of TripDetails"""
        trip = TripDetails.objects.create(
            user=self.profile,
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 2),
        )

        trip.facility.set([self.facility])

        expected = f"{self.user.username}'s Trip to {self.facility.name} on {trip.start_date}"

        self.assertEqual(str(trip), expected)

    def test_default_number_of_people(self):
        """Test that number_of_people defaults to 1"""
        trip = TripDetails.objects.create(
            user=self.profile,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 3),
        )
        trip.facility.set([self.facility])

        self.assertEqual(trip.number_of_people, 1)

    def test_trip_with_null_facility(self):
        """Test TripDetails can be created without a facility (nullable)"""
        trip = TripDetails.objects.create(
            user=self.profile,
            start_date=date(2025, 9, 10),
            end_date=date(2025, 9, 15),
        )
        trip.facility.clear()
        self.assertEqual(trip.facility.count(), 0)

    def test_missing_required_fields(self):
        """Test that required fields raise errors if missing"""
        with self.assertRaises(Exception):
            TripDetails.objects.create(
                user=self.profile,
                start_date=None,  # Required field
                end_date=date(2025, 10, 1),
            )

            self.trip.facility.set([self.facility])

