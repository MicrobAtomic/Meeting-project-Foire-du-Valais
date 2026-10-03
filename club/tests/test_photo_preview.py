import tempfile
from io import BytesIO
from pathlib import Path
import struct
import zlib

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from club.models import Member
from club.services.photos import normalize_member_photo, save_profile_photo
from club.tests.helpers import make_member
from club.tests.test_photos import upload


@override_settings(PROFILE_PHOTO_UPLOADS_ENABLED=True,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PhotoPreviewTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        override = override_settings(MEDIA_ROOT=self.directory.name)
        override.enable()
        self.addCleanup(override.disable)
        self.member = make_member("preview@example.com")
        self.other = make_member("other@example.com")
        self.client.force_login(self.member.user)
        self.url = reverse("club:profile_photo_preview")

    def test_preview_is_the_final_jpeg_without_saving_or_changing_any_profile(self):
        save_profile_photo(self.member, normalize_member_photo(upload()))
        before = list(Member.objects.values("pk", "photo"))
        files = set(Path(self.directory.name).rglob("*"))
        data = upload("PNG", size=(160, 320)).read()
        expected = normalize_member_photo(SimpleUploadedFile("source.png", data)).read()
        response = self.client.post(self.url, {"photo": SimpleUploadedFile("source.png", data), "member": self.other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("Cookie", response["Vary"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(list(Member.objects.values("pk", "photo")), before)
        self.assertEqual(set(Path(self.directory.name).rglob("*")), files)

    def test_preview_requires_login_post_csrf_and_enabled_uploads(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(Client().post(self.url, {"photo": upload()}).status_code, 302)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.member.user)
        self.assertEqual(strict.post(self.url, {"photo": upload()}).status_code, 403)
        strict.get(reverse("club:profile_edit"))
        response = strict.post(self.url, {"photo": upload()}, HTTP_X_CSRFTOKEN=strict.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 200)
        with override_settings(PROFILE_PHOTO_UPLOADS_ENABLED=False):
            self.assertEqual(self.client.post(self.url, {"photo": upload()}).status_code, 403)

    def test_missing_or_invalid_image_returns_a_safe_validation_error(self):
        for data in ({}, {"photo": SimpleUploadedFile("bad.svg", b"<svg/>")}):
            response = self.client.post(self.url, data)
            self.assertEqual(response.status_code, 400)
            self.assertTrue(response.json()["error"])
        self.assertFalse(list(Path(self.directory.name).rglob("*.jpg")))

    def test_heic_avif_and_high_resolution_phone_photo_are_automatically_converted(self):
        for format in ("HEIF", "AVIF", "JPEG"):
            source = upload(format, size=(8064, 6048) if format == "JPEG" else (120, 180))
            result = normalize_member_photo(source)
            with Image.open(result) as image:
                self.assertEqual(image.format, "JPEG", format)
                self.assertEqual(image.size, (512, 512), format)
                self.assertEqual(image.mode, "RGB", format)
                self.assertFalse(image.getexif(), format)
        # HEIC can be previewed even when the browser cannot display the original format.
        response = self.client.post(self.url, {"photo": upload("HEIF")})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xff\xd8"))

    def test_exif_orientation_and_transparent_background_are_preserved_visually(self):
        image = Image.new("RGB", (100, 100), "red")
        image.paste("blue", (50, 0, 100, 100))
        exif = Image.Exif()
        exif[274] = 6
        raw = BytesIO()
        image.save(raw, "JPEG", exif=exif)
        result = normalize_member_photo(SimpleUploadedFile("rotated.jpg", raw.getvalue()))
        with Image.open(result) as normalized:
            self.assertGreater(normalized.getpixel((256, 64))[0], 200)
            self.assertGreater(normalized.getpixel((256, 448))[2], 200)
        raw = BytesIO()
        Image.new("RGBA", (50, 100), (0, 0, 0, 0)).save(raw, "PNG")
        with Image.open(normalize_member_photo(SimpleUploadedFile("alpha.png", raw.getvalue()))) as normalized:
            self.assertEqual(normalized.getpixel((256, 256)), (255, 255, 255))

    def test_pixel_budget_is_checked_before_decoding_an_oversized_image(self):
        # A valid PNG header announcing 56 MP must be rejected before its small IDAT can be decoded.
        raw = bytearray(upload("PNG").read())
        raw[16:24] = struct.pack(">II", 8000, 7000)
        raw[29:33] = struct.pack(">I", zlib.crc32(raw[12:29]))
        response = self.client.post(self.url, {"photo": SimpleUploadedFile("oversized.png", raw)})
        self.assertEqual(response.status_code, 400)
        self.assertIn("50", response.json()["error"])
