from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core import mail, signing
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from club.models import DigestEntry, EmailPreferences, NotificationCampaign, PersonalNote
from club.services.digests import UNSUBSCRIBE_SALT, prepare_digest, unsubscribe_token
from club.services.notifications import process_notifications
from club.tests.helpers import assert_csp_clean, make_member


@override_settings(NOTIFICATIONS_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   PUBLIC_BASE_URL="https://club.example", PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DigestTests(TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 1, 9, tzinfo=ZoneInfo("Europe/Zurich"))
        self.reader = make_member("reader@example.com")
        EmailPreferences.objects.create(member=self.reader, monthly_digest=True)

    def candidate(self, index=1, **extra):
        fields = {"admitted_at": self.now - timedelta(days=2), "onboarding_done": True,
                  "first_name": f"Nouveau{index}", "last_name": "Fictif", "digest_teaser": "Accroche choisie"}
        fields.update(extra)
        member = make_member(f"person{index}@example.com", **fields)
        EmailPreferences.objects.create(member=member, allow_member_spotlight=True)
        return member

    def test_zero_one_many_and_one_campaign_per_month(self):
        self.assertEqual(prepare_digest(self.now), 0)
        self.assertFalse(NotificationCampaign.objects.exists())
        candidate = self.candidate()
        self.assertEqual(process_notifications(now=self.now)["sent"], 1)
        self.assertEqual(mail.outbox[0].subject, "Un nouveau visage au Club !")
        self.assertEqual(prepare_digest(self.now), 0)
        self.assertEqual(DigestEntry.objects.get().member, candidate)
        self.candidate(2)
        self.assertEqual(prepare_digest(self.now), 0)
        self.assertEqual(NotificationCampaign.objects.count(), 1)

    def test_eligibility_and_late_completion(self):
        historical = self.candidate(1, admitted_at=None)
        incomplete = self.candidate(2, onboarding_done=False)
        this_month = self.candidate(3, admitted_at=self.now)
        hidden = self.candidate(4, visible_in_directory=False)
        unconsenting = self.candidate(5)
        unconsenting.email_preferences.allow_member_spotlight = False
        unconsenting.email_preferences.save()
        self.assertEqual(prepare_digest(self.now), 0)
        incomplete.onboarding_done = True
        incomplete.save()
        self.assertEqual(prepare_digest(self.now + timedelta(days=30)), 1)
        self.assertEqual(set(DigestEntry.objects.values_list("member_id", flat=True)), {incomplete.pk, this_month.pk})

    def test_four_previews_only_and_no_private_data_in_text_or_html(self):
        for index in range(10):
            candidate = self.candidate(index, phone="SECRET-PHONE", linkedin_url="https://example.com/SECRET-LINKEDIN",
                                        fun_fact="SECRET-ANECDOTE", digest_teaser="x" * 120)
            PersonalNote.objects.create(owner=self.reader, target=candidate, text="SECRET-NOTE")
        self.assertEqual(process_notifications(now=self.now)["sent"], 1)
        message = mail.outbox[0]
        self.assertIn("De nouveaux visages", message.subject)
        for content in (message.body, message.alternatives[0].content):
            self.assertEqual(content.count("https://club.example/membres/"), 4)
            for secret in ("SECRET-PHONE", "SECRET-LINKEDIN", "SECRET-ANECDOTE", "SECRET-NOTE", "person0@example.com", "x" * 81):
                self.assertNotIn(secret, content)
            self.assertNotIn("<img", content)
            self.assertNotIn("sesame=", content)
        self.assertIn("(6)", message.body)

    def test_recheck_visibility_and_recipient_preference_before_send(self):
        candidate = self.candidate()
        prepare_digest(self.now)
        candidate.visible_in_directory = False
        candidate.save()
        self.assertEqual(process_notifications(now=self.now)["skipped"], 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_dry_run_and_swiss_nine_am_guard(self):
        self.candidate()
        self.assertEqual(prepare_digest(self.now - timedelta(minutes=1)), 0)
        self.assertEqual(prepare_digest(self.now, dry_run=True), 1)
        self.assertFalse(DigestEntry.objects.exists())
        self.assertFalse(NotificationCampaign.objects.exists())

    def test_a_digest_containing_only_recipient_is_not_created(self):
        self.reader.admitted_at = self.now - timedelta(days=3)
        self.reader.onboarding_done = True
        self.reader.save()
        prefs = self.reader.email_preferences
        prefs.allow_member_spotlight = True
        prefs.save()
        self.assertEqual(prepare_digest(self.now), 0)

    def test_digest_text_and_html_follow_recipient_language(self):
        for language, title, body in (("de", "Ein neues Gesicht", "Entdecke"), ("en", "A new face", "Discover")):
            self.reader.preferred_language = language
            self.reader.save()
            candidate = self.candidate(1 if language == "de" else 2)
            moment = self.now if language == "de" else self.now + timedelta(days=30)
            process_notifications(now=moment)
            self.assertIn(title, mail.outbox[-1].subject)
            self.assertIn(body, mail.outbox[-1].body)
            self.assertIn(body, mail.outbox[-1].alternatives[0].content)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class UnsubscribeTests(TestCase):
    def setUp(self):
        self.member = make_member("private@example.com")
        self.preferences = EmailPreferences.objects.create(member=self.member, monthly_digest=True)
        self.token = unsubscribe_token(self.member)
        self.url = reverse("club:email_unsubscribe", args=[self.token])

    def test_get_confirms_without_change_and_post_changes_only_digest(self):
        page = self.client.get(self.url)
        assert_csp_clean(self, page)
        self.assertNotContains(page, self.member.user.email)
        self.preferences.refresh_from_db()
        self.assertTrue(self.preferences.monthly_digest)
        self.client.post(self.url)
        self.preferences.refresh_from_db()
        self.assertFalse(self.preferences.monthly_digest)
        self.assertTrue(self.preferences.event_announcements)
        self.assertTrue(self.preferences.event_reminders)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_signature_purpose_expiry_and_csrf(self):
        invalid = [self.token + "altered", signing.dumps({"member": self.member.pk, "purpose": "event_announcements"}, salt=UNSUBSCRIBE_SALT)]
        with patch("django.core.signing.time.time", return_value=1):
            invalid.append(unsubscribe_token(self.member))
        for token in invalid:
            response = self.client.post(reverse("club:email_unsubscribe", args=[token]))
            self.assertEqual(response.status_code, 400)
            self.assertNotContains(response, self.member.user.email, status_code=400)
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(self.url).status_code, 403)
        self.preferences.refresh_from_db()
        self.assertTrue(self.preferences.monthly_digest)
