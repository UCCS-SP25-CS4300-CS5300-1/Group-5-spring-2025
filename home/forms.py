# this contains the user creation form for a CampUser

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import TripDetails


# custom creation form for use with CampUser
class CampUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['username','password1','password2']




class TripDetailsForm(forms.ModelForm):
    class Meta:
        model = TripDetails
        fields = ['start_date', 'end_date', 'number_of_people']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }