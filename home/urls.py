from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    #path function defines a url pattern
    #'' is empty to represent based path to app
    # views.index is the function defined in views.py
    # name='index' parameter is to dynamically create url
    # example in html <a href="{% url 'index' %}">Home</a>.
    path('', views.index, name='index'),
    path('search/', views.search_view, name='search'),
    path("facility/<str:facility_id>/", views.facility_detail, name="facility_detail"),
    path("save/<str:facility_id>/", views.save_facility, name="save_facility"),

    #FOR USER
    path('register/', views.register_view, name='register'),
    path('profile/', views.user_profile,name='user_profile'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout/', views.logoutUser, name='logout'),

]