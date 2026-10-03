from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from club.models import Event, NotificationCampaign, NotificationDelivery
from club.services.notifications import claim_delivery, publish_event
from club.tests.helpers import make_member, make_staff
from club.models import Member, RSVP, Substitute
from club.services.substitutions import approve_substitute, request_substitute
from club.tests.test_substitutions import substitute_data
from django.core.exceptions import ValidationError
from club.models import InvitationRequest
from club.services.membership import accept_invitation
from club.services.digests import prepare_digest
from datetime import datetime
from zoneinfo import ZoneInfo


@skipUnless(connection.vendor == "postgresql", "Concurrency must be verified on PostgreSQL")
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class NotificationConcurrencyTests(TransactionTestCase):
    def test_two_workers_can_claim_only_once(self):
        member = make_member("claim@example.com")
        campaign = NotificationCampaign.objects.create(kind="welcome", scope_key="concurrent:claim")
        delivery = NotificationDelivery.objects.create(campaign=campaign, recipient=member)
        barrier = Barrier(2)

        def claim():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return claim_delivery(delivery.pk)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        delivery.refresh_from_db()
        self.assertEqual(delivery.attempts, 1)

    def test_two_publishers_create_one_campaign(self):
        staff = make_staff()
        make_member("recipient@example.com")
        event = Event.objects.create(title="Concurrency", location="Test", kind="apero",
                                     starts_at=timezone.now() + timedelta(days=30))
        barrier = Barrier(2)

        def publish():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return publish_event(event.pk, staff).pk
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda _: publish(), range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(NotificationCampaign.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 1)

    def test_two_approvals_of_one_request_create_one_identity_and_delivery(self):
        staff = make_staff()
        principal = make_member("principal@example.com")
        event = Event.objects.create(is_published=True, title="Concurrent guest", location="Test", kind="apero",
                                     starts_at=timezone.now() + timedelta(days=3))
        request = request_substitute(event.pk, principal, substitute_data())
        barrier = Barrier(2)

        def approve():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return approve_substitute(request.pk, staff).pk
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda _: approve(), range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(Member.objects.filter(kind="guest").count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 1)
        self.assertEqual(RSVP.objects.filter(event=event, status="yes").count(), 1)

    def test_two_principals_cannot_approve_same_guest_for_same_event(self):
        staff = make_staff()
        first, second = make_member("first@example.com"), make_member("second@example.com")
        event = Event.objects.create(is_published=True, title="Concurrent presence", location="Test", kind="apero",
                                     starts_at=timezone.now() + timedelta(days=3))
        requests = [request_substitute(event.pk, member, substitute_data()) for member in (first, second)]
        barrier = Barrier(2)

        def approve(request):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return approve_substitute(request.pk, staff).pk
                except ValidationError:
                    return None
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(approve, requests))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(Substitute.objects.filter(status="approved").count(), 1)
        self.assertEqual(Member.objects.filter(kind="guest").count(), 1)

    def test_concurrent_admission_creates_one_member_and_one_welcome(self):
        staff = make_staff()
        invitation = InvitationRequest.objects.create(first_name="Fictif", last_name="Test", email="new@example.com",
                                                       company="Test", job_title="Test")
        barrier = Barrier(2)

        def accept():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return accept_invitation(invitation.pk, staff).pk
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: accept(), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 1)

    def test_concurrent_monthly_preparation_reserves_one_campaign(self):
        from club.models import DigestEntry, EmailPreferences
        candidate = make_member("candidate@example.com", admitted_at=timezone.now() - timedelta(days=60), onboarding_done=True)
        recipient = make_member("recipient@example.com")
        EmailPreferences.objects.create(member=candidate, allow_member_spotlight=True)
        EmailPreferences.objects.create(member=recipient, monthly_digest=True)
        now = datetime(timezone.now().year + 1, 2, 1, 9, tzinfo=ZoneInfo("Europe/Zurich"))
        barrier = Barrier(2)

        def prepare():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return prepare_digest(now)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: prepare(), range(2)))
        self.assertEqual(sorted(results), [0, 1])
        self.assertEqual(DigestEntry.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 1)
