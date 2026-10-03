"""Separate identities and bounded access for approved substitute guests."""
from datetime import timedelta
import unicodedata

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max, Q
from django.utils import timezone
from django.utils.translation import gettext as _

from club.models import RSVP, EmailPreferences, Event, Member, NotificationCampaign, Substitute
from club.services.events import invalidate_event_plans
from club.services.membership import require_staff


def require_regular(member):
    if not member.user.is_active or member.kind != Member.Kind.MEMBER:
        raise PermissionDenied


def require_open_event(event):
    if not event.responses_open:
        raise ValidationError(_("Les réponses sont fermées pour cet événement."))


def valid_guest_invitations(member, now=None):
    now = now or timezone.now()
    return Substitute.objects.filter(guest=member, status=Substitute.Status.APPROVED,
        event__is_published=True, event__cancelled_at__isnull=True,
        event__starts_at__gt=now - timedelta(hours=settings.GUEST_ACCESS_HOURS))


def member_access_valid(member, now=None):
    now = now or timezone.now()
    if not member.user.is_active:
        return False
    return member.kind == Member.Kind.MEMBER or bool(member.guest_access_until and member.guest_access_until > now
                                                       and valid_guest_invitations(member, now).exists())


@transaction.atomic
def recalculate_guest_access(guest):
    if guest.kind != Member.Kind.GUEST:
        return
    user = get_user_model().objects.select_for_update().get(pk=guest.user_id)
    current = Member.objects.select_for_update().get(pk=guest.pk)
    latest = valid_guest_invitations(guest).aggregate(latest=Max("event__starts_at"))["latest"]
    guest.guest_access_until = latest + timedelta(hours=settings.GUEST_ACCESS_HOURS) if latest else None
    current.guest_access_until = guest.guest_access_until
    current.save(update_fields=["guest_access_until"])
    if not latest and user.is_active:
        user.is_active = False
        user.save(update_fields=["is_active"])
    guest.user.is_active = user.is_active


@transaction.atomic
def request_substitute(event_id, principal, data):
    require_regular(principal)
    event = Event.objects.select_for_update().get(pk=event_id)
    require_open_event(event)
    fields = {key: data[key] for key in ("first_name", "last_name", "email", "job_title", "speaks_fr", "speaks_de", "speaks_en", "preferred_language")}
    fields["email"] = fields["email"].strip().lower()
    if not any(fields[key] for key in ("speaks_fr", "speaks_de", "speaks_en")):
        raise ValidationError(_("Choisis au moins une langue parlée."))
    current = Substitute.objects.filter(event=event, member=principal).first()
    if current and current.status == Substitute.Status.APPROVED:
        raise ValidationError(_("Annule le remplacement validé avant de le modifier."))
    fields.update(company=principal.company, status=Substitute.Status.PENDING, guest=None, approved_at=None)
    substitute, _created = Substitute.objects.update_or_create(event=event, member=principal, defaults=fields)
    RSVP.objects.update_or_create(event=event, member=principal, defaults={"status": RSVP.Status.NO})
    invalidate_event_plans(event)
    return substitute


def identity_name(text):
    return unicodedata.normalize("NFKC", text).strip().casefold()


@transaction.atomic
def approve_substitute(substitute_id, actor):
    require_staff(actor)
    event_id = Substitute.objects.values_list("event_id", flat=True).get(pk=substitute_id)
    event = Event.objects.select_for_update().get(pk=event_id)
    substitute = Substitute.objects.select_for_update().select_related("member__user").get(pk=substitute_id)
    require_open_event(event)
    if substitute.member.kind != Member.Kind.MEMBER or not substitute.member.user.is_active:
        raise ValidationError(_("Le titulaire doit être un membre actif."))
    if substitute.status == Substitute.Status.APPROVED:
        if not substitute.guest_id:
            raise ValidationError(_("Le profil invité a été supprimé. Crée une nouvelle demande."))
        return substitute.guest
    if substitute.status != Substitute.Status.PENDING:
        raise ValidationError(_("Cette demande n'est plus en attente."))
    if substitute.company != substitute.member.company:
        raise ValidationError(_("Confirme que la personne représente la même entreprise."))
    email = substitute.email.strip().lower()
    users = list(get_user_model().objects.select_for_update().filter(Q(email__iexact=email) | Q(username__iexact=email)))
    try:
        with transaction.atomic():
            if users:
                if len(users) != 1:
                    raise ValidationError(_("Identité ambiguë : rapprochement manuel nécessaire."))
                user = users[0]
                guest = Member.objects.select_for_update().filter(user=user).first()
                if user.is_staff or user.is_superuser or not guest or guest.kind != Member.Kind.GUEST:
                    raise ValidationError(_("Cette adresse appartient à un membre ou au staff. Aucun compte ne sera converti."))
                if (identity_name(guest.first_name), identity_name(guest.last_name)) != (identity_name(substitute.first_name), identity_name(substitute.last_name)):
                    raise ValidationError(_("Les noms diffèrent du compte invité existant. Vérifie l'identité avant validation."))
            else:
                user = get_user_model().objects.create_user(username=email, email=email, password=None)
                guest = Member.objects.create(user=user, kind=Member.Kind.GUEST, first_name=substitute.first_name,
                    last_name=substitute.last_name, company=substitute.company, job_title=substitute.job_title,
                    sector=substitute.member.sector, speaks_fr=substitute.speaks_fr, speaks_de=substitute.speaks_de,
                    speaks_en=substitute.speaks_en, preferred_language=substitute.preferred_language,
                    member_since=timezone.localdate().year)
                EmailPreferences.objects.create(member=guest, event_announcements=False, event_reminders=False)
            if Substitute.objects.filter(event=event, guest=guest, status=Substitute.Status.APPROVED).exclude(pk=substitute.pk).exists():
                raise ValidationError(_("Cet invité représente déjà un autre membre à cet événement."))
            substitute.guest, substitute.status, substitute.approved_at = guest, Substitute.Status.APPROVED, timezone.now()
            substitute.save(update_fields=["guest", "status", "approved_at"])
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            recalculate_guest_access(guest)
            RSVP.objects.update_or_create(event=event, member=guest, defaults={"status": RSVP.Status.YES})
            RSVP.objects.update_or_create(event=event, member=substitute.member, defaults={"status": RSVP.Status.NO})
            invalidate_event_plans(event)
            from club.services.notifications import queue_recipients
            campaign, created = NotificationCampaign.objects.get_or_create(scope_key=f"substitute:{substitute.pk}:access",
                defaults={"kind": NotificationCampaign.Kind.GUEST_ACCESS, "substitute": substitute, "event": event})
            queue_recipients(campaign, [guest])
            if not created and campaign.cancelled_at:
                campaign.cancelled_at = None
                campaign.save(update_fields=["cancelled_at"])
                # Confirmed skipped access can be prepared again; sent/uncertain messages are never reset.
                campaign.deliveries.filter(status="skipped").update(status="pending", attempts=0, next_attempt_at=timezone.now())
    except IntegrityError:
        raise ValidationError(_("Conflit de validation : vérifie la demande et réessaie.")) from None
    return guest


@transaction.atomic
def cancel_substitute(event_id, principal, actor=None):
    if actor:
        require_staff(actor)
    else:
        require_regular(principal)
    event = Event.objects.select_for_update().get(pk=event_id)
    if actor:
        if event.is_past:
            raise ValidationError(_("Cet événement est déjà passé."))
    else:
        require_open_event(event)
    substitute = Substitute.objects.select_for_update().filter(event=event, member=principal).first()
    if not substitute or substitute.status == Substitute.Status.CANCELLED:
        return
    guest = substitute.guest
    substitute.status = Substitute.Status.CANCELLED
    substitute.save(update_fields=["status"])
    if guest:
        RSVP.objects.filter(event=event, member=guest).delete()
        recalculate_guest_access(guest)
    NotificationCampaign.objects.filter(substitute=substitute).update(cancelled_at=timezone.now())
    invalidate_event_plans(event)
