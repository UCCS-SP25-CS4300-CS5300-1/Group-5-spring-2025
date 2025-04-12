from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
# *** NEED TO ADD RESERVABLE & URL ATTRIBUTES... MAYBE ALSO INCORPORATE MEDIA TOO ***
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
    reservable = models.BooleanField(default=False)
    url =  models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name
    


class TripDetails(models.Model):
    # this is the user that created the trip
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    facility = models.ManyToManyField('Facility', blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    number_of_people = models.PositiveIntegerField(default=1)
    packing_list = models.TextField(blank=True, help_text="Comma-separated packing list items generated via AI.")
    

    def __str__(self):
        facilities = " ,".join([f.name for f in self.facility.a()])
        return f"{self.user.user.username}'s Trip to {facilities} on {self.start_date}"


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
    
    # this line of code is unneeded but removing it breaks a lot of tests, need to redesign tests when get the chance
    preference = models.CharField(max_length=20)

# A user profile that contains amenity preferences and favorite locations
class UserProfile(models.Model):
    user = models.OneToOneField(CampUser, on_delete=models.CASCADE)
    favorited_loc = models.ManyToManyField(Facility, blank=True)
    


    def __str__(self):
          return f"{self.user.username}'s Profile"
    

# User preferences 
class UserPreferences(models.Model):
    # the related_name param makes it so CampUser model can access user preferences 
    user = models.OneToOneField(CampUser, on_delete=models.CASCADE, related_name="preferences")
    campground = models.BooleanField(default=True)
    rangerstation = models.BooleanField(default=True)
    hotel = models.BooleanField(default=True)
    trail = models.BooleanField(default=True)
    facility = models.BooleanField(default=True)
    reservable = models.BooleanField(default=True)

    