import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from club.models import BingoSquare, Connection, Event, Member, new_qr_token


class DemoToolsTests(TestCase):
    """The README's demo kit: Lukas's fixed QR code, and the command that replays the meeting."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.camille = Member.objects.get(user__email="camille.rey@example.com")
        cls.lukas = Member.objects.get(user__email="lukas.imboden@example.com")

    def test_the_readme_link_opens_lukas_card(self):
        self.client.force_login(self.camille.user)
        response = self.client.get("/m/demo-lukas/")
        self.assertContains(response, "Ajouter Lukas à mon album")

    def test_demo_reset_replays_the_meeting(self):
        self.client.force_login(self.camille.user)
        self.client.post("/m/demo-lukas/")
        self.assertEqual(Connection.involving(self.camille).count(), 3)
        dinner = Event.objects.get(title="Dîner d'automne")
        square = BingoSquare.objects.get(event=dinner, player=self.camille, found=self.lukas)  # the scan ticked her bingo
        self.lukas.qr_token = new_qr_token()  # someone regenerated Lukas's QR code in the admin
        self.lukas.save()

        out = StringIO()
        call_command("demo_reset", stdout=out)
        self.assertIn("1 meeting(s) removed, 1 bingo square(s) cleared", out.getvalue())
        self.assertEqual(Connection.involving(self.camille).count(), 2)  # the 2 cards of the demo data stay
        square.refresh_from_db()
        self.assertIsNone(square.found)
        self.lukas.refresh_from_db()
        self.assertEqual(self.lukas.qr_token, "demo-lukas")
        self.assertContains(self.client.get("/m/demo-lukas/"), "Ajouter Lukas à mon album")

    def test_demo_qr_writes_the_svg_for_the_online_address(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder, "qr.svg")
            out = StringIO()
            call_command("demo_qr", "https://club.example.com/", output=str(output), stdout=out)
            self.assertIn("https://club.example.com" + reverse("club:scan", args=["demo-lukas"]), out.getvalue())
            self.assertTrue(output.read_text().startswith("<?xml"))


class DemoResetWithoutDataTests(TestCase):
    def test_explains_what_to_do(self):
        with self.assertRaisesMessage(CommandError, "seed_demo"):
            call_command("demo_reset", stdout=StringIO())
