from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from club.models import Member
from club.services.photos import delete_unreferenced_photo


@receiver(post_delete, sender=Member)
def cleanup_member_photo(sender, instance, **kwargs):
    if instance.photo:
        name, storage = instance.photo.name, instance.photo.storage
        transaction.on_commit(lambda: delete_unreferenced_photo(name, storage))
