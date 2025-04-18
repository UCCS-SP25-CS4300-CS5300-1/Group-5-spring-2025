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
import requests


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
# returns a facility (called campsite) data type which attributes can be accessed by the dot operator
# attributes can be found in RIDB API Facility schema
# exp: get facility name: campsite.FacilityName
# also returns facility address and url 
def facility_detail(request, facility_id):
    campsite = return_facility_detail(facility_id)

    facility_address = return_facility_address(facility_id)

    url = return_facility_url(facility_id)
   

    return render(request, "facility_detail.html", {"campsite": campsite, "facility_address": facility_address,  'url': url})

# function for saving a facility to a users profile
def save_facility(request, facility_id):
    # first, we get the user based on their username 
    # this CampUser model is located in users/models.py; this is where 
    #Im getting the data from 
    user = CampUser.objects.get(username=request.user.username)

    # make API call to get facility: this returns a facility data type that we can extract attribute info from by getting value from key
    testfacility = return_facility_detail(facility_id)
    # get facility details from facility data type 
    name = testfacility["FacilityName"]
    type = testfacility["FacilityTypeDescription"]
    acessibility_txt = testfacility["FacilityAccessibilityText"]
    ada = testfacility["FacilityAdaAccess"]
    phone = testfacility["FacilityPhone"]
    email = testfacility["FacilityEmail"]
    desc = testfacility["FacilityDescription"]
    reservable = testfacility["Reservable"]
    url = return_facility_url(facility_id)
    location = return_facility_address(facility_id)

    # create the saved facility (or get it if it already exists in user profile)
    facility, created = Facility.objects.get_or_create(

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

    #associate trip details with the user
    trips = TripDetails.objects.filter(user=prof)

 


    # context will be sent to the return request with the users profile and favorite locations
    # available locations are currently being set as a way to test adding favorite locations
    context = {
        'user_profile': prof,
        'favorite_loc': favorite_loc,
        'preferences': preferences,
        'trips': trips,

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

    
# this allows users to delete a saved facility from their profile
@login_required
def delete_facility(request, facility_id):
    facility = Facility.objects.get(f_id = facility_id)

    if request.method == "POST":
        facility.delete()
        return redirect("user_profile")



@login_required
def create_trip_async(request, facility_id):
    if request.method == 'POST':
        # list of favorite facilities
        selected_facility_ids = request.POST.getlist('favorite_facilities')
        selected_facility = Facility.objects.filter(id__in=selected_facility_ids)

        # fetching the facility ID for the location pressed on user profile
        if facility_id:
            facility = get_object_or_404(Facility, id=facility_id)
            selected_facility = selected_facility | Facility.objects.filter(id=facility.id)

        form = TripDetailsForm(request.POST)
        if form.is_valid():
            trip_data = form.cleaned_data
            start_date = trip_data['start_date']
            end_date = trip_data['end_date']
            number_of_people = trip_data['number_of_people']
            
            # Generate packing list using OpenAI
            prompt = (
                f"Generate a packing list for {number_of_people} people camping at {", ".join([facility.name for facility in selected_facility])} "
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
                start_date=start_date,
                end_date=end_date,
                number_of_people=number_of_people,
                packing_list=packing_list,
            )
            
            #correctly setting the data for a Many to Many field
            trip.facility.set(selected_facility)

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
def edit_trip(request):


    return redirect('user_profile')

import requests

@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(TripDetails, id=trip_id)

    # Assume one facility per trip for simplicity (or average lat/lon for multiple)
    facility = trip.facility.first()
    weather_forecast = []
    hazards_detected = False

    if facility:
        lat = facility.latitude
        lon = facility.longitude

        # Format trip dates
        start_date = trip.start_date.strftime('%Y-%m-%d')
        end_date = trip.end_date.strftime('%Y-%m-%d')

        # Request weather forecast
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={start_date}&end_date={end_date}"
            f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&timezone=auto"
        )
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            daily = zip(
                data['daily']['time'],
                data['daily']['temperature_2m_max'],
                data['daily']['temperature_2m_min'],
                data['daily']['weathercode']
            )

            # Map weather codes to readable conditions
            code_map = {
                61: 'Moderate rainfall', 63: 'Heavy rain', 65: 'Very heavy rain',
                71: 'Moderate snowfall', 73: 'Heavy snowfall', 95: 'Thunderstorm',
                96: 'Thunderstorm w/ slight hail', 99: 'Thunderstorm w/ heavy hail',
                85: 'Heavy snow showers', 81: 'Violent rain showers',
                57: 'Dense freezing drizzle', 66: 'Heavy freezing rain',
                # Add others if needed
            }

            for date, tmax, tmin, code in daily:
                condition = code_map.get(code, "Unknown")
                weather_forecast.append({
                    'date': date,
                    'temp_max': round(tmax * 9/5 + 32),  # convert to F
                    'temp_min': round(tmin * 9/5 + 32),
                    'condition': condition
                })

            # Check for hazards
            hazards_found = check_hazards(weather_forecast)
            hazards_detected = len(hazards_found) > 0

    return render(request, 'users/trip_details.html', {
        'trip': trip,
        'weather_forecast': weather_forecast,
        'hazards_detected': hazards_detected
    })
