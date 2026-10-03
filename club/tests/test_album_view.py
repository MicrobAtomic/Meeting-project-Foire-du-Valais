from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from club.models import Connection, Member
from club.tests.helpers import assert_csp_clean, make_member


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DemoAlbumTests(TestCase):
    """The checks of docs/PLAN.md phase 3, run on the seeded demo club (50 members, Camille's point of view)."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.camille = Member.objects.get(user__email="camille.rey@example.com")
        cls.lukas = Member.objects.get(user__email="lukas.imboden@example.com")

    def setUp(self):
        self.client.force_login(self.camille.user)

    def album(self, **params):
        response = self.client.get(reverse("club:album"), params)
        self.assertEqual(response.status_code, 200)
        return response

    def test_album_lists_everybody_but_me(self):
        response = self.album()
        members = response.context["members"]
        self.assertEqual(len(members), 49)
        self.assertNotIn(self.camille, members)
        self.assertEqual(response.context["progress"], (2, 49))

    def test_status_filters(self):
        self.assertEqual(len(self.album(statut="album").context["members"]), 2)
        self.assertEqual(len(self.album(statut="a-rencontrer").context["members"]), 47)
        recruits = self.album(statut="nouveaux").context["members"]
        self.assertTrue(recruits)
        self.assertTrue(all(m.member_since == timezone.localdate().year for m in recruits))

    def test_language_filter_keeps_only_german_speakers(self):
        members = self.album(langue="de").context["members"]
        self.assertTrue(members)
        self.assertTrue(all(m.speaks_de for m in members))

    def test_search_by_name(self):
        members = self.album(q="Lukas").context["members"]
        self.assertEqual([m.first_name for m in members], ["Lukas"])

    def test_sector_filter(self):
        members = self.album(secteur="construction").context["members"]
        self.assertIn(self.lukas, members)
        self.assertTrue(all(m.sector == "construction" for m in members))

    def test_unknown_filter_values_are_ignored(self):
        self.assertEqual(len(self.album(secteur="<hack>", langue="xx", statut="zzz").context["members"]), 49)

    def test_cards_show_rank_and_sector_and_are_csp_clean(self):
        response = self.album()
        assert_csp_clean(self, response)
        self.assertContains(response, "Pilier du Club")
        self.assertContains(response, "Nouvelle recrue")
        self.assertContains(response, "✅ Dans ton album")
        self.assertContains(response, "🔒 À rencontrer")

    def test_album_does_not_run_one_query_per_card(self):
        with CaptureQueriesContext(connection) as queries:
            self.album()
        self.assertLess(len(queries), 25)

    def test_hidden_member_is_listed_only_once_collected(self):
        hidden = Member.objects.exclude(pk__in=[self.camille.pk, self.lukas.pk]).exclude(
            pk__in=[m.pk for m in self.album(statut="album").context["members"]]
        ).first()
        hidden.visible_in_directory = False
        hidden.save()
        self.assertNotIn(hidden, self.album().context["members"])
        Connection.link(self.camille, hidden)
        self.assertIn(hidden, self.album().context["members"])

    def test_detail_page_shows_common_points_with_lukas(self):
        response = self.client.get(reverse("club:member_detail", args=[self.lukas.pk]))
        assert_csp_clean(self, response)
        self.assertContains(response, "Vos points communs")
        self.assertContains(response, "Petite Arvine")
        self.assertContains(response, "Ski de randonnée")
        self.assertNotContains(response, self.lukas.user.email)  # not met yet: contact stays locked
        self.assertContains(response, "Scanne son QR code")


class DetailAndQrPagesTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com", first_name="Alice")
        self.bob = make_member("bob@example.com", first_name="Bob", phone="+41 79 111 22 33",
                               linkedin_url="https://www.linkedin.com/in/bob")
        self.client.force_login(self.alice.user)

    def test_met_member_shows_contact_phone_linkedin_and_vcard(self):
        Connection.link(self.alice, self.bob)
        response = self.client.get(reverse("club:member_detail", args=[self.bob.pk]))
        self.assertContains(response, 'href="mailto:bob@example.com"')
        self.assertContains(response, 'href="tel:+41791112233"')
        self.assertContains(response, 'href="https://www.linkedin.com/in/bob"')
        self.assertContains(response, reverse("club:member_vcard", args=[self.bob.pk]))

    def test_unsafe_linkedin_scheme_is_never_rendered_as_a_link(self):
        self.bob.linkedin_url = "javascript:alert(1)"
        self.bob.save()
        Connection.link(self.alice, self.bob)
        response = self.client.get(reverse("club:member_detail", args=[self.bob.pk]))
        self.assertNotContains(response, "javascript:")

    def test_my_own_page_offers_edit_and_hides_the_status_footer(self):
        response = self.client.get(reverse("club:member_detail", args=[self.alice.pk]))
        self.assertContains(response, reverse("club:profile_edit"))
        self.assertNotContains(response, "À rencontrer")
        self.assertNotContains(response, "Vos points communs")

    def test_qr_page_has_a_resizable_svg(self):
        response = self.client.get(reverse("club:my_qr"))
        assert_csp_clean(self, response)
        self.assertContains(response, "<svg viewBox=")
        self.assertContains(response, reverse("club:scan", args=[self.alice.qr_token]))

    def test_scan_confirmation_then_post_collects_the_card(self):
        url = reverse("club:scan", args=[self.bob.qr_token])
        page = self.client.get(url)
        assert_csp_clean(self, page)
        self.assertContains(page, "Ajouter Bob à mon album")
        self.assertContains(page, "csrfmiddlewaretoken")
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Carte ajoutée à ton album")
        self.assertTrue(Connection.exists_between(self.alice, self.bob))
