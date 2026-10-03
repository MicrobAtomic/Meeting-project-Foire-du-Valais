from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from club.models import Event, SeatingPlan
from club.tests.helpers import make_staff


class EventAdminTests(TestCase):
    """The event form has one box per language and one for the animations; seating only for a seated dinner."""

    def setUp(self):
        user = make_staff()
        user.is_superuser = True
        user.save()
        self.client.force_login(user)
        self.event = Event.objects.create(is_published=True, title="Apéro", kind="apero", location="Sion",
                                          starts_at=timezone.now() + timedelta(days=4))

    def test_one_box_per_language_and_the_animations(self):
        page = self.client.get(reverse("admin:club_event_change", args=[self.event.pk])).content.decode()
        for box in ("Français (FR)", "Deutsch (DE)", "English (EN)", "Animations"):
            self.assertIn(box, page)
        for field in ("title_de", "location_de", "description_de", "title_en", "location_en", "description_en", "has_bingo"):
            self.assertIn(f'name="{field}"', page)

    def test_the_seating_action_skips_a_standing_drinks(self):
        url = reverse("admin:club_event_changelist")
        response = self.client.post(url, {"action": "make_seating", "_selected_action": [self.event.pk]}, follow=True)
        self.assertContains(response, "pas de repas assis")
        self.assertFalse(SeatingPlan.objects.filter(event=self.event).exists())
