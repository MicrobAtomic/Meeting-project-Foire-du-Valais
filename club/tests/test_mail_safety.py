from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase, override_settings

from club.models import NotificationCampaign, NotificationDelivery
from club.services.auth_links import send_login_link
from club.services.notifications import process_notifications
from club.tests.helpers import make_member


@override_settings(DEMO_MODE=True, NOTIFICATIONS_ENABLED=True,
                   EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DemoMailSafetyTests(TestCase):
    def test_direct_login_links_cannot_use_smtp_in_demo_mode(self):
        member = make_member("demo@example.com")
        with patch("club.services.auth_links.send_mail") as send:
            with self.assertRaises(ValidationError):
                send_login_link(RequestFactory().get("/", HTTP_HOST="localhost"), member)
            send.assert_not_called()

    def test_queued_notifications_cannot_open_smtp_or_change_state_in_demo_mode(self):
        member = make_member("demo@example.com")
        campaign = NotificationCampaign.objects.create(kind="welcome", scope_key="demo:guard")
        delivery = NotificationDelivery.objects.create(campaign=campaign, recipient=member)
        with patch("club.services.notifications.get_connection") as backend:
            with self.assertRaises(ValidationError):
                process_notifications()
            backend.assert_not_called()
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "pending")
        self.assertEqual(delivery.attempts, 0)
