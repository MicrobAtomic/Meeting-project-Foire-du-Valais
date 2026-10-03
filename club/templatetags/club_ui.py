import re

from django import template
from django.utils.safestring import mark_safe

from club.models import MemberTag
from club.ui import RANK_STYLE, SECTOR_STYLE

register = template.Library()

LANGUAGE_ORDER = ("fr", "de", "en")
_SVG_SIZE = re.compile(r'<svg[^>]*?\swidth="(\d+)"[^>]*?\sheight="(\d+)"')


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



@register.filter
def language_codes(member):
    """'FR · DE' in a fixed order (the model exposes an unordered set)."""
    return " · ".join(code.upper() for code in LANGUAGE_ORDER if code in member.languages)


@register.filter
def scalable_svg(svg):
    """Give the inline QR SVG a viewBox so CSS (h-64 w-64…) can resize it; segno only sets width/height."""
    svg = str(svg)
    size = _SVG_SIZE.search(svg)
    if "viewBox" not in svg and size:
        svg = svg.replace("<svg ", f'<svg viewBox="0 0 {size.group(1)} {size.group(2)}" ', 1)
    return mark_safe(svg)  # produced by segno from our own URL: no user-controlled markup


SENTIMENTS = MemberTag.Sentiment
