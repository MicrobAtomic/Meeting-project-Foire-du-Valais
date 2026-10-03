from datetime import timedelta

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_http_methods

from club.decorators import staff_required
from club.forms import SeatingForm
from club.models import RSVP, Event, InvitationRequest, Match, SeatingPlan, Tag
from club.services.events import attendees, generate_matches, generate_seating
from club.services.federation import (
    active_connections,
    active_members,
    club_stats,
    degrees,
    isolated_members,
)
from club.ui import round_label

ISOLATED_SHOWN = 20


@staff_required
def dashboard(request):
    now = timezone.now()
    counts = degrees()
    isolated = sorted(isolated_members(), key=lambda m: (counts[m.pk], m.last_name, m.first_name))
    new_requests = InvitationRequest.objects.filter(status=InvitationRequest.Status.NEW).order_by("-created_at")
    context = {
        "stats": club_stats(),
        "recent_connections": active_connections().filter(created_at__gte=now - timedelta(days=30)).count(),
        "new_recruits": active_members().filter(member_since=timezone.localdate().year).count(),
        "isolated": [(m, counts[m.pk]) for m in isolated[:ISOLATED_SHOWN]],
        "isolated_more": max(len(isolated) - ISOLATED_SHOWN, 0),
        "upcoming": Event.objects.filter(starts_at__gte=now)
        .annotate(yes_count=Count("rsvps", filter=Q(rsvps__status=RSVP.Status.YES)))
        .order_by("starts_at"),
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
        if action == "matches":
            count = generate_matches(event)
            messages.success(request, ngettext("%(count)s rencontre générée.", "%(count)s rencontres générées.", count) % {"count": count})
            return redirect("club:staff_event", pk=event.pk)
        if action != "seating":
            return HttpResponseBadRequest("Unknown action")
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
    }
    return render(request, "staff/event_tools.html", context)
