from django.test import TestCase
from django.urls import reverse

from club.models import MemberTag, Tag
from club.tests.helpers import assert_csp_clean, make_member


class ProfileEditTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com", company="Alice SA")
        self.bob = make_member("bob@example.com", company="Bob SA")
        self.golf = Tag.objects.create(slug="golf", emoji="⛳", category="hobby", label_fr="Golf")
        self.client.force_login(self.alice.user)
        self.url = reverse("club:profile_edit")

    def data(self, **extra):
        data = {
            "first_name": "Alice", "last_name": "Martin", "company": "Alice SA", "job_title": "CEO",
            "sector": "finance", "region": "Sion", "speaks_fr": "on", "fun_fact": "A couru Sierre-Zinal.",
            "talk_to_me_about": "La finance durable", "phone": "+41 79 000 00 00", "linkedin_url": "",
            "visible_in_directory": "on",
        }
        data.update(extra)
        return data

    def test_form_page_is_prefilled_and_csp_clean(self):
        response = self.client.get(self.url)
        assert_csp_clean(self, response)
        self.assertContains(response, 'value="Alice SA"')
        self.assertContains(response, 'name="tag_golf"')
        self.assertContains(response, 'type="tel"')

    def test_posted_forbidden_fields_are_ignored(self):
        original = (self.alice.member_since, self.alice.is_founder, self.alice.qr_token, self.alice.referral_code)
        response = self.client.post(self.url, self.data(
            member_since="1990", is_founder="on", qr_token="hacked", referral_code="HACKED", user=self.bob.user.pk,
        ))
        self.assertEqual(response.status_code, 302)
        self.alice.refresh_from_db()
        self.assertEqual((self.alice.member_since, self.alice.is_founder, self.alice.qr_token, self.alice.referral_code), original)
        self.assertEqual(self.alice.user_id, self.alice.user.pk)
        self.assertNotEqual(self.alice.user_id, self.bob.user_id)

    def test_post_updates_my_profile_only_and_saves_tags(self):
        response = self.client.post(self.url, self.data(company="Nouvelle SA", tag_golf="like", tag_unknown="like"))
        self.assertRedirects(response, reverse("club:member_detail", args=[self.alice.pk]), fetch_redirect_response=False)
        self.alice.refresh_from_db()
        self.bob.refresh_from_db()
        self.assertEqual(self.alice.company, "Nouvelle SA")
        self.assertEqual(self.alice.sector, "finance")
        self.assertEqual(self.bob.company, "Bob SA")
        self.assertEqual(MemberTag.objects.get(member=self.alice, tag=self.golf).sentiment, "like")
        self.assertFalse(MemberTag.objects.filter(member=self.bob).exists())

    def test_confirmation_message_is_shown_after_saving(self):
        response = self.client.post(self.url, self.data(), follow=True)
        self.assertContains(response, "Profil enregistré")

    def test_invalid_form_shows_errors_and_saves_nothing(self):
        response = self.client.post(self.url, self.data(company="", tag_golf="dislike"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="alert"')
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.company, "Alice SA")
        self.assertFalse(MemberTag.objects.filter(member=self.alice).exists())
        self.assertContains(response, 'value="dislike" class="peer sr-only" checked')  # the tick is kept on redisplay

    def test_staff_without_member_profile_cannot_open_it(self):
        from club.tests.helpers import make_staff

        self.client.force_login(make_staff())
        self.assertEqual(self.client.get(self.url).status_code, 302)  # sent to the staff dashboard
