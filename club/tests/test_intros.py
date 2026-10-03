from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from club.models import RSVP, Event, Match, Tag
from club.services.events import generate_seating
from club.services.intros import intros_for, seats_for
from club.tests.helpers import make_member


class IntrosTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(is_published=True, title="Dîner", kind="dinner", location="Martigny",
                                          starts_at=timezone.now() + timedelta(days=5), has_seating=True)
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        Tag.objects.create(slug="golf", emoji="⛳", category="hobby", label_fr="Golf", icebreaker_fr="Ton parcours ?")

    def test_intro_has_other_person_reasons_and_icebreaker(self):
        a, b = sorted([self.alice, self.bob], key=lambda m: m.pk)
        Match.objects.create(event=self.event, member_a=a, member_b=b, score=5, shared_likes=["golf"])
        intro = intros_for(self.alice, self.event)[0]
        self.assertEqual(intro["other"], self.bob)
        self.assertEqual([t.slug for t in intro["likes"]], ["golf"])
        self.assertEqual(intro["icebreaker"], "Ton parcours ?")

    def test_seats_for_lists_one_table_per_round(self):
        self.assertEqual(seats_for(self.alice, self.event), [])
        for member in (self.alice, self.bob):
            RSVP.objects.create(event=self.event, member=member, status=RSVP.Status.YES)
        generate_seating(self.event, rounds=3, table_size=6)
        seats = seats_for(self.alice, self.event)
        self.assertEqual([s["label"] for s in seats], ["Entrée", "Plat", "Dessert"])
