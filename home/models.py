from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Facility(models.Model):
    name = models.CharField(max_length=255)
    # for now, location will be character field.... address, city, state? from facility RIDB api schema
    location = models.CharField(max_length=255)  
    # Unique ID from RIDB API
    f_id = models.CharField(max_length=50, unique=True)  
    type = models.CharField(max_length=255)
    # RIDB api returns accessbility text.. can later add logic to make this true or false by detecting 
    # text such as "n/a" for false?...
    accessibility_txt = models.CharField(max_length=255, blank=True, null=True)
    # RIDB api also has Y or N schema for ADA accessbility
    ada_accessibility = models.CharField(max_length=3, blank=True, null=True)
    #reservation_url = models.CharField(max_length=255)
    # commenting out & may get rid of reservation url, API is kind of useless w/ returning the url, its basically 
    #nonexistent for all entries
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    description = models.TextField()

    def __str__(self):
        return self.name


# models has the CampUser class, Amenities class,
# and UserProfile class which each user has and contain a user's Amenities and Favorite Locations

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
    