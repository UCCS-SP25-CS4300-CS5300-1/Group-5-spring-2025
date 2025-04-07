from bs4 import BeautifulSoup
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from home.models import UserProfile, TripDetails, Facility
from datetime import date

class TripDetailHTMLTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='htmluser', password='pass123')
        self.profile = UserProfile.objects.create(user=self.user)
        self.facility = Facility.objects.create(
            f_id='F999',
            name='Soup Camp',
            location='Soup Forest'
        )
        self.trip = TripDetails.objects.create(
            user=self.profile,
            facility=self.facility,
            start_date=date(2025, 5, 1),
            end_date=date(2025, 5, 3),
            number_of_people=2,
            packing_list='Tent, Sleeping Bag, Flashlight'
        )

    def test_trip_detail_page_content(self):
        self.client.login(username='htmluser', password='pass123')
        url = reverse('trip_detail', args=[self.trip.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for the title
        h2 = soup.find('h2')
        self.assertIn(self.facility.name, h2.text)
        self.assertIn(self.user.username, h2.text)

        # Check that the packing list is shown
        packing_items = [p.text.strip() for p in soup.find_all('p') if 'Packing' not in p.text]
        found_items = ', '.join(packing_items)
        self.assertTrue('Tent' in found_items or 'Sleeping Bag' in found_items)

        # Check checkboxes are rendered
        checkboxes = soup.find_all('input', {'type': 'checkbox'})
        self.assertGreaterEqual(len(checkboxes), 1)

        # Check Save/Cancel buttons are present
        buttons = soup.find_all('button')
        button_texts = [btn.text.lower() for btn in buttons]
        self.assertIn('save trip', button_texts)
        self.assertIn('start over', button_texts)
