from django.test import TestCase
from django.urls import reverse

from club.models import MemberTag, Tag
from club.services.profile import save_tag_answers
from club.tests.helpers import PASSWORD, make_member


class ProfileTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        Tag.objects.create(slug="golf", emoji="⛳", category="hobby", label_fr="Golf")
        Tag.objects.create(slug="raclette", emoji="🧀", category="valais", label_fr="Raclette")

    def test_save_tag_answers_only_touches_given_member_and_valid_values(self):
        saved = save_tag_answers(self.alice, {"tag_golf": "like", "tag_raclette": "hack", "tag_unknown": "like"})
        self.assertEqual(saved, 1)
        self.assertEqual(MemberTag.objects.get(member=self.alice, tag__slug="golf").sentiment, "like")
        self.assertFalse(MemberTag.objects.filter(member=self.bob).exists())
        save_tag_answers(self.alice, {"tag_golf": "dislike"})
        self.assertEqual(MemberTag.objects.get(member=self.alice, tag__slug="golf").sentiment, "dislike")

    def test_login_with_email_is_case_insensitive(self):
        response = self.client.post(reverse("login"), {"username": "  Alice@Example.COM ", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(reverse("club:home")).status_code, 200)


class HelpersTests(TestCase):
    def test_collected_ids_and_common_tags(self):
        from club.models import Connection
        from club.services.federation import collected_ids
        from club.services.profile import common_tags

        alice, bob, carla = (make_member(f"{n}@example.com") for n in ("alice", "bob", "carla"))
        Connection.link(alice, bob)
        Connection.link(carla, alice)
        self.assertEqual(collected_ids(alice), {bob.pk, carla.pk})
        golf = Tag.objects.create(slug="golf", emoji="⛳", category="hobby", label_fr="Golf")
        a9 = Tag.objects.create(slug="a9", emoji="🚗", category="work", label_fr="A9")
        save_tag_answers(alice, {"tag_golf": "like", "tag_a9": "dislike"})
        save_tag_answers(bob, {"tag_golf": "like", "tag_a9": "like"})
        self.assertEqual(common_tags(alice, bob), {"likes": [golf], "dislikes": []})
