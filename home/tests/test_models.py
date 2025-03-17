from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Facility, User

from django.urls import reverse
from django.http import HttpResponse
from .forms import CampUserCreationForm
from django.contrib.auth import get_user_model

class FacilityModelTest(TestCase):
    def setUp(self):
        self.facility_data = {
            "name": "National Park Facility",
            "location": "123 Park Lane",
            "f_id": "NP123",
            "type": "Park",
            "accessibility_txt": "Fully Accessible",
            "ada_accessibility": True,
            "reservation_url": "http://example.com/reserve",
            "phone": "5551234567",
            "email": "info@example.com",
            "description": "A facility located in the national park."
        }

    def test_facility_creation(self):
        #Test that a Facility instance is created correctly and its __str__ method
        #returns the facility's name.
        
        facility = Facility.objects.create(**self.facility_data)
        self.assertEqual(facility.name, self.facility_data["name"])
        self.assertEqual(str(facility), self.facility_data["name"])
        self.assertEqual(facility.location, self.facility_data["location"])
        self.assertEqual(facility.f_id, self.facility_data["f_id"])
        self.assertEqual(facility.type, self.facility_data["type"])
        self.assertEqual(facility.accessibility_txt, self.facility_data["accessibility_txt"])
        self.assertTrue(facility.ada_accessibility)
        self.assertEqual(facility.reservation_url, self.facility_data["reservation_url"])
        self.assertEqual(facility.phone, self.facility_data["phone"])
        self.assertEqual(facility.email, self.facility_data["email"])
        self.assertEqual(facility.description, self.facility_data["description"])

    def test_f_id_unique_constraint(self):
        #Test that the f_id field is unique by attempting to create two facilities with the same f_id.
        
        Facility.objects.create(**self.facility_data)
        duplicate_data = self.facility_data.copy()
        duplicate_data["name"] = "Another Facility"
        # Creating a duplicate should raise an IntegrityError when saved to the database.
        with self.assertRaises(IntegrityError):
            Facility.objects.create(**duplicate_data)

    def test_email_field_validation(self):
        #Test that an invalid email format causes a ValidationError during model validation.
        
        invalid_data = self.facility_data.copy()
        invalid_data["email"] = "invalid-email-format"
        facility = Facility(**invalid_data)
        with self.assertRaises(ValidationError):
            # full_clean() will run model validations, including for EmailField.
            facility.full_clean()

    def test_phone_field_accepts_valid_length(self):
        #Although phone is a CharField with max_length=15, this test verifies that
        #a valid phone string (within 15 characters) passes model validation.
        valid_data = self.facility_data.copy()
        valid_data["phone"] = "1234567890"  # 10 characters is within the limit
        facility = Facility(**valid_data)
        try:
            facility.full_clean()  # Should not raise a ValidationError.
        except ValidationError:
            self.fail("Facility.full_clean() raised ValidationError unexpectedly for a valid phone number.")



# tests for the user model
class UserTests(TestCase):
    def test_create(self):
        # test data for creating a user
        test_data = {
            'username': 'Testuser',
            'password': 'Password123!',
        }

        # retrieving the model and creating a user
        CampUser = get_user_model()
        user = CampUser.objects.create_user(
            username=test_data['username'],
            password=test_data['password'],
        )

        # verifying creation of user and username/password is correctly saved
        self.assertEqual(user.username, 'Testuser')
        self.assertTrue(user.check_password('Password123!'))


# tests for Registration
class RegisterTests(TestCase):
    # testing that register is returning the correct status and contains the form
    def test_form_response(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')