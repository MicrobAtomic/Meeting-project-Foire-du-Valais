from django.test import TestCase, override_settings
from django.urls import reverse

from club.models import EmailPreferences
from club.services.auth_links import email_language
from club.tests.helpers import make_member, make_staff


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class EmailPreferenceTests(TestCase):
    def test_defaults_language_and_only_own_preferences(self):
        a, b = make_member("a@example.com"), make_member("b@example.com")
        self.assertEqual(email_language(a), "fr")
        self.client.force_login(a.user)
        page = self.client.get(reverse("club:profile_edit"))
        self.assertFalse(EmailPreferences.objects.exists())  # GET has no persistence side effect
        data = {field: getattr(a, field) for field in ("first_name", "last_name", "company", "job_title", "sector")}
        data.update(visible_in_directory="on", speaks_fr="on", preferred_language="de", monthly_digest="on", allow_member_spotlight="on",
                    event_announcements="on", event_reminders="on", member=b.pk, admitted_at="2000-01-01",
                    digest_teaser="Accroche volontaire")
        self.assertEqual(self.client.post(reverse("club:profile_edit"), data).status_code, 302)
        a.refresh_from_db()
        self.assertIsNone(a.admitted_at)
        self.assertEqual(email_language(a), "de")
        self.assertTrue(a.speaks_fr)
        self.assertTrue(EmailPreferences.objects.get(member=a).monthly_digest)
        self.assertFalse(EmailPreferences.objects.filter(member=b).exists())
        self.client.force_login(b.user)
        detail = self.client.get(reverse("club:member_detail", args=[a.pk]))
        self.assertNotContains(detail, "Accroche volontaire")
        self.assertNotContains(detail, 'name="monthly_digest"')

    def test_admin_shows_explicit_and_inferred_communication_languages(self):
        explicit = make_member("explicit@example.com", preferred_language="de", speaks_fr=True)
        inferred = make_member("inferred@example.com", speaks_fr=False, speaks_de=False, speaks_en=True)
        staff = make_staff()
        staff.is_superuser = True
        staff.save(update_fields=["is_superuser"])
        self.client.force_login(staff)
        page = self.client.get(reverse("admin:club_member_changelist"))
        self.assertContains(page, "Langue des communications")
        model_admin = page.context["cl"].model_admin
        self.assertEqual(str(model_admin.communication_language(explicit)), "Allemand")
        self.assertEqual(str(model_admin.communication_language(inferred)), "Anglais")
        self.assertIn("communication_language", page.context["cl"].list_display)
        edit = self.client.get(reverse("admin:club_member_change", args=[explicit.pk]))
        self.assertContains(edit, "Langue des communications")

    def test_invalid_teaser_opens_email_options_and_saves_nothing(self):
        member = make_member("invalid@example.com", preferred_language="fr")
        preferences = EmailPreferences.objects.create(member=member, monthly_digest=True)
        self.client.force_login(member.user)
        data = {field: getattr(member, field) for field in ("first_name", "last_name", "company", "job_title", "sector")}
        data.update(preferred_language="en", digest_teaser="x" * 121)
        page = self.client.post(reverse("club:profile_edit"), data)
        self.assertContains(page, "<details open>", html=False)
        self.assertIn("digest_teaser", page.context["form"].errors)
        member.refresh_from_db()
        preferences.refresh_from_db()
        self.assertEqual(member.preferred_language, "fr")
        self.assertTrue(preferences.monthly_digest)
