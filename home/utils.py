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
                        facility for facility in facilities
                        if facility.get("Reservable", False) # default is false if there is no data available
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
                        facility for facility in facilities
                        if any(f_type in facility["FacilityTypeDescription"] for f_type in selected_types)
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
    
# returns facility address based on facility id as a string
# this is for the facility detail page
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
        try:
            # JSON data in the form City:... AddressStateCode:...
            # want to access the URL attribute, so thats why syntax response.json().get("RECDATA", [{}])[0].get("City") is done
            # we do this as an exception because the data may return no data with 
            # a successful response code still, so theres no index to index to; hence IndexError
            city = response.json().get("RECDATA", [{}])[0].get("City")
            state = response.json().get("RECDATA", [{}])[0].get("AddressStateCode")
            address = response.json().get("RECDATA", [{}])[0].get("FacilityStreetAddress1")
            facility_address = address + ', ' + city + ', ' + state
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
    params = {"facilityID": facility_id,
              "apikey": RIDB_API_KEY}

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




