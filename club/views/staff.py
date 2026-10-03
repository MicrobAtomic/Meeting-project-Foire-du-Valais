from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_http_methods

from club.decorators import staff_required
from club.forms import SeatingForm
from club.models import RSVP, Event, InvitationRequest, Match, SeatingPlan, Substitute, Tag
from club.services.bingo import event_stats
from club.services.events import attendees, generate_matches, generate_seating, with_attendee_counts
from club.services.notifications import cancel_event, publish_event
from club.services.federation import (
    active_connections,
    active_members,
    club_stats,
    degrees,
    isolated_members,
)
from club.services.milestones import club_progress
from club.services.qr import qr_svg
from club.ui import round_label

ISOLATED_SHOWN = 20


@staff_required
def dashboard(request):
    now = timezone.now()
    counts = degrees()
    isolated = sorted(isolated_members(), key=lambda m: (counts[m.pk], m.last_name, m.first_name))
    new_requests = InvitationRequest.objects.filter(status=InvitationRequest.Status.NEW).order_by("-created_at")
    stats = club_stats()
    context = {
        "stats": stats,
        "club_progress": club_progress(stats),
        "recent_connections": active_connections().filter(created_at__gte=now - timedelta(days=30)).count(),
        "new_recruits": active_members().filter(member_since=timezone.localdate().year).count(),
        "isolated": [(m, counts[m.pk]) for m in isolated[:ISOLATED_SHOWN]],
        "isolated_more": max(len(isolated) - ISOLATED_SHOWN, 0),
        "upcoming": with_attendee_counts(Event.objects.filter(starts_at__gte=now).order_by("starts_at")),
        "past": Event.objects.filter(starts_at__lt=now)
        .annotate(meetings=Count("connections"))
        .order_by("-starts_at"),
        "new_request_count": new_requests.count(),
        "new_requests": new_requests[:5],
    }
    return render(request, "staff/dashboard.html", context)


def matches_for_display(event):
    tags = {tag.slug: tag for tag in Tag.objects.all()}
    matches = Match.objects.filter(event=event).select_related("member_a", "member_b").order_by("-score", "pk")
    return [
        {
            "a": m.member_a,
            "b": m.member_b,
            "score": m.score,
            "likes": [tags[s] for s in m.shared_likes if s in tags],
            "dislikes": [tags[s] for s in m.shared_dislikes if s in tags],
        }
        for m in matches
    ]


def seating_for_display(plan):
    """[{'label': 'Entrée', 'tables': [{'number': 1, 'members': [Member, …]}, …]}, …]"""
    rounds = {}
    for seat in plan.assignments.select_related("member"):
        tables = rounds.setdefault(seat.round_index, {})
        tables.setdefault(seat.table_number, []).append(seat.member)
    return [
        {
            "label": round_label(index),
            "tables": [{"number": number, "members": members} for number, members in sorted(tables.items())],
        }
        for index, tables in sorted(rounds.items())
    ]


@staff_required
@require_http_methods(["GET", "POST"])
def event_tools(request, pk):
    event = get_object_or_404(Event, pk=pk)
    seating_form = SeatingForm()
    if request.method == "POST":
        action = request.POST.get("action")
        if action in ("publish", "cancel"):
            try:
                if action == "publish":
                    publish_event(event.pk, request.user)
                    messages.success(request, _("Annonce préparée. L'envoi est traité par la commande périodique."))
                else:
                    cancel_event(event.pk, request.user)
                    messages.info(request, _("Événement annulé. Contacte les inscrits via le processus habituel de l'équipe."))
            except ValidationError as error:
                messages.error(request, " ".join(error.messages))
            return redirect("club:staff_event", pk=event.pk)
        if action == "matches":
            count = generate_matches(event)
            messages.success(request, ngettext("%(count)s rencontre générée.", "%(count)s rencontres générées.", count) % {"count": count})
            return redirect("club:staff_event", pk=event.pk)
        if action != "seating":
            return HttpResponseBadRequest("Unknown action")
        if not event.has_seating:
            messages.error(request, _("Pas de repas assis pour cet événement : pas de plan de tables."))
            return redirect("club:staff_event", pk=event.pk)
        seating_form = SeatingForm(request.POST)
        if seating_form.is_valid():
            plan = generate_seating(event, **seating_form.cleaned_data)
            messages.success(
                request,
                _("Plan généré : %(new)s nouvelles paires, %(repeated)s répétition(s).")
                % {"new": plan.new_pairs, "repeated": plan.repeated_pairs},
            )
            return redirect("club:staff_event", pk=event.pk)
    plan = SeatingPlan.objects.filter(event=event).first()
    context = {
        "event": event,
        "attendee_count": attendees(event).count(),
        "seating_form": seating_form,
        "matches": matches_for_display(event),
        "plan": plan,
        "rounds": seating_for_display(plan) if plan else [],
        "substitutions": event.substitutes.select_related("member", "guest"),
        "bingo": event_stats(event) if event.has_bingo else None,
    }
    return render(request, "staff/event_tools.html", context)


BADGES_PER_PAGE = 8  # 2 columns x 4 rows on an A4 sheet


@staff_required
def badges(request, pk):
    """Printable name badges (A4, 2 x 4): first name, company, 'Parle-moi de…', and the QR code that opens the card."""
    event = get_object_or_404(Event, pk=pk)
    members = attendees(event).select_related("user").order_by("last_name", "first_name")
    badges = [
        (member, qr_svg(request.build_absolute_uri(reverse("club:scan", args=[member.qr_token])) + (f"?event={event.pk}" if member.kind == member.Kind.GUEST else "")))
        for member in members
    ]
    pages = [badges[i : i + BADGES_PER_PAGE] for i in range(0, len(badges), BADGES_PER_PAGE)]
    return render(request, "staff/badges.html", {"event": event, "pages": pages, "badge_count": len(badges)})
