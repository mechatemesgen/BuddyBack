from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Resource
import os

@receiver(pre_save, sender=Resource)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file when updating the resource file
    """
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).file
    except sender.DoesNotExist:
        return False

    new_file = instance.file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

@receiver(post_delete, sender=Resource)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file when corresponding Resource object is deleted
    """
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)