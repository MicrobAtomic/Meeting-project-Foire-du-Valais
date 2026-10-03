import tempfile
from io import BytesIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from club.forms import MemberAdminForm, MemberProfileForm
from club.models import Connection
from club.services.photos import available_photo, normalize_member_photo, save_profile_photo
from club.tests.helpers import make_member


def upload(format="PNG", size=(100, 200), **kwargs):
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, format, **kwargs)
    return SimpleUploadedFile("untrusted.name", buffer.getvalue(), content_type="text/plain")


@override_settings(PROFILE_PHOTO_UPLOADS_ENABLED=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PhotoTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(MEDIA_ROOT=directory.name)
        override.enable()
        self.addCleanup(override.disable)
        self.a = make_member("a@example.com")
        self.b = make_member("b@example.com")
        self.client.force_login(self.a.user)

    def test_normalization_and_exif_removal(self):
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "SECRET-METADATA"
        data = normalize_member_photo(upload("JPEG", exif=exif))
        raw = data.read()
        with Image.open(BytesIO(raw)) as image:
            self.assertEqual(image.size, (512, 512))
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.mode, "RGB")
            self.assertFalse(image.getexif())
        self.assertNotIn(b"SECRET-METADATA", raw)

    def test_formats_size_dimensions_and_malformed_input(self):
        for invalid in (upload("GIF"), upload(size=(4097, 1)),
                        SimpleUploadedFile("bad.jpg", b"not a JPEG"),
                        SimpleUploadedFile("bad.svg", b"<svg/>"),
                        SimpleUploadedFile("huge.jpg", b"x" * (2 * 1024 * 1024 + 1)),
                        SimpleUploadedFile("cut.jpg", upload("JPEG").read()[:30])):
            with self.assertRaises(ValidationError):
                normalize_member_photo(invalid)
        for format in ("PNG", "JPEG", "WEBP"):
            self.assertTrue(normalize_member_photo(upload(format)).size)
        buffer = BytesIO()
        Image.new("RGB", (10, 10), "red").save(buffer, "WEBP", save_all=True, append_images=[Image.new("RGB", (10, 10), "blue")])
        with self.assertRaises(ValidationError):
            normalize_member_photo(SimpleUploadedFile("animated.webp", buffer.getvalue()))

    def test_private_read_hidden_connected_missing_and_anonymous(self):
        save_profile_photo(self.b, normalize_member_photo(upload()))
        url = reverse("club:member_photo", args=[self.b.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("Cookie", response["Vary"])
        self.assertTrue(b"".join(response.streaming_content).startswith(b"\xff\xd8"))
        self.assertEqual(self.client.post(url).status_code, 405)
        self.b.visible_in_directory = False
        self.b.save()
        self.assertEqual(self.client.get(url).status_code, 404)
        Connection.link(self.a, self.b)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.b.photo.storage.delete(self.b.photo.name)
        self.assertFalse(available_photo(self.b))
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.get("/media/member_photos/anything.jpg").status_code, 404)

    def test_replace_remove_delete_and_failed_save(self):
        save_profile_photo(self.a, normalize_member_photo(upload()))
        old, storage = self.a.photo.name, self.a.photo.storage
        with self.captureOnCommitCallbacks(execute=True):
            save_profile_photo(self.a, normalize_member_photo(upload("JPEG")))
        self.assertFalse(storage.exists(old))
        old = self.a.photo.name
        with patch.object(self.a, "save", side_effect=RuntimeError("database failed")):
            with self.assertRaises(RuntimeError):
                save_profile_photo(self.a, normalize_member_photo(upload()))
        self.assertEqual(self.a.photo.name, old)
        self.assertTrue(storage.exists(old))
        with self.captureOnCommitCallbacks(execute=True):
            save_profile_photo(self.a, remove=True)
        self.assertFalse(storage.exists(old))
        save_profile_photo(self.a, normalize_member_photo(upload()))
        old = self.a.photo.name
        with self.captureOnCommitCallbacks(execute=True):
            self.a.delete()
        self.assertFalse(storage.exists(old))

    def test_forms_and_production_gate(self):
        self.assertNotIn('Currently:', str(MemberAdminForm(instance=self.a)["photo"]))
        self.assertIsNone(MemberProfileForm(instance=self.a)["photo"].value())
        form = MemberProfileForm({"remove_photo": "on"}, {"photo": upload()}, instance=self.a)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        self.assertFalse(self.a.photo)
        with override_settings(PROFILE_PHOTO_UPLOADS_ENABLED=False):
            form = MemberProfileForm(instance=self.a)
            self.assertNotIn("photo", form.fields)
            self.assertNotIn("remove_photo", form.fields)
