"""Ready-to-display data for event pages: 'Tes rencontres' and 'Ton placement'."""

from django.db.models import Q
from django.utils.translation import gettext as _

from club.models import Match, SeatingPlan, Tag
from club.services.expertise import topics_by_slug
from club.ui import GENERIC_ICEBREAKER, round_label


def synergy_lines(member, other, synergies, topics) -> list[dict]:
    """The synergies of a match as `member` sees them: the ones where they are looked for come first.

    [{'topic': Expertise, 'text': 'Tu cherches « Digital & IA » : Camille peut t'aider.'}, …]"""
    lines = []
    for helper_id, seeker_id, slug in synergies:
        topic = topics.get(slug)
        if topic is None or member.pk not in (helper_id, seeker_id):
            continue
        if seeker_id == member.pk:
            text = _("Tu cherches « %(topic)s » : %(name)s peut t'aider.")
        else:
            text = _("%(name)s cherche « %(topic)s » : c'est ton domaine.")
        lines.append({"topic": topic, "i_am_the_seeker": seeker_id == member.pk,
                      "text": text % {"topic": topic.label, "name": other.first_name}})
    return sorted(lines, key=lambda line: not line["i_am_the_seeker"])


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
    topics = topics_by_slug({synergy[2] for m in matches for synergy in m.synergies})
    intros = []
    for match in matches:
        likes = [tags[s] for s in match.shared_likes if s in tags]
        dislikes = [tags[s] for s in match.shared_dislikes if s in tags]
        first = (likes or dislikes or [None])[0]
        other = match.other(member)
        intros.append(
            {
                "other": other,
                "score": match.score,
                "likes": likes,
                "dislikes": dislikes,
                "cross_sector": match.cross_sector,
                "welcomes_newcomer": match.welcomes_newcomer,
                "synergies": synergy_lines(member, other, match.synergies, topics),
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
