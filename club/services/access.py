"""Shared profile visibility checks. Notes never grant visibility or contact access."""
from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404

from club.models import Member
from club.services.federation import collected_ids
from club.services.substitutions import valid_guest_invitations
from club.services.events import attendees, visible_events
from django.utils import timezone
from django.conf import settings
from datetime import timedelta


def coparticipant_ids(viewer):
    now = timezone.now()
    if viewer.kind == Member.Kind.GUEST:
        events = visible_events(viewer).filter(pk__in=valid_guest_invitations(viewer).values("event_id"))
    else:
        events = visible_events().filter(cancelled_at__isnull=True,
            starts_at__gt=now - timedelta(hours=settings.GUEST_ACCESS_HOURS), rsvps__member=viewer, rsvps__status="yes")
    ids = set()
    for event in events:
        ids.update(attendees(event).values_list("pk", flat=True))
    return ids


def visible_members(viewer):
    collected = collected_ids(viewer)
    coparticipants = coparticipant_ids(viewer)
    regular = Q(kind=Member.Kind.MEMBER, user__is_active=True)
    active_guests = Q(kind=Member.Kind.GUEST, pk__in=coparticipants, user__is_active=True, guest_access_until__gt=timezone.now())
    met_guests = Q(kind=Member.Kind.GUEST, pk__in=collected)
    members = Member.objects.filter(regular | active_guests | met_guests | Q(pk=viewer.pk)).filter(
        Q(visible_in_directory=True) | Q(pk__in=collected) | Q(pk=viewer.pk))
    if viewer.kind == Member.Kind.GUEST:
        members = members.filter(Q(pk__in=coparticipants) | Q(pk__in=collected) | Q(pk=viewer.pk))
    return members.distinct()


def visible_target(viewer, pk):
    return get_object_or_404(visible_members(viewer).select_related("user").prefetch_related("tag_links__tag"), pk=pk)


def can_open_profile(viewer, target):
    return visible_members(viewer).filter(pk=target.pk).exists()


def scan_event(viewer, target, context_id=None):
    events = visible_events(viewer).filter(cancelled_at__isnull=True, starts_at__date=timezone.localdate())
    common = [event for event in events if attendees(event).filter(pk=viewer.pk).exists()
              and attendees(event).filter(pk=target.pk).exists()]
    if context_id:
        selected = next((event for event in common if str(event.pk) == str(context_id)), None)
        if selected is None:
            raise Http404
        return selected
    if len(common) == 1:
        return common[0]
    if viewer.kind == Member.Kind.GUEST or target.kind == Member.Kind.GUEST:
        raise Http404
    return None
