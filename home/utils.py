from calendar import HTMLCalendar
from datetime import date

import requests
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

from .models import *

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
    response = requests.get(url, params=params, headers={"User-Agent": "campmate-app"})

    if response.status_code == 200:
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    if response.status_code != 200 or not data:
        # Log an error message
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

    response = requests.get(base_url, params=params)

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

    # Now apply user preferences if logged in
    if user and user.is_authenticated:
        try:
            preferences = user.preferences

            # Filter by reservable
            if preferences.reservable:
                facilities = [
                    facility for facility in facilities
                    if facility.get("Reservable", False)
                ]

            # Filter by preferred types
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
                    facility for facility in facilities
                    if any(
                        t in facility.get("FacilityTypeDescription", "")
                        for t in selected_types
                    )
                ]
        except UserPreferences.DoesNotExist:
            pass

    return facilities



# returns a single facility based on the id.
# this is for a facility detail page.
def return_facility_detail(facility_id):

    # get base url based on what we want from api: in this case, facilities/facility_id
    base_url = f"https://ridb.recreation.gov/api/v1//facilities/{facility_id}"

    # define parameters; for now, only need apikey
    params = {"apikey": RIDB_API_KEY}

    # get response from API
    response = requests.get(base_url, params=params)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        return response.json()
    else:
        return {}


# returns facility address based on facility id as a string
# this is for the facility detail page
def return_facility_address(facility_id):

    # get base url based on what we want from api: in this case, /facilities/{facilityId}/facilityaddresses
    base_url = (
        f"https://ridb.recreation.gov/api/v1/facilities/{facility_id}/facilityaddresses"
    )

    # define parameters; for now, only need apikey
    params = {"apikey": RIDB_API_KEY}

    # get response from API
    response = requests.get(base_url, params=params)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        try:
            # JSON data in the form City:... AddressStateCode:...
            # want to access the URL attribute, so thats why syntax response.json().get("RECDATA", [{}])[0].get("City") is done
            # we do this as an exception because the data may return no data with
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
# needs own def since grabbing the url consists of diff request url
def return_facility_url(facility_id):

    # get base url based on what we want from api: in this case, facility id and link
    base_url = f"https://ridb.recreation.gov/api/v1/facilities/{facility_id}/links"

    # define parameters; id and key needed
    params = {"facilityID": facility_id, "apikey": RIDB_API_KEY}

    # get response from API
    response = requests.get(base_url, params=params)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        # get facility url
        # JSON data in the form EntityLinkID:... LinkType:... ... URL:
        # want to access the URL attribute, so thats why syntax url[0].get("URL") is done
        # we do this as an exception because the return_facility_url may return no data with
        # a successful response code still, so theres no index to index to; hence IndexError
        url = response.json().get("RECDATA", [])
        try:
            url = url[0].get("URL")
        except IndexError:
            url = ""

        return url

    else:
        return {}


# calendar stuff
# create a custom class based off python's built-in html calendar
# note: i wanted to incorporate bootstrap into the html calendar, so i have to override the methods of the class in order to have
# bootstrap formatting.
# based off this documentation: https://docs.python.org/3/library/calendar.html
# code thats overwritten can be found here https://github.com/python/cpython/blob/3.13/Lib/calendar.py
class MyHTMLCalendar(HTMLCalendar):
    def __init__(self, trips, year, month):
        super().__init__()
        self.trips = trips
        self.year = year
        self.month = month

    """
    Return a string representing a single day. if day is 0, return a string representing empty day (for days bordering or trailing months) 
    Weekday parameter is unused. 
    """

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
                    return f'<td class="day-trip table-light text-center">{day} <br> <a href="{trip_url}"><img src="{img_url}"  width="60" height="60"></a> </td>'
            # normal weekday, no trip
            return f'<td class="table-light text-center">{day}</td>'
        # bordering day
        return '<td class="table-secondary"></td>'

    """
    Return a string representing a single week with no newline. uses formatday func to do this, iterating through all days in a week
    """

    def formatweek(self, theweek):
        week_html = "".join(self.formatday(d, wd) for d, wd in theweek)
        return f"<tr>{week_html}</tr>"

    """
    Return a month's calendar in a multiline string (bootstrap table)
    withyear=True means the year will be included in the output
    """

    def formatmonth(self, withyear=True):
        # this is how the whole table calendar itself is formated
        # small, bordered, and color changes if hovering above row (might change later)
        cal = f'<table class="table table-bordered table-sm">'
        cal += f"{self.formatmonthname(self.year, self.month, withyear=withyear)}"
        # first calendar table row that shows month and year
        cal += f"{self.formatweekheader()}"
        # monthdays2calendar returns a list of the weeks in the month of the year as full weeks; weeks are lists of seven tuples of day numbers and
        # weekday numbers
        for week in self.monthdays2calendar(self.year, self.month):
            cal += self.formatweek(week)
        cal += "</table>"
        return cal


# import requests

# def fetch_weather(lat, lon, start_date, end_date):
#     """Get weather forecast using Open-Meteo API."""
#     url = (
#         f"https://api.open-meteo.com/v1/forecast"
#         f"?latitude={lat}&longitude={lon}"
#         f"&start_date={start_date}&end_date={end_date}"
#         f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
#         f"&timezone=auto"
#     )
#     res = requests.get(url)
#     if res.status_code != 200:
#         return []

#     data = res.json()

#     code_map = {
#         0: "Clear sky",
#         1: "Mainly clear",
#         2: "Partly cloudy",
#         3: "Overcast",
#         45: "Fog",
#         48: "Depositing rime fog",
#         51: "Light drizzle",
#         53: "Moderate drizzle",
#         55: "Dense drizzle",
#         56: "Light freezing drizzle",
#         57: "Dense freezing drizzle",
#         61: "Slight rain",
#         63: "Moderate rain",
#         65: "Heavy rain",
#         66: "Light freezing rain",
#         67: "Heavy freezing rain",
#         71: "Slight snow fall",
#         73: "Moderate snow fall",
#         75: "Heavy snow fall",
#         77: "Snow grains",
#         80: "Slight rain showers",
#         81: "Moderate rain showers",
#         82: "Violent rain showers",
#         85: "Slight snow showers",
#         86: "Heavy snow showers",
#         95: "Thunderstorm",
#         96: "Thunderstorm with slight hail",
#         99: "Thunderstorm with heavy hail",
#     }

#     forecast = []
#     for date, tmax, tmin, code in zip(
#         data['daily']['time'],
#         data['daily']['temperature_2m_max'],
#         data['daily']['temperature_2m_min'],
#         data['daily']['weathercode']
#     ):
#         forecast.append({
#             'date': date,
#             'temp_max': round(tmax * 9/5 + 32),
#             'temp_min': round(tmin * 9/5 + 32),
#             'condition': code_map.get(code, "Unknown")
#         })

#     return forecast


from datetime import datetime, timedelta

import requests


def fetch_weather(lat, lon, start_date, end_date):
    """Get weather forecast using Open-Meteo API."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=auto"
    )
    res = requests.get(url)
    if res.status_code != 200:
        return []

    data = res.json()

    code_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    forecast = []
    dates_available = data["daily"]["time"]
    max_date_available = datetime.strptime(dates_available[-1], "%Y-%m-%d").date()

    for date, tmax, tmin, code in zip(
        data["daily"]["time"],
        data["daily"]["temperature_2m_max"],
        data["daily"]["temperature_2m_min"],
        data["daily"]["weathercode"],
    ):
        forecast.append(
            {
                "date": date,
                "temp_max": round(tmax * 9 / 5 + 32),
                "temp_min": round(tmin * 9 / 5 + 32),
                "condition": code_map.get(code, "Unknown"),
            }
        )

    # Fill in unavailable forecast days if trip goes beyond what API returns
    actual_start = datetime.strptime(start_date, "%Y-%m-%d").date()
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
