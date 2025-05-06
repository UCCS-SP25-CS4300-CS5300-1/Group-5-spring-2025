import json
import re
from datetime import datetime
import openai
from openai.error import OpenAIError
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML

from home.models import Facility
from home.utils import (
    check_hazards,
    fetch_weather,
    return_facility_address,
    return_facility_detail,
    return_facility_url,
    search_facilities,
    get_facility_defaults,
    build_packing_prompt,
    generate_packing_list,
)

from .forms import CampUserCreationForm, UserPreferenceForm, TripDetailsForm
from .models import UserProfile, TripDetails
from .utils import UserPreferences, MyHTMLCalendar, settings, geocode_location


# Create your views here.
def index(request):
    """Renders the landing page of the application."""
    return render(request, "index.html")

#ABI UPDATED THIS
def search_view(request):
    """Processes a location search query and optionally applies user filters.
    Performs geocoding and returns search results rendered on a map.
    """
    query = request.GET.get("q")  # location name input
    apply_filters = request.GET.get("applyFilters") == "on"
    campsites = []

    if query:
        lat, lon = geocode_location(query)
        if lat and lon:
            campsites = search_facilities(
                lat=lat,
                lon=lon,
                user=request.user if apply_filters else None
            )
        else:
            # fallback: no geocode result, maybe use keyword search
            campsites = search_facilities(
                location=query,
                user=request.user if apply_filters else None
            )

    return render(
        request,
        "search_results.html",
        {"campsites": campsites, "query": query, "apply_filters": apply_filters},
    )


# view for facility detail
# returns a facility data type which attributes can be accessed by the dot operator
# attributes can be found in RIDB API Facility schema
# exp: get facility name: campsite.FacilityName
# also returns facility address and url
def facility_detail(request, facility_id):
    """ Renders the detail page for a specific facility."""
    campsite = return_facility_detail(facility_id)

    facility_address = return_facility_address(facility_id)

    url = return_facility_url(facility_id)

    return render(
        request,
        "facility_detail.html",
        {"campsite": campsite, "facility_address": facility_address, "url": url},
    )


# function for saving a facility to a users profile
def save_facility(request, facility_id):
    """Saves a facility to the user's profile."""
    user = request.user
    defaults = get_facility_defaults(facility_id)
    facility, _ = Facility.objects.update_or_create(
        f_id=facility_id, defaults=defaults
    )
    user.userprofile.favorited_loc.add(facility)
    return redirect("user_profile")


# this gets the user creation form for CampUser - uses the form created in forms.py
# redirects to the root directory upon completion
def register_view(request):
    """Handles user registration."""
    if request.method == "POST":
        form = CampUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")
    else:
        form = CampUserCreationForm()
    return render(request, "users/register.html", {"form": form})


# this currently gets the users profile and outputs favorite locations
# functionality to add amenities will be updated here
@login_required
def user_profile(request):
    """Renders the user's profile page with their favorite locations and preferences."""
    # retrieve the users profile
    prof = UserProfile.objects.get(user=request.user)

    # retrieve favorited location IDs
    favorite_loc = prof.favorited_loc.all()

    # retrieve user preferences, or create them if they don't exist yet
    preferences, _ = UserPreferences.objects.get_or_create(user=request.user)

    # associate trip details with the user
    trips = TripDetails.objects.filter(user=prof)

    # context will be sent to the return request with the users profile and favorite locations
    # available locations are currently being set as a way to test adding favorite locations
    context = {
        "user_profile": prof,
        "favorite_loc": favorite_loc,
        "preferences": preferences,
        "trips": trips,
    }

    return render(request, "users/profile.html", context)


# log out the user
def logout_user(request):
    """Logs out the user and redirects to the landing page."""
    logout(request)
    # after logging out returns user to landing page
    return redirect("index")


# this allows users to edit their user preferences
@login_required
def edit_preferences(request):
    """Allows users to edit their preferences."""
    # get user
    user = request.user

    # get users preferences if they exist; if they dont, create them
    preferences, _ = UserPreferences.objects.get_or_create(user=user)

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
    """Deletes a facility from the user's profile."""
    facility = Facility.objects.get(f_id=facility_id)

    if request.method == "POST":
        facility.delete()
        return redirect("user_profile")
    return redirect("user_profile")


@login_required
def create_trip_async(request, facility_id):
    """Creates a trip asynchronously and redirects to the trip preview."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"})

    # 1. gather facilities (just 2 locals)
    ids = request.POST.getlist("favorite_facilities")
    qs  = Facility.objects.filter(id__in=ids)
    if facility_id:
        qs |= Facility.objects.filter(id=facility_id)

    # 2. validate form (1 local)
    form = TripDetailsForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "error": form.errors.as_json()})

    cd = form.cleaned_data
    prompt = build_packing_prompt(qs, cd["start_date"], cd["end_date"], cd["number_of_people"])
    packing = generate_packing_list(prompt)

    # 3. create trip (2 locals)
    trip = TripDetails.objects.create(
        user=request.user.userprofile,
        start_date=cd["start_date"],
        end_date=cd["end_date"],
        number_of_people=cd["number_of_people"],
        packing_list=packing,
    )
    trip.facility.set(qs)
    request.session["trip_preview_id"] = trip.id

    return redirect("trip_preview")


@login_required
def trip_preview(request):
    """Renders the trip preview page."""
    # Retrieve the trip preview id from session
    trip_id = request.session.get("trip_preview_id")
    if not trip_id:
        return redirect("index")  # or display an appropriate error message
    trip = get_object_or_404(TripDetails, id=trip_id)
    return render(request, "users/trip_details_preview.html", {"trip": trip})


@login_required
def confirm_trip(request):
    """Confirms the trip and saves it to the user's profile."""
    # When the user clicks the "Save Trip" button, confirm the trip.
    # You could perform additional processing here if needed.
    if "trip_preview_id" in request.session:
        del request.session["trip_preview_id"]
    # Redirect to the user profile or trips list page after saving
    return redirect("user_profile")


@login_required
def cancel_trip(request):
    """Cancels the trip and deletes it from the user's profile."""
    # When the user clicks "Start Over", delete the temporary trip and clear the session data.
    trip_id = request.session.get("trip_preview_id") or request.GET.get("trip_id")
    if trip_id:
        try:
            trip = TripDetails.objects.get(id=trip_id, user=request.user.userprofile)
            trip.delete()
        except TripDetails.DoesNotExist:
            pass
        # Safely delete the session key if it exists and matches
        if request.session.get("trip_preview_id") == int(trip_id):
            del request.session["trip_preview_id"]
    return redirect("user_profile")


@login_required
def edit_trip(request, trip_id):
    """Allows users to edit an existing trip."""
    trip = get_object_or_404(TripDetails, id=trip_id)

    if request.method == "POST":
        # Get the submitted data
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        number_of_people = request.POST.get("number_of_people")
        facility_ids = request.POST.get("edit_facilities", "").split(",")

        # Update trip details
        trip.start_date = start_date
        trip.end_date = end_date
        trip.number_of_people = number_of_people
        facilities = Facility.objects.filter(id__in=facility_ids)
        trip.facility.set(facilities)

        trip.save()

        return redirect("trip_detail", trip_id=trip.id)
    return render(request, "edit_trip.html", {"trip": trip})


@csrf_exempt
def chatbot_view(request):
    """Handles chatbot interactions for camping trip assistance."""
    if request.method == "POST":
        body = json.loads(request.body)
        user_message = body.get("message", "")

        # Construct smart prompt with instruction for follow-ups
        prompt = f"""You are a helpful camping trip assistant. The user asked: "{user_message}"
        First, give a helpful, concise answer. Then, suggest 2-3 follow-up questions the user might ask next.
        List them clearly under the heading "Follow-up questions:", like this:
                Follow-up questions:
                - Question 1
                - Question 2
                - Question 3
                """

        try:
            openai.api_key = settings.OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-4", messages=[{"role": "user", "content": prompt}]
            )
            full_reply = response.choices[0].message.content.strip()

            # Extract follow-up questions using regex
            followups = re.findall(r"- (.+)", full_reply)

            # Clean + trim to under 100 chars, limit to 3
            cleaned_followups = [q.strip() for q in followups if len(q.strip()) <= 100][
                :3
            ]

            return JsonResponse({"reply": full_reply, "followups": cleaned_followups})

        except OpenAIError as e:
            return JsonResponse({"reply": f"Sorry, something went wrong: {str(e)}"})

    return JsonResponse({"reply": "This endpoint only accepts POST requests."})


@login_required
def trip_detail(request, trip_id):
    """Renders the trip details page."""
    trip = get_object_or_404(TripDetails, id=trip_id)

    facility = trip.facility.first()
    weather_forecast = []
    hazards_detected = False

    if facility and facility.latitude and facility.longitude:
        lat = facility.latitude
        lon = facility.longitude

        start_date = trip.start_date.strftime("%Y-%m-%d")
        end_date = trip.end_date.strftime("%Y-%m-%d")

        forecast = fetch_weather(lat, lon, start_date, end_date)
        hazards_found = check_hazards(forecast)
        hazards_detected = bool(hazards_found)
        weather_forecast = forecast

    return render(
        request,
        "users/trip_details.html",
        {
            "trip": trip,
            "weather_forecast": weather_forecast,
            "hazards_detected": hazards_detected,
        },
    )


@login_required
def trip_detail_pdf(request, trip_id):
    """Generates a PDF of the trip details."""
    trip = get_object_or_404(TripDetails, id=trip_id)
    packing_items = [
        item.strip()
        for item in trip.packing_list.split(",")
        if item.strip()
    ]

    facility = trip.facility.first()
    if facility and facility.latitude and facility.longitude:
        weather_forecast = fetch_weather(
            facility.latitude,
            facility.longitude,
            trip.start_date.strftime("%Y-%m-%d"),
            trip.end_date.strftime("%Y-%m-%d"),
        )
        hazards_detected = bool(check_hazards(weather_forecast))
    else:
        weather_forecast = []
        hazards_detected = False

    html = HTML(
        string=render_to_string(
            "users/trip_details_pdf.html",
            {
                "trip": trip,
                "user": request.user,
                "packing_items": packing_items,
                "weather_forecast": weather_forecast,
                "hazards_detected": hazards_detected,
            },
            request=request,
        ),
        base_url=request.build_absolute_uri("/"),
    )
    pdf_content = html.write_pdf()
    response = HttpResponse(pdf_content, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="trip_{trip.id}.pdf"'
    )
    return response


# generate calendar
# year and month are optional. this is bc user can navigate to next month if desired
@login_required
def calendar_view(request, year=None, month=None):
    """Renders a calendar view for the user's trips."""
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    # simple way to prevent index error
    if month != 12:
        month = month % 12
    trips = TripDetails.objects.filter(user=request.user.userprofile)

    # very naive logic for grabbing the next month and corresponding year
    # user can only traverse through one month at a time, backward or forward.
    if month == 12:
        nextmonth = 1
        nextyear = year + 1
    else:
        nextmonth = month + 1
        nextyear = year

    if month == 1:
        prevmonth = 12
        prevyear = year - 1
    else:
        prevmonth = month - 1
        prevyear = year

    # create calendar object
    # calendar object code can be viewed in utils.py
    cal_obj = MyHTMLCalendar(trips, year, month)
    # from calendar object, create html calendar for template
    html_cal = cal_obj.formatmonth()

    context = {
        "calendar": html_cal,
        "month": month,
        "year": year,
        "nextyear": nextyear,
        "nextmonth": nextmonth,
        "prevyear": prevyear,
        "prevmonth": prevmonth,
    }

    return render(request, "users/calendar.html", context)
