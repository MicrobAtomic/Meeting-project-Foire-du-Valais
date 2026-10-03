from django.db import transaction
from django.db.models.signals import post_delete, pre_delete, post_save, pre_save
from django.dispatch import receiver

from club.models import RSVP, Event, Member, Substitute
from django.utils import timezone
from club.services.events import invalidate_event_plans
from club.services.substitutions import recalculate_guest_access
from club.services.photos import delete_unreferenced_photo


@receiver(post_delete, sender=Member)
def cleanup_member_photo(sender, instance, **kwargs):
    if instance.photo:
        name, storage = instance.photo.name, instance.photo.storage
        transaction.on_commit(lambda: delete_unreferenced_photo(name, storage), robust=True)


@receiver(pre_delete, sender=Member)
def anonymize_substitute_identity(sender, instance, **kwargs):
    if instance.kind == Member.Kind.GUEST:
        invitations = Substitute.objects.filter(guest=instance)
        for invitation in invitations.select_related("event"):
            if not invitation.event.is_past:
                invalidate_event_plans(invitation.event)
        invitations.update(first_name="", last_name="", email="", company="", job_title="")
        invitations.filter(event__starts_at__gt=timezone.now()).update(status=Substitute.Status.CANCELLED)


@receiver(post_delete, sender=Substitute)
def revoke_deleted_substitution(sender, instance, **kwargs):
    event = Event.objects.filter(pk=instance.event_id).first()
    if event and not event.is_past:
        invalidate_event_plans(event)
        if instance.guest_id and not Substitute.objects.filter(event=event, guest_id=instance.guest_id, status="approved").exists():
            RSVP.objects.filter(event=event, member_id=instance.guest_id).delete()
    guest = Member.objects.filter(pk=instance.guest_id, kind=Member.Kind.GUEST).first()
    if guest:
        recalculate_guest_access(guest)


@receiver(pre_save, sender=RSVP)
def remember_rsvp_status(sender, instance, **kwargs):
    instance._previous_status = RSVP.objects.filter(pk=instance.pk).values_list("status", flat=True).first() if instance.pk else None


@receiver(post_save, sender=RSVP)
@receiver(post_delete, sender=RSVP)
def invalidate_changed_presence(sender, instance, **kwargs):
    if "created" not in kwargs or kwargs["created"] or getattr(instance, "_previous_status", None) != instance.status:
        event = Event.objects.filter(pk=instance.event_id).first()
        if event and not event.is_past:
            invalidate_event_plans(event)


@receiver(pre_save, sender=Event)
def remember_event_dates(sender, instance, **kwargs):
    instance._previous_dates = Event.objects.filter(pk=instance.pk).values_list("starts_at", "cancelled_at").first() if instance.pk else None


@receiver(post_save, sender=Event)
def refresh_changed_event_access(sender, instance, created, **kwargs):
    if not created and getattr(instance, "_previous_dates", None) != (instance.starts_at, instance.cancelled_at):
        if not instance.is_past:
            invalidate_event_plans(instance)
        guests = Member.objects.filter(guest_invitations__event=instance, kind=Member.Kind.GUEST).distinct()
        for guest in guests:
            recalculate_guest_access(guest)
