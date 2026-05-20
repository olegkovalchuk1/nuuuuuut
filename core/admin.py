from django.contrib import admin

from .models import (
    GoalTest,
    KcalTracker,
    MealSchedule,
    Notification,
    ProgressTracker,
    Recipe,
    UserProfile,
    WaterTracker,
    Workout,
    WorkoutTracker,
)

admin.site.register(UserProfile)
admin.site.register(Recipe)
# admin.site.register(Workout)
admin.site.register(WorkoutTracker)
admin.site.register(WaterTracker)
admin.site.register(KcalTracker)
admin.site.register(MealSchedule)
admin.site.register(GoalTest)
admin.site.register(ProgressTracker)
admin.site.register(Notification)
