from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    age = models.IntegerField(null=True, blank=True)
    gender = models.IntegerField(null=True, blank=True)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    weight = models.FloatField()
    height = models.FloatField()
    activity_level = models.CharField(max_length=50)
    goal = models.CharField(max_length=100)

    def __str__(self):
        return f"Profile of {self.user.username}"