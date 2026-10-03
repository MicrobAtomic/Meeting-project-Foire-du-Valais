from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from club.models import InvitationRequest, Member
from club.tests.helpers import assert_csp_clean, make_member, make_staff


class LandingTests(TestCase):
    def setUp(self):
        self.lukas = make_member("lukas.imboden@example.com", first_name="Lukas", last_name="Imboden", sector="construction")
        make_member("camille.rey@example.com", first_name="Camille", last_name="Rey", sector="tech")
        gone = make_member("gone@example.com", first_name="Parti", last_name="Loin", sector="finance")
        gone.user.is_active = False
        gone.user.save()

    def test_landing_is_public_and_csp_clean(self):
        response = self.client.get(reverse("club:landing"))
        assert_csp_clean(self, response)
        self.assertContains(response, "Plus jamais d'inconnus au Club.")
        self.assertContains(response, reverse("club:join"))
        self.assertContains(response, reverse("login"))

    def test_landing_shows_only_aggregate_numbers_of_active_members(self):
        response = self.client.get(reverse("club:landing"))
        self.assertEqual(response.context["member_count"], 2)
        self.assertEqual(response.context["sector_count"], 2)  # the inactive member's sector does not count
        self.assertContains(response, "4–5")

    def test_landing_never_names_a_member(self):
        html = self.client.get(reverse("club:landing")).content.decode()
        for word in ("Imboden", "Lukas", "Camille", "Rey", "example.com", "Loin", "Lärchenwerk"):
            self.assertNotIn(word, html)

    def test_landing_is_the_same_for_a_logged_in_member(self):
        self.client.force_login(self.lukas.user)
        self.assertEqual(self.client.get(reverse("club:landing")).status_code, 200)


@override_settings(MEMBERSHIP_PRICE=500, REFERRAL_NEW_MEMBER_PRICE=350, REFERRAL_SPONSOR_DISCOUNT=100, REFERRAL_OFFER_ENABLED=True)
class InvitePageTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com", first_name="Alice", last_name="Aubert")
        self.bob = make_member("bob@example.com", first_name="Bob", last_name="Bonvin")
        self.url = reverse("club:invite")

    def invitation(self, sponsor, **extra):
        data = {"first_name": "Invité", "last_name": "Test", "company": "Test SA", "job_title": "CEO",
                "email": "invite@exemple.ch", "referred_by": sponsor}
        data.update(extra)
        return InvitationRequest.objects.create(**data)

    def test_visitors_are_sent_to_login_and_staff_without_profile_to_the_dashboard(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.client.force_login(make_staff())
        self.assertRedirects(self.client.get(self.url), reverse("club:staff_dashboard"))

    def test_page_shows_my_personal_link_qr_and_the_offer(self):
        self.client.force_login(self.alice.user)
        response = self.client.get(self.url)
        assert_csp_clean(self, response)
        link = "http://testserver" + reverse("club:join") + "?ref=" + self.alice.referral_code
        self.assertContains(response, f'value="{link}"')
        self.assertNotContains(response, self.bob.referral_code)
        self.assertContains(response, "<svg viewBox=")
        self.assertContains(response, "350 CHF")
        self.assertContains(response, "500 CHF")
        self.assertContains(response, "−100 CHF")
        self.assertContains(response, 'data-copy="#invite-link"')
        self.assertContains(response, "js/copy.js")

    def test_the_link_works_for_a_visitor(self):
        self.client.force_login(self.alice.user)
        link = self.client.get(self.url).context["invite_link"]
        self.client.logout()
        response = self.client.get(link)
        self.assertContains(response, "Invité·e par Alice A.")

    def test_page_lists_only_my_invitees_with_their_status(self):
        mine = self.invitation(self.alice, first_name="Julie", last_name="Perrin", status="contacted")
        self.invitation(self.bob, first_name="Marc", last_name="Pasamoi", email="marc@exemple.ch")
        self.invitation(None, first_name="Spontané", last_name="Visiteur", email="spontane@exemple.ch")
        self.client.force_login(self.alice.user)
        response = self.client.get(self.url)
        self.assertContains(response, "Julie Perrin")
        self.assertContains(response, "Contactée")
        self.assertNotContains(response, "Pasamoi")
        self.assertNotContains(response, "Visiteur")
        self.assertEqual(list(response.context["referrals"]), [mine])

    def test_empty_state(self):
        self.client.force_login(self.alice.user)
        self.assertContains(self.client.get(self.url), "Personne pour l'instant")

    def test_invite_link_is_reachable_from_home_and_profile(self):
        self.client.force_login(self.alice.user)
        for name in ("club:home", "club:profile_edit"):
            self.assertContains(self.client.get(reverse(name)), f'href="{self.url}"')


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DemoReferralTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.lukas = Member.objects.get(user__email="lukas.imboden@example.com")

    def test_lukas_has_two_invitees_and_the_staff_sees_two_new_requests(self):
        self.client.force_login(self.lukas.user)
        page = self.client.get(reverse("club:invite"))
        self.assertContains(page, "Julie Perrin")
        self.assertContains(page, "Markus Zenhäusern")
        self.client.force_login(make_staff("chef@example.com"))
        dashboard = self.client.get(reverse("club:staff_dashboard"))
        self.assertContains(dashboard, "2 nouvelles demandes")
        self.assertContains(dashboard, "Anne-Laure Dubuis")


class LandingFiguresTests(TestCase):
    def test_members_are_shown_as_a_round_figure_that_stays_true(self):
        for i in range(12):
            make_member(f"m{i}@example.com", sector="tech" if i % 2 else "finance")
        make_member("new@example.com", sector="other")  # a new account that has not picked its sector yet
        response = self.client.get(reverse("club:landing"))
        self.assertContains(response, ">10+</p>")
        self.assertEqual(response.context["sector_count"], 2)  # "Autre secteur" is not a sector of the Club

    def test_a_small_club_shows_its_exact_count(self):
        for i in range(3):
            make_member(f"m{i}@example.com")
        self.assertContains(self.client.get(reverse("club:landing")), ">3</p>")
