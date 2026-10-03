from datetime import timedelta
from io import StringIO

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from club.models import RSVP, Connection, Event, Match, Member, NotificationCampaign, PersonalNote, SeatingPlan, Substitute
from club.services.events import attendees, generate_matches, generate_seating
from club.services.federation import club_stats, collection_progress
from club.services.substitutions import approve_substitute, cancel_substitute, request_substitute
from club.tests.helpers import assert_csp_clean, make_member, make_staff


def substitute_data(**extra):
    data = {"first_name": "Alex", "last_name": "Fictif", "email": "guest@example.com", "job_title": "Collègue",
            "speaks_fr": False, "speaks_de": True, "speaks_en": False, "preferred_language": "de"}
    data.update(extra)
    return data


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SubstitutionTests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.main = make_member("main@example.com", first_name="TitulaireAbsent", company="Fictive SA")
        self.other = make_member("other@example.com", first_name="Participant")
        self.event = Event.objects.create(is_published=True, title="Dîner invité", kind="dinner", location="Sion",
                                          starts_at=timezone.now() + timedelta(days=1))
        RSVP.objects.create(member=self.main, event=self.event, status="yes")
        RSVP.objects.create(member=self.other, event=self.event, status="yes")

    def approve(self, **extra):
        request = request_substitute(self.event.pk, self.main, substitute_data(**extra))
        return request, approve_substitute(request.pk, self.staff)

    def test_request_does_not_create_guest_and_only_staff_can_approve(self):
        request = request_substitute(self.event.pk, self.main, substitute_data())
        self.assertEqual(Member.objects.count(), 2)
        self.assertEqual(RSVP.objects.get(member=self.main, event=self.event).status, "no")
        self.assertEqual(set(attendees(self.event)), {self.other})
        with self.assertRaises(PermissionDenied):
            approve_substitute(request.pk, self.other.user)
        guest = approve_substitute(request.pk, self.staff)
        self.assertEqual(approve_substitute(request.pk, self.staff).pk, guest.pk)
        self.assertNotEqual(guest.qr_token, self.main.qr_token)
        self.assertFalse(guest.user.has_usable_password())
        self.assertFalse(guest.speaks_fr)
        self.assertTrue(guest.speaks_de)
        self.assertEqual(guest.rank, Member.RANK_GUEST)
        self.assertEqual(guest.guest_access_until, self.event.starts_at + timedelta(hours=48))
        self.assertEqual(set(attendees(self.event)), {guest, self.other})
        self.assertEqual(NotificationCampaign.objects.get().kind, "guest_access")

    def test_tables_badges_and_statistics_use_real_guest_and_old_plans_are_removed(self):
        generate_matches(self.event)
        generate_seating(self.event)
        request, guest = self.approve()
        self.assertFalse(Match.objects.filter(event=self.event).exists())
        self.assertFalse(SeatingPlan.objects.filter(event=self.event).exists())
        plan = generate_seating(self.event)
        self.assertEqual(set(plan.assignments.values_list("member_id", flat=True)), {guest.pk, self.other.pk})
        self.client.force_login(self.staff)
        badges = self.client.get(reverse("club:staff_badges", args=[self.event.pk]))
        self.assertContains(badges, "Alex")
        self.assertNotContains(badges, "TitulaireAbsent")
        self.assertContains(badges, "Invité")
        self.assertEqual(club_stats()["members"], 2)
        Connection.link(guest, self.other)
        self.assertEqual(club_stats()["connections"], 0)
        self.assertEqual(collection_progress(self.other), (0, 1))

    def test_conflicts_with_regular_staff_or_duplicate_guest_do_not_convert_accounts(self):
        for email in (self.main.user.email, self.other.user.email, self.staff.email):
            request = request_substitute(self.event.pk, self.main, substitute_data(email=email))
            with self.assertRaises(ValidationError):
                approve_substitute(request.pk, self.staff)
        request, guest = self.approve()
        duplicate = request_substitute(self.event.pk, self.other, substitute_data())
        with self.assertRaises(ValidationError):
            approve_substitute(duplicate.pk, self.staff)
        self.assertEqual(Member.objects.filter(kind="guest").count(), 1)

    def test_cancel_removes_only_this_event_and_reuses_confirmed_guest_without_overwriting_profile(self):
        request, guest = self.approve()
        second = Event.objects.create(is_published=True, title="Autre invitation", kind="apero", location="Sion",
                                       starts_at=timezone.now() + timedelta(days=5))
        request2 = request_substitute(second.pk, self.main, substitute_data(job_title="Nouveau titre", preferred_language="en"))
        guest.phone = "+41 79 000 00 00"
        guest.save()
        self.assertEqual(approve_substitute(request2.pk, self.staff).pk, guest.pk)
        cancel_substitute(self.event.pk, self.main)
        guest.refresh_from_db()
        self.assertEqual(guest.phone, "+41 79 000 00 00")
        self.assertEqual(guest.preferred_language, "de")
        self.assertEqual(guest.guest_access_until, second.starts_at + timedelta(hours=48))
        self.assertTrue(guest.user.is_active)
        self.assertFalse(RSVP.objects.filter(event=self.event, member=guest).exists())
        self.assertTrue(RSVP.objects.filter(event=second, member=guest, status="yes").exists())

    def test_http_ownership_csrf_and_double_presence(self):
        self.client.force_login(self.main.user)
        url = reverse("club:member_substitute", args=[self.event.pk])
        assert_csp_clean(self, self.client.get(url))
        data = substitute_data(member=self.other.pk, is_staff=True, company="Spoofed")
        self.assertEqual(self.client.post(url, data).status_code, 302)
        request = Substitute.objects.get()
        self.assertEqual(request.member, self.main)
        self.assertEqual(request.company, self.main.company)
        self.client.post(reverse("club:event_rsvp", args=[self.event.pk]), {"status": "yes"})
        self.assertEqual(RSVP.objects.get(member=self.main, event=self.event).status, "no")
        self.client.post(reverse("club:member_substitute_cancel", args=[self.event.pk]))
        self.client.post(reverse("club:event_rsvp", args=[self.event.pk]), {"status": "yes"})
        self.assertEqual(RSVP.objects.get(member=self.main, event=self.event).status, "yes")

    def test_matching_uses_guest_languages_instead_of_principals(self):
        _request, guest = self.approve()
        # Principal and participant speak French; their guest speaks only German.
        self.assertEqual(generate_matches(self.event), 0)
        self.other.speaks_de = True
        self.other.save(update_fields=["speaks_de"])
        self.assertEqual(generate_matches(self.event), 1)
        match = Match.objects.get(event=self.event)
        self.assertEqual({match.member_a_id, match.member_b_id}, {guest.pk, self.other.pk})
        self.assertFalse(match.welcomes_newcomer)

    def test_demo_is_opt_in_idempotent_and_preserves_camille_introductions(self):
        # This scenario requires the base seed, so keep it in a separate cleared test database transaction.
        from club.tests.test_seed import SeedDemoTests
        helper = SeedDemoTests()
        self.main.user.delete()
        self.other.user.delete()
        self.staff.delete()
        self.event.delete()
        call_command("seed_demo", stdout=StringIO())
        before = helper.camille_intros()
        call_command("seed_substitute_demo", stdout=StringIO())
        call_command("seed_substitute_demo", stdout=StringIO())
        self.assertEqual(helper.camille_intros(), before)
        self.assertEqual(Member.objects.filter(kind="member").count(), 50)
        self.assertEqual(Member.objects.filter(kind="guest").count(), 1)
