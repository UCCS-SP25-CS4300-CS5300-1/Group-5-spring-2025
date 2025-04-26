from datetime import date

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from home.models import Facility, TripDetails, UserProfile


class TripDetailTemplateTests(TestCase):
    def setUp(self):
        CampUser = get_user_model()
        self.user = CampUser.objects.create_user(
            username="testuser", password="password123"
        )
        self.user_profile = self.user.userprofile  # auto-created from signals

        self.facility = Facility.objects.create(
            name="Mountain Base",
            location="Colorado",
            f_id="CO123",
            type="Campground",
            accessibility_txt="Wheelchair accessible",
            ada_accessibility="Y",
            phone="555-1234",
            email="info@camp.com",
            description="Beautiful mountain base camping.",
        )

        self.trip = TripDetails.objects.create(
            user=self.user_profile,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 5),
            number_of_people=3,
            packing_list="Tent, Sleeping Bag, Lantern",
        )
        self.trip.facility.set([self.facility])

        self.client.login(username="testuser", password="password123")

    def test_trip_detail_template_renders(self):
        url = reverse(
            "trip_detail", kwargs={"trip_id": self.trip.id}
        )  # Adjust URL name if needed
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, "html.parser")

        # Test heading content
        h2 = soup.find("h2")
        self.assertIn(self.user.username, h2.text)
        self.assertIn(self.facility.name, h2.text)

        # Format the dates as they appear in the rendered template (e.g., "June 1, 2025")
        formatted_start = self.trip.start_date.strftime("%B %d, %Y").replace(
            " 0", " "
        )  # macOS/Linux
        formatted_end = self.trip.end_date.strftime("%B %d, %Y").replace(
            " 0", " "
        )  # macOS/Linux

        # If you're on Windows, use this instead:
        # formatted_start = self.trip.start_date.strftime("%B %#d, %Y")
        # formatted_end = self.trip.end_date.strftime("%B %#d, %Y")

        p_elements = soup.find_all("p")
        all_text = " ".join(el.get_text() for el in p_elements)

        self.assertIn("From", all_text)
        self.assertIn(formatted_start, all_text)
        self.assertIn("to", all_text)
        self.assertIn(formatted_end, all_text)
        self.assertIn("people", all_text)

        # Check for packing list container
        container = soup.find("div", {"id": "packingListContainer"})
        self.assertIsNotNone(container)

        # Check for form to delete trip
        form = soup.find("form")
        self.assertEqual(form["method"].lower(), "post")
        self.assertIn("trip_id", form["action"])
        self.assertIn("Delete", form.text)

        # Check presence of script block that builds packing list
        scripts = soup.find_all("script")
        self.assertTrue(any("packingListString" in script.text for script in scripts))

    def test_trip_detail_packing_list_rendered_in_script(self):
        url = reverse("trip_detail", kwargs={"trip_id": self.trip.id})
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        scripts = soup.find_all("script")
        self.assertTrue(any("Tent" in script.text for script in scripts))
        self.assertTrue(any("Sleeping Bag" in script.text for script in scripts))
        self.assertTrue(any("Lantern" in script.text for script in scripts))
