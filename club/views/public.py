import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from sesame.views import LoginView as SesameLoginView
from django.contrib.auth import logout
from club.services.substitutions import member_access_valid

from club.forms import InvitationRequestForm, MagicLinkRequestForm
from club.models import EmailPreferences, InvitationRequest, Member
from club.services.digests import unsubscribe_member_id
from club.services.auth_links import send_login_link

logger = logging.getLogger(__name__)


@login_not_required
def landing(request):
    """Public showcase: only aggregate numbers, never a name."""
    members = Member.objects.filter(user__is_active=True, kind=Member.Kind.MEMBER)
    context = {
        "member_count": members.count(),
        "sector_count": members.values("sector").distinct().count(),
    }
    return render(request, "public/landing.html", context)


def referrer_from(request):
    """The member whose personal link (?ref=CODE) was used. An unknown code is silently ignored."""
    code = request.GET.get("ref", "").strip().upper()
    if not code:
        return None
    return Member.objects.filter(referral_code=code, user__is_active=True, kind=Member.Kind.MEMBER).first()


@login_not_required
@require_http_methods(["GET", "POST"])
def join(request):
    """Public 'Demander une invitation' mini-form (no account needed, nothing about members is shown)."""
    referrer = referrer_from(request)
    if request.method == "POST":
        form = InvitationRequestForm(request.POST)
        if form.is_valid():
            recent = InvitationRequest.objects.filter(
                email__iexact=form.cleaned_data["email"], created_at__gte=timezone.now() - timedelta(hours=24)
            )
            # Bots (honeypot) and double submissions get the same "thank you": nothing is stored, nothing is revealed.
            if not form.is_bot and not recent.exists():
                invitation = form.save(commit=False)
                invitation.referred_by = referrer
                invitation.language = (get_language() or "fr")[:2]
                invitation.save()
            return redirect("club:join_thanks")
    else:
        form = InvitationRequestForm()
    return render(request, "public/join.html", {
        "form": form, "referrer": referrer, "membership_price": settings.MEMBERSHIP_PRICE,
    })


@login_not_required
def join_thanks(request):
    return render(request, "public/join_thanks.html")


@login_not_required
@require_http_methods(["GET", "POST"])
@never_cache
def email_unsubscribe(request, token):
    member_id = unsubscribe_member_id(token)
    done = False
    if member_id and request.method == "POST":
        EmailPreferences.objects.filter(member_id=member_id).update(monthly_digest=False)
        done = True
    return render(request, "public/email_unsubscribe.html", {"valid": bool(member_id), "done": done}, status=200 if member_id else 400)


class MagicLoginView(SesameLoginView):
    """The page an e-mailed link opens. Same behaviour as django-sesame (log in, then redirect), but an expired or
    already used link gets a friendly page (still a 403) instead of the bare 'forbidden' one."""

    def login_failed(self):
        return render(self.request, "registration/magic_link_expired.html", status=403)

    def login_success(self):
        member = getattr(self.request.user, "member", None)
        if member and not member_access_valid(member):
            logout(self.request)
            return self.login_failed()
        return super().login_success()


@login_not_required
@require_http_methods(["GET", "POST"])
def magic_link_request(request):
    """'Recevoir un lien de connexion par e-mail'. The answer is the same whether or not the address is a member's,
    so nobody can use this page to find out who is in the Club."""
    if request.method == "POST":
        form = MagicLinkRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            member = Member.objects.select_related("user").filter(user__email__iexact=email, user__is_active=True).first()
            # one e-mail per address and minute: this page cannot be used to flood someone's mailbox
            if member and member_access_valid(member) and cache.add(f"magic-link:{email}", True, timeout=60):
                try:
                    send_login_link(request, member)
                except Exception:  # a failing mail server must not reveal that the address exists
                    logger.exception("Could not send the login link")
            messages.info(request, _("Si cette adresse est connue, un lien vient d'être envoyé."))
            return redirect("club:magic_link_request")
    else:
        form = MagicLinkRequestForm()
    return render(request, "public/magic_link_request.html", {"form": form})
