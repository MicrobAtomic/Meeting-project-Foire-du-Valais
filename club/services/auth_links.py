"""Magic login links sent by e-mail (django-sesame: signed, valid SESAME_MAX_AGE seconds, single use)."""

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from sesame.utils import get_query_string


def email_language(member) -> str:
    """The language the member reads: French by default, German/English only when that is all they speak."""
    if member.preferred_language in ("fr", "de", "en"):
        return member.preferred_language
    languages = member.languages
    if "fr" in languages or not languages:
        return "fr"
    return "de" if "de" in languages else "en"


def login_link(request, member) -> str:
    return request.build_absolute_uri(reverse("magic_login")) + get_query_string(member.user)


def send_login_link(request, member) -> None:
    link = login_link(request, member)
    with translation.override(email_language(member)):
        subject = _("Ton accès au Club des Affaires")
        body = _(
            "Salut %(name)s,\n\n"
            "Voici ton lien de connexion au Club des Affaires :\n\n"
            "%(link)s\n\n"
            "Il est valable %(minutes)s minutes et ne fonctionne qu'une seule fois. "
            "Si tu n'as rien demandé, ignore simplement ce message.\n\n"
            "À bientôt !\n"
            "L'équipe du Club"
        ) % {"name": member.first_name, "link": link, "minutes": settings.SESAME_MAX_AGE // 60}
    send_mail(subject, body, None, [member.user.email])
