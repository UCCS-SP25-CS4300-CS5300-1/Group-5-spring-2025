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


# this gets the user creation form for CampUser - uses the form created in forms.py
# redirects to the root directory upon completion
def register_view(request):

    if request.method == "POST":
        form = CampUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")
    else:    
        form = UserCreationForm()
    return render(request, "home/register.html", { "form": form})

# this currently gets the users profile and outputs favorite locations
# functionality to add amenities will be updated here
@login_required
def user_profile(request):
    # retrieve the users profile
    prof = UserProfile.objects.get(user=request.user)

    # retrieve favorited location IDs
    favorite_loc = prof.favorited_loc.all()

    # getting previously favorited locations
    # Piper editing: dont need to loop through favorite_loc; favorite_loc holds all facility instances
    '''
    favorite_loc = []
    for loc in favorited_loc_id:
        loc_details = return_facility_detail(loc.f_id)
        if loc_details:
            favorite_loc.append(loc_details)'
    '''

    # getting available locations to prepare to add new favorites
    location = 'denver'
    available_loc = search_facilities(location)

    # adding new favorite campsites
    if request.method == 'POST':
        favorite_ids = request.POST.getlist('favorite_loc')
        for new_loc_id in favorite_ids:
            try:
                loc = Facility.objects.get(f_id=new_loc_id)
                prof.favorited_loc.add(loc)
            except Facility.DoesNotExist:
                print(f"Facility with f_id {new_loc_id} does not exist.")
        return redirect('user_profile')    

    # context will be sent to the return request with the users profile and favorite locations
    # available locations are currently being set as a way to test adding favorite locations
    context = {
        'user_profile': prof,
        'favorite_loc': favorite_loc,
        'available_loc': available_loc, 
    }

    return render(request, 'home/profile.html', context)


# sorry Zach, had to make own manual view for logging out user. couldnt figure out why orig code not working 
# log out the user
def logoutUser(request):
    logout(request)
    # after logging out returns user to landing page 
    return redirect('index')
 