import smtplib
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from club.models import RSVP, EmailPreferences, Event, NotificationCampaign, NotificationDelivery
from club.services.notifications import claim_delivery, prepare_reminders, process_notifications, publish_event
from club.tests.helpers import make_member, make_staff


@override_settings(NOTIFICATIONS_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   PUBLIC_BASE_URL="https://club.example", PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class NotificationTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.clock = patch("django.utils.timezone.now", return_value=self.now)
        self.clock.start()
        self.addCleanup(lambda: self.clock.stop())
        self.staff = make_staff()
        self.a = make_member("a@example.com")
        self.b = make_member("b@example.com", preferred_language="de")
        self.event = Event.objects.create(title="Soirée", title_de="Abend", title_en="Evening", location="Martigny",
                                          kind="dinner", starts_at=self.now + timedelta(days=30))

    def announce(self):
        publish_event(self.event.pk, self.staff)
        return process_notifications(now=self.now)

    def advance(self, days):
        self.now += timedelta(days=days)
        self.clock.stop()
        self.clock = patch("django.utils.timezone.now", return_value=self.now)
        self.clock.start()

    def test_one_delivery_per_recipient_and_repeated_publication_or_execution_is_safe(self):
        self.assertEqual(self.announce()["sent"], 2)
        publish_event(self.event.pk, self.staff)
        self.assertEqual(process_notifications(now=self.now)["sent"], 0)
        self.assertEqual(NotificationCampaign.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, [self.a.user.email])
        self.assertEqual(mail.outbox[0].cc, [])
        self.assertIn("Nouvel événement", mail.outbox[0].subject)
        self.assertIn("Abend", mail.outbox[1].subject)
        for message in mail.outbox:
            self.assertIn("https://club.example/evenements/", message.body)
            self.assertNotIn("sesame", message.body)
            self.assertEqual(message.alternatives[0].mimetype, "text/html")

    def test_reminders_are_for_no_response_and_stop_after_any_response(self):
        self.announce()
        self.advance(16)
        RSVP.objects.create(member=self.b, event=self.event, status="no")
        self.assertEqual(prepare_reminders(self.now), 1)
        self.assertEqual(process_notifications(now=self.now)["sent"], 1)
        self.advance(11)
        prepare_reminders(self.now)
        RSVP.objects.create(member=self.a, event=self.event, status="yes")
        self.assertEqual(process_notifications(now=self.now)["skipped"], 1)
        self.assertEqual(len(mail.outbox), 3)

    def test_two_stages_at_most_and_72_hour_spacing(self):
        self.announce()
        self.advance(16)
        self.assertEqual(process_notifications(now=self.now)["sent"], 2)
        self.assertEqual(process_notifications(now=self.now)["sent"], 0)
        self.advance(11)
        self.assertEqual(process_notifications(now=self.now)["sent"], 2)
        self.advance(1)
        self.assertEqual(process_notifications(now=self.now)["sent"], 0)
        self.assertEqual(len(mail.outbox), 6)

    def test_late_publication_and_scheduler_restart_only_latest_stage(self):
        self.event.starts_at = self.now + timedelta(days=5)
        self.event.save()
        self.announce()
        self.advance(2)
        self.assertEqual(prepare_reminders(self.now), 0)  # 72h not reached
        self.advance(1)
        self.assertEqual(process_notifications(now=self.now)["sent"], 2)
        self.assertFalse(NotificationCampaign.objects.filter(scope_key__endswith=":14").exists())

    def test_preferences_and_inactive_rechecked_before_send(self):
        publish_event(self.event.pk, self.staff)
        EmailPreferences.objects.create(member=self.a, event_announcements=False)
        self.b.user.is_active = False
        self.b.user.save()
        self.assertEqual(process_notifications(now=self.now)["skipped"], 2)
        self.assertEqual(len(mail.outbox), 0)

    def test_dry_run_changes_nothing_even_with_due_work(self):
        self.announce()
        self.advance(28)
        before = list(NotificationDelivery.objects.values())
        campaigns = list(NotificationCampaign.objects.values())
        call_command("process_notifications", dry_run=True, stdout=StringIO())
        self.assertEqual(before, list(NotificationDelivery.objects.values()))
        self.assertEqual(campaigns, list(NotificationCampaign.objects.values()))
        self.assertFalse(EmailPreferences.objects.exists())
        self.assertEqual(len(mail.outbox), 2)

    def test_confirmed_failure_has_three_attempts_and_ambiguous_is_not_retried(self):
        publish_event(self.event.pk, self.staff)
        with patch("club.services.notifications.EmailMultiAlternatives.send", side_effect=smtplib.SMTPDataError(550, b"rejected")):
            self.assertEqual(process_notifications(now=self.now)["failed"], 2)
            for minutes in (15, 60, 60):
                self.now += timedelta(minutes=minutes)
                self.clock.stop()
                self.clock = patch("django.utils.timezone.now", return_value=self.now)
                self.clock.start()
                process_notifications(now=self.now)
        self.assertEqual(set(NotificationDelivery.objects.values_list("attempts", flat=True)), {3})
        NotificationDelivery.objects.update(status="pending", attempts=0)
        with patch("club.services.notifications.EmailMultiAlternatives.send", side_effect=TimeoutError()):
            self.assertEqual(process_notifications(now=self.now)["uncertain"], 2)
        self.assertEqual(process_notifications(now=self.now)["sent"], 0)

    def test_conditional_claim_and_abandoned_claim(self):
        publish_event(self.event.pk, self.staff)
        delivery = NotificationDelivery.objects.first()
        self.assertTrue(claim_delivery(delivery.pk, self.now))
        self.assertFalse(claim_delivery(delivery.pk, self.now))
        NotificationDelivery.objects.filter(pk=delivery.pk).update(claimed_at=self.now - timedelta(minutes=16))
        process_notifications(now=self.now)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "uncertain")

    def test_welcome_link_is_created_at_send_time_and_date_only_after_smtp_acceptance(self):
        from club.models import InvitationRequest
        from club.services.membership import accept_invitation
        invitation = InvitationRequest.objects.create(first_name="Nouveau", last_name="Fictif", company="Test",
            job_title="Direction", email="new@example.com", language="en")
        with patch("club.services.notifications.get_query_string", return_value="?sesame=fresh") as token:
            member = accept_invitation(invitation.pk, self.staff)
            token.assert_not_called()
            invitation.refresh_from_db()
            self.assertIsNone(invitation.welcome_sent_at)
            process_notifications(now=self.now)
            token.assert_called_once_with(member.user)
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.welcome_sent_at)
        self.assertIn("Welcome", mail.outbox[0].subject)
        self.assertIn("?sesame=fresh", mail.outbox[0].body)
        self.assertIn("Your account is ready", mail.outbox[0].alternatives[0].content)

    def test_restart_does_not_catch_up_two_stages_and_deleted_event_is_skipped(self):
        self.announce()
        self.advance(28)
        self.assertEqual(process_notifications(now=self.now)["sent"], 2)
        self.assertFalse(NotificationCampaign.objects.filter(scope_key__endswith=":14").exists())
        self.assertTrue(NotificationCampaign.objects.filter(scope_key__endswith=":3").exists())
        self.event.delete()
        self.assertEqual(process_notifications(now=self.now)["sent"], 0)

    def test_english_event_content_and_removed_reminder_preference(self):
        self.b.preferred_language = "en"
        self.b.save()
        self.announce()
        self.assertEqual(mail.outbox[1].subject, "New event: Evening")
        self.assertIn("Discover this event", mail.outbox[1].body)
        self.advance(16)
        prepare_reminders(self.now)
        EmailPreferences.objects.create(member=self.b, event_reminders=False)
        self.assertEqual(process_notifications(now=self.now)["skipped"], 1)

    @override_settings(NOTIFICATIONS_ENABLED=False)
    def test_send_requires_explicit_activation(self):
        publish_event(self.event.pk, self.staff)
        with self.assertRaises(ValidationError):
            process_notifications()
        self.assertEqual(set(NotificationDelivery.objects.values_list("status", flat=True)), {"pending"})
