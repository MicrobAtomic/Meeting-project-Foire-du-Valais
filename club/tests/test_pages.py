from django.test import TestCase
from django.urls import reverse

from club.models import Connection
from club.tests.helpers import PASSWORD, assert_csp_clean, make_member, make_staff


class BasePagesTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com", first_name="Alice")
        self.bob = make_member("bob@example.com")
        self.staff = make_staff()

    def test_login_page_is_styled_and_csp_clean(self):
        response = self.client.get(reverse("login"))
        assert_csp_clean(self, response)
        self.assertContains(response, "Espace membres du Club des Affaires")
        self.assertContains(response, 'name="username"')

    def test_wrong_password_shows_a_friendly_error(self):
        response = self.client.post(reverse("login"), {"username": "alice@example.com", "password": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-mail ou mot de passe incorrect.")

    def test_landing_is_public_and_csp_clean(self):
        assert_csp_clean(self, self.client.get(reverse("club:landing")))

    def test_home_greets_member_and_shows_federation_index(self):
        Connection.link(self.alice, self.bob)
        self.client.force_login(self.alice.user)
        response = self.client.get(reverse("club:home"))
        assert_csp_clean(self, response)
        self.assertContains(response, "Salut Alice")
        self.assertContains(response, "1 / 1 cartes")
        self.assertContains(response, "Le Club est connecté à 100")  # 2 members, 1 connection

    def test_navigation_matches_the_role(self):
        self.client.force_login(self.alice.user)
        member_page = self.client.get(reverse("club:home"))
        self.assertContains(member_page, reverse("club:my_qr"))
        self.assertNotContains(member_page, reverse("club:staff_dashboard"))
        self.client.force_login(self.staff)
        staff_page = self.client.get(reverse("club:staff_dashboard"))
        assert_csp_clean(self, staff_page)
        self.assertContains(staff_page, reverse("club:staff_dashboard"))
        self.assertNotContains(staff_page, reverse("club:my_qr"))

    def test_logout_is_a_post_form_never_a_link(self):
        self.client.force_login(self.alice.user)
        html = self.client.get(reverse("club:home")).content.decode()
        self.assertIn(f'<form method="post" action="{reverse("logout")}">', html)
        self.assertNotIn(f'href="{reverse("logout")}"', html)

    def test_language_switch_sets_the_cookie_and_returns_to_the_page(self):
        response = self.client.post(reverse("set_language"), {"language": "de", "next": reverse("club:landing")})
        self.assertRedirects(response, reverse("club:landing"), fetch_redirect_response=False)
        self.assertEqual(response.cookies["django_language"].value, "de")

    def test_error_pages_use_the_site_design(self):
        self.client.force_login(self.alice.user)
        not_found = self.client.get("/cette-page-nexiste-pas/")
        self.assertEqual(not_found.status_code, 404)
        self.assertContains(not_found, "perdue en montagne", status_code=404)
        forbidden = self.client.get(reverse("club:staff_dashboard"))
        self.assertContains(forbidden, "Cette porte est réservée", status_code=403)

    def test_staff_dashboard_shows_the_three_tiles(self):
        Connection.link(self.alice, self.bob)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("club:staff_dashboard"))
        self.assertContains(response, "Rencontres enregistrées")
        self.assertContains(response, "Indice de fédération")
        self.assertContains(response, reverse("admin:index"))


class HeadingTests(TestCase):
    def test_member_page_has_exactly_one_h1_with_the_name(self):
        alice = make_member("alice@example.com", first_name="Alice", last_name="Aubert")
        bob = make_member("bob@example.com", first_name="Bob", last_name="Bonvin")
        self.client.force_login(alice.user)
        html = self.client.get(reverse("club:member_detail", args=[bob.pk])).content.decode()
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn(">Bob Bonvin</h1>", html)

    def test_list_cards_keep_a_small_heading(self):
        alice = make_member("alice@example.com")
        make_member("bob@example.com", first_name="Bob", last_name="Bonvin")
        self.client.force_login(alice.user)
        html = self.client.get(reverse("club:album")).content.decode()
        self.assertEqual(html.count("<h1"), 1)  # the page title only
        self.assertIn(">Bob Bonvin</h3>", html)
