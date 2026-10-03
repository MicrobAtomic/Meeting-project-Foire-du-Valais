"""One monthly batch with consent rechecked for each recipient."""
from datetime import datetime
from zoneinfo import ZoneInfo

from django.core import signing
from django.db import transaction
from django.utils import timezone

from club.models import DigestEntry, Member, NotificationCampaign

UNSUBSCRIBE_SALT = "club.monthly-digest.unsubscribe.v1"


def presentable_members():
    return Member.objects.filter(kind=Member.Kind.MEMBER, user__is_active=True, onboarding_done=True, visible_in_directory=True,
                                  admitted_at__isnull=False, email_preferences__allow_member_spotlight=True)


def digest_members(campaign, recipient):
    return list(presentable_members().filter(digest_entry__campaign=campaign).exclude(pk=recipient.pk))


def prepare_digest(now=None, dry_run=False):
    from club.services.notifications import queue_recipients
    now = now or timezone.now()
    local = now.astimezone(ZoneInfo("Europe/Zurich"))
    start = datetime(local.year, local.month, 1, tzinfo=ZoneInfo("Europe/Zurich"))
    scope = f"new-members:{local:%Y-%m}"
    if local < start.replace(hour=9) or NotificationCampaign.objects.filter(scope_key=scope).exists():
        return 0
    candidates = list(presentable_members().filter(admitted_at__lt=start, digest_entry__isnull=True))
    recipients = [member for member in Member.objects.filter(kind=Member.Kind.MEMBER, user__is_active=True, email_preferences__monthly_digest=True)
                  .exclude(user__email="") if any(candidate.pk != member.pk for candidate in candidates)]
    if not candidates or not recipients:
        return 0
    if dry_run:
        return len(recipients)
    with transaction.atomic():
        campaign, created = NotificationCampaign.objects.get_or_create(scope_key=scope,
            defaults={"kind": NotificationCampaign.Kind.DIGEST, "month": start.date()})
        if not created:
            return 0
        # A second month racing with this one cannot reserve a person twice.
        DigestEntry.objects.bulk_create([DigestEntry(member=member, campaign=campaign) for member in candidates], ignore_conflicts=True)
        recipients = [recipient for recipient in recipients if digest_members(campaign, recipient)]
        queue_recipients(campaign, recipients, now=now)
    return len(recipients)


def unsubscribe_token(member):
    return signing.dumps({"member": member.pk, "purpose": "monthly_digest"}, salt=UNSUBSCRIBE_SALT)


def unsubscribe_member_id(token):
    try:
        payload = signing.loads(token, salt=UNSUBSCRIBE_SALT, max_age=90 * 24 * 60 * 60)
        if payload.get("purpose") == "monthly_digest" and type(payload.get("member")) is int and payload["member"] > 0:
            return payload["member"]
    except (signing.BadSignature, ValueError, TypeError, AttributeError):
        pass
    return None
