"""Security safety net: who may open what. Closed by default — a new route must be classified here or the suite fails."""

import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import get_resolver, reverse

from club.models import Event
from club.tests.helpers import make_member, make_staff

PUBLIC = {  # reachable without an account (nothing about members is exposed there)
    "login", "magic_login", "set_language", "club:landing", "club:magic_link_request", "club:join", "club:join_thanks",
}
MEMBER = {  # members only (a Member profile is required)
    "club:home", "club:onboarding", "club:album", "club:profile_edit", "club:my_qr", "club:invite",
    "club:member_detail", "club:member_vcard", "club:event_list", "club:event_detail", "club:event_rsvp", "club:scan",
}
STAFF = {"club:staff_dashboard", "club:staff_event", "club:staff_badges"}
ANY_LOGGED_IN = {"logout"}
POST_ONLY = {"set_language", "logout", "club:event_rsvp"}  # state-changing: a GET must never change anything


def route_names():
    def walk(patterns, namespace=""):
        for pattern in patterns:
            if hasattr(pattern, "url_patterns"):
                prefix = f"{pattern.namespace}:" if pattern.namespace else namespace
                if str(pattern.pattern) == "admin/":
                    continue  # the Django admin has its own, tested, login
                yield from walk(pattern.url_patterns, prefix)
            else:
                yield namespace + pattern.name

    return set(walk(get_resolver().url_patterns))


class AccessMatrixTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        self.event = Event.objects.create(title="Dîner", kind="dinner", location="Martigny", starts_at="2030-01-01T18:00Z")
        self.staff = make_staff()
        self.args = {
            "club:member_detail": [self.bob.pk], "club:member_vcard": [self.bob.pk], "club:event_detail": [self.event.pk],
            "club:event_rsvp": [self.event.pk], "club:scan": [self.bob.qr_token],
            "club:staff_event": [self.event.pk], "club:staff_badges": [self.event.pk],
        }

    def url(self, name):
        return reverse(name, args=self.args.get(name, []))

    def test_every_route_is_classified(self):
        classified = PUBLIC | MEMBER | STAFF | ANY_LOGGED_IN
        self.assertEqual(route_names() - classified, set(), "new route: add it to the access matrix")
        self.assertEqual(classified - route_names(), set(), "classified route that no longer exists")

    def test_anonymous_visitors_reach_only_the_public_pages(self):
        for name in sorted(route_names() - PUBLIC):
            response = self.client.get(self.url(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn(reverse("login"), response.url, name)
        for name in sorted(PUBLIC - POST_ONLY):
            self.assertIn(self.client.get(self.url(name)).status_code, (200, 403), name)  # 403 = magic link without token

    def test_members_are_kept_out_of_the_staff_pages(self):
        self.client.force_login(self.alice.user)
        for name in sorted(STAFF):
            self.assertEqual(self.client.get(self.url(name)).status_code, 403, name)
            self.assertEqual(self.client.post(self.url(name), {"action": "matches"}).status_code, 403, name)

    def test_staff_accounts_without_a_member_profile_are_sent_to_their_dashboard(self):
        self.client.force_login(self.staff)
        for name in sorted(MEMBER):
            response = self.client.get(self.url(name))
            self.assertRedirects(response, reverse("club:staff_dashboard"), msg_prefix=name)

    def test_members_can_open_every_member_page(self):
        self.client.force_login(self.alice.user)
        for name in sorted(MEMBER - POST_ONLY - {"club:member_vcard", "club:scan"}):
            self.assertEqual(self.client.get(self.url(name)).status_code, 200, name)

    def test_state_changing_routes_refuse_get(self):
        self.client.force_login(self.alice.user)
        for name in ("club:event_rsvp", "logout"):
            self.assertEqual(self.client.get(self.url(name)).status_code, 405, name)
        # Django's set_language only redirects on GET: the language is never changed by a link
        response = self.client.get(self.url("set_language") + "?language=de&next=/")
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)

    def test_contact_data_routes_need_a_real_meeting(self):
        self.client.force_login(self.alice.user)
        self.assertEqual(self.client.get(self.url("club:member_vcard")).status_code, 403)  # not met bob yet


class CsrfInTemplatesTests(TestCase):
    def test_every_post_form_carries_a_csrf_token(self):
        missing = []
        for path in sorted(Path(settings.BASE_DIR, "templates").rglob("*.html")):
            html = path.read_text(encoding="utf-8")
            for form in re.finditer(r"<form\b[^>]*method=\"post\"[^>]*>(.*?)</form>", html, re.S | re.I):
                if "{% csrf_token %}" not in form.group(1):
                    missing.append(str(path))
        self.assertEqual(missing, [])

    def test_no_state_changing_link_hides_behind_a_get(self):
        """Links to actions that change data (logout, answering an event, scanning) must be forms, never <a href>."""
        offenders = []
        for path in sorted(Path(settings.BASE_DIR, "templates").rglob("*.html")):
            html = path.read_text(encoding="utf-8")
            for target in ("{% url 'logout' %}", "{% url 'club:event_rsvp'", "{% url 'set_language' %}"):
                for match in re.finditer(r"<a\b[^>]*" + re.escape(target), html):
                    offenders.append(f"{path}: {match.group(0)[:80]}")
        self.assertEqual(offenders, [])
