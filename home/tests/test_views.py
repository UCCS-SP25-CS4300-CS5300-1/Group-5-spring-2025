import json
from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from home.models import CampUser, Facility, TripDetails, UserProfile


class ViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_model = get_user_model()
        self.test_username = "testuser"
        self.test_password = "testpass123"
        self.user = self.user_model.objects.create_user(
            username=self.test_username, password=self.test_password
        )
        # Ensure a UserProfile exists for the user.
        UserProfile.objects.get_or_create(user=self.user)

    def test_index_view(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    @patch("home.views.geocode_location")
    @patch("home.views.search_facilities")
    def test_search_view_no_query(self, mock_search_facilities, mock_geocode_location):
        # No query provided, so neither geocode_location nor search_facilities should be called.
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_results.html")
        self.assertEqual(response.context.get("campsites"), [])
        self.assertIsNone(response.context.get("query"))
        mock_search_facilities.assert_not_called()
        mock_geocode_location.assert_not_called()


    @patch("home.views.return_facility_detail")
    @patch("home.views.return_facility_address")
    def test_facility_detail_view_with_addresses(
        self, mock_return_facility_address, mock_return_facility_detail
    ):
        facility_id = "123"
        # Simulate valid responses from the external functions.
        mock_return_facility_detail.return_value = {
            "f_id": facility_id,
            "name": "Camp A",
        }
        mock_return_facility_address.return_value = "123 test, Denver, Colorado"
        url = reverse("facility_detail", kwargs={"facility_id": facility_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "facility_detail.html")
        self.assertEqual(
            response.context.get("campsite"), {"f_id": facility_id, "name": "Camp A"}
        )
        self.assertEqual(
            response.context.get("facility_address"), "123 test, Denver, Colorado"
        )
        mock_return_facility_detail.assert_called_once_with(facility_id)
        mock_return_facility_address.assert_called_once_with(facility_id)

    @patch("home.views.return_facility_detail")
    @patch("home.views.return_facility_address")
    def test_facility_detail_view_without_addresses(
        self, mock_return_facility_address, mock_return_facility_detail
    ):
        facility_id = "456"
        mock_return_facility_detail.return_value = {
            "f_id": facility_id,
            "name": "Camp B",
        }
        mock_return_facility_address.return_value = ""
        url = reverse("facility_detail", kwargs={"facility_id": facility_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "facility_detail.html")
        self.assertEqual(
            response.context.get("campsite"), {"f_id": facility_id, "name": "Camp B"}
        )
        self.assertEqual(response.context.get("facility_address"), "")

    #@patch("home.views.return_facility_detail")
    #@patch("home.views.return_facility_address")
    #@patch("home.views.return_facility_url")
    #def test_save_facility_view(
      #  self,
      ##  mock_return_facility_address,
    #    mock_return_facility_url,
     #   mock_return_facility_detail,
   # ):
        # Log in the test user.
   #     self.client.login(username=self.test_username, password=self.test_password)
        # Simulate mock API call
    #    facility_id = "123"

        # Mock the return_facility_detail response to match what the view expects
     #   mock_return_facility_detail.return_value = {
      #      "FacilityName": "Camp Save",
       #     "FacilityTypeDescription": "Campground",
      #      "FacilityAccessibilityText": "Accessible",
       ##     "FacilityAdaAccess": "Y",
        #    "FacilityPhone": "123 456-78910",
         #   "FacilityEmail": "email@test.com",
          #  "FacilityDescription": "Description here",
           # "Reservable": True,
        #}
      #  mock_return_facility_address.return_value = "123 test, Denver, CO"
       # mock_return_facility_url.return_value = "www.url.com"

     #   url = reverse("save_facility", kwargs={"facility_id": facility_id})
    #    response = self.client.get(url)
    #    self.assertEqual(response.status_code, 302)
     #   self.assertRedirects(response, reverse("user_profile"))
        # Verify that the facility was created and added to the user's profile.
   #     facility = Facility.objects.get(f_id=facility_id)
   #     self.assertEqual(facility.name, "Camp Save")
   #     profile = UserProfile.objects.get(user=self.user)
    #    self.assertIn(facility, profile.favorited_loc.all())

    def test_register_view_get(self):
        url = reverse("register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")
        self.assertIn("form", response.context)

    def test_register_view_post_valid(self):
        url = reverse("register")
        data = {
            "username": "newuser",
            "password1": "newpassword123",
            "password2": "newpassword123",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/")
        # Check that the new user is created.
        new_user = self.user_model.objects.get(username="newuser")
        self.assertIsNotNone(new_user)

    @patch("home.views.search_facilities")
    def test_user_profile_view_get(self, mock_search_facilities):
        self.client.login(username=self.test_username, password=self.test_password)
        mock_search_facilities.return_value = [{"name": "Camp A"}]
        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")
        # Check that context contains the expected keys.
        self.assertIn("user_profile", response.context)
        self.assertIn("favorite_loc", response.context)

    def test_logout_user_view(self):
        self.client.login(username=self.test_username, password=self.test_password)
        url = reverse("logout")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))
        # After logging out, accessing a login_required view should not return 200.
        response2 = self.client.get(reverse("user_profile"))
        self.assertNotEqual(response2.status_code, 200)





class TripViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )
        self.user_profile = self.user.userprofile
        self.facility = Facility.objects.create(
            name="Camp Alpha",
            location="Hills",
            f_id="ALPHA1",
            type="Park",
            description="Testing facility",
        )
        self.client.login(username="testuser", password="testpass")

    @patch("home.views.openai.ChatCompletion.create")
    def test_create_trip_async_success(self, mock_openai):
        # Properly mock OpenAI API response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Tent, Sleeping Bag, Flashlight"
        mock_response.choices = [mock_choice]
        mock_openai.return_value = mock_response

        url = reverse("create_trip_async", kwargs={"facility_id": self.facility.id})
        response = self.client.post(
            url,
            {
                "start_date": "2025-06-01",
                "end_date": "2025-06-03",
                "number_of_people": 2,
            },
        )

        # Redirects to preview page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("trip_preview"))

        # Trip should exist
        trip = TripDetails.objects.latest("id")
        self.assertEqual(trip.user, self.user_profile)
        self.assertEqual(trip.number_of_people, 2)
        self.assertIn("Tent", trip.packing_list)

        # Session should hold preview ID
        session = self.client.session
        self.assertEqual(session["trip_preview_id"], trip.id)

    def test_create_trip_async_invalid_method(
        self,
    ):
        url = reverse("create_trip_async", kwargs={"facility_id": self.facility.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content, {"success": False, "error": "Invalid request"}
        )

    def test_trip_preview_view(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
            number_of_people=2,
            packing_list="Tent, Flashlight",
        )
        trip.facility.set([self.facility])

        session = self.client.session
        session["trip_preview_id"] = trip.id
        session.save()

        response = self.client.get(reverse("trip_preview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tent")

    def test_confirm_trip_clears_session(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
        )
        trip.facility.set([self.facility])

        session = self.client.session
        session["trip_preview_id"] = trip.id
        session.save()

        response = self.client.get(reverse("confirm_trip"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("user_profile"))

        self.assertNotIn("trip_preview_id", self.client.session)

    def test_cancel_trip_deletes_and_redirects(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
        )
        trip.facility.set([self.facility])
        session = self.client.session
        session["trip_preview_id"] = trip.id
        session.save()

        response = self.client.get(reverse("cancel_trip"))
        self.assertRedirects(response, reverse("user_profile"))
        self.assertFalse(TripDetails.objects.filter(id=trip.id).exists())
        self.assertNotIn("trip_preview_id", self.client.session)

    def test_trip_detail_view(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
            packing_list="Tent, Flashlight",
        )

        trip.facility.set([self.facility])

        response = self.client.get(reverse("trip_detail", kwargs={"trip_id": trip.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.facility.name)
        self.assertContains(response, "Tent")

    def test_trip_edit_view(self):
        trip = TripDetails.objects.create(
            user=self.user_profile,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
            number_of_people=2,
        )
        trip.facility.set([self.facility])

        new_start = "2025-06-05"
        new_end = "2025-06-08"
        new_people = 4
        new_facility = Facility.objects.create(
            name="Camp Beta",
            location="Valley",
            f_id="BETA1",
            type="Campground",
            description="Second facility for testing",
        )

        url = reverse("edit_trip", kwargs={"trip_id": trip.id})
        response = self.client.post(
            url,
            {
                "start_date": new_start,
                "end_date": new_end,
                "number_of_people": new_people,
                "edit_facilities": f"{new_facility.id}",
            },
        )

        trip.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('trip_detail', kwargs={'trip_id': trip.id})
        )
        self.assertEqual(str(trip.start_date), new_start)
        self.assertEqual(str(trip.end_date), new_end)
        self.assertEqual(trip.number_of_people, new_people)
        self.assertIn(new_facility, trip.facility.all())


# test for calendar view
class CalendarViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CampUser.objects.create_user(
            username="testuser", password="testpassword123"
        )
        self.profile = self.user.userprofile

        self.trip = TripDetails.objects.create(
            user=self.profile,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            number_of_people=2,
        )

    def test_calendar_view_authenticated(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("current_calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/calendar.html")

    def test_trip_appears_in_calendar(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("current_calendar"))
        # find needle in haystack:
        # this specific line of html should appear if view functions as it should
        # special html format for calendar day based on trip
        needle = (
            f'<td class="day-trip table-light text-center">{self.trip.start_date.day} <br>'
            f'<a href="/trip/{self.trip.id}/">'
            f'<img src="/static/images/cm.png"  width="60" height="60"></a> </td>'
        )
        haystack = response.content.decode()
        self.assertInHTML(needle, haystack)

    def test_calendar_navigation(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("traverse_calendar", args=[2025, 1]))
        self.assertEqual(response.context["nextmonth"], 2)
        self.assertEqual(response.context["nextyear"], 2025)
        self.assertEqual(response.context["prevmonth"], 12)
        self.assertEqual(response.context["prevyear"], 2024)


class ChatbotViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("chatbot")  # Make sure your URL name is 'chatbot'

    @patch("openai.ChatCompletion.create")
    def test_chatbot_view_successful_post(self, mock_openai_create):
        mock_message = Mock()
        mock_message.content = """Here are some helpful tips...

        Follow-up questions:
        - How do I pack for a weekend trip?
        - What should I eat while camping?
        - How do I stay warm at night?
        """

        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]

        mock_openai_create.return_value = mock_response

        data = {"message": "What are tips for first-time campers?"}
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("reply", content)
        self.assertIn("followups", content)
        self.assertEqual(len(content["followups"]), 3)

    def test_chatbot_view_rejects_non_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("reply", content)
