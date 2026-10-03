"""Real temporary identities, privacy boundaries and session expiry."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
import tempfile

from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from sesame.utils import get_query_string

from club.models import RSVP, Connection, Event, Member, PersonalNote, Substitute
from club.services.access import visible_members
from club.services.events import attendees
from club.services.substitutions import approve_substitute, cancel_substitute, member_access_valid, request_substitute
from club.tests.helpers import make_member, make_staff
from club.tests.test_access_matrix import MEMBER, STAFF
from club.tests.test_substitutions import substitute_data


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
                   EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class GuestAccessTests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.main = make_member("principal@example.com")
        self.participant = make_member("participant@example.com")
        self.outsider = make_member("outsider@example.com")
        self.event = Event.objects.create(is_published=True, title="Autorisé", kind="dinner", location="Sion",
                                          starts_at=timezone.now() + timedelta(days=1))
        self.unrelated = Event.objects.create(is_published=True, title="Hors périmètre", kind="apero", location="Sion",
                                              starts_at=timezone.now() + timedelta(days=2))
        RSVP.objects.create(member=self.participant, event=self.event, status="yes")
        self.request = request_substitute(self.event.pk, self.main, substitute_data())
        self.guest = approve_substitute(self.request.pk, self.staff)
        self.client.force_login(self.guest.user)

    def url(self, name, target=None):
        args = [] if target is None else [target.pk]
        return reverse("club:" + name, args=args)

    def test_guest_routes_and_direct_urls_are_scoped(self):
        for name in ("home", "album", "event_list", "profile_edit", "onboarding", "my_qr"):
            self.assertEqual(self.client.get(self.url(name)).status_code, 200, name)
        self.assertEqual(self.client.get(self.url("event_detail", self.event)).status_code, 200)
        self.assertNotContains(self.client.get(self.url("event_list")), "Hors périmètre")
        self.assertEqual(self.client.get(self.url("event_detail", self.unrelated)).status_code, 404)
        self.assertEqual(self.client.get(self.url("member_detail", self.participant)).status_code, 200)
        for name in ("member_detail", "member_photo", "member_vcard"):
            self.assertEqual(self.client.get(self.url(name, self.outsider)).status_code, 404, name)
        self.assertEqual(self.client.post(self.url("member_note", self.outsider), {"text": "forged"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("club:scan", args=[self.outsider.qr_token])).status_code, 404)
        self.assertEqual(PersonalNote.objects.count(), 0)
        self.assertEqual(Connection.objects.count(), 0)

    def test_guest_cannot_act_as_regular_member_or_staff(self):
        self.assertEqual(self.client.get(self.url("invite")).status_code, 403)
        for name in ("event_rsvp", "member_substitute", "member_substitute_cancel"):
            self.assertEqual(self.client.post(self.url(name, self.event), substitute_data(status="no")).status_code, 403, name)
        self.assertEqual(RSVP.objects.get(member=self.guest, event=self.event).status, "yes")
        for name in STAFF:
            args = [] if name == "club:staff_dashboard" else [self.event.pk]
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403, name)

    def test_hidden_profile_and_private_request_remain_private(self):
        self.participant.visible_in_directory = False
        self.participant.save(update_fields=["visible_in_directory"])
        self.assertEqual(self.client.get(self.url("member_detail", self.participant)).status_code, 404)
        Connection.link(self.guest, self.participant)
        self.assertEqual(self.client.get(self.url("member_detail", self.participant)).status_code, 200)
        self.client.force_login(self.outsider.user)
        self.assertNotContains(self.client.get(self.url("event_detail", self.event)), self.guest.user.email)
        self.assertEqual(self.client.get(self.url("member_detail", self.guest)).status_code, 404)

    def test_scan_attaches_only_real_people_and_notes_never_reach_the_principal(self):
        with patch("django.utils.timezone.now", return_value=self.event.starts_at - timedelta(hours=1)):
            response = self.client.post(reverse("club:scan", args=[self.participant.qr_token]), {"event": self.event.pk})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Connection.exists_between(self.guest, self.participant))
        self.assertFalse(Connection.exists_between(self.main, self.participant))
        self.assertEqual(Connection.objects.get().event, self.event)
        self.assertEqual(self.client.get(self.url("member_vcard", self.participant)).status_code, 200)
        sentinel = "PRIVATE-GUEST-NOTE-8735"
        self.client.post(self.url("member_note", self.participant), {"text": sentinel})
        self.assertContains(self.client.get(self.url("member_detail", self.participant)), sentinel)
        for user in (self.main.user, self.participant.user, self.staff):
            self.client.force_login(user)
            for name, target in (("home", None), ("album", None), ("member_detail", self.participant), ("member_vcard", self.guest)):
                self.assertNotIn(sentinel.encode(), self.client.get(self.url(name, target)).content)

    def test_contact_is_not_unlocked_by_coparticipation(self):
        self.assertEqual(self.client.get(self.url("member_vcard", self.participant)).status_code, 403)
        self.client.force_login(self.participant.user)
        self.assertEqual(self.client.get(self.url("member_vcard", self.guest)).status_code, 403)

    def test_photo_route_uses_same_scope_and_keeps_real_met_guest_after_expiry(self):
        from club.services.photos import normalize_member_photo, save_profile_photo
        from club.tests.test_photos import upload
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            for member in (self.guest, self.participant, self.outsider):
                save_profile_photo(member, normalize_member_photo(upload()))
            response = self.client.get(self.url("member_photo", self.participant))
            self.assertEqual(response.status_code, 200)
            self.assertIn("no-store", response["Cache-Control"])
            self.assertTrue(b"".join(response.streaming_content).startswith(b"\xff\xd8"))
            self.assertEqual(self.client.get(self.url("member_photo", self.outsider)).status_code, 404)
            Connection.link(self.guest, self.participant)
            with patch("django.utils.timezone.now", return_value=self.event.starts_at + timedelta(hours=49)):
                self.assertEqual(self.client.get(self.url("member_photo", self.participant)).status_code, 403)
                self.client.force_login(self.participant.user)
                response = self.client.get(self.url("member_photo", self.guest))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(b"".join(response.streaming_content).startswith(b"\xff\xd8"))
                self.client.force_login(self.outsider.user)
                self.assertEqual(self.client.get(self.url("member_photo", self.guest)).status_code, 404)

    def test_expired_open_session_is_blocked_on_every_member_route_before_cron(self):
        arguments = {"member_detail": self.participant, "member_note": self.participant,
                     "member_photo": self.participant, "member_vcard": self.participant,
                     "event_detail": self.event, "event_rsvp": self.event,
                     "member_substitute": self.event, "member_substitute_cancel": self.event, "event_bingo": self.event}
        with patch("django.utils.timezone.now", return_value=self.event.starts_at + timedelta(hours=49)):
            for qualified in MEMBER:
                name = qualified.split(":")[1]
                url = reverse(qualified, args=[self.participant.qr_token]) if name == "scan" else self.url(name, arguments.get(name))
                self.assertEqual(self.client.get(url).status_code, 403, name)
                self.assertEqual(self.client.post(url, {"text": "blocked", "status": "yes"}).status_code, 403, name)
        self.guest.user.refresh_from_db()
        self.assertTrue(self.guest.user.is_active)  # Security does not depend on deactivation by the job.

    def test_magic_links_do_not_extend_expired_access(self):
        self.client.logout()
        with patch("django.utils.timezone.now", return_value=self.event.starts_at + timedelta(hours=49)):
            token = get_query_string(self.guest.user)  # Even a fresh token is not an access extension.
            response = self.client.get(reverse("magic_login") + token)
            self.assertEqual(response.status_code, 403)
            self.assertNotIn("_auth_user_id", self.client.session)
            known = self.client.post(self.url("magic_link_request"), {"email": self.guest.user.email}, follow=True)
            unknown = self.client.post(self.url("magic_link_request"), {"email": "unknown@example.com"}, follow=True)
            self.assertEqual(known.status_code, unknown.status_code)
            self.assertEqual(len(mail.outbox), 0)

    def test_expiry_preserves_real_history_and_reactivation_reuses_identity(self):
        Connection.link(self.guest, self.participant, event=self.event)
        PersonalNote.objects.create(owner=self.guest, target=self.participant, text="history")
        qr = self.guest.qr_token
        with patch("django.utils.timezone.now", return_value=self.event.starts_at + timedelta(hours=49)):
            call_command("expire_guest_access", "--dry-run", stdout=StringIO())
            self.guest.user.refresh_from_db()
            self.assertTrue(self.guest.user.is_active)
            call_command("expire_guest_access", stdout=StringIO())
            self.guest.user.refresh_from_db()
            self.assertFalse(self.guest.user.is_active)
            self.client.force_login(self.participant.user)
            self.assertContains(self.client.get(self.url("member_detail", self.guest)), "Alex")
            self.assertEqual(self.client.get(self.url("member_vcard", self.guest)).status_code, 200)
            self.assertIn(self.guest, attendees(self.event))  # Past attendance remains accurate.
            self.assertNotIn(self.guest, visible_members(self.outsider))
            second = Event.objects.create(is_published=True, title="Réactivation", kind="apero", location="Sion",
                                           starts_at=timezone.now() + timedelta(days=3))
            request = request_substitute(second.pk, self.main, substitute_data())
            reactivated = approve_substitute(request.pk, self.staff)
            self.assertEqual(reactivated.pk, self.guest.pk)
            self.assertEqual(reactivated.qr_token, qr)
            self.assertTrue(reactivated.user.is_active)
            self.assertTrue(member_access_valid(reactivated))
        self.assertEqual(Connection.objects.count(), 1)
        self.assertEqual(PersonalNote.objects.get().text, "history")
        self.main.user.refresh_from_db()
        self.assertTrue(self.main.user.is_active)

    def test_cancelling_or_deleting_parent_event_revokes_access(self):
        self.event.cancelled_at = timezone.now()
        self.event.save(update_fields=["cancelled_at"])
        self.guest.refresh_from_db()
        self.assertFalse(member_access_valid(self.guest))
        self.assertNotIn(self.guest, attendees(self.event))
        self.event.delete()
        self.guest.refresh_from_db()
        self.assertFalse(member_access_valid(self.guest))

    def test_deleting_guest_anonymizes_copied_identity(self):
        self.guest.delete()
        self.request.refresh_from_db()
        self.assertIsNone(self.request.guest_id)
        self.assertEqual(self.request.status, Substitute.Status.CANCELLED)
        self.assertEqual(self.request.email, "")
        self.assertEqual(self.request.first_name, "")

    def test_two_same_day_events_require_a_validated_context_for_guest_scans(self):
        self.unrelated.starts_at = self.event.starts_at + timedelta(minutes=30)
        self.unrelated.save(update_fields=["starts_at"])
        second = request_substitute(self.unrelated.pk, self.main, substitute_data())
        approve_substitute(second.pk, self.staff)
        RSVP.objects.create(event=self.unrelated, member=self.participant, status="yes")
        url = reverse("club:scan", args=[self.participant.qr_token])
        with patch("django.utils.timezone.now", return_value=self.event.starts_at - timedelta(hours=1)):
            self.assertEqual(self.client.post(url).status_code, 404)
            self.assertEqual(self.client.post(url, {"event": 999999}).status_code, 404)
            self.assertEqual(self.client.post(url, {"event": self.unrelated.pk}).status_code, 302)
        self.assertEqual(Connection.objects.get().event, self.unrelated)

    def test_substitution_writes_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.main.user)
        for name in ("member_substitute", "member_substitute_cancel"):
            self.assertEqual(client.post(self.url(name, self.event), substitute_data()).status_code, 403)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, "approved")

    @override_settings(NOTIFICATIONS_ENABLED=True, PUBLIC_BASE_URL="https://club.example.com")
    def test_guest_gets_only_valid_personal_access_email(self):
        from club.models import EmailPreferences, NotificationCampaign, NotificationDelivery
        from club.services.notifications import eligible, process_notifications, publish_event
        from club.services.digests import presentable_members
        process_notifications()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.guest.user.email])
        self.assertIn("Gastzugang", mail.outbox[0].subject)
        self.assertNotIn(self.main.user.email, mail.outbox[0].body)
        EmailPreferences.objects.filter(member=self.guest).update(event_announcements=True, event_reminders=True,
                                                                 monthly_digest=True, allow_member_spotlight=True)
        self.guest.admitted_at = timezone.now()
        self.guest.onboarding_done = True
        self.guest.save()
        self.assertNotIn(self.guest, presentable_members())
        self.unrelated.is_published = False
        self.unrelated.save(update_fields=["is_published"])
        campaign = publish_event(self.unrelated.pk, self.staff)
        self.assertFalse(campaign.deliveries.filter(recipient=self.guest).exists())
        # A different live invitation cannot justify sending access to a cancelled event.
        second = request_substitute(self.unrelated.pk, self.main, substitute_data())
        approve_substitute(second.pk, self.staff)
        cancel_substitute(self.event.pk, self.main)
        delivery = NotificationDelivery.objects.get(campaign__substitute=self.request)
        delivery.campaign.refresh_from_db()
        self.guest.refresh_from_db()
        self.assertTrue(member_access_valid(self.guest))
        self.assertFalse(eligible(delivery, timezone.now()))
