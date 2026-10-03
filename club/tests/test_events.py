from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from club.models import RSVP, Event, Member
from club.services.events import generate_matches, generate_seating
from club.tests.helpers import assert_csp_clean, make_member, make_staff


def make_event(days=5, **extra):
    fields = {"is_published": True, "title": "Dîner d'essai", "kind": "dinner", "location": "Martigny", "has_seating": True,
              "starts_at": timezone.now() + timedelta(days=days)}
    fields.update(extra)
    return Event.objects.create(**fields)


class RsvpTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        self.event = make_event()
        self.past = make_event(days=-10, title="Apéro passé")
        self.client.force_login(self.alice.user)
        self.url = reverse("club:event_rsvp", args=[self.event.pk])

    def test_post_creates_then_changes_only_my_answer(self):
        RSVP.objects.create(event=self.event, member=self.bob, status="yes")
        self.client.post(self.url, {"status": "yes"})
        self.assertEqual(RSVP.objects.get(event=self.event, member=self.alice).status, "yes")
        self.client.post(self.url, {"status": "no"})
        self.assertEqual(RSVP.objects.filter(event=self.event, member=self.alice).count(), 1)
        self.assertEqual(RSVP.objects.get(event=self.event, member=self.alice).status, "no")
        self.assertEqual(RSVP.objects.get(event=self.event, member=self.bob).status, "yes")  # untouched

    def test_confirmation_message_and_redirect_to_the_event(self):
        response = self.client.post(self.url, {"status": "yes"}, follow=True)
        self.assertRedirects(response, reverse("club:event_detail", args=[self.event.pk]))
        self.assertContains(response, "est noté, à bientôt")

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertFalse(RSVP.objects.exists())

    def test_invalid_status_is_rejected(self):
        for value in ("maybe", "", "YES"):
            self.assertEqual(self.client.post(self.url, {"status": value}).status_code, 400)
        self.assertEqual(self.client.post(self.url).status_code, 400)
        self.assertFalse(RSVP.objects.exists())

    def test_past_event_refuses_answers(self):
        response = self.client.post(reverse("club:event_rsvp", args=[self.past.pk]), {"status": "yes"}, follow=True)
        self.assertContains(response, "déjà passé")
        self.assertFalse(RSVP.objects.exists())

    def test_unknown_event_is_404_and_staff_without_profile_is_redirected(self):
        self.assertEqual(self.client.post(reverse("club:event_rsvp", args=[9999]), {"status": "yes"}).status_code, 404)
        self.client.force_login(make_staff())
        self.assertEqual(self.client.post(self.url, {"status": "yes"}).status_code, 302)
        self.assertFalse(RSVP.objects.exists())

    def test_anonymous_visitors_are_sent_to_login(self):
        self.client.logout()
        response = self.client.post(self.url, {"status": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class EventPagesTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com", first_name="Alice", last_name="Aubert", sector="tech")
        self.bob = make_member("bob@example.com", first_name="Bob", last_name="Bonvin", sector="finance")
        self.carla = make_member("carla@example.com", first_name="Carla", last_name="Cachée", sector="health")
        self.event = make_event()
        self.past = make_event(days=-10, title="Apéro passé")
        self.client.force_login(self.alice.user)

    def register(self, *members, event=None):
        for member in members:
            RSVP.objects.create(event=event or self.event, member=member, status="yes")

    def detail(self, event=None):
        return self.client.get(reverse("club:event_detail", args=[(event or self.event).pk]))

    def test_list_shows_upcoming_then_past_with_my_answer(self):
        self.register(self.alice, self.bob)
        response = self.client.get(reverse("club:event_list"))
        assert_csp_clean(self, response)
        html = response.content.decode()
        self.assertLess(html.index("Dîner d&#x27;essai"), html.index("Apéro passé"))
        self.assertContains(response, "2 inscrits")
        self.assertContains(response, "✅ Tu viens")

    def test_detail_is_csp_clean_and_lists_who_comes(self):
        self.register(self.alice, self.bob)
        response = self.detail()
        assert_csp_clean(self, response)
        self.assertContains(response, "Bob Bonvin")
        self.assertNotContains(response, "Carla Cachée")  # not registered
        self.assertContains(response, 'name="status" value="yes"')

    def test_intros_and_placement_appear_only_when_registered(self):
        self.register(self.bob, self.carla)
        generate_matches(self.event)
        generate_seating(self.event, rounds=3, table_size=6)
        self.assertNotContains(self.detail(), "Tes rencontres")  # alice has not answered yet
        self.register(self.alice)
        generate_matches(self.event)
        generate_seating(self.event, rounds=3, table_size=6)
        response = self.detail()
        self.assertContains(response, "Tes rencontres")
        self.assertContains(response, "Bob Bonvin")
        self.assertContains(response, "Ton placement")
        self.assertContains(response, "Entrée")
        self.assertContains(response, "Dessert")

    def test_registered_without_introductions_yet_gets_a_friendly_message(self):
        self.register(self.alice)
        self.assertContains(self.detail(), "Tes rencontres arrivent bientôt")

    def test_members_who_hide_their_card_are_neither_listed_nor_introduced(self):
        self.carla.visible_in_directory = False
        self.carla.save()
        self.register(self.alice, self.bob, self.carla)
        generate_matches(self.event)
        response = self.detail()
        self.assertContains(response, "Bob Bonvin")
        self.assertNotContains(response, "Carla Cachée")
        self.assertContains(response, "3 inscrits")  # still counted

    def test_past_event_has_no_answer_buttons(self):
        self.register(self.alice, event=self.past)
        response = self.detail(self.past)
        self.assertNotContains(response, 'name="status"')
        self.assertNotContains(response, "Tes rencontres arrivent bientôt")

    def test_home_shows_the_next_event_and_my_answer(self):
        response = self.client.get(reverse("club:home"))
        self.assertContains(response, "Dîner d&#x27;essai")
        self.assertContains(response, "Pas encore répondu")
        self.register(self.alice, self.bob)
        generate_matches(self.event)
        response = self.client.get(reverse("club:home"))
        self.assertContains(response, "Tu viens")
        self.assertContains(response, "Bob Bonvin")


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DemoEventScenarioTests(TestCase):
    """Phase 4 check of docs/PLAN.md, on the seeded club: what Camille sees for the autumn dinner."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.camille = Member.objects.get(user__email="camille.rey@example.com")
        cls.dinner = Event.objects.get(title="Dîner d'automne")

    def setUp(self):
        self.client.force_login(self.camille.user)

    def test_home_shows_the_dinner_and_her_three_introductions_with_a_first_reason(self):
        response = self.client.get(reverse("club:home"))
        assert_csp_clean(self, response)
        for text in ("Dîner d&#x27;automne", "Lukas Imboden", "Joëlle Moret", "Olivier Gay", "Petite Arvine"):
            self.assertContains(response, text)  # short version: first common affinity + icebreaker

    def test_event_page_shows_every_reason_of_the_introductions(self):
        response = self.client.get(reverse("club:event_detail", args=[self.dinner.pk]))
        assert_csp_clean(self, response)
        for text in ("Lukas Imboden", "Petite Arvine", "Ski de randonnée", "Course à pied &amp; trail", "Les réunions du lundi matin"):
            self.assertContains(response, text)
        self.assertContains(response, "Secteurs complémentaires")
        self.assertContains(response, "Accueille une nouvelle recrue")
        self.assertContains(response, "💬")

    def test_changing_the_answer_works_and_placement_shows_after_generation(self):
        url = reverse("club:event_rsvp", args=[self.dinner.pk])
        self.client.post(url, {"status": "no"})
        self.assertEqual(RSVP.objects.get(event=self.dinner, member=self.camille).status, "no")
        self.client.post(url, {"status": "yes"})
        self.assertEqual(RSVP.objects.get(event=self.dinner, member=self.camille).status, "yes")
        generate_seating(self.dinner)
        response = self.client.get(reverse("club:event_detail", args=[self.dinner.pk]))
        self.assertContains(response, "Ton placement")
        self.assertContains(response, "Plat")
