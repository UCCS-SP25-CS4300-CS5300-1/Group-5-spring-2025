import requests
from django.conf import settings

from .models import *

# this is my api key for RIDB
RIDB_API_KEY = "3d213c37-c624-440f-aec2-68ac2728b395"


# THIS NEEDS TO BE FIXED, RIGHT NOW, LOCATION IS ACTUALLY KEYWORD: HAVE TO COMPROMISE, MAKE USER INPUT STATE AS WELL FOR QUERY?
# THEN HAVE TO PARSE QUERY... OR MAYBE INCORPORATE FILTERS? FORCE STATE AND RADIUS PARAMETERS... THEN USER ENTERS WHATEVER INTO SEARCH
# returns all campsite based on user entered location (& later, radius)
# for search/landing page
def search_facilities(location, user, radius=5):
    """Fetch campsites from RIDB API based on user location."""
    # get base url based on what we want from api: in this case, facilities
    base_url = "https://ridb.recreation.gov/api/v1/facilities"

    # define parameters; query is the criteria of which campsites are searched by
    # will add in radius later (this will be a filter for search bar; radius is a param
    # that will correspond to the filter mile radius; for now, radius isnt user input)
    params = {
        "query": location,  # City or ZIP code
        "limit": 10,  # Limit results
        "apikey": RIDB_API_KEY,
        "radius": radius,
    }

    # get response from API
    response = requests.get(base_url, params=params)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        # RECDATA is the title for the response data
        # will be returned in the form of a list of dictionaries
        facilities = response.json().get("RECDATA", [])  # List of campsites

        # apply user preferences as filter IF user is authenticated
        if user and user.is_authenticated:

            try:
                # first, get user preferences
                preferences = user.preferences

                # first, get reservable attribute, and filter results based on preference
                if preferences.reservable:
                    facilities = [
                        facility
                        for facility in facilities
                        if facility.get(
                            "Reservable", False
                        )  # default is false if there is no data available
                    ]

                # facilities now contains results that are relevant to the user preference for reservable
                # now, get user preferences based on facility type; do this by appending appropriate type
                # to list as filter through user preferences
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

                # if there are user preferences for facility types (list isnt empty), filter again
                # according to preferences
                # if facility has matching type from selected_types list, keep in list
                if selected_types:
                    facilities = [
                        facility
                        for facility in facilities
                        if any(
                            f_type in facility["FacilityTypeDescription"]
                            for f_type in selected_types
                        )
                    ]

            # take into account if user preferences don't exist
            except UserPreferences.DoesNotExist:
                pass

        return facilities
    else:

        return []


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


import requests
from datetime import datetime, timedelta

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
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
        77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
        82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
    }

    forecast = []
    dates_available = data['daily']['time']
    max_date_available = datetime.strptime(dates_available[-1], "%Y-%m-%d").date()

    for date, tmax, tmin, code in zip(
        data['daily']['time'],
        data['daily']['temperature_2m_max'],
        data['daily']['temperature_2m_min'],
        data['daily']['weathercode']
    ):
        forecast.append({
            'date': date,
            'temp_max': round(tmax * 9/5 + 32),
            'temp_min': round(tmin * 9/5 + 32),
            'condition': code_map.get(code, "Unknown")
        })

    # Fill in unavailable forecast days if trip goes beyond what API returns
    actual_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    actual_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    current_day = max_date_available + timedelta(days=1)

    while current_day <= actual_end:
        forecast.append({
            'date': current_day.strftime('%Y-%m-%d'),
            'temp_max': None,
            'temp_min': None,
            'condition': "Forecast unavailable — exceeds API range"
        })
        current_day += timedelta(days=1)

    return forecast




hazards = [
    'Dense freezing drizzle', 'Heavy rain', 'Heavy freezing rain',
    'Moderate snowfall', 'Heavy snowfall', 'Violent rain showers',
    'Heavy snow showers', 'Thunderstorm', 'Thunderstorm w/ slight hail',
    'Thunderstorm w/ heavy hail'
]

def check_hazards(daily_conditions):
    """Return list of days that match hazardous conditions."""
    return [day for day in daily_conditions if day['condition'] in hazards]


