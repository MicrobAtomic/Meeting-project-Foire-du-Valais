"""'Je peux aider sur… / Je cherche…': the themes of mutual help a member offers or looks for.

A discreet, optional door: a member picks at most MAX_PER_KIND themes of each kind. The same limit is enforced by
the profile form, by the admin and here, in the one function that writes a member's themes."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from club.models import Expertise, MemberExpertise

MAX_PER_KIND = 3


def too_many_themes(kind) -> ValidationError:
    return ValidationError(
        _("Choisis %(max)s thèmes au plus pour « %(kind)s »."),
        code="too_many_themes",
        params={"max": MAX_PER_KIND, "kind": MemberExpertise.Kind(kind).label},
    )


def topics_by_slug(slugs=None) -> dict[str, Expertise]:
    """{slug: Expertise} in display order; every theme, or only the given slugs."""
    topics = Expertise.objects.all() if slugs is None else Expertise.objects.filter(slug__in=set(slugs))
    return {topic.slug: topic for topic in topics}


def members_offering(slug):
    """Subquery of the ids of the members who can help on this theme (album filter 'Peut m'aider sur…')."""
    return MemberExpertise.objects.filter(kind=MemberExpertise.Kind.OFFER, expertise__slug=slug).values("member_id")


@transaction.atomic
def save_expertise(member, offers, needs) -> None:
    """Replace the themes of THIS member: `offers` and `needs` are iterables of Expertise.

    More than MAX_PER_KIND distinct themes of one kind raises a ValidationError and writes nothing."""
    wanted = {
        MemberExpertise.Kind.OFFER: list({theme.pk: theme for theme in offers}.values()),
        MemberExpertise.Kind.NEED: list({theme.pk: theme for theme in needs}.values()),
    }
    for kind, themes in wanted.items():
        if len(themes) > MAX_PER_KIND:
            raise too_many_themes(kind)
    for kind, themes in wanted.items():
        links = MemberExpertise.objects.filter(member=member, kind=kind)
        links.exclude(expertise__in=themes).delete()
        already = set(links.values_list("expertise_id", flat=True))
        MemberExpertise.objects.bulk_create(
            MemberExpertise(member=member, expertise=theme, kind=kind) for theme in themes if theme.pk not in already
        )
