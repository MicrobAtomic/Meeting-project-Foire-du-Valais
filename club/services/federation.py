from collections import Counter

from club.models import Connection, Member


def federation_index(member_count: int, connection_count: int) -> float:
    """Share of member pairs who know each other (density of the 'who met whom' graph), 0.0 -> 1.0."""
    possible = member_count * (member_count - 1) // 2
    return connection_count / possible if possible else 0.0


def active_members():
    return Member.objects.filter(user__is_active=True, kind=Member.Kind.MEMBER)


def active_connections():
    return Connection.objects.filter(member_a__user__is_active=True, member_b__user__is_active=True,
                                     member_a__kind=Member.Kind.MEMBER, member_b__kind=Member.Kind.MEMBER)


def club_stats() -> dict:
    members = active_members().count()
    connections = active_connections().count()
    return {"members": members, "connections": connections, "index": federation_index(members, connections)}


def degrees() -> Counter:
    counts = Counter()
    for a, b in active_connections().values_list("member_a_id", "member_b_id"):
        counts[a] += 1
        counts[b] += 1
    return counts


def isolated_members(max_connections: int = 2):
    counts = degrees()
    return [m for m in active_members() if counts[m.pk] <= max_connections]


def collection_progress(member) -> tuple[int, int]:
    """(cards collected, cards available) for the member's album."""
    eligible = active_members().exclude(pk=member.pk)
    if member.kind == Member.Kind.GUEST:
        from club.services.access import visible_members
        eligible = eligible.filter(pk__in=visible_members(member).values("pk"))
    return eligible.filter(pk__in=collected_ids(member)).count(), eligible.count()


def collected_ids(member) -> set[int]:
    """Ids of the members already met by `member` (the cards in their album)."""
    pairs = Connection.involving(member).values_list("member_a_id", "member_b_id")
    return {b if a == member.pk else a for a, b in pairs}


def collected_guest_count(member):
    return Member.objects.filter(kind=Member.Kind.GUEST, pk__in=collected_ids(member)).count()
