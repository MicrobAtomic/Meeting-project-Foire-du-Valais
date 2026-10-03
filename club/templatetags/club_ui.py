import re

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from club.services.photos import available_photo
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from club.models import MemberTag
from club.ui import EVENT_KIND_EMOJI, RANK_STYLE, SECTOR_STYLE

register = template.Library()
DEMO_PHOTOS = {key: f"img/demo/{key}.jpg" for key in ("camille", "lukas", "joelle")}


@register.filter
def demo_photo(member):
    path = DEMO_PHOTOS.get(member.demo_photo_key) if settings.DEMO_MODE else None
    return static(path) if path else ""


@register.filter
def member_portrait(member):
    if available_photo(member):
        return reverse("club:member_photo", args=[member.pk])
    return demo_photo(member) if not member.photo else ""

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
def kind_emoji(event):
    return EVENT_KIND_EMOJI.get(event.kind, "📅")


@register.filter
def percent(value):
    # Translators: a percentage; French and German put a space before the % sign, English does not.
    return gettext("%(value)s %%") % {"value": round(value * 100)}


# The date filters below read their Django date format from the translation catalog, so the order of
# weekday / day / month follows each language (de: "Donnerstag, 15. Oktober", en: "Thursday, October 15").
@register.filter(expects_localtime=True)
def datetime_short(value):
    # Translators: Django date format, e.g. "jeudi 15 octobre, 19:00"
    return date_format(value, gettext("l j F, H:i"))


@register.filter(expects_localtime=True)
def datetime_long(value):
    # Translators: Django date format, e.g. "jeudi 15 octobre 2026, 19:00"
    return date_format(value, gettext("l j F Y, H:i"))


@register.filter(expects_localtime=True)
def date_long(value):
    # Translators: Django date format, e.g. "15 octobre 2026"
    return date_format(value, gettext("j F Y"))


@register.filter(expects_localtime=True)
def date_short(value):
    # Translators: Django date format, e.g. "15 octobre"
    return date_format(value, gettext("j F"))



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
