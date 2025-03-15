from django.shortcuts import render, redirect
from .utils import *
from .models import *
# this is getting the models from the users app
from users.models import *


# Create your views here.
def index(request):
    return render(request, 'index.html')

# view for search bar function
def search_view(request):
    # Get location from search bar
    query = request.GET.get("q")  
    campsites = []

    # if user input ok, search facilities based on query
    # this calls search_facilities function in utils.py, which makes the API request. 
    if query:
        campsites = search_facilities(query)

    return render(request, "search_results.html", {"campsites": campsites, "query": query})

# view for facility detail 
def facility_detail(request, facility_id):
    campsite = return_facility_detail(facility_id)

    # return_facility_address actually returns a dicitonary inside a list
    # exp: [{'AddressCountryCode': 'USA', 'AddressStateCode': 'CO', 'City': 'Hotchkiss', ....}]
    # to get the data I want, have to parse it through [0]['attribute_name']
    # so, first get the list
    facility_addresses = return_facility_address(facility_id)
    # then fill out data if it actually returns something 
    # though this doesnt guarantee all attributes are filled out. exp, some results have no street address.
    # have to add in checks for this, do it later. 
    if facility_addresses:
        city = facility_addresses[0].get("City") 
        state = facility_addresses[0].get("AddressStateCode")
        address = facility_addresses[0].get("FacilityStreetAddress1")
    else:
        city = "N/A"
        state = "N/A"
        address = 'N/A'
  

    return render(request, "facility_detail.html", {"campsite": campsite, "city": city, "state": state, "address": address})

# function for saving a facility to a users profile
def save_facility(request, facility_id):
    # first, we get the user based on their username 
    # this CampUser model is located in users/models.py; this is where 
    #Im getting the data from 
    user = CampUser.objects.get(username=request.user.username)

    # create the saved facility (or get it if it already exists in user profile)
    facility, created = Facility.objects.get_or_create(
        # the facility id is passed in, so thats why we use it directly
        # all other attributes are passed in from the html template facility_detail.html
        # thats why we use request.GET with the appropriate name 
        f_id=facility_id,
        defaults={
            "name": request.GET.get("name"),
            "location": request.GET.get("location"),
            "type": request.GET.get("type"),
            "accessibility_txt": request.GET.get("a_txt"),
            "ada_accessibility": request.GET.get("ada"),
            "phone": request.GET.get("phone"),
            "email": request.GET.get("email"),
            "description": request.GET.get("description")
            
        }
    )

    # add this facility to user's favorited_loc attribute
    # (but really this is an attribute of UserProfile which is an attribute of user... have 
    # to ask Zach more about this... )
    user.userprofile.favorited_loc.add(facility)
    # redirects to user profile that shows all favorited campsites 
    return redirect("user_profile")