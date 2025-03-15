# signals handles the automatic creation of a UserProfile whenever a CampUser is created

from .views import UserProfile
from .models import CampUser
from django.dispatch import receiver
from django.db.models.signals import post_save

# send a signal to create a user profile whenever a user is created
@receiver(post_save, sender=CampUser)
def create_user_prof(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)