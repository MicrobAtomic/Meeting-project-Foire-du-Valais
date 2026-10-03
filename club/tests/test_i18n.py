import re
from datetime import datetime
from html import unescape
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management import call_command
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ngettext

from club.models import Event, Member, Tag
from club.services.events import generate_matches, generate_seating
from club.tests.helpers import make_member, make_staff

LOCALE_DIR = Path(settings.BASE_DIR) / "locale"


def parse_po_block(block):
    """Fields of one .po entry, with the strings that gettext wraps over several lines joined back."""
    fields, key = {}, None
    for line in block.splitlines():
        if line.startswith("#"):
            continue
        match = re.match(r'^(msgid_plural|msgid|msgstr\[\d\]|msgstr) "(.*)"$', line)
        if match:
            key = match.group(1)
            fields[key] = match.group(2)
        elif line.startswith('"') and key:
            fields[key] += line[1:-1]
    return {k: v.replace('\\"', '"').replace("\\n", "\n") for k, v in fields.items()}


def read_catalog(language):
    """({msgid: msgstr} for singular entries, problems found in the .po file) — tiny parser, no dependency."""
    text = (LOCALE_DIR / language / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
    messages, problems = {}, []
    for block in re.split(r"\n\s*\n", text.strip())[1:]:  # [0] is the header
        if "#, fuzzy" in block:
            problems.append(f"fuzzy: {block[:80]!r}")
        fields = parse_po_block(block)
        msgid = fields["msgid"]
        if "msgid_plural" in fields:
            forms = [fields.get("msgstr[0]", ""), fields.get("msgstr[1]", "")]
            if not all(forms):
                problems.append(f"plural not fully translated: {msgid!r}")
            continue
        if not fields.get("msgstr"):
            problems.append(f"untranslated: {msgid!r}")
        messages[msgid] = fields.get("msgstr", "")
    return messages, problems


class LanguageIsolatedTestCase(TestCase):
    """A request with another language leaves it active in the thread (each real request re-activates its own).
    Restore French after every test so that later tests calling services without a request still see French."""

    def setUp(self):
        super().setUp()
        self.addCleanup(translation.activate, settings.LANGUAGE_CODE)


class CatalogTests(TestCase):
    def test_catalogs_are_complete_compiled_and_use_swiss_spelling(self):
        for language in ("fr", "de", "en"):
            messages, problems = read_catalog(language)
            self.assertEqual(problems, [], language)
            self.assertGreater(len(messages), 250, language)
            # The .mo files are committed: the host (Render) has no gettext to build them.
            self.assertGreater((LOCALE_DIR / language / "LC_MESSAGES" / "django.mo").stat().st_size, 5000, language)
        german = (LOCALE_DIR / "de" / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
        self.assertNotIn("ß", german)

    def test_every_language_translates_the_same_strings(self):
        keys = {language: set(read_catalog(language)[0]) for language in ("fr", "de", "en")}
        self.assertEqual(keys["fr"], keys["de"])
        self.assertEqual(keys["fr"], keys["en"])


class LanguageSelectionTests(LanguageIsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_member("alice@example.com", first_name="Alice")

    def test_default_language_is_french(self):
        page = self.client.get(reverse("login"))
        self.assertContains(page, 'lang="fr"')
        self.assertContains(page, "Mot de passe")

    def test_accept_language_header_picks_german_or_english(self):
        german = self.client.get(reverse("login"), headers={"Accept-Language": "de-CH,de;q=0.9,fr;q=0.5"})
        self.assertContains(german, 'lang="de"')
        self.assertContains(german, "Passwort")
        english = self.client.get(reverse("login"), headers={"Accept-Language": "en-GB,en;q=0.8"})
        self.assertContains(english, 'lang="en"')
        self.assertContains(english, "Password")

    def test_language_switch_is_remembered_across_pages(self):
        self.client.post(reverse("set_language"), {"language": "de", "next": reverse("login")})
        self.client.force_login(self.alice.user)
        home = self.client.get(reverse("club:home"))
        self.assertContains(home, "Hallo Alice")
        self.assertContains(home, "Anlässe")
        self.assertContains(self.client.get(reverse("club:album")), "Das Album des Clubs")
        self.client.post(reverse("set_language"), {"language": "en", "next": "/"})
        self.assertContains(self.client.get(reverse("club:home")), "Hi Alice")

    def test_tag_labels_and_icebreakers_come_from_the_database_in_each_language(self):
        Tag.objects.create(slug="ski", emoji="⛷️", category="hobby", label_fr="Ski de randonnée", label_de="Skitouren",
                           label_en="Ski touring", icebreaker_fr="Ta plus belle course ?", icebreaker_de="Deine schönste Tour?",
                           icebreaker_en="Your best tour?")
        self.client.force_login(self.alice.user)
        for language, expected in (("fr", "Ski de randonnée"), ("de", "Skitouren"), ("en", "Ski touring")):
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
            self.assertContains(self.client.get(reverse("club:onboarding")), expected)


class FormattingTests(TestCase):
    def render(self, template, **context):
        return Template("{% load club_ui %}" + template).render(Context(context))

    def test_dates_follow_each_language(self):
        when = datetime(2026, 10, 15, 19, 0, tzinfo=ZoneInfo("Europe/Zurich"))
        expected = {
            "fr": ("jeudi 15 octobre, 19:00", "jeudi 15 octobre 2026, 19:00", "15 octobre 2026", "15 octobre"),
            "de": ("Donnerstag, 15. Oktober, 19:00", "Donnerstag, 15. Oktober 2026, 19:00", "15. Oktober 2026", "15. Oktober"),
            "en": ("Thursday, October 15, 7:00 PM", "Thursday, October 15, 2026, 7:00 PM", "October 15, 2026", "October 15"),
        }
        for language, (short, long, day_long, day_short) in expected.items():
            with translation.override(language):
                self.assertEqual(self.render("{{ w|datetime_short }}", w=when), short, language)
                self.assertEqual(self.render("{{ w|datetime_long }}", w=when), long, language)
                self.assertEqual(self.render("{{ w|date_long }}", w=when), day_long, language)
                self.assertEqual(self.render("{{ w|date_short }}", w=when), day_short, language)

    def test_dates_are_shown_in_swiss_time(self):
        utc_evening = datetime(2026, 10, 15, 17, 0, tzinfo=ZoneInfo("UTC"))  # 19:00 in Switzerland (CEST)
        with translation.override("fr"):
            self.assertEqual(self.render("{{ w|datetime_short }}", w=utc_evening), "jeudi 15 octobre, 19:00")

    def test_percent_follows_each_language(self):
        for language, expected in (("fr", "15 %"), ("de", "15 %"), ("en", "15%")):
            with translation.override(language):
                self.assertEqual(self.render("{{ v|percent }}", v=0.146), expected, language)

    def test_french_counts_zero_as_singular_and_german_as_plural(self):
        with translation.override("fr"):
            self.assertEqual(ngettext("%(n)s inscrit", "%(n)s inscrits", 0) % {"n": 0}, "0 inscrit")
            self.assertEqual(ngettext("%(n)s inscrit", "%(n)s inscrits", 1) % {"n": 1}, "1 inscrit")
            self.assertEqual(ngettext("%(n)s inscrit", "%(n)s inscrits", 2) % {"n": 2}, "2 inscrits")
        with translation.override("de"):
            self.assertEqual(ngettext("%(n)s inscrit", "%(n)s inscrits", 0) % {"n": 0}, "0 Anmeldungen")
            self.assertEqual(ngettext("%(n)s inscrit", "%(n)s inscrits", 1) % {"n": 1}, "1 Anmeldung")
        with translation.override("en"):
            self.assertEqual(ngettext("%(n)s inscrit", "%(n)s inscrits", 1) % {"n": 1}, "1 attendee")
            self.assertEqual(ngettext("%(n)s inscrit", "%(n)s inscrits", 5) % {"n": 5}, "5 attendees")


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class NoFrenchLeftTests(LanguageIsolatedTestCase):
    """Walk through every page in German and English: no French interface string may remain.
    (Content typed by people — names, job titles, event titles — is data and stays as it was written.)"""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.camille = Member.objects.get(user__email="camille.rey@example.com")
        cls.lukas = Member.objects.get(user__email="lukas.imboden@example.com")
        cls.dinner = Event.objects.get(title="Dîner d'automne")
        generate_matches(cls.dinner)
        generate_seating(cls.dinner)
        cls.staff = make_staff("chef@example.com")

    def french_strings(self, language):
        french = read_catalog("fr")[0]
        translated = read_catalog(language)[0]
        data = " ".join(f"{e.title} {e.description} {e.location}" for e in Event.objects.all())
        return sorted(
            msgid for msgid in french
            if translated[msgid] != msgid and len(msgid) >= 6 and "%(" not in msgid and "%%" not in msgid
            and msgid not in data  # e.g. the event "Conférence de presse" is data, not the "Conférence" interface label
            and not re.fullmatch(r"[a-zA-Z ]{1,4}(, | )?[a-zA-Z: ]{0,6}", msgid)  # date formats like "l j F, H:i"
        )

    def leftovers(self, response, strings):
        page = unescape(response.content.decode())
        return [s for s in strings if s in page]

    def test_member_and_public_pages_are_fully_translated(self):
        urls_member = [
            reverse("club:home"), reverse("club:album"), reverse("club:album") + "?statut=album",
            reverse("club:member_detail", args=[self.lukas.pk]), reverse("club:member_detail", args=[self.camille.pk]),
            reverse("club:my_qr"), reverse("club:invite"), reverse("club:profile_edit"), reverse("club:onboarding"),
            reverse("club:event_list"), reverse("club:event_detail", args=[self.dinner.pk]),
            reverse("club:scan", args=[self.lukas.qr_token]), "/cette-page-nexiste-pas/",
        ]
        urls_public = [reverse("club:landing"), reverse("login"), reverse("club:join"), reverse("club:join_thanks")]
        for language in ("de", "en"):
            strings = self.french_strings(language)
            self.assertGreater(len(strings), 150)
            self.client.logout()  # logout() also clears the cookies: choose the language afterwards
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
            for url in urls_public:
                self.assertEqual(self.leftovers(self.client.get(url), strings), [], f"{language} {url}")
            self.client.force_login(self.camille.user)
            for url in urls_member:
                self.assertEqual(self.leftovers(self.client.get(url, follow=True), strings), [], f"{language} {url}")
            forbidden = self.client.get(reverse("club:staff_dashboard"))
            self.assertEqual(self.leftovers(forbidden, strings), [], f"{language} 403")

    def test_staff_pages_are_fully_translated(self):
        urls = [reverse("club:staff_dashboard"), reverse("club:staff_event", args=[self.dinner.pk])]
        for language in ("de", "en"):
            strings = self.french_strings(language)
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
            self.client.force_login(self.staff)
            for url in urls:
                self.assertEqual(self.leftovers(self.client.get(url), strings), [], f"{language} {url}")

    def test_german_pages_really_are_german(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "de"
        self.client.force_login(self.camille.user)
        home = self.client.get(reverse("club:home"))
        for text in ("Hallo Camille", "Der Club ist zu 15 % vernetzt", "Nächster Anlass", "Deine Begegnungen", "Dein Album"):
            self.assertContains(home, text)
        event = self.client.get(reverse("club:event_detail", args=[self.dinner.pk]))
        for text in ("Donnerstag, 15. Oktober 2026", "Dein Sitzplatz", "Vorspeise", "Skitouren"):
            self.assertContains(event, text)
