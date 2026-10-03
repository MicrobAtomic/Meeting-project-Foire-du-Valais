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
