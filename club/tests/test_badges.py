from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from club.models import RSVP, Event
from club.services.qr import qr_svg
from club.tests.helpers import assert_csp_clean, make_member, make_staff


class BadgesTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(is_published=True, title="Dîner badges", kind="dinner", location="Martigny",
                                          starts_at=timezone.now() + timedelta(days=3))
        self.members = [make_member(f"m{i}@example.com", first_name=f"Prénom{i:02d}", last_name=f"Nom{i:02d}",
                                    company=f"Société {i:02d} SA") for i in range(9)]
        self.outsider = make_member("absent@example.com", first_name="Absent", last_name="Pasinscrit")
        self.members[0].talk_to_me_about = "Les vins du Valais"
        self.members[0].save()
        self.members[1].visible_in_directory = False  # a hidden card still needs a badge
        self.members[1].save()
        for member in self.members:
            RSVP.objects.create(event=self.event, member=member, status="yes")
        RSVP.objects.create(event=self.event, member=self.outsider, status="no")
        self.url = reverse("club:staff_badges", args=[self.event.pk])
        self.client.force_login(make_staff())

    def test_members_and_visitors_cannot_print_badges(self):
        self.client.force_login(self.members[0].user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_one_badge_per_registered_member_eight_per_page(self):
        response = self.client.get(self.url)
        assert_csp_clean(self, response)
        pages = response.context["pages"]
        self.assertEqual([len(page) for page in pages], [8, 1])
        self.assertEqual(response.context["badge_count"], 9)
        for i in range(9):
            self.assertContains(response, f"Prénom{i:02d}")
            self.assertContains(response, f"Société {i:02d} SA")
        self.assertNotContains(response, "Pasinscrit")  # answered "no"
        self.assertContains(response, "Les vins du Valais")
        self.assertContains(response, "Parle-moi de…")

    def test_each_qr_code_opens_the_scan_page_of_its_member(self):
        pages = self.client.get(self.url).context["pages"]
        for member, qr in (badge for page in pages for badge in page):
            expected = qr_svg("http://testserver" + reverse("club:scan", args=[member.qr_token]))
            self.assertEqual(qr, expected, member)

    def test_print_button_script_and_page_breaks(self):
        response = self.client.get(self.url)
        self.assertContains(response, "data-print")
        self.assertContains(response, "js/print.js")
        self.assertContains(response, "print:break-after-page")  # between the two A4 sheets, not after the last
        self.assertEqual(response.content.decode().count("print:break-after-page"), 1)

    def test_empty_event_explains_itself(self):
        empty = Event.objects.create(is_published=True, title="Vide", kind="apero", location="Sion", starts_at=timezone.now() + timedelta(days=9))
        response = self.client.get(reverse("club:staff_badges", args=[empty.pk]))
        self.assertContains(response, "Aucun inscrit pour l")
        self.assertNotContains(response, "data-print")

    def test_unknown_event_is_404_and_event_tools_link_to_the_badges(self):
        self.assertEqual(self.client.get(reverse("club:staff_badges", args=[9999])).status_code, 404)
        self.assertContains(self.client.get(reverse("club:staff_event", args=[self.event.pk])), self.url)
