from django.test import TestCase
from django.urls import reverse

from club.models import Connection
from club.services.vcard import build_vcard
from club.tests.helpers import assert_csp_clean, make_member

# Every member page WITHOUT url arguments added later must be appended here (see docs/PLAN.md).
# Pages with arguments: call assert_csp_clean(self, response) in their own tests.
PAGES_TO_CHECK = ["club:home", "club:my_qr", "club:album", "club:profile_edit", "club:event_list"]


class AlbumSecurityTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        self.client.force_login(self.alice.user)

    def test_contact_details_only_after_meeting(self):
        page = self.client.get(reverse("club:member_detail", args=[self.bob.pk]))
        self.assertNotContains(page, "bob@example.com")
        self.assertEqual(self.client.get(reverse("club:member_vcard", args=[self.bob.pk])).status_code, 403)
        Connection.link(self.alice, self.bob)
        page = self.client.get(reverse("club:member_detail", args=[self.bob.pk]))
        self.assertContains(page, "bob@example.com")
        vcard = self.client.get(reverse("club:member_vcard", args=[self.bob.pk]))
        self.assertEqual(vcard.status_code, 200)
        self.assertEqual(vcard["Content-Type"], "text/vcard; charset=utf-8")

    def test_hidden_member_is_404_for_strangers(self):
        self.bob.visible_in_directory = False
        self.bob.save()
        self.assertEqual(self.client.get(reverse("club:member_detail", args=[self.bob.pk])).status_code, 404)

    def test_scan_get_has_no_side_effect_and_post_is_idempotent(self):
        url = reverse("club:scan", args=[self.bob.qr_token])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(Connection.exists_between(self.alice, self.bob))
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(Connection.objects.count(), 1)
        connection = Connection.objects.get()
        self.assertLess(connection.member_a_id, connection.member_b_id)

    def test_scanning_own_card_or_unknown_token(self):
        self.client.post(reverse("club:scan", args=[self.alice.qr_token]))
        self.assertEqual(Connection.objects.count(), 0)
        self.assertEqual(self.client.get(reverse("club:scan", args=["nope"])).status_code, 404)

    def test_csp_header_and_no_inline_code(self):
        Connection.link(self.alice, self.bob)
        urls = [reverse(name) for name in PAGES_TO_CHECK]
        urls.append(reverse("club:member_detail", args=[self.bob.pk]))
        for url in urls:
            assert_csp_clean(self, self.client.get(url))

    def test_vcard_escapes_injection(self):
        self.bob.company = "Evil\nEMAIL:attacker@example.com"
        card = build_vcard(self.bob)
        self.assertNotIn("\nEMAIL:attacker", card)
        self.assertIn("ORG:Evil\\nEMAIL:attacker@example.com", card)
