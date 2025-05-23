from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserActivity

@receiver(post_save, sender=User)
def create_user_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(user=instance)