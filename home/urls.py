from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # path function defines a url pattern
    #'' is empty to represent based path to app
    # views.index is the function defined in views.py
    # name='index' parameter is to dynamically create url
    # example in html <a href="{% url 'index' %}">Home</a>.
    path("", views.index, name="index"),
    path("search/", views.search_view, name="search"),
    path("facility/<str:facility_id>/", views.facility_detail, name="facility_detail"),
    path("save/<str:facility_id>/", views.save_facility, name="save_facility"),
    path("edit_preferences/", views.edit_preferences, name="edit_preferences"),
    path(
        "delete_review/<str:facility_id>/",
        views.delete_facility,
        name="delete_facility",
    ),
    # FOR TRIP DETAILS
    path("trip/preview/", views.trip_preview, name="trip_preview"),
    path("trip/confirm/", views.confirm_trip, name="confirm_trip"),
    path("trip/cancel/", views.cancel_trip, name="cancel_trip"),
    path("trip/<int:trip_id>/", views.trip_detail, name="trip_detail"),
    path("trip/<int:trip_id>/pdf/", views.trip_detail_pdf, name="trip_detail_pdf"),
    path(
        "trip/create/<str:facility_id>/",
        views.create_trip_async,
        name="create_trip_async",
    ),
    path("trip/edit/<int:trip_id>/", views.edit_trip, name="edit_trip"),
    # FOR USER
    path("register/", views.register_view, name="register"),
    path("profile/", views.user_profile, name="user_profile"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("calendar/", views.calendar_view, name="current_calendar"),
    path(
        "calendar/<int:year>/<int:month>", views.calendar_view, name="traverse_calendar"
    ),
]
