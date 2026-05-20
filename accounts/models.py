from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone


class CustomUser(AbstractUser):
    age = models.IntegerField(null=True, blank=True)
    gender = models.IntegerField(null=True, blank=True)


class Profile(models.Model):
    GOAL_WEIGHT_LOSS = "weight_loss"
    GOAL_WEIGHT_GAIN = "weight_gain"
    GOAL_MAINTENANCE = "maintenance"
    GOAL_CHOICES = (
        (GOAL_WEIGHT_LOSS, "Weight Loss"),
        (GOAL_WEIGHT_GAIN, "Weight Gain"),
        (GOAL_MAINTENANCE, "Maintenance"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    activity_level = models.CharField(max_length=50, blank=True)
    goal = models.CharField(
        max_length=20,
        choices=GOAL_CHOICES,
        default=GOAL_MAINTENANCE,
    )
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Profile of {self.user.username}"


class RecipeQuerySet(models.QuerySet):
    def search(self, keyword):
        if not keyword:
            return self
        return self.filter(name_recipe__icontains=keyword.strip())

    def by_goal(self, goal_type):
        if not goal_type:
            return self
        return self.filter(goal_type__iexact=goal_type.strip())

    def by_calories(self, calories_min=None, calories_max=None):
        calories_query = Q()
        if calories_min is not None:
            calories_query &= Q(calories__gte=calories_min)
        if calories_max is not None:
            calories_query &= Q(calories__lte=calories_max)
        return self.filter(calories_query)

    def by_macros(
        self,
        protein_min=None,
        protein_max=None,
        fat_min=None,
        fat_max=None,
        carbs_min=None,
        carbs_max=None,
    ):
        macros_query = Q()
        if protein_min is not None:
            macros_query &= Q(protein__gte=protein_min)
        if protein_max is not None:
            macros_query &= Q(protein__lte=protein_max)
        if fat_min is not None:
            macros_query &= Q(fat__gte=fat_min)
        if fat_max is not None:
            macros_query &= Q(fat__lte=fat_max)
        if carbs_min is not None:
            macros_query &= Q(carbs__gte=carbs_min)
        if carbs_max is not None:
            macros_query &= Q(carbs__lte=carbs_max)
        return self.filter(macros_query)


class Recipe(models.Model):
    class GoalType(models.TextChoices):
        WEIGHT_LOSS = "weight_loss", "Weight Loss"
        MUSCLE_GAIN = "muscle_gain", "Muscle Gain"
        MAINTENANCE = "maintenance", "Maintenance"

    name_recipe = models.CharField(max_length=255, db_index=True)
    calories = models.PositiveIntegerField(db_index=True)
    protein = models.FloatField(db_index=True)
    fat = models.FloatField(db_index=True)
    carbs = models.FloatField(db_index=True)
    goal_type = models.CharField(
        max_length=20,
        choices=GoalType.choices,
        default=GoalType.MAINTENANCE,
        db_index=True,
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ("name_recipe",)

    def __str__(self):
        return self.name_recipe


class WorkoutQuerySet(models.QuerySet):
    def by_type(self, workout_type):
        if not workout_type:
            return self
        return self.filter(category__iexact=workout_type.strip())

    def by_duration_mode(self, duration_mode):
        if duration_mode == "under_30":
            return self.filter(duration_minutes__lt=30)
        if duration_mode == "over_60":
            return self.filter(duration_minutes__gt=60)
        return self

    def by_duration_range(self, duration_min=None, duration_max=None):
        duration_query = Q()
        if duration_min is not None:
            duration_query &= Q(duration_minutes__gte=duration_min)
        if duration_max is not None:
            duration_query &= Q(duration_minutes__lte=duration_max)
        return self.filter(duration_query)


class Workout(models.Model):
    class Category(models.TextChoices):
        CARDIO = "cardio", "Cardio"
        STRENGTH = "strength", "Strength"
        STRETCHING = "stretching", "Stretching"

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    name = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        db_index=True,
    )
    duration_minutes = models.PositiveIntegerField(
        help_text="Workout duration in minutes.",
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        db_index=True,
    )
    media_url = models.URLField(
        blank=True,
        help_text="Optional video/photo URL for the workout.",
    )
    calories_burned = models.PositiveIntegerField(
        default=0,
        help_text="Estimated calories burned per workout session.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_workouts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    objects = WorkoutQuerySet.as_manager()

    def __str__(self):
        return self.name
