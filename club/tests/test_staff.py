from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from club.models import RSVP, Connection, Event, InvitationRequest, Match, Member, SeatAssignment, SeatingPlan
from club.tests.helpers import PASSWORD, assert_csp_clean, make_member, make_staff


class StaffToolsTests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.members = [make_member(f"m{i}@example.com", first_name=f"Prénom{i}", last_name=f"Nom{i}",
                                    sector=["tech", "finance", "health"][i % 3]) for i in range(9)]
        self.event = Event.objects.create(is_published=True, title="Dîner test", kind="dinner", location="Martigny", has_seating=True,
                                          starts_at=timezone.now() + timedelta(days=4))
        for member in self.members[:8]:  # 8 registered, 1 not
            RSVP.objects.create(event=self.event, member=member, status="yes")
        self.url = reverse("club:staff_event", args=[self.event.pk])
        self.client.force_login(self.staff)

    def test_members_and_visitors_are_kept_out_of_the_staff_pages(self):
        urls = [reverse("club:staff_dashboard"), self.url]
        self.client.force_login(self.members[0].user)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)
            self.assertEqual(self.client.post(url, {"action": "matches"}).status_code, 403, url)
        self.client.logout()
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn(reverse("login"), response.url)
        self.assertFalse(Match.objects.exists())

    def test_staff_pages_are_csp_clean(self):
        assert_csp_clean(self, self.client.get(reverse("club:staff_dashboard")))
        assert_csp_clean(self, self.client.get(self.url))

    def test_post_matches_generates_introductions(self):
        response = self.client.post(self.url, {"action": "matches"}, follow=True)
        self.assertRedirects(response, self.url)
        self.assertTrue(Match.objects.filter(event=self.event).exists())
        self.assertContains(response, "rencontres générées")
        attendees = {m.pk for m in self.members[:8]}
        for match in Match.objects.filter(event=self.event):
            self.assertIn(match.member_a_id, attendees)
            self.assertIn(match.member_b_id, attendees)

    def test_post_seating_creates_one_seat_per_guest_and_service(self):
        response = self.client.post(self.url, {"action": "seating", "rounds": "3", "table_size": "4"}, follow=True)
        self.assertRedirects(response, self.url)
        plan = SeatingPlan.objects.get(event=self.event)
        self.assertEqual((plan.rounds, plan.table_size), (3, 4))
        self.assertEqual(SeatAssignment.objects.filter(plan=plan).count(), 8 * 3)
        self.assertContains(response, "Plan généré")

    def test_default_settings_are_three_services_of_six(self):
        page = self.client.get(self.url)
        self.assertContains(page, 'name="rounds" value="3"')
        self.assertContains(page, 'name="table_size" value="6"')

    def test_out_of_range_settings_are_refused(self):
        for rounds, size in (("3", "50"), ("3", "3"), ("0", "6"), ("9", "6"), ("x", "6"), ("3", "")):
            response = self.client.post(self.url, {"action": "seating", "rounds": rounds, "table_size": size})
            self.assertEqual(response.status_code, 200, (rounds, size))
            self.assertContains(response, 'role="alert"')
        self.assertFalse(SeatingPlan.objects.exists())
        self.assertFalse(SeatAssignment.objects.exists())

    def test_unknown_or_missing_action_is_a_bad_request(self):
        self.assertEqual(self.client.post(self.url, {"action": "drop-everything"}).status_code, 400)
        self.assertEqual(self.client.post(self.url).status_code, 400)

    def test_get_never_generates_anything(self):
        self.client.get(self.url)
        self.assertFalse(Match.objects.exists())
        self.assertFalse(SeatingPlan.objects.exists())

    def test_csrf_token_is_required(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        self.assertEqual(strict.post(self.url, {"action": "matches"}).status_code, 403)
        self.assertFalse(Match.objects.exists())

    def test_page_lists_matches_and_the_seating_plan_with_a_print_button(self):
        self.client.post(self.url, {"action": "matches"})
        self.client.post(self.url, {"action": "seating", "rounds": "2", "table_size": "4"})
        page = self.client.get(self.url)
        self.assertContains(page, "Rencontres proposées (")
        self.assertContains(page, " ↔ ")
        self.assertContains(page, "Entrée")
        self.assertContains(page, "Plat")
        self.assertNotContains(page, "Dessert")  # only 2 services were asked for
        self.assertContains(page, "data-print")
        self.assertContains(page, "js/print.js")
        self.assertContains(page, "Table 1")

    def test_unknown_event_is_404(self):
        self.assertEqual(self.client.get(reverse("club:staff_event", args=[9999])).status_code, 404)


class StaffDashboardTests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.client.force_login(self.staff)

    def test_dashboard_lists_isolated_members_requests_and_events(self):
        alice = make_member("alice@example.com", first_name="Alice", last_name="Seule")
        bob = make_member("bob@example.com", first_name="Bob", last_name="Entouré")
        crowd = [make_member(f"c{i}@example.com") for i in range(4)]
        for other in crowd:
            Connection.link(bob, other)
        event = Event.objects.create(is_published=True, title="Dîner à préparer", kind="dinner", location="Martigny",
                                     starts_at=timezone.now() + timedelta(days=3))
        old = Event.objects.create(is_published=True, title="Soirée passée", kind="apero", location="Sion",
                                   starts_at=timezone.now() - timedelta(days=3))
        Connection.link(alice, crowd[0], event=old)
        InvitationRequest.objects.create(first_name="Marie", last_name="Dupont", company="Dupont SA",
                                         job_title="Directrice", email="marie@exemple.ch")
        page = self.client.get(reverse("club:staff_dashboard"))
        self.assertContains(page, "Alice Seule")
        self.assertNotContains(page, "Bob Entouré")  # 4 meetings: not isolated
        self.assertContains(page, "Marie Dupont")
        self.assertContains(page, "1 nouvelle demande")
        self.assertContains(page, reverse("club:staff_event", args=[event.pk]))
        self.assertContains(page, "Soirée passée")
        self.assertContains(page, reverse("admin:club_member_change", args=[alice.pk]))

    def test_dashboard_without_any_data_still_renders(self):
        page = self.client.get(reverse("club:staff_dashboard"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Aucun événement à venir")
        self.assertContains(page, "0 nouvelle")  # singular or plural: French rules arrive with the fr catalog (phase 8)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DemoStaffScenarioTests(TestCase):
    """Phase 5 check of docs/PLAN.md on the seeded club."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.dinner = Event.objects.get(title="Dîner d'automne")
        cls.camille = Member.objects.get(user__email="camille.rey@example.com")

    def test_dashboard_shows_fifteen_percent_and_camille_as_isolated(self):
        self.client.force_login(make_staff("chef@example.com"))
        page = self.client.get(reverse("club:staff_dashboard"))
        self.assertContains(page, "15 %")
        self.assertContains(page, "Camille Rey")
        self.assertContains(page, "Dîner d&#x27;automne")

    def test_generating_the_dinner_plan_with_tables_of_six(self):
        staff = make_staff("chef@example.com")
        self.client.force_login(staff)
        url = reverse("club:staff_event", args=[self.dinner.pk])
        response = self.client.post(url, {"action": "seating", "rounds": "3", "table_size": "6"}, follow=True)
        plan = SeatingPlan.objects.get(event=self.dinner)
        self.assertEqual(SeatAssignment.objects.filter(plan=plan).count(), 38 * 3)
        self.assertGreater(plan.new_pairs, 200)
        self.assertLessEqual(plan.repeated_pairs, 3)
        self.assertContains(response, "Plan généré")
        # ...and Camille then sees her placement on the event page
        self.client.force_login(self.camille.user)
        page = self.client.get(reverse("club:event_detail", args=[self.dinner.pk]))
        self.assertContains(page, "Ton placement")
        self.assertContains(page, "Entrée")
