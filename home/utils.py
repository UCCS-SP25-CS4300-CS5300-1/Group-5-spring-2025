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

        # apply user preferences as filter if user is authenticated
        if user and user.is_authenticated:
      
            try:
                # get user preferences
                preferences = user.preferences
                # loop through each return item (facility) in list of dictionary & 
                # see if it matches preference
                # done by boolean values; for example, if preferences.campground (=True) and Campground in facility["FacilityTypeDescription"] (=True)
                # then this condition is true and the facility is kept in the list
                # thus, each facility is kept in the new list if AT LEAST ONE PREFERENCE MATCHES
                facilities = [ 
                    facility for facility in facilities
                    if (preferences.campground and "Campground" in facility["FacilityTypeDescription"])
                    or (preferences.trail and "Trail" in facility["FacilityTypeDescription"])
                    or (preferences.hotel and "Hotel" in facility["FacilityTypeDescription"])
                    or (preferences.rangerstation and "Ranger Station" in facility["FacilityTypeDescription"])
                    or (preferences.facility and "Facility" in facility["FacilityTypeDescription"])
                    or (preferences.reservable and facility.get("Reservable"))

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
    params = {
        "apikey": RIDB_API_KEY
    }

    # get response from API
    response = requests.get(base_url, params=params)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        return response.json()
    else:
        return {}
    
# returns facility address based on facility id
# this if for the facility detail page
def return_facility_address(facility_id):

    # get base url based on what we want from api: in this case, /facilities/{facilityId}/facilityaddresses
    base_url = f"https://ridb.recreation.gov/api/v1/facilities/{facility_id}/facilityaddresses"

    # define parameters; for now, only need apikey 
    params = {
        "apikey": RIDB_API_KEY
    }

    # get response from API
    response = requests.get(base_url, params=params)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        return response.json().get("RECDATA", [])
    else:
        return {}
    
# returns facility website url
# needs own def since grabbing the url consists of diff request url
def return_facility_url(facility_id):

    base_url = f"https://ridb.recreation.gov/api/v1/facilities/{facility_id}/links"

    params = {"facilityID": facility_id,
              "apikey": RIDB_API_KEY}

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json().get("RECDATA", [])
    else:
        return {}




