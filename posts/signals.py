import os
from django.db import models
from django.db.models.signals import post_delete,pre_save
from django.dispatch import receiver
from .models import BlogPost  # adjust if in signals.py
from django.core.files.storage import default_storage

@receiver(post_delete, sender=BlogPost)
def delete_featured_image_file(sender, instance, **kwargs):
    """
    Deletes the featured_image file from the filesystem
    when the BlogPost object is deleted.
    """
    if instance.featured_image:
        if os.path.isfile(instance.featured_image.path):
            os.remove(instance.featured_image.path)


@receiver(pre_save, sender=BlogPost)
def delete_old_featured_image_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return  # new instance, no old file

    try:
        old_instance = BlogPost.objects.get(pk=instance.pk)
    except BlogPost.DoesNotExist:
        return

    old_file = old_instance.featured_image
    new_file = instance.featured_image

    if old_file and old_file != new_file:
        if default_storage.exists(old_file.name):
            default_storage.delete(old_file.name)
