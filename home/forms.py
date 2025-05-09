# this contains the user creation form for a CampUser

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from .models import Facility,UserPreferences
from .models import TripDetails


# custom creation form for use with CampUser
class CampUserCreationForm(UserCreationForm):
    """Custom user creation form for the CampUser model."""
    class Meta:
        model = get_user_model()
        fields = ["username", "password1", "password2"]


class UserPreferenceForm(ModelForm):
    """Form for user preferences."""
    class Meta:
        model = UserPreferences
        fields = [
            "campground",
            "rangerstation",
            "hotel",
            "trail",
            "facility",
            "reservable",
        ]


class TripDetailsForm(forms.ModelForm):
    """Form for trip details."""
    facility = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Locations",
    )

    number_of_people = forms.TypedChoiceField(
        choices=[(i, str(i)) for i in range(1, 11)],  # Options 1 through 10
        coerce=int,  # This converts the submitted value to an integer
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = TripDetails
        fields = ["start_date", "end_date", "number_of_people"]
        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
