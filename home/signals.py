# signals handles the automatic creation of a UserProfile whenever a CampUser is created

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CampUser
from .views import UserProfile


# send a signal to create a user profile whenever a user is created
@receiver(post_save, sender=CampUser)
def create_user_prof(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
