"""Ready-to-display data for event pages: 'Tes rencontres' and 'Ton placement'."""

from django.db.models import Q

from club.models import Match, SeatingPlan, Tag
from club.ui import GENERIC_ICEBREAKER, round_label


def intros_for(member, event) -> list[dict]:
    """Introductions proposed to `member` for `event`, best first."""
    matches = list(
        Match.objects.filter(event=event)
        .filter(Q(member_a=member) | Q(member_b=member))
        .select_related("member_a__user", "member_b__user")
        .order_by("-score")
    )
    slugs = {slug for m in matches for slug in m.shared_likes + m.shared_dislikes}
    tags = {tag.slug: tag for tag in Tag.objects.filter(slug__in=slugs)}
    intros = []
    for match in matches:
        likes = [tags[s] for s in match.shared_likes if s in tags]
        dislikes = [tags[s] for s in match.shared_dislikes if s in tags]
        first = (likes or dislikes or [None])[0]
        intros.append(
            {
                "other": match.other(member),
                "score": match.score,
                "likes": likes,
                "dislikes": dislikes,
                "cross_sector": match.cross_sector,
                "welcomes_newcomer": match.welcomes_newcomer,
                "icebreaker": (first.icebreaker if first and first.icebreaker else GENERIC_ICEBREAKER),
            }
        )
    return intros


def seats_for(member, event) -> list[dict]:
    """[{'label': 'Entrée', 'table': 3}, …] or [] when there is no seating plan."""
    plan = SeatingPlan.objects.filter(event=event).first()
    if plan is None:
        return []
    seats = plan.assignments.filter(member=member).order_by("round_index")
    return [{"label": round_label(seat.round_index), "table": seat.table_number} for seat in seats]
