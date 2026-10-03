from io import StringIO

from django.core.management import call_command
from django.db.models import Q
from django.test import TestCase, override_settings

from club.models import Event, Match, Member


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SeedDemoTests(TestCase):
    def seed(self, **options):
        call_command("seed_demo", stdout=StringIO(), **options)

    def camille_intros(self):
        camille = Member.objects.get(user__email="camille.rey@example.com")
        event = Event.objects.get(title="Dîner d'automne")
        matches = Match.objects.filter(event=event).filter(Q(member_a=camille) | Q(member_b=camille))
        return [(m.other(camille).full_name, m.score) for m in matches.order_by("-score", "pk")]

    def test_the_demo_storyline_is_identical_after_every_reset(self):
        self.seed()
        first = self.camille_intros()
        self.seed(reset=True)
        self.seed(reset=True)
        self.assertEqual(self.camille_intros(), first)
        self.assertEqual(first, [("Lukas Imboden", 16), ("Joëlle Moret", 16), ("Olivier Gay", 11)])

    def test_if_empty_leaves_existing_data_alone(self):
        self.seed()
        members = Member.objects.count()
        Member.objects.filter(first_name="Lukas").update(company="Modifiée à la main")
        self.seed(if_empty=True)
        self.assertEqual(Member.objects.count(), members)
        self.assertTrue(Member.objects.filter(company="Modifiée à la main").exists())

    def test_demo_numbers_match_the_documentation(self):
        self.seed()
        self.assertEqual(Member.objects.count(), 50)
        self.assertEqual(Event.objects.count(), 5)
        self.assertEqual(sorted(Event.objects.values_list("pk", flat=True)), [1, 2, 3, 4, 5])
