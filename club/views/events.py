from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods

from club.decorators import member_required
from club.models import RSVP, Event, Substitute
from club.forms import SubstituteForm
from club.services.events import attendees, invalidate_event_plans, visible_events, with_attendee_counts
from club.services.access import can_open_profile, visible_members
from club.services.substitutions import cancel_substitute, request_substitute, require_open_event, require_regular
from club.services.federation import collected_ids
from club.services.intros import intros_for, seats_for


def visible_intros(member, event):
    """'Tes rencontres' without the people who chose to hide their card (they cannot be introduced)."""
    return [intro for intro in intros_for(member, event) if can_open_profile(member, intro["other"])]


@member_required
def event_list(request):
    now = timezone.now()
    events = visible_events(request.member)
    answers = dict(RSVP.objects.filter(member=request.member).values_list("event_id", "status"))
    context = {
        "upcoming": [(e, answers.get(e.pk)) for e in with_attendee_counts(events.filter(starts_at__gte=now).order_by("starts_at"))],
        "past": [(e, answers.get(e.pk)) for e in with_attendee_counts(events.filter(starts_at__lt=now).order_by("-starts_at"))],
    }
    return render(request, "club/event_list.html", context)


@member_required
def event_detail(request, pk):
    me = request.member
    event = get_object_or_404(visible_events(me), pk=pk)
    answer = RSVP.objects.filter(event=event, member=me).values_list("status", flat=True).first()
    registered = answer == RSVP.Status.YES
    collected = collected_ids(me)
    coming = (
        attendees(event)
        .filter(pk__in=visible_members(me).values("pk"))
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
        "substitution": Substitute.objects.filter(event=event, member=me).first() if me.kind == me.Kind.MEMBER else None,
    }
    return render(request, "club/event_detail.html", context)


@member_required
@require_POST
@transaction.atomic
def event_rsvp(request, pk):
    require_regular(request.member)
    event = get_object_or_404(visible_events(request.member).select_for_update(), pk=pk)
    status = request.POST.get("status")
    if status not in RSVP.Status.values:
        return HttpResponseBadRequest("Invalid status")
    if event.is_past:
        messages.error(request, _("Cet événement est déjà passé."))
        return redirect("club:event_detail", pk=event.pk)
    if not event.responses_open:
        messages.error(request, _("Les réponses sont fermées pour cet événement."))
        return redirect("club:event_detail", pk=event.pk)
    if status == RSVP.Status.YES and Substitute.objects.filter(event=event, member=request.member, status__in=["pending", "approved"]).exists():
        messages.error(request, _("Annule ton remplacement avant de répondre que tu viens."))
        return redirect("club:event_detail", pk=event.pk)
    previous = RSVP.objects.filter(event=event, member=request.member).values_list("status", flat=True).first()
    RSVP.objects.update_or_create(event=event, member=request.member, defaults={"status": status})
    if previous != status:
        invalidate_event_plans(event)
    if status == RSVP.Status.YES:
        messages.success(request, _("C'est noté, à bientôt ! 🥂"))
    else:
        messages.info(request, _("C'est noté. On pensera à toi !"))
    return redirect("club:event_detail", pk=event.pk)


@member_required
@require_http_methods(["GET", "POST"])
def member_substitute(request, pk):
    require_regular(request.member)
    event = get_object_or_404(visible_events(request.member), pk=pk)
    try:
        require_open_event(event)
    except ValidationError:
        messages.error(request, _("Les réponses sont fermées pour cet événement."))
        return redirect("club:event_detail", pk=event.pk)
    existing = Substitute.objects.filter(event=event, member=request.member).first()
    form = SubstituteForm(request.POST if request.method == "POST" else None, instance=existing)
    if request.method == "POST" and form.is_valid():
        try:
            request_substitute(event.pk, request.member, form.cleaned_data)
            messages.success(request, _("Remplacement demandé. L'équipe vérifiera l'identité avant d'envoyer l'accès."))
            return redirect("club:event_detail", pk=event.pk)
        except ValidationError as error:
            form.add_error(None, error)
    return render(request, "club/substitute_form.html", {"event": event, "form": form})


@member_required
@require_POST
def member_substitute_cancel(request, pk):
    require_regular(request.member)
    event = get_object_or_404(visible_events(request.member), pk=pk)
    try:
        cancel_substitute(event.pk, request.member)
        messages.success(request, _("Remplacement annulé. Tu peux répondre de nouveau."))
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    return redirect("club:event_detail", pk=event.pk)
