from datetime import timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from club.models import Event, NotificationCampaign, RSVP
from club.services.notifications import cancel_event, publish_event
from club.tests.helpers import make_member, make_staff


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class EventPublicationTests(TestCase):
    def setUp(self):
        self.member = make_member("a@example.com")
        self.staff = make_staff()
        self.event = Event.objects.create(title="BROUILLON-SECRET", location="Sion", kind="apero",
                                          starts_at=timezone.now() + timedelta(days=5))
        self.client.force_login(self.member.user)

    def test_save_never_publishes_or_sends_and_draft_is_invisible(self):
        self.event.save()
        self.assertFalse(NotificationCampaign.objects.exists())
        for route in ("club:home", "club:event_list"):
            self.assertNotContains(self.client.get(reverse(route)), self.event.title)
        for route in ("club:event_detail", "club:event_rsvp"):
            self.assertEqual(self.client.get(reverse(route, args=[self.event.pk])).status_code, 404 if route.endswith("detail") else 405)
        self.assertEqual(self.client.post(reverse("club:event_rsvp", args=[self.event.pk]), {"status": "yes"}).status_code, 404)

    def test_cancelled_or_closed_event_keeps_history_but_refuses_answers(self):
        publish_event(self.event.pk, self.staff)
        cancel_event(self.event.pk, self.staff)
        self.assertContains(self.client.get(reverse("club:event_detail", args=[self.event.pk])), "Événement annulé")
        self.client.post(reverse("club:event_rsvp", args=[self.event.pk]), {"status": "yes"})
        self.assertFalse(RSVP.objects.exists())
        self.assertTrue(NotificationCampaign.objects.get().cancelled_at)
