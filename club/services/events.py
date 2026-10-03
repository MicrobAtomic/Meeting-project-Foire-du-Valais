from collections import defaultdict

from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from club.models import RSVP, Connection, Event, Match, Member, MemberTag, SeatAssignment, SeatingPlan, Substitute
from club.services.matching import Profile, compute_matches
from club.services.seating import Guest, compute_seating


def attendees(event):
    if event.cancelled_at and not event.is_past:
        return Member.objects.none()
    replacements = Substitute.objects.filter(event=event, member_id=OuterRef("pk"), status__in=["pending", "approved"])
    approvals = Substitute.objects.filter(event=event, guest_id=OuterRef("pk"), status="approved")
    members = Member.objects.filter(rsvps__event=event, rsvps__status=RSVP.Status.YES).annotate(
        has_replacement=Exists(replacements), approved_guest=Exists(approvals))
    guest_access = Q() if event.is_past else Q(user__is_active=True, guest_access_until__gt=timezone.now())
    return members.filter(Q(kind=Member.Kind.MEMBER, user__is_active=True, has_replacement=False)
                          | (Q(kind=Member.Kind.GUEST, approved_guest=True) & guest_access)).distinct()


def connected_pairs(member_ids) -> set[tuple[int, int]]:
    return set(
        Connection.objects.filter(member_a_id__in=member_ids, member_b_id__in=member_ids).values_list(
            "member_a_id", "member_b_id"
        )
    )


def current_event():
    """Event taking place today (used to tag the connections made during it)."""
    return visible_events().filter(cancelled_at__isnull=True, starts_at__date=timezone.localdate()).first()


def visible_events(member=None):
    events = Event.objects.filter(is_published=True)
    if member and member.kind == Member.Kind.GUEST:
        events = events.filter(substitutes__guest=member, substitutes__status=Substitute.Status.APPROVED)
    return events


def invalidate_event_plans(event):
    Match.objects.filter(event=event).delete()
    SeatingPlan.objects.filter(event=event).delete()


def with_attendee_counts(events):
    result = list(events)
    for event in result:
        event.yes_count = attendees(event).count()
    return result


@transaction.atomic
def generate_matches(event, per_person: int = 3) -> int:
    event = Event.objects.select_for_update().get(pk=event.pk)
    members = list(attendees(event))
    ids = [m.pk for m in members]
    likes, dislikes = defaultdict(set), defaultdict(set)
    for member_id, slug, sentiment in MemberTag.objects.filter(member_id__in=ids).values_list(
        "member_id", "tag__slug", "sentiment"
    ):
        if sentiment == MemberTag.Sentiment.LIKE:
            likes[member_id].add(slug)
        elif sentiment == MemberTag.Sentiment.DISLIKE:
            dislikes[member_id].add(slug)
    profiles = [
        Profile(
            id=m.pk,
            sector=m.sector,
            languages=m.languages,
            likes=frozenset(likes[m.pk]),
            dislikes=frozenset(dislikes[m.pk]),
            is_newcomer=m.rank == Member.RANK_NEWCOMER,
            is_pillar=m.rank in (Member.RANK_FOUNDER, Member.RANK_PILLAR),
        )
        for m in members
    ]
    proposals = compute_matches(profiles, connected_pairs(ids), per_person=per_person, seed=event.pk)
    Match.objects.filter(event=event).delete()
    Match.objects.bulk_create(
        Match(
            event=event,
            member_a_id=p.a,
            member_b_id=p.b,
            score=p.score,
            shared_likes=list(p.shared_likes),
            shared_dislikes=list(p.shared_dislikes),
            cross_sector=p.cross_sector,
            welcomes_newcomer=p.welcomes_newcomer,
        )
        for p in proposals
    )
    return len(proposals)


@transaction.atomic
def generate_seating(event, rounds: int = 3, table_size: int = 6) -> SeatingPlan:
    event = Event.objects.select_for_update().get(pk=event.pk)
    members = list(attendees(event))
    ids = [m.pk for m in members]
    result = compute_seating(
        [Guest(id=m.pk, sector=m.sector, languages=m.languages) for m in members],
        rounds=rounds,
        table_size=table_size,
        already_connected=frozenset(connected_pairs(ids)),
        seed=event.pk,
    )
    plan, _ = SeatingPlan.objects.update_or_create(
        event=event,
        defaults={
            "rounds": rounds,
            "table_size": table_size,
            "new_pairs": result.new_pairs,
            "repeated_pairs": result.repeated_pairs,
        },
    )
    plan.assignments.all().delete()
    SeatAssignment.objects.bulk_create(
        SeatAssignment(plan=plan, round_index=r, table_number=t + 1, member_id=member_id)
        for r, tables in enumerate(result.rounds)
        for t, table in enumerate(tables)
        for member_id in table
    )
    return plan
