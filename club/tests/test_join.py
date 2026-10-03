from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from club.models import InvitationRequest
from club.tests.helpers import PASSWORD, assert_csp_clean, make_member


def valid_data(**extra):
    data = {"first_name": "Marie", "last_name": "Dupont", "email": "Marie.Dupont@Exemple.CH",
            "company": "Dupont SA", "job_title": "Directrice", "website": ""}
    data.update(extra)
    return data


class JoinFormTests(TestCase):
    def setUp(self):
        self.url = reverse("club:join")

    def test_login_page_links_to_the_form_and_the_form_is_public(self):
        login = self.client.get(reverse("login"))
        self.assertContains(login, f'href="{self.url}"')
        self.assertContains(login, "Demander une invitation")
        page = self.client.get(self.url)  # anonymous: no redirect to the login
        assert_csp_clean(self, page)
        for name in ("first_name", "last_name", "email", "company", "job_title"):
            self.assertContains(page, f'name="{name}"')
        self.assertNotContains(page, 'name="message"')  # mini form

    def test_valid_submission_is_stored_and_the_visitor_thanked(self):
        response = self.client.post(self.url, valid_data())
        self.assertRedirects(response, reverse("club:join_thanks"))
        request = InvitationRequest.objects.get()
        self.assertEqual((request.first_name, request.last_name, request.company, request.job_title),
                         ("Marie", "Dupont", "Dupont SA", "Directrice"))
        self.assertEqual(request.email, "marie.dupont@exemple.ch")  # normalised
        self.assertEqual(request.status, InvitationRequest.Status.NEW)
        self.assertIsNone(request.referred_by)
        thanks = self.client.get(reverse("club:join_thanks"))
        assert_csp_clean(self, thanks)
        self.assertContains(thanks, "Merci pour ta demande")

    def test_invalid_submission_shows_errors_and_stores_nothing(self):
        response = self.client.post(self.url, valid_data(email="pas-un-email", company=""))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'value="Marie"')  # what was typed is kept
        self.assertFalse(InvitationRequest.objects.exists())

    def test_honeypot_stores_nothing_but_looks_successful(self):
        response = self.client.post(self.url, valid_data(website="http://spam.example"))
        self.assertRedirects(response, reverse("club:join_thanks"))
        self.assertFalse(InvitationRequest.objects.exists())

    def test_double_submission_within_a_day_is_stored_once(self):
        self.client.post(self.url, valid_data())
        self.client.post(self.url, valid_data(email="MARIE.DUPONT@exemple.ch", first_name="Autre"))
        self.assertEqual(InvitationRequest.objects.count(), 1)
        InvitationRequest.objects.update(created_at=timezone.now() - timedelta(hours=25))
        self.client.post(self.url, valid_data())
        self.assertEqual(InvitationRequest.objects.count(), 2)

    def test_csrf_token_is_required(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(self.url, valid_data()).status_code, 403)
        self.assertFalse(InvitationRequest.objects.exists())

    def test_page_accepts_only_get_and_post(self):
        self.assertEqual(self.client.put(self.url).status_code, 405)


class ReferralLinkTests(TestCase):
    def setUp(self):
        self.sponsor = make_member("camille@example.com", first_name="Camille", last_name="Rey")

    def url(self, code):
        return reverse("club:join") + f"?ref={code}"

    def test_valid_code_is_announced_and_recorded(self):
        page = self.client.get(self.url(self.sponsor.referral_code.lower()))  # case-insensitive
        self.assertContains(page, "Invité·e par Camille R.")
        self.client.post(self.url(self.sponsor.referral_code), valid_data())
        self.assertEqual(InvitationRequest.objects.get().referred_by, self.sponsor)

    def test_unknown_code_is_ignored_without_any_message(self):
        page = self.client.get(self.url("ZZZZZZZZ"))
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "Invité")
        self.client.post(self.url("ZZZZZZZZ"), valid_data())
        self.assertIsNone(InvitationRequest.objects.get().referred_by)

    def test_code_of_an_inactive_member_is_ignored(self):
        self.sponsor.user.is_active = False
        self.sponsor.user.save()
        self.assertNotContains(self.client.get(self.url(self.sponsor.referral_code)), "Invité")

    def test_the_public_form_never_lists_members(self):
        page = self.client.get(self.url(self.sponsor.referral_code))
        self.assertNotContains(page, self.sponsor.user.email)
        self.assertNotContains(page, "Rey")  # only "Camille R." (first name + initial)


class SessionLengthTests(TestCase):
    SIX_MONTHS = 180 * 24 * 60 * 60

    def test_login_keeps_the_member_connected_for_six_months(self):
        member = make_member("alice@example.com")
        response = self.client.post(reverse("login"), {"username": "alice@example.com", "password": PASSWORD})
        self.assertEqual(int(response.cookies["sessionid"]["max-age"]), self.SIX_MONTHS)

    def test_every_visit_pushes_the_expiry_back(self):
        member = make_member("alice@example.com")
        self.client.force_login(member.user)
        response = self.client.get(reverse("club:home"))
        self.assertEqual(int(response.cookies["sessionid"]["max-age"]), self.SIX_MONTHS)
