# models has the CampUser class, Amenities class,
# and UserProfile class which each user has and contain a user's Amenities and Favorite Locations

from django.db import models
from django.contrib.auth.models import AbstractUser
from home.models import Facility

# inherited user to add preferences and campsites
class CampUser(AbstractUser):
    #just a test for now
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='campuser_set',
        blank=True
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name ='campuser_set',
        blank=True
    )
    
    preference = models.CharField(max_length=20)

# Amenities for a location
class Amenity(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# A user profile that contains amenity preferences and favorite locations
class UserProfile(models.Model):
    user = models.OneToOneField(CampUser, on_delete=models.CASCADE)
    amenity_pref = models.ManyToManyField('Amenity', blank=True)
    favorited_loc = models.ManyToManyField(Facility, blank=True)

    def __str__(self):
          return f"{self.user.username}'s Profile"
    