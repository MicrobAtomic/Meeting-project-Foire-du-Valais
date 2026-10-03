import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from club.tests.helpers import PASSWORD, assert_csp_clean, make_member, make_staff

LINK = re.compile(r"https?://\S+/connexion/lien/\?sesame=\S+")


class MagicLinkRequestTests(TestCase):
    def setUp(self):
        cache.clear()  # the one-mail-per-minute guard lives in the cache
        self.alice = make_member("alice@example.com", first_name="Alice")
        self.url = reverse("club:magic_link_request")

    def answer(self, email, client=None):
        response = (client or self.client).post(self.url, {"email": email}, follow=True)
        return response, [str(m) for m in response.context["messages"]]

    def test_page_is_public_csp_clean_and_linked_from_the_login_page(self):
        assert_csp_clean(self, self.client.get(self.url))
        self.assertContains(self.client.get(reverse("login")), f'href="{self.url}"')
        self.assertContains(self.client.get(reverse("login")), "Recevoir un lien de connexion par e-mail")

    def test_known_member_gets_exactly_one_email_with_a_working_one_time_link(self):
        response, messages = self.answer("Alice@Example.com")
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["alice@example.com"])
        self.assertEqual(message.subject, "Ton accès au Club des Affaires")
        self.assertIn("/connexion/lien/?sesame=", message.body)
        self.assertIn("15 minutes", message.body)
        self.assertIn("Salut Alice", message.body)
        link = LINK.search(message.body).group(0)
        # a fresh browser (the phone that opens the e-mail) is logged in by the link...
        phone = Client()
        self.assertEqual(phone.get(link).status_code, 302)
        self.assertEqual(phone.get(reverse("club:home")).status_code, 200)
        # ...but it works only once
        other = Client()
        expired = other.get(link)
        self.assertEqual(expired.status_code, 403)
        self.assertContains(expired, "Ce lien n&#x27;est plus valable".replace("&#x27;", "'"), status_code=403)

    def test_unknown_address_gets_the_same_answer_and_no_email(self):
        known, known_messages = self.answer("alice@example.com")
        mail.outbox.clear()
        stranger, stranger_messages = self.answer("inconnu@example.com", Client())
        self.assertEqual(mail.outbox, [])
        self.assertEqual(known_messages, stranger_messages)
        self.assertEqual(known_messages, ["Si cette adresse est connue, un lien vient d'être envoyé."])
        self.assertEqual(known.redirect_chain, stranger.redirect_chain)
        self.assertEqual(known.status_code, stranger.status_code)

    def test_inactive_members_and_staff_accounts_get_nothing(self):
        self.alice.user.is_active = False
        self.alice.user.save()
        self.answer("alice@example.com")
        make_staff("equipe@example.com")
        self.answer("equipe@example.com")
        self.assertEqual(mail.outbox, [])

    def test_one_email_per_address_and_minute(self):
        for _ in range(3):
            _response, messages = self.answer("alice@example.com")
            self.assertEqual(len(messages), 1)  # always the same friendly answer
        self.assertEqual(len(mail.outbox), 1)
        cache.clear()
        self.answer("alice@example.com")
        self.assertEqual(len(mail.outbox), 2)

    def test_invalid_address_shows_the_form_error_and_sends_nothing(self):
        response = self.client.post(self.url, {"email": "pas-un-email"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="alert"')
        self.assertEqual(mail.outbox, [])

    def test_csrf_token_is_required(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(self.url, {"email": "alice@example.com"}).status_code, 403)
        self.assertEqual(mail.outbox, [])

    def test_a_failing_mail_server_does_not_change_the_answer(self):
        with mock.patch("club.views.public.send_login_link", side_effect=OSError("SMTP down")):
            with self.assertLogs("club.views.public", level="ERROR"):  # the failure is logged, not shown
                response, messages = self.answer("alice@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(messages, ["Si cette adresse est connue, un lien vient d'être envoyé."])

    def test_email_is_written_in_the_language_the_member_reads(self):
        german = make_member("hans@example.com", first_name="Hans", speaks_fr=False, speaks_de=True)
        english = make_member("eve@example.com", first_name="Eve", speaks_fr=False, speaks_en=True)
        bilingual = make_member("marie@example.com", first_name="Marie", speaks_de=True)
        for address in ("hans@example.com", "eve@example.com", "marie@example.com"):
            self.answer(address)
        by_recipient = {m.to[0]: m for m in mail.outbox}
        self.assertEqual(by_recipient["hans@example.com"].subject, "Dein Zugang zum Club des Affaires")
        self.assertIn("Hallo Hans", by_recipient["hans@example.com"].body)
        self.assertEqual(by_recipient["eve@example.com"].subject, "Your access to the Club des Affaires")
        self.assertIn("Hi Eve", by_recipient["eve@example.com"].body)
        self.assertEqual(by_recipient["marie@example.com"].subject, "Ton accès au Club des Affaires")  # speaks French too


class MagicLoginPageTests(TestCase):
    def test_garbage_or_missing_token_gets_the_friendly_page_with_a_403(self):
        for url in (reverse("magic_login") + "?sesame=garbage", reverse("magic_login")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
            self.assertContains(response, "Recevoir un nouveau lien", status_code=403)
            self.assertContains(response, reverse("club:magic_link_request"), status_code=403)
            self.assertIn("script-src 'self'", response["Content-Security-Policy"])

    def test_next_parameter_cannot_redirect_to_another_site(self):
        from club.services.auth_links import login_link

        member = make_member("alice@example.com")
        request = self.client.get(reverse("club:landing")).wsgi_request
        link = login_link(request, member)
        response = self.client.get(link + "&next=https://evil.example.org/")
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("evil.example.org", response.url)


class AdminLoginLinkActionTests(TestCase):
    def test_admin_can_send_login_links_to_selected_members(self):
        admin_user = get_user_model().objects.create_superuser("admin@example.com", "admin@example.com", PASSWORD)
        self.client.force_login(admin_user)
        active = make_member("alice@example.com")
        inactive = make_member("bob@example.com")
        inactive.user.is_active = False
        inactive.user.save()
        response = self.client.post(
            reverse("admin:club_member_changelist"),
            {"action": "send_login_links", "_selected_action": [active.pk, inactive.pk]},
            follow=True,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])
        self.assertContains(response, "1 lien envoyé")
