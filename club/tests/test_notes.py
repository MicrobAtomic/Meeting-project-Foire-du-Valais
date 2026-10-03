from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from club.models import Connection, PersonalNote
from club.tests.helpers import assert_csp_clean, make_member, make_staff


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PersonalNoteTests(TestCase):
    def setUp(self):
        self.a = make_member("a@example.com")
        self.b = make_member("b@example.com")
        self.c = make_member("c@example.com")
        self.url = reverse("club:member_note", args=[self.b.pk])
        self.detail = reverse("club:member_detail", args=[self.b.pk])
        self.secret = "SENTINELLE-PRIVEE-A"
        self.client.force_login(self.a.user)

    def test_only_owner_can_read_and_overposted_owner_cannot_change_another_note(self):
        self.assertEqual(self.client.post(self.url, {"text": self.secret}).status_code, 302)
        page = self.client.get(self.detail)
        self.assertContains(page, self.secret)
        self.assertIn("no-store", page["Cache-Control"])
        self.assertIn("Cookie", page["Vary"])
        for reader in (self.b, self.c):
            self.client.force_login(reader.user)
            self.assertNotContains(self.client.get(self.detail), self.secret)
        note = PersonalNote.objects.get(owner=self.a)
        self.client.post(self.url, {"text": "Note C", "owner": self.a.pk, "note_id": note.pk})
        note.refresh_from_db()
        self.assertEqual(note.text, self.secret)
        self.assertEqual(PersonalNote.objects.get(owner=self.c).text, "Note C")

    def test_hidden_inactive_and_self_are_denied(self):
        self.b.visible_in_directory = False
        self.b.save()
        self.assertEqual(self.client.post(self.url, {"text": self.secret}).status_code, 404)
        Connection.link(self.a, self.b)
        self.assertEqual(self.client.post(self.url, {"text": self.secret}).status_code, 302)
        self.b.user.is_active = False
        self.b.user.save()
        self.assertEqual(self.client.post(self.url, {"text": "change"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("club:member_note", args=[self.a.pk]), {"text": "self"}).status_code, 404)

    def test_blank_deletes_and_oversized_preserves_previous_text(self):
        self.client.post(self.url, {"text": self.secret})
        response = self.client.post(self.url, {"text": "x" * 2001})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["note_form"].errors)
        self.assertEqual(PersonalNote.objects.get().text, self.secret)
        self.client.post(self.url, {"text": "  \n  "})
        self.assertFalse(PersonalNote.objects.exists())

    def test_text_is_escaped_and_csp_remains_strict(self):
        self.client.post(self.url, {"text": '<script>alert("secret")</script>'})
        page = self.client.get(self.detail)
        self.assertContains(page, "&lt;script&gt;")
        self.assertNotContains(page, '<script>alert')
        assert_csp_clean(self, page)

    def test_csrf_and_post_only(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.a.user)
        self.assertEqual(strict.post(self.url, {"text": self.secret}).status_code, 403)
        self.assertFalse(PersonalNote.objects.exists())

    def test_no_leak_through_album_vcard_public_staff_or_admin(self):
        self.client.post(self.url, {"text": self.secret})
        Connection.link(self.a, self.b)
        for name, args in (("club:album", []), ("club:member_vcard", [self.b.pk]), ("club:landing", [])):
            self.assertNotContains(self.client.get(reverse(name, args=args)), self.secret)
        self.client.force_login(make_staff())
        self.assertNotContains(self.client.get(reverse("club:staff_dashboard")), self.secret)
        self.assertNotIn(PersonalNote, admin.site._registry)

    def test_database_constraints_and_cascades(self):
        PersonalNote.objects.create(owner=self.a, target=self.b, text=self.secret)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PersonalNote.objects.create(owner=self.a, target=self.b, text="duplicate")
        with self.assertRaises(IntegrityError), transaction.atomic():
            PersonalNote.objects.create(owner=self.a, target=self.a, text="self")
        self.b.delete()
        self.assertFalse(PersonalNote.objects.exists())
