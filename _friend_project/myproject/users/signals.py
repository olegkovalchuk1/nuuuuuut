from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile

# сигнал спрацьовує після створення користувача
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Ств профіль пов'язаний із користувачем
        Profile.objects.create(user=instance)