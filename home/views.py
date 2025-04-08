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


#FOR AI STUFF
import openai
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from .models import TripDetails
from datetime import datetime
from .forms import TripDetailsForm
from django.shortcuts import render, get_object_or_404




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

    #associate trip details with the user
    trips = TripDetails.objects.filter(user=prof)

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
        'trips': trips,
    }

    return render(request, 'users/profile.html', context)


# sorry Zach, had to make own manual view for logging out user. couldnt figure out why orig code not working 
# log out the user
def logoutUser(request):
    logout(request)
    # after logging out returns user to landing page 
    return redirect('index')
 


@login_required
def create_trip_async(request, facility_id):
    if request.method == 'POST':
        facility = get_object_or_404(Facility, id=facility_id)
        form = TripDetailsForm(request.POST)
        if form.is_valid():
            trip_data = form.cleaned_data
            start_date = trip_data['start_date']
            end_date = trip_data['end_date']
            number_of_people = trip_data['number_of_people']
            
            # Generate packing list using OpenAI
            prompt = (
                f"Generate a packing list for {number_of_people} people camping at {facility.name} "
                f"from {start_date} to {end_date}. Focus on essentials. Consider the weather at this time and location. Give response in a comma separated list"
            )
            try:
                openai.api_key = settings.OPENAI_API_KEY
                ai_response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
                packing_list = ai_response.choices[0].message.content.strip()
            except Exception as e:
                print("OpenAI API error:", e)  # Log the error for debugging
                packing_list = "Tent, sleeping bag, food, water, flashlight"  # fallback
            
            # Create a temporary TripDetails instance
            trip = TripDetails.objects.create(
                user=request.user.userprofile,
                facility=facility,
                start_date=start_date,
                end_date=end_date,
                number_of_people=number_of_people,
                packing_list=packing_list,
            )
            
            # Store the trip id in session for preview
            request.session['trip_preview_id'] = trip.id

            # Return the URL for the trip preview page
            return redirect('trip_preview')
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()})
    return JsonResponse({'success': False, 'error': 'Invalid request'})




@login_required
def trip_preview(request):
    # Retrieve the trip preview id from session
    trip_id = request.session.get('trip_preview_id')
    if not trip_id:
        return redirect('index')  # or display an appropriate error message
    trip = get_object_or_404(TripDetails, id=trip_id)
    return render(request, 'users/trip_details_preview.html', {'trip': trip})

@login_required
def confirm_trip(request):
    # When the user clicks the "Save Trip" button, confirm the trip.
    # You could perform additional processing here if needed.
    if 'trip_preview_id' in request.session:
        del request.session['trip_preview_id']
    # Redirect to the user profile or trips list page after saving
    return redirect('user_profile')

@login_required
def cancel_trip(request):
    # When the user clicks "Start Over", delete the temporary trip and clear the session data.
    trip_id = request.session.get('trip_preview_id') or request.GET.get('trip_id')
    if trip_id:
        try:
            trip = TripDetails.objects.get(id=trip_id, user=request.user.userprofile)
            trip.delete()
        except TripDetails.DoesNotExist:
            pass
        # Safely delete the session key if it exists and matches
        if request.session.get('trip_preview_id') == int(trip_id):
            del request.session['trip_preview_id']
    return redirect('user_profile')  

@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(TripDetails, id=trip_id)
    return render(request, 'users/trip_details.html', {'trip': trip})