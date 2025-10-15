from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, AppAccess

User = get_user_model()

@receiver(post_save, sender=User)
def assign_all_apps_to_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        profile, _ = Profile.objects.get_or_create(user=instance)
        all_apps = AppAccess.objects.all()
        profile.allowed_apps.set(all_apps)



