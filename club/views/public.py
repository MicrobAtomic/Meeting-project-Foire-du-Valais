from datetime import timedelta

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from club.forms import InvitationRequestForm
from club.models import InvitationRequest, Member


@login_not_required
def landing(request):
    """Public showcase: only aggregate numbers, never a name."""
    members = Member.objects.filter(user__is_active=True)
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
    return Member.objects.filter(referral_code=code, user__is_active=True).first()


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
                invitation.save()
            return redirect("club:join_thanks")
    else:
        form = InvitationRequestForm()
    return render(request, "public/join.html", {"form": form, "referrer": referrer})


@login_not_required
def join_thanks(request):
    return render(request, "public/join_thanks.html")
