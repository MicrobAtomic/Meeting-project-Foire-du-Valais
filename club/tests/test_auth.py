from django.test import TestCase
from django.urls import reverse
from sesame.utils import get_query_string

from club.tests.helpers import make_member, make_staff


class AuthTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        self.staff = make_staff()

    def test_public_pages_are_reachable_anonymously(self):
        for url in [reverse("club:landing"), reverse("login"), "/admin/login/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        response = self.client.post(reverse("set_language"), {"language": "de", "next": "/"})
        self.assertEqual(response.status_code, 302)

    def test_everything_else_requires_login(self):
        for url in [
            reverse("club:home"),
            reverse("club:member_detail", args=[self.bob.pk]),
            reverse("club:scan", args=[self.bob.qr_token]),
            reverse("club:staff_dashboard"),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn(reverse("login"), response.url)

    def test_staff_area_is_forbidden_to_members(self):
        self.client.force_login(self.alice.user)
        self.assertEqual(self.client.get(reverse("club:staff_dashboard")).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("club:staff_dashboard")).status_code, 200)

    def test_staff_without_member_profile_is_sent_to_staff_dashboard(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("club:home"))
        self.assertRedirects(response, reverse("club:staff_dashboard"))

    def test_logout_requires_post(self):
        self.client.force_login(self.alice.user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)

    def test_magic_link_logs_in_once(self):
        url = reverse("magic_login") + get_query_string(self.alice.user)
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.get(reverse("club:home")).status_code, 200)
        self.client.post(reverse("logout"))
        self.assertEqual(self.client.get(url).status_code, 403)  # SESAME_ONE_TIME: a link works only once
