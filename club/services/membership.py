from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from club.models import EmailPreferences, InvitationRequest, Member, Sector


def require_staff(actor):
    if not (actor.is_active and actor.is_staff):
        raise PermissionDenied


@transaction.atomic
def accept_invitation(invitation_id, actor):
    require_staff(actor)
    invitation = InvitationRequest.objects.select_for_update().get(pk=invitation_id)
    if invitation.status == InvitationRequest.Status.ACCEPTED:
        if invitation.member_id:
            return invitation.member
        raise ValidationError(_("Demande déjà acceptée sans compte lié : rapprochement manuel nécessaire."))
    if invitation.member_id:
        raise ValidationError(_("Cette demande possède déjà un compte lié."))
    email = invitation.email.strip().lower()
    User = get_user_model()
    if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
        raise ValidationError(_("Un compte utilise déjà cette adresse : rapprochement manuel nécessaire."))
    try:
        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, password=None,
                                            first_name=invitation.first_name, last_name=invitation.last_name)
            member = Member.objects.create(
                user=user, first_name=invitation.first_name, last_name=invitation.last_name,
                company=invitation.company, job_title=invitation.job_title, sector=Sector.OTHER,
                member_since=timezone.localdate().year, admitted_at=timezone.now(),
                preferred_language=invitation.language, onboarding_done=False,
                speaks_fr=invitation.language == "fr", speaks_de=invitation.language == "de", speaks_en=invitation.language == "en",
            )
            EmailPreferences.objects.create(member=member)
            invitation.member = member
            invitation.status = InvitationRequest.Status.ACCEPTED
            invitation.save(update_fields=["member", "status"])
    except IntegrityError:
        raise ValidationError(_("Un compte utilise déjà cette adresse : rapprochement manuel nécessaire.")) from None
    return member
