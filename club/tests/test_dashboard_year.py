from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from club.models import Connection
from club.tests.helpers import assert_csp_clean, make_member, make_staff


@override_settings(TIME_ZONE="Europe/Zurich", PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DashboardYearTests(TestCase):
    def test_calendar_year_uses_local_midnight_and_counts_only_active_members_until_now(self):
        now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
        start = datetime(2025, 12, 31, 23, tzinfo=timezone.utc)  # Midnight on January 1 in Zurich.
        anchor = make_member("anchor@example.com")
        for index, date in enumerate((start - timedelta(seconds=1), start, now - timedelta(days=5), now + timedelta(days=1))):
            partner = make_member(f"partner{index}@example.com", member_since=2026 if index == 1 else 2020)
            connection, _ = Connection.link(anchor, partner)
            connection.created_at = date
            connection.save(update_fields=["created_at"])
        inactive = make_member("inactive@example.com")
        inactive.user.is_active = False
        inactive.user.save()
        guest = make_member("guest@example.com", kind="guest")
        for partner in (inactive, guest):
            connection, _ = Connection.link(anchor, partner)
            connection.created_at = now - timedelta(days=1)
            connection.save(update_fields=["created_at"])
        self.client.force_login(make_staff())
        headings = {
            "fr": ("Rencontres enregistrées cette année", "Nouveaux membres cette année"),
            "de": ("Begegnungen dieses Jahr", "Neue Mitglieder dieses Jahr"),
            "en": ("Connections this year", "New members this year"),
        }
        with patch("django.utils.timezone.now", return_value=now):
            for language, labels in headings.items():
                with self.subTest(language=language):
                    self.client.cookies["django_language"] = language
                    response = self.client.get(reverse("club:staff_dashboard"))
                    assert_csp_clean(self, response)
                    self.assertEqual(response.context["year_connections"], 2)
                    self.assertEqual(response.context["recent_connections"], 3)
                    self.assertEqual(response.context["stats"]["connections"], 4)
                    self.assertEqual(response.context["new_recruits"], 1)
                    for label in labels:
                        self.assertContains(response, label)
