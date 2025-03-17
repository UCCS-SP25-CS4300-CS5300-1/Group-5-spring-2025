from django.test import TestCase, Client
from bs4 import BeautifulSoup

# Create your tests here.

class BaseTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_base_template_contains_campmate_header(self):
        #Check that the header 'CampMate' is present in the template.
        response = self.client.get('/')  # Adjust URL if needed
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        header = soup.find('h1')
        self.assertIsNotNone(header, "The page should contain an <h1> header")
        self.assertEqual(header.text.strip(), 'CampMate')

    def test_static_css_is_included(self):
        #Ensure the custom CSS file is linked in the template.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        css_link = soup.find('link', href=lambda href: href and 'css/styles.css' in href)
        self.assertIsNotNone(css_link, "The page should include the custom CSS file.")

    def test_bootstrap_css_is_included(self):
        #Check that the Bootstrap CSS is loaded via the CDN.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        bootstrap_css = soup.find('link', href=lambda href: href and 'bootstrap.min.css' in href)
        self.assertIsNotNone(bootstrap_css, "Bootstrap CSS should be included.")

    def test_dark_mode_toggle_exists(self):
        #Verify that the dark mode toggle button and its icon exist.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        dark_mode_button = soup.find('button', id='darkModeToggle')
        self.assertIsNotNone(dark_mode_button, "Dark mode toggle button should be present.")
        dark_mode_icon = dark_mode_button.find('i', id='darkModeIcon')
        self.assertIsNotNone(dark_mode_icon, "The dark mode toggle button should include an icon.")

    def test_navigation_menu_exists(self):
        #Ensure that the menu dropdown is present in the header.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Using a lambda to handle any extra spaces or formatting
        menu_link = soup.find('a', string=lambda text: text and text.strip() == 'Menu')
        self.assertIsNotNone(menu_link, "The navigation menu should be present.")


