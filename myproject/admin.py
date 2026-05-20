from django.contrib import admin
from .models import CustomUser, Profile
from .models import FoodEntry

admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(FoodEntry)