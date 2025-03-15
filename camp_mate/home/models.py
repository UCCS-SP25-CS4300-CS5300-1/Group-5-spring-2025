from django.db import models

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