from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudyGroup, GroupMembership

@receiver(post_save, sender=StudyGroup)
def add_creator_as_admin(sender, instance, created, **kwargs):
    if created:
        GroupMembership.objects.create(
            user=instance.creator,
            group=instance,
            role='ADMIN'
        )