from django.contrib import admin

# Register your models here.
from django.contrib import admin


# Register your models here.
from .models import Facility, CampUser, UserProfile


admin.site.register(Facility)
admin.site.register(CampUser)
admin.site.register(UserProfile)
