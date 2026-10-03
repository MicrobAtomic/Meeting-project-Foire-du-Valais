from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from club.models import RSVP, Connection, Event, Match, SeatingPlan
from club.tests.helpers import PASSWORD, make_member


class AdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser("admin@example.com", "admin@example.com", PASSWORD)
        self.client.force_login(self.admin_user)
        self.members = [make_member(f"m{i}@example.com", sector=["tech", "finance"][i % 2]) for i in range(8)]
        self.event = Event.objects.create(is_published=True, title="Dîner", kind="dinner", location="Martigny",
                                          starts_at=timezone.now() + timedelta(days=3), has_seating=True)
        for member in self.members:
            RSVP.objects.create(event=self.event, member=member, status=RSVP.Status.YES)

    def test_every_changelist_loads(self):
        for model in ["member", "event", "tag", "connection", "match", "seatingplan", "invitationrequest"]:
            url = reverse(f"admin:club_{model}_changelist")
            self.assertEqual(self.client.get(url).status_code, 200, url)
        url = reverse("admin:club_member_change", args=[self.members[0].pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_event_actions_generate_matches_and_seating(self):
        url = reverse("admin:club_event_changelist")
        for action in ["make_matches", "make_seating"]:
            self.client.post(url, {"action": action, "_selected_action": [self.event.pk]})
        self.assertTrue(Match.objects.filter(event=self.event).exists())
        self.assertEqual(SeatingPlan.objects.get(event=self.event).assignments.count(), 8 * 3)

    def test_connection_form_orders_the_pair(self):
        high, low = sorted(self.members[:2], key=lambda m: -m.pk)
        url = reverse("admin:club_connection_add")
        response = self.client.post(url, {"member_a": high.pk, "member_b": low.pk, "source": "admin",
                                          "created_at_0": "2026-10-03", "created_at_1": "12:00:00"})
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["adminform"].errors)
        connection = Connection.objects.get()
        self.assertLess(connection.member_a_id, connection.member_b_id)
