from django.db import models
from django.contrib.auth.models import AbstractUser

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


class UserProfile(models.Model):
    user = models.OneToOneField(CampUser, on_delete=models.CASCADE)
    amenity_preference = models.ManyToManyField('Amenity', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Amenity(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name