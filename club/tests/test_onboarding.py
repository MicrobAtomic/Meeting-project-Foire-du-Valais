import re

from django.test import TestCase
from django.urls import reverse

from club.models import MemberTag, Tag
from club.tests.helpers import assert_csp_clean, make_member, make_staff


class OnboardingTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        self.golf = Tag.objects.create(slug="golf", emoji="⛳", category="hobby", label_fr="Golf", order=1)
        self.raclette = Tag.objects.create(slug="raclette", emoji="🧀", category="valais", label_fr="Raclette", order=2)
        self.a9 = Tag.objects.create(slug="a9", emoji="🚗", category="work", label_fr="Les bouchons sur l'A9", order=3)
        self.url = reverse("club:onboarding")
        self.client.force_login(self.alice.user)

    def test_page_follows_the_contract_of_swipe_js(self):
        response = self.client.get(self.url)
        assert_csp_clean(self, response)
        html = response.content.decode()
        self.assertIn('id="swipe-form"', html)
        self.assertEqual(html.count('class="swipe-card '), 3)  # one card per tag
        self.assertRegex(html, r'id="swipe-controls" hidden')  # revealed by the script only
        for answer in ("dislike", "neutral", "like"):
            self.assertIn(f'data-answer="{answer}"', html)
            self.assertEqual(len(re.findall(rf'type="radio" name="tag_\w+" value="{answer}"', html)), 3)
        self.assertIn('id="swipe-progress"', html)
        self.assertIn("js/swipe.js", html)
        self.assertIn('class="swipe-deck', html)
        self.assertIn('class="swipe-choices', html)  # the no-JS fallback

    def test_existing_answers_are_pre_checked_and_unanswered_default_to_neutral(self):
        MemberTag.objects.create(member=self.alice, tag=self.golf, sentiment="like")
        MemberTag.objects.create(member=self.alice, tag=self.a9, sentiment="dislike")
        html = self.client.get(self.url).content.decode()
        self.assertRegex(html, r'name="tag_golf" value="like" class="peer sr-only" checked')
        self.assertRegex(html, r'name="tag_a9" value="dislike" class="peer sr-only" checked')
        self.assertRegex(html, r'name="tag_raclette" value="neutral" class="peer sr-only" checked')
        self.assertNotRegex(html, r'name="tag_golf" value="neutral" class="peer sr-only" checked')

    def test_post_saves_my_answers_marks_onboarding_done_and_goes_home(self):
        self.assertFalse(self.alice.onboarding_done)
        response = self.client.post(self.url, {"tag_golf": "like", "tag_raclette": "dislike", "tag_a9": "neutral"}, follow=True)
        self.assertRedirects(response, reverse("club:home"))
        self.assertContains(response, "Profil complété")
        answers = dict(MemberTag.objects.filter(member=self.alice).values_list("tag__slug", "sentiment"))
        self.assertEqual(answers, {"golf": "like", "raclette": "dislike", "a9": "neutral"})
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.onboarding_done)

    def test_invalid_values_and_unknown_tags_are_ignored(self):
        self.client.post(self.url, {"tag_golf": "adore", "tag_raclette": "LIKE", "tag_a9": "like", "tag_nope": "like", "evil": "like"})
        answers = dict(MemberTag.objects.filter(member=self.alice).values_list("tag__slug", "sentiment"))
        self.assertEqual(answers, {"a9": "like"})
        self.assertFalse(Tag.objects.filter(slug="nope").exists())

    def test_answers_are_replaced_not_duplicated_and_other_members_untouched(self):
        MemberTag.objects.create(member=self.bob, tag=self.golf, sentiment="dislike")
        self.client.post(self.url, {"tag_golf": "like"})
        self.client.post(self.url, {"tag_golf": "dislike"})
        self.assertEqual(MemberTag.objects.filter(member=self.alice, tag=self.golf).count(), 1)
        self.assertEqual(MemberTag.objects.get(member=self.alice, tag=self.golf).sentiment, "dislike")
        self.assertEqual(MemberTag.objects.get(member=self.bob, tag=self.golf).sentiment, "dislike")  # bob's own answer

    def test_home_banner_invites_to_complete_the_profile_until_done(self):
        home = reverse("club:home")
        self.assertContains(self.client.get(home), "Complète ton profil en 2 minutes")
        self.assertContains(self.client.get(home), self.url)
        self.client.post(self.url, {"tag_golf": "like"})
        self.assertNotContains(self.client.get(home), "Complète ton profil en 2 minutes")

    def test_profile_page_offers_to_redo_the_swipe(self):
        self.assertContains(self.client.get(reverse("club:profile_edit")), f'href="{self.url}"')

    def test_visitors_are_sent_to_login_and_staff_without_profile_to_the_dashboard(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.client.force_login(make_staff())
        self.assertRedirects(self.client.get(self.url), reverse("club:staff_dashboard"))
