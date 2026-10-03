from django import template

from club.models import MemberTag
from club.ui import RANK_STYLE, SECTOR_STYLE

register = template.Library()


@register.filter
def sector_emoji(member):
    return SECTOR_STYLE.get(member.sector, ("🏢", ""))[0]


@register.filter
def sector_classes(member):
    return SECTOR_STYLE.get(member.sector, ("", "bg-stone-500 text-white"))[1]


@register.filter
def rank_label(member):
    return RANK_STYLE[member.rank][0]


@register.filter
def rank_ring(member):
    return RANK_STYLE[member.rank][1]


@register.filter
def rank_badge(member):
    return RANK_STYLE[member.rank][2]


@register.simple_tag
def tags_with(member, sentiment):
    """{% tags_with member "like" as likes %} — needs prefetch_related("tag_links__tag") to avoid N+1 queries."""
    return [link.tag for link in member.tag_links.all() if link.sentiment == sentiment]


@register.filter
def percent(value):
    return f"{round(value * 100)} %"


SENTIMENTS = MemberTag.Sentiment
