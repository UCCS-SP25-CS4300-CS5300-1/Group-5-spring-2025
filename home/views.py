from django.shortcuts import render, redirect
from .utils import *
from .models import *


#FOR USER STUFF
from django.contrib.auth.forms import UserCreationForm
from home.utils import return_facility_detail
from django.contrib.auth.decorators import login_required
from .forms import CampUserCreationForm
from home.models import Facility
from home.utils import return_facility_detail, search_facilities
from django.contrib.auth import logout
from .forms import *



# Create your views here.
def index(request):
    return render(request, 'index.html')

# view for search bar function
def search_view(request):
    # Get location from search bar
    query = request.GET.get("q")  

    # get user preferences
    # this is done by accessing the applyFilters id of the switch on the html page, 
    # getting its value, and testing if its equal to "on"; false means no, true means yes
    apply_filters = request.GET.get("applyFilters") == "on"
    
    campsites = []

    # if user input ok, search facilities based on query
    # this calls search_facilities function in utils.py, which makes the API request. 
    if query:
        campsites = search_facilities(query, user=request.user if apply_filters else None)

    return render(request, "search_results.html", {"campsites": campsites, "query": query, "apply_filters": apply_filters})

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

    # get facility url
    # the return_facility_url returns the RECDATA that contains JSON data in the form
    # EntityLinkID:... LinkType:... ... URL:
    # want to access the URL attribute, so thats why syntax url[0].get("URL") is done
    # we do this as an exception because the return_facility_url may return no data with 
    # a successful response code still, so theres not index to index to; hence IndexError

    try:
        url = return_facility_url(facility_id)
        url = url[0].get("URL")
    except IndexError:
        url = ""
   
  

    return render(request, "facility_detail.html", {"campsite": campsite, "city": city, "state": state, "address": address, 'url': url})

# function for saving a facility to a users profile
def save_facility(request, facility_id):
    # first, we get the user based on their username 
    # this CampUser model is located in users/models.py; this is where 
    #Im getting the data from 
    user = CampUser.objects.get(username=request.user.username)


    # make API call to get facility
    testfacility = return_facility_detail(facility_id)
    # get facility details from api
    
    name = testfacility["FacilityName"]
    type = testfacility["FacilityTypeDescription"]
    acessibility_txt = testfacility["FacilityAccessibilityText"]
    ada = testfacility["FacilityAdaAccess"]
    phone = testfacility["FacilityPhone"]
    email = testfacility["FacilityEmail"]
    desc = testfacility["FacilityDescription"]
    reservable = True
    # temp for now 
    url = "thisisanurl"
    location = "location"

        # create the saved facility (or get it if it already exists in user profile)
    facility, created = Facility.objects.get_or_create(
        # the facility id is passed in, so thats why we use it directly
        # all other attributes are passed in from the html template facility_detail.html
        # thats why we use request.GET with the appropriate name 

        f_id=facility_id,
        defaults={
            "name": name,
            "location": location,
            "type": type,
            "accessibility_txt": acessibility_txt,
            "ada_accessibility": ada,
            "phone": phone,
            "email": email,
            "description": desc,
            "reservable": reservable,
            "url": url
            
        }
        
    )
    


    '''
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
            "description": request.GET.get("description"),
            "reservable": (request.GET.get("reservable", "").lower()) == 'true',
            "url": request.GET.get("url")
            
        }
        
    )'
    '''
    

    # add this facility to user's favorited_loc attribute
    # (but really this is an attribute of UserProfile which is an attribute of user... have 
    # to ask Zach more about this... )
    user.userprofile.favorited_loc.add(facility)
    # redirects to user profile that shows all favorited campsites 
    return redirect("user_profile")


# this gets the user creation form for CampUser - uses the form created in forms.py
# redirects to the root directory upon completion
def register_view(request):

    if request.method == "POST":
        form = CampUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")
    else:    
        form = CampUserCreationForm()
    return render(request, "users/register.html", { "form": form})

# this currently gets the users profile and outputs favorite locations
# functionality to add amenities will be updated here
@login_required
def user_profile(request):
    # retrieve the users profile
    prof = UserProfile.objects.get(user=request.user)

    # retrieve favorited location IDs
    favorite_loc = prof.favorited_loc.all()

    # retrieve user preferences, or create them if they don't exist yet
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)

    # context will be sent to the return request with the users profile and favorite locations
    # available locations are currently being set as a way to test adding favorite locations
    context = {
        'user_profile': prof,
        'favorite_loc': favorite_loc,
        'preferences': preferences,
    }

    return render(request, 'users/profile.html', context)


# sorry Zach, had to make own manual view for logging out user. couldnt figure out why orig code not working 
# log out the user
def logoutUser(request):
    logout(request)
    # after logging out returns user to landing page 
    return redirect('index')
 
# this allows users to edit their user preferences
@login_required
def edit_preferences(request):
    # get user
    user = request.user

    # get users preferences if they exist; if they dont, create them
    preferences, created = UserPreferences.objects.get_or_create(user=user)

    if request.method == "POST":
        form = UserPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            return redirect("user_profile")
    else:
        form = UserPreferenceForm(instance=preferences)

    return render(request, "users/edit_preferences.html", {"form": form})

    


