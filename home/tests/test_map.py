from django.test import TestCase
from django.urls import reverse
from home.models import Facility

class TemplateRenderingTests(TestCase):

    def test_search_results_template_with_campsites(self):
        # Clear any preexisting data so that the test runs in isolation.
        Facility.objects.all().delete()

        # Create a unique facility so that only this record is returned by the query.
        facility = Facility.objects.create(
            name="UniqueTestCampsite",  # Use a unique name.
            location="123 Camp Road",
            f_id="TC001",
            type="Campground",
            accessibility_txt="Accessible",
            ada_accessibility="Y",
            phone="1234567890",
            email="camp@example.com",
            description="A test campsite."
        )
        
        # Use a search query that should match only our unique facility.
        response = self.client.get(reverse('search') + '?q=UniqueTestCampsite')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_results.html')
        # Now we expect to see our unique facility's name in the rendered HTML.
        self.assertContains(response, "UniqueTestCampsite")

    def test_search_results_template_with_no_campsites(self):
        # Delete all facilities to simulate an empty search result.
        Facility.objects.all().delete()
        
        # Use a query that will not match any facility.
        response = self.client.get(reverse('search') + '?q=no_match_12345')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_results.html')
        # With no matching facilities, the template should show "No results found."
        self.assertContains(response, "No results found.")
