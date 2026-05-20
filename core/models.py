from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import Workout


class UserProfile(models.Model):
    GENDER_CHOICES = [("M", "Male"), ("F", "Female")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    weight = models.FloatField()
    height = models.FloatField()
    activity_level = models.CharField(max_length=100)  # low, medium, high
    daily_calorie_limit = models.PositiveIntegerField(default=2000)

    def __str__(self):
        return self.user.get_username()


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    calories = models.PositiveIntegerField()
    protein = models.FloatField()
    fat = models.FloatField()
    carbs = models.FloatField()
    goal_type = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes",
    )

    def __str__(self):
        return self.name


class WorkoutTracker(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "workout", "date"], name="uniq_user_workout_date"
            )
        ]


class WaterTracker(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    amount = models.PositiveIntegerField()  # ml

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="uniq_user_water_date")
        ]


class KcalTracker(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    calories = models.PositiveIntegerField()
    protein = models.FloatField()
    fat = models.FloatField()
    carbs = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="uniq_user_kcal_date")
        ]


class MealSchedule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meal_type = models.CharField(max_length=100)
    time = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "meal_type", "time"], name="uniq_user_meal_time"
            )
        ]


class GoalTest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    goal = models.CharField(max_length=255)


class ProgressTracker(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    planned = models.FloatField()
    actual = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"], name="uniq_user_progress_date"
            )
        ]


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    text = models.CharField(max_length=255)
    important = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    source_key = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "source_key"],
                name="uniq_user_notification_source_key",
            )
        ]

    def __str__(self):
        return f"{self.user_id}: {self.text[:40]}"
