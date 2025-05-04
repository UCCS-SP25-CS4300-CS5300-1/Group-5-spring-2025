from calendar import HTMLCalendar
from datetime import date, datetime, timedelta
import requests
from django.conf import settings # pylint: disable=unused-import
from django.templatetags.static import static
from django.urls import reverse
from .models import UserPreferences
import openai
from openai.error import OpenAIError


# this is my api key for RIDB
RIDB_API_KEY = "3d213c37-c624-440f-aec2-68ac2728b395"



#THIS IS SO WE CAN USE LOCATION INSTEAD OF KEYWORD
def geocode_location(location_name):
    """Convert a location name to latitude and longitude using OpenStreetMap."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location_name,
        "format": "json",
        "limit": 1,
    }
    response = requests.get(url, params=params, headers={"User-Agent": "campmate-app"}, timeout=15)

    if response.status_code == 200:
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon

    # Always fallback here if the above block doesn't return
    print(f"Geocoding failed for location: {location_name}")
    return None, None



#ABI UPDATED THIS FUNCTION
def search_facilities(lat=None, lon=None, location=None, user=None, radius=100):
    """Fetch campsites from RIDB API based on latitude/longitude or fallback to location keyword."""
    base_url = "https://ridb.recreation.gov/api/v1/facilities"

    params = {
        "apikey": RIDB_API_KEY,
        "limit": 50,
        "radius": radius,
    }

    if lat is not None and lon is not None:
        params["latitude"] = lat
        params["longitude"] = lon
    elif location:
        params["query"] = location

    response = requests.get(base_url, params=params, timeout=20)

    if response.status_code != 200:
        return []

    facilities = response.json().get("RECDATA", [])

    for f in facilities:
        media = f.get("MEDIA", [])
        if media:
            primary = next((m for m in media if m.get("IsPrimary")), media[0])
            f["image_url"] = primary.get("URL")
        else:
            f["image_url"] = None

    if user and user.is_authenticated:
        facilities = _filter_facilities_by_user_preferences(user, facilities)

    return facilities


def _filter_facilities_by_user_preferences(user, facilities):
    """Apply user preference filters (campground, trail, hotel, etc.) to facility list."""
    try:
        preferences = user.preferences

        # Filter by reservable
        if preferences.reservable:
            facilities = [f for f in facilities if f.get("Reservable", False)]

        selected_types = []
        if preferences.campground:
            selected_types.append("Campground")
        if preferences.rangerstation:
            selected_types.append("Ranger Station")
        if preferences.hotel:
            selected_types.append("Hotel")
        if preferences.trail:
            selected_types.append("Trail")
        if preferences.facility:
            selected_types.append("Facility")

        if selected_types:
            facilities = [
                f for f in facilities
                if any(t in f.get("FacilityTypeDescription", "") for t in selected_types)
            ]
    except UserPreferences.DoesNotExist:
        pass

    return facilities



# returns a single facility based on the id. this is for a facility detail page.
def return_facility_detail(facility_id):

    # get base url based on what we want from api: in this case, facilities/facility_id
    base_url = f"https://ridb.recreation.gov/api/v1//facilities/{facility_id}"

    # define parameters; for now, only need apikey
    params = {"apikey": RIDB_API_KEY}

    # get response from API
    response = requests.get(base_url, params=params, timeout=20)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        return response.json()
    return {}

# returns facility address based on facility id as a string. this is for the facility detail page
def return_facility_address(facility_id):

    # get base url based on what we want from api
    base_url = (
        f"https://ridb.recreation.gov/api/v1/facilities/{facility_id}/facilityaddresses"
    )

    # define parameters; for now, only need apikey
    params = {"apikey": RIDB_API_KEY}

    # get response from API
    response = requests.get(base_url, params=params, timeout=20)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        try:
            # get city, state, address
            # do this as an exception because the data may return no data with
            # a successful response code still, so theres no index to index to; hence IndexError
            city = response.json().get("RECDATA", [{}])[0].get("City")
            state = response.json().get("RECDATA", [{}])[0].get("AddressStateCode")
            address = (
                response.json().get("RECDATA", [{}])[0].get("FacilityStreetAddress1")
            )
            facility_address = address + ", " + city + ", " + state
            return facility_address

        except IndexError:
            return ""
    else:
        return {}


# returns facility website url as a string
# if no url, returns empty string
def return_facility_url(facility_id):

    # get base url based on what we want from api: in this case, facility id and link
    base_url = f"https://ridb.recreation.gov/api/v1/facilities/{facility_id}/links"

    # define parameters; id and key needed
    params = {"facilityID": facility_id, "apikey": RIDB_API_KEY}

    # get response from API
    response = requests.get(base_url, params=params, timeout=20)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        # get facility url
        # want to access the URL attribute, so thats why syntax url[0].get("URL") is done
        # we do this as an exception because the return_facility_url may return no data with
        # a successful response code still, so theres no index to index to; hence IndexError
        url = response.json().get("RECDATA", [])
        try:
            url = url[0].get("URL")
        except IndexError:
            url = ""

        return url
    return {}

# returns a html/bootstrap calendar
# based off this documentation: https://docs.python.org/3/library/calendar.html
# orig code found here https://github.com/python/cpython/blob/3.13/Lib/calendar.py
class MyHTMLCalendar(HTMLCalendar):
    def __init__(self, trips, year, month):
        super().__init__()
        self.trips = trips
        self.year = year
        self.month = month

    # Return a string representing a single day. if day is 0, return a string representing empty day
    # (for days bordering or trailing months)
    # Weekday parameter is unused.
    def formatday(self, day, weekday):

        # if day is NOT a bordering day (day of past or next month)
        if day != 0:
            current_date = date(self.year, self.month, day)
            # if trip occurs on weekday, format special w/ link to trip details
            for trip in self.trips:
                if trip.start_date <= current_date <= trip.end_date:
                    # have to do these
                    trip_url = reverse("trip_detail", args=[trip.id])
                    img_url = static("images/cm.png")
                    return (
                        f'<td class="day-trip table-light text-center">{day}'
                        f'<br> <a href="{trip_url}"><img src="{img_url}"'
                        f' width="60" height="60"></a> </td>'
                    )
            # normal weekday, no trip
            return f'<td class="table-light text-center">{day}</td>'
        # bordering day
        return '<td class="table-secondary"></td>'

    # Return a string representing a single week with no newline
    def formatweek(self, theweek):
        week_html = "".join(self.formatday(d, wd) for d, wd in theweek)
        return f"<tr>{week_html}</tr>"

    # Return a month's calendar in a multiline string (bootstrap table)
    # withyear=True means the year will be included in the output
    def formatmonth(self, theyear=None, themonth=None, withyear=True):
        # this is how the whole table calendar itself is formated
        # small, bordered
        cal = '<table class="table table-bordered table-sm">'
        cal += f"{self.formatmonthname(self.year, self.month, withyear=withyear)}"
        # first calendar table row that shows month and year
        cal += f"{self.formatweekheader()}"
        # monthdays2calendar returns list of weeks; 7 tuples of day #s and weekdays
        for week in self.monthdays2calendar(self.year, self.month):
            cal += self.formatweek(week)
        cal += "</table>"
        return cal

WEATHER_CODE_MAP = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def fetch_weather(lat, lon, start_date, end_date):
    """Get weather forecast using Open-Meteo API."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=auto"
    )
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        return []

    data = res.json()

    forecast = []
    max_date_available = datetime.strptime(data["daily"]["time"][-1], "%Y-%m-%d").date()


    for forecast_date, tmax, tmin, code in zip(
        data["daily"]["time"],
        data["daily"]["temperature_2m_max"],
        data["daily"]["temperature_2m_min"],
        data["daily"]["weathercode"],
    ):
        forecast.append(
            {
                "date": forecast_date,
                "temp_max": round(tmax * 9 / 5 + 32),
                "temp_min": round(tmin * 9 / 5 + 32),
                "condition": WEATHER_CODE_MAP.get(code, "Unknown")
            }
        )

    # Fill in unavailable forecast days if trip goes beyond what API returns
    actual_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    current_day = max_date_available + timedelta(days=1)

    while current_day <= actual_end:
        forecast.append(
            {
                "date": current_day.strftime("%Y-%m-%d"),
                "temp_max": None,
                "temp_min": None,
                "condition": "Forecast unavailable — exceeds API range",
            }
        )
        current_day += timedelta(days=1)

    return forecast


hazards = [
    "Dense freezing drizzle",
    "Heavy rain",
    "Heavy freezing rain",
    "Moderate snowfall",
    "Heavy snowfall",
    "Violent rain showers",
    "Heavy snow showers",
    "Thunderstorm",
    "Thunderstorm w/ slight hail",
    "Thunderstorm w/ heavy hail",
]


def check_hazards(daily_conditions):
    """Return list of days that match hazardous conditions."""
    return [day for day in daily_conditions if day["condition"] in hazards]

# home/utils.py

def get_facility_defaults(facility_id):
    data = return_facility_detail(facility_id)
    # find primary image (or None)
    media = data.get("MEDIA", [])
    image_url = next((m["URL"] for m in media if m.get("IsPrimary")), None)

    return {
        "name": data["FacilityName"],
        "type": data["FacilityTypeDescription"],
        "accessibility_txt": data["FacilityAccessibilityText"],
        "ada_accessibility": data["FacilityAdaAccess"],
        "phone": data["FacilityPhone"],
        "email": data["FacilityEmail"],
        "description": data["FacilityDescription"],
        "reservable": data["Reservable"],
        "url":    return_facility_url(facility_id),
        "location": return_facility_address(facility_id),
        "latitude":  data.get("FacilityLatitude"),
        "longitude": data.get("FacilityLongitude"),
        "image_url": image_url,
    }

# home/utils.py

def build_packing_prompt(facilities, start, end, num_people):
    names = ", ".join(f.name for f in facilities)
    return (
      f"Generate a packing list for {num_people} people camping at {names}"
      f" from {start} to {end}. Focus on essentials, include quantities. "
      "Consider the weather at this time and location. "
      "Give response in a comma separated list"
    )

def generate_packing_list(prompt):
    try:
        openai.api_key = settings.OPENAI_API_KEY
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.5
        )
        items = [i.strip().capitalize()
                 for i in resp.choices[0].message.content.split(",")]
        return ", ".join(items)
    except OpenAIError:
        return "Tent, sleeping bag, food, water, flashlight"
