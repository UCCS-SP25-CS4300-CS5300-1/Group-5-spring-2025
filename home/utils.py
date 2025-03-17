import requests
from django.conf import settings

# this is my api key for RIDB 
RIDB_API_KEY = "3d213c37-c624-440f-aec2-68ac2728b395"

# THIS NEEDS TO BE FIXED, RIGHT NOW, LOCATION IS ACTUALLY KEYWORD: HAVE TO COMPROMISE, MAKE USER INPUT STATE AS WELL FOR QUERY?
# THEN HAVE TO PARSE QUERY... OR MAYBE INCORPORATE FILTERS? FORCE STATE AND RADIUS PARAMETERS... THEN USER ENTERS WHATEVER INTO SEARCH
# returns all campsite based on user entered location (& later, radius)
# for search/landing page
def search_facilities(location, radius=5):
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
        #"state": 'CO',
    }

    # get response from API
    response = requests.get(base_url, params=params)

    # this is based on API documentation -- a successful response code is 200
    # if response was successful, return the data
    if response.status_code == 200:
        # RECDATA is the title for the response data
        return response.json().get("RECDATA", [])  # List of campsites
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
