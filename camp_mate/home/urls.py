from django.urls import path, include
from . import views

urlpatterns = [
    #path function defines a url pattern
    #'' is empty to represent based path to app
    # views.index is the function defined in views.py
    # name='index' parameter is to dynamically create url
    # example in html <a href="{% url 'index' %}">Home</a>.
    path('', views.index, name='index'),
    path('search/', views.search_view, name='search'),
    path("facility/<str:facility_id>/", views.facility_detail, name="facility_detail")

]