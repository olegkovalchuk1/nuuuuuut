from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile
from .services import calculate_water_intake
from .services import calculate_bmr, calculate_tdee


# сигнал спрацьовує після створення користувача
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Ств профіль пов'язаний із користувачем
        Profile.objects.create(user=instance)


from .services import (
    calculate_water_intake,
    calculate_bmr,
    calculate_tdee,
    adjust_calories_for_goal
)

@receiver(post_save, sender=Profile)
def calculate_all_health_data(sender, instance, created, **kwargs):
    updates = {}

    # вода
    if instance.weight:
        water = calculate_water_intake(instance.weight)
        updates['water_intake'] = water

    # калорії
    if instance.weight and instance.height and instance.age:
        bmr = calculate_bmr(
            weight=instance.weight,
            height=instance.height,
            age=instance.age,
            gender=instance.gender
        )

        tdee = calculate_tdee(bmr, instance.activity_level)
        final = adjust_calories_for_goal(tdee, instance.goal)

        updates['bmr'] = bmr
        updates['daily_calories'] = final

    # один update = без циклів
    if updates:
        Profile.objects.filter(id=instance.id).update(**updates)