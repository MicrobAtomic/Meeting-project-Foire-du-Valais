from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings

from club.models import Member
from club.templatetags.club_ui import demo_photo


class DemoPhotoTests(SimpleTestCase):
    @override_settings(DEMO_MODE=True)
    def test_closed_list_and_local_files(self):
        for key in ("camille", "lukas", "joelle"):
            member = Member(demo_photo_key=key)
            self.assertTrue(demo_photo(member).endswith(f"img/demo/{key}.jpg"))
            self.assertIsNotNone(finders.find(f"img/demo/{key}.jpg"))
        for key in ("", "../../etc/passwd", "https://evil.example/image"):
            self.assertEqual(demo_photo(Member(demo_photo_key=key)), "")

    @override_settings(DEMO_MODE=False)
    def test_no_demo_portrait_outside_demo(self):
        self.assertEqual(demo_photo(Member(demo_photo_key="camille")), "")
