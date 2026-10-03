from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation

from club.models import Event
from club.tests.helpers import make_member, make_staff


class EventLanguagesTests(TestCase):
    """Event texts are typed in French and, optionally, in German and English: the page shows the reader's language."""

    def setUp(self):
        self.event = Event.objects.create(
            title="Apéro de Noël", title_de="Weihnachtsapéro", kind="apero", starts_at=timezone.now() + timedelta(days=9),
            location="Lieu surprise", location_de="Überraschungsort", location_en="Secret venue",
            description="On monte, il y aura de la neige.", description_de="Es geht bergauf, es wird Schnee liegen.",
        )
        self.addCleanup(translation.activate, settings.LANGUAGE_CODE)

    def test_each_language_gets_its_text_and_falls_back_to_french(self):
        with translation.override("de"):
            self.assertEqual(self.event.localized_title, "Weihnachtsapéro")
            self.assertEqual(self.event.localized_location, "Überraschungsort")
            self.assertEqual(str(self.event), "Weihnachtsapéro")
        with translation.override("en"):
            self.assertEqual(self.event.localized_title, "Apéro de Noël")  # no English title typed in
            self.assertEqual(self.event.localized_location, "Secret venue")
            self.assertEqual(self.event.localized_description, "On monte, il y aura de la neige.")
        with translation.override("fr"):
            self.assertEqual(self.event.localized_title, "Apéro de Noël")

    def test_member_home_and_staff_dashboard_follow_the_language(self):
        member = make_member("alice@example.com")
        self.client.force_login(member.user)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "de"
        page = self.client.get(reverse("club:home"))
        self.assertContains(page, "Weihnachtsapéro")
        self.assertContains(page, "Überraschungsort")
        self.assertNotContains(page, "Apéro de Noël")
        self.client.force_login(make_staff())
        self.assertContains(self.client.get(reverse("club:staff_dashboard")), "Weihnachtsapéro")
