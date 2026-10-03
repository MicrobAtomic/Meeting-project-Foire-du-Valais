from datetime import timedelta

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from club.models import RSVP, Connection, Event, Match
from club.services.milestones import CLUB_MILESTONES, album_goal, club_progress, connections_needed
from club.tests.helpers import make_member, make_staff


def stats(members, connections):
    pairs = members * (members - 1) // 2
    return {"members": members, "connections": connections, "index": connections / pairs if pairs else 0.0}


class ClubProgressTests(SimpleTestCase):
    def test_needed_connections_use_exact_arithmetic(self):
        self.assertEqual(connections_needed(20, 50), 245)  # 20 % of 1225 pairs, not 246
        self.assertEqual(connections_needed(35, 50), 429)  # 428.75 rounds up
        self.assertEqual(connections_needed(100, 50), 1225)

    def test_the_demo_club_has_passed_the_first_milestone_and_aims_at_the_second(self):
        progress = club_progress(stats(50, 180))  # 15 %
        self.assertEqual(progress["current"].percent, 10)
        self.assertEqual(progress["next"].percent, 20)
        self.assertEqual(progress["remaining"], 65)
        fills = [round(segment["fill"], 2) for segment in progress["segments"]]
        self.assertEqual(fills, [1.0, 0.47, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual([s["is_next"] for s in progress["segments"]], [False, True, False, False, False, False])

    def test_reaching_a_milestone_exactly(self):
        progress = club_progress(stats(50, 245))
        self.assertEqual(progress["current"].percent, 20)
        self.assertEqual(progress["next"].percent, 35)
        self.assertEqual(progress["remaining"], 429 - 245)

    def test_everybody_knows_everybody(self):
        progress = club_progress(stats(2, 1))
        self.assertEqual(progress["current"], CLUB_MILESTONES[-1])
        self.assertIsNone(progress["next"])

    def test_an_empty_club_has_reached_nothing(self):
        for members in (0, 1):
            progress = club_progress(stats(members, 0))
            self.assertIsNone(progress["current"])
            self.assertEqual(progress["next"], CLUB_MILESTONES[0])
            self.assertEqual(progress["remaining"], 0)


class AlbumGoalTests(SimpleTestCase):
    def test_goals_are_5_15_30_then_the_full_album(self):
        self.assertEqual(album_goal(2, 49), {"target": 5, "emoji": "🥉", "remaining": 3, "full_album": False})
        self.assertEqual(album_goal(5, 49)["target"], 15)
        self.assertEqual(album_goal(29, 49)["target"], 30)
        self.assertEqual(album_goal(30, 49), {"target": 49, "emoji": "💎", "remaining": 19, "full_album": True})
        self.assertIsNone(album_goal(49, 49))

    def test_a_small_club_skips_the_goals_it_cannot_offer(self):
        self.assertEqual(album_goal(0, 3), {"target": 3, "emoji": "💎", "remaining": 3, "full_album": True})


class MilestonePagesTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com", first_name="Alice")
        self.members = [make_member(f"m{i}@example.com", first_name=f"M{i}") for i in range(5)]  # 6 members, 15 pairs

    def test_home_shows_the_next_milestone_and_the_album_goal(self):
        Connection.link(self.alice, self.members[0])  # 1 / 15 = 7 %
        self.client.force_login(self.alice.user)
        response = self.client.get(reverse("club:home"))
        self.assertContains(response, "Le Club est connecté à 7")
        self.assertContains(response, "Prochain palier : 🌱 Les premiers liens à 10")
        self.assertContains(response, "Encore 1 rencontre : chaque QR code scanné compte.")
        self.assertContains(response, "Prochain objectif : 💎 l'album complet, encore 4 rencontres.")

    def test_staff_dashboard_lists_every_milestone_with_its_reward(self):
        self.client.force_login(make_staff())
        response = self.client.get(reverse("club:staff_dashboard"))
        self.assertContains(response, "Paliers du Club")
        for milestone in CLUB_MILESTONES:
            self.assertContains(response, str(milestone.reward).replace("'", "&#x27;"))
        self.assertContains(response, "encore 2 rencontres")  # 10 % of 15 pairs


class DemoContactTests(TestCase):
    def setUp(self):
        self.camille = make_member("camille@example.com", first_name="Camille")
        self.lukas = make_member("lukas@example.com", first_name="Lukas", last_name="Imboden")
        self.event = Event.objects.create(title="Dîner", kind="dinner", location="Martigny",
                                          starts_at=timezone.now() + timedelta(days=5))
        for member in (self.camille, self.lukas):
            RSVP.objects.create(event=self.event, member=member, status=RSVP.Status.YES)
        Match.objects.create(event=self.event, member_a=self.camille, member_b=self.lukas, score=5)
        self.client.force_login(self.camille.user)

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_offers_the_qr_code_of_the_first_introduction(self):
        response = self.client.get(reverse("club:home"))
        self.assertContains(response, "Rencontre Lukas Imboden")
        self.assertContains(response, reverse("club:scan", args=[self.lukas.qr_token]))
        self.assertContains(response, "<svg")

    @override_settings(DEMO_MODE=True)
    def test_once_met_the_demo_offers_someone_else(self):
        Connection.link(self.camille, self.lukas)
        other = make_member("other@example.com", first_name="Zoé", last_name="Zufferey")
        response = self.client.get(reverse("club:home"))
        self.assertNotContains(response, "Rencontre Lukas Imboden")
        self.assertContains(response, reverse("club:scan", args=[other.qr_token]))

    @override_settings(DEMO_MODE=False)
    def test_never_outside_demo_mode(self):
        response = self.client.get(reverse("club:home"))
        self.assertNotContains(response, "Mode démo")
        self.assertNotContains(response, self.lukas.qr_token)
