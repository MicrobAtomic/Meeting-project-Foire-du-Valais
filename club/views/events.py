from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from club.decorators import member_required
from club.models import RSVP, Event
from club.services.events import attendees
from club.services.federation import collected_ids
from club.services.intros import intros_for, seats_for


def visible_intros(member, event):
    """'Tes rencontres' without the people who chose to hide their card (they cannot be introduced)."""
    return [intro for intro in intros_for(member, event) if intro["other"].visible_in_directory]


@member_required
def event_list(request):
    now = timezone.now()
    events = Event.objects.annotate(yes_count=Count("rsvps", filter=Q(rsvps__status=RSVP.Status.YES)))
    answers = dict(RSVP.objects.filter(member=request.member).values_list("event_id", "status"))
    context = {
        "upcoming": [(e, answers.get(e.pk)) for e in events.filter(starts_at__gte=now).order_by("starts_at")],
        "past": [(e, answers.get(e.pk)) for e in events.filter(starts_at__lt=now).order_by("-starts_at")],
    }
    return render(request, "club/event_list.html", context)


@member_required
def event_detail(request, pk):
    me = request.member
    event = get_object_or_404(Event, pk=pk)
    answer = RSVP.objects.filter(event=event, member=me).values_list("status", flat=True).first()
    registered = answer == RSVP.Status.YES
    collected = collected_ids(me)
    coming = (
        attendees(event)
        .filter(Q(visible_in_directory=True) | Q(pk__in=collected) | Q(pk=me.pk))
        .select_related("user")
        .prefetch_related("tag_links__tag")
    )
    intros = visible_intros(me, event) if registered else []
    context = {
        "event": event,
        "my_status": answer,
        "registered": registered,
        "attendee_count": attendees(event).count(),
        # (member, collected?) — None hides the footer on my own card
        "attendees": [(m, None if m.pk == me.pk else m.pk in collected) for m in coming],
        "intros": intros,
        "show_intros": registered and (not event.is_past or bool(intros)),
        "seats": seats_for(me, event) if registered else [],
    }
    return render(request, "club/event_detail.html", context)


@member_required
@require_POST
def event_rsvp(request, pk):
    event = get_object_or_404(Event, pk=pk)
    status = request.POST.get("status")
    if status not in RSVP.Status.values:
        return HttpResponseBadRequest("Invalid status")
    if event.is_past:
        messages.error(request, _("Cet événement est déjà passé."))
        return redirect("club:event_detail", pk=event.pk)
    RSVP.objects.update_or_create(event=event, member=request.member, defaults={"status": status})
    if status == RSVP.Status.YES:
        messages.success(request, _("C'est noté, à bientôt ! 🥂"))
    else:
        messages.info(request, _("C'est noté. On pensera à toi !"))
    return redirect("club:event_detail", pk=event.pk)
