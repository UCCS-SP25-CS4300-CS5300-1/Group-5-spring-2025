# this contains the user creation form for a CampUser

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.forms import ModelForm

# custom creation form for use with CampUser
class CampUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['username','password1','password2']

class UserPreferenceForm(ModelForm):
    class Meta:
        model = UserPreferences
        fields = ['campground', 'rangerstation', 'hotel', 'trail', 'reservable' ]
