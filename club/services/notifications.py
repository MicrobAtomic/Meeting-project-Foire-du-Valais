"""Persistent notification queue. A successful SMTP handoff is not proof of delivery or reading."""
import smtplib
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import transaction
from django.db.models import F, Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from sesame.utils import get_query_string

from club.models import RSVP, EmailPreferences, Event, InvitationRequest, Member, NotificationCampaign, NotificationDelivery
from club.services.auth_links import email_language
from club.services.membership import require_staff

Kind = NotificationCampaign.Kind
Status = NotificationDelivery.Status


def preferences(member):
    # In particular, preview/GET operations must not create preference rows.
    return EmailPreferences.objects.filter(member=member).first() or EmailPreferences(member=member)


def private_url(name, *args):
    return settings.PUBLIC_BASE_URL + reverse(name, args=args)


def queue_recipients(campaign, recipients, now=None):
    now = now or timezone.now()
    NotificationDelivery.objects.bulk_create(
        [NotificationDelivery(campaign=campaign, recipient=member, next_attempt_at=now) for member in recipients], ignore_conflicts=True,
    )


def queue_welcome(invitation):
    campaign, created = NotificationCampaign.objects.get_or_create(
        scope_key=f"invitation:{invitation.pk}:welcome", defaults={"kind": Kind.WELCOME, "invitation": invitation},
    )
    if created:
        queue_recipients(campaign, [invitation.member])
    return campaign


@transaction.atomic
def publish_event(event_id, actor):
    require_staff(actor)
    event = Event.objects.select_for_update().get(pk=event_id)
    if event.is_published:
        return NotificationCampaign.objects.filter(scope_key=f"event:{event.pk}:announcement").first()
    now = timezone.now()
    if (not event.title.strip() or not event.location.strip() or event.starts_at <= now or event.cancelled_at
            or (event.rsvp_deadline and not now < event.rsvp_deadline <= event.starts_at)):
        raise ValidationError(_("Vérifie le titre, le lieu, la date future et la fin des réponses avant publication."))
    event.is_published, event.published_at = True, now
    event.save(update_fields=["is_published", "published_at"])
    campaign = NotificationCampaign.objects.create(kind=Kind.ANNOUNCEMENT, scope_key=f"event:{event.pk}:announcement", event=event)
    recipients = Member.objects.filter(user__is_active=True).exclude(user__email="").filter(
        Q(email_preferences__isnull=True) | Q(email_preferences__event_announcements=True)
    )
    queue_recipients(campaign, recipients)
    return campaign


@transaction.atomic
def cancel_event(event_id, actor):
    require_staff(actor)
    event = Event.objects.select_for_update().get(pk=event_id)
    if not event.cancelled_at:
        event.cancelled_at = timezone.now()
        event.save(update_fields=["cancelled_at"])
        event.notification_campaigns.update(cancelled_at=event.cancelled_at)
    return event


def reminder_eligible(member, event, now):
    prefs = preferences(member)
    if not prefs.event_announcements or not prefs.event_reminders or RSVP.objects.filter(member=member, event=event).exists():
        return False
    sent = NotificationDelivery.objects.filter(recipient=member, campaign__event=event, status=Status.SENT)
    if not sent.filter(campaign__kind=Kind.ANNOUNCEMENT).exists() or sent.filter(campaign__kind=Kind.REMINDER).count() >= 2:
        return False
    return not sent.filter(sent_at__gt=now - timedelta(hours=72)).exists()


def prepare_reminders(now=None, dry_run=False):
    now = now or timezone.now()
    due = 0
    for event in Event.objects.filter(is_published=True, cancelled_at__isnull=True, starts_at__gt=now, published_at__isnull=False):
        if (event.rsvp_deadline or event.starts_at) <= now:
            continue
        stages = [days for days in (14, 3) if event.published_at <= event.starts_at - timedelta(days=days) <= now]
        if not stages:
            continue
        stage = min(stages)  # Only the latest due stage after a scheduler interruption.
        members = [member for member in Member.objects.filter(user__is_active=True).exclude(user__email="")
                   if reminder_eligible(member, event, now)]
        scope = f"event:{event.pk}:reminder:{stage}"
        existing = NotificationDelivery.objects.filter(campaign__scope_key=scope).values_list("recipient_id", flat=True)
        members = [member for member in members if member.pk not in set(existing)]
        due += len(members)
        if members and not dry_run:
            with transaction.atomic():
                campaign, _created = NotificationCampaign.objects.get_or_create(
                    scope_key=scope, defaults={"kind": Kind.REMINDER, "event": event},
                )
                queue_recipients(campaign, members, now=now)
    return due


def eligible(delivery, now):
    member, campaign = delivery.recipient, delivery.campaign
    if not member.user.is_active or not member.user.email or campaign.cancelled_at:
        return False
    if campaign.kind == Kind.WELCOME:
        return bool(campaign.invitation_id and campaign.invitation.member_id == member.pk
                    and campaign.invitation.status == InvitationRequest.Status.ACCEPTED)
    if campaign.kind == Kind.DIGEST:
        from club.services.digests import digest_members
        return preferences(member).monthly_digest and bool(digest_members(campaign, member))
    if campaign.kind in (Kind.ANNOUNCEMENT, Kind.REMINDER):
        event = campaign.event
        if not event or not event.is_published or event.cancelled_at or min(event.starts_at, event.rsvp_deadline or event.starts_at) <= now:
            return False
        if not preferences(member).event_announcements:
            return False
        if campaign.kind == Kind.REMINDER:
            if campaign.scope_key.endswith(":14") and now >= event.starts_at - timedelta(days=3):
                return False
            return reminder_eligible(member, event, now)
        return True
    return False


def build_message(delivery, connection):
    member, campaign = delivery.recipient, delivery.campaign
    with translation.override(email_language(member)):
        context = {"name": member.first_name, "site_name": settings.SITE_NAME,
                   "preferences_url": private_url("club:profile_edit") + "#preferences-email"}
        if campaign.kind == Kind.WELCOME:
            context.update(link=private_url("magic_login") + get_query_string(member.user), minutes=settings.SESAME_MAX_AGE // 60)
            subject, template = _("Bienvenue au Club des Affaires"), "welcome"
        elif campaign.kind == Kind.DIGEST:
            from club.services.digests import digest_members, unsubscribe_token
            members = digest_members(campaign, member)
            context.update(previews=[{"name": candidate.full_name, "company": candidate.company,
                "sector": candidate.get_sector_display(),
                "teaser": candidate.digest_teaser if len(candidate.digest_teaser) <= 80 else candidate.digest_teaser[:79] + "…",
                "url": private_url("club:member_detail", candidate.pk)} for candidate in members[:4]],
                remaining=max(len(members) - 4, 0), album_url=private_url("club:album"),
                unsubscribe_url=private_url("club:email_unsubscribe", unsubscribe_token(member)))
            subject = _("Un nouveau visage au Club !") if len(members) == 1 else _("De nouveaux visages au Club !")
            context["subject"] = subject
            template = "digest"
        else:
            event = campaign.event
            context.update(event=event, link=private_url("club:event_detail", event.pk),
                           date=date_format(timezone.localtime(event.starts_at), "DATETIME_FORMAT"))
            subject = (_("Nouvel événement : %(title)s") if campaign.kind == Kind.ANNOUNCEMENT
                       else _("Ta réponse pour : %(title)s")) % {"title": event.localized_title}
            template = "event"
        message = EmailMultiAlternatives(subject, render_to_string(f"emails/{template}.txt", context),
                                         None, [member.user.email], connection=connection)
        message.attach_alternative(render_to_string(f"emails/{template}.html", context), "text/html")
    return message


def claim_delivery(pk, now=None):
    now = now or timezone.now()
    with transaction.atomic():
        changed = NotificationDelivery.objects.filter(pk=pk, status__in=[Status.PENDING, Status.FAILED],
            attempts__lt=3, next_attempt_at__lte=now).update(status=Status.SENDING, claimed_at=now, attempts=F("attempts") + 1)
    return bool(changed)


def retry_confirmed_failures(queryset):
    return queryset.filter(status=Status.FAILED, attempts__lt=3).update(next_attempt_at=timezone.now())


def process_notifications(limit=50, dry_run=False, now=None):
    now = now or timezone.now()
    pending = NotificationDelivery.objects.filter(status__in=[Status.PENDING, Status.FAILED],
                                                   attempts__lt=3, next_attempt_at__lte=now)
    if dry_run:
        from club.services.digests import prepare_digest
        return {"queued": pending.count(), "reminders_due": prepare_reminders(now, dry_run=True),
                "digest_due": prepare_digest(now, dry_run=True), "sent": 0}
    if not settings.NOTIFICATIONS_ENABLED:
        raise ValidationError("NOTIFICATIONS_ENABLED=0")
    if settings.DEMO_MODE and settings.EMAIL_BACKEND not in (
        "django.core.mail.backends.locmem.EmailBackend", "django.core.mail.backends.console.EmailBackend",
        "django.core.mail.backends.dummy.EmailBackend", "django.core.mail.backends.filebased.EmailBackend",
    ):
        raise ValidationError("SMTP is disabled in demo mode")
    NotificationDelivery.objects.filter(status=Status.SENDING, claimed_at__lt=now - timedelta(minutes=15)).update(
        status=Status.UNCERTAIN, last_error_code="abandoned_claim")
    prepare_reminders(now)
    from club.services.digests import prepare_digest
    prepare_digest(now)
    results = {"sent": 0, "skipped": 0, "failed": 0, "uncertain": 0}
    connection = get_connection(fail_silently=False)
    try:
        # A refused connection occurs before any handoff; pending deliveries remain unclaimed.
        connection.open()
        for pk in list(pending.order_by("next_attempt_at", "pk").values_list("pk", flat=True)[:limit]):
            if not claim_delivery(pk, now):
                continue
            delivery = NotificationDelivery.objects.select_related("recipient__user", "campaign__event", "campaign__invitation").get(pk=pk)
            if not eligible(delivery, timezone.now()):
                delivery.status = Status.SKIPPED
            else:
                try:
                    accepted = build_message(delivery, connection).send(fail_silently=False)
                    if accepted != 1:
                        raise smtplib.SMTPRecipientsRefused({})
                except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError,
                        smtplib.SMTPAuthenticationError) as error:
                    delivery.status = Status.FAILED
                    delivery.last_error_code = type(error).__name__
                    delivery.next_attempt_at = now + timedelta(minutes=15 if delivery.attempts == 1 else 60)
                except Exception as error:
                    delivery.status = Status.UNCERTAIN
                    delivery.last_error_code = type(error).__name__[:40]
                else:
                    delivery.status, delivery.sent_at = Status.SENT, timezone.now()
                    if delivery.campaign.kind == Kind.WELCOME:
                        InvitationRequest.objects.filter(pk=delivery.campaign.invitation_id).update(welcome_sent_at=delivery.sent_at)
            delivery.save(update_fields=["status", "next_attempt_at", "sent_at", "last_error_code"])
            results[delivery.status] += 1
    finally:
        connection.close()
    return results
