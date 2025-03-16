# views handles the user registration view and user profile view
# used with register.html and profile.html located within the templates

from django.shortcuts import render, redirect
from .models import UserProfile
from django.contrib.auth.forms import UserCreationForm
from home.utils import return_facility_detail
from django.contrib.auth.decorators import login_required
from .forms import CampUserCreationForm
from home.models import Facility
from home.utils import return_facility_detail, search_facilities
from django.contrib.auth import logout

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
    return render(request, "users/register.html", { "form": form})

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

    return render(request, 'users/profile.html', context)

# sorry Zach, had to make own manual view for logging out user. couldnt figure out why orig code not working 
# log out the user
def logoutUser(request):
    logout(request)
    # after logging out returns user to landing page 
    return redirect('index')
