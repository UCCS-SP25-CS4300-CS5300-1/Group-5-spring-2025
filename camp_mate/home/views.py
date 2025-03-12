from django.shortcuts import render
from .utils import *

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
    return render(request, "facility_detail.html", {"campsite": campsite})