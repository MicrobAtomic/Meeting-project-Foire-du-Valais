from django.test import TestCase, override_settings
from django.urls import reverse

from club.tests.helpers import assert_csp_clean, make_member


@override_settings(
    MEMBERSHIP_PRICE=720, REFERRAL_NEW_MEMBER_PRICE=490,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class ReferralPriceTests(TestCase):
    def test_offer_requires_an_active_sponsor_and_enabled_offer_in_every_language(self):
        sponsor = make_member("sponsor@example.com")
        url = reverse("club:join")
        sponsored = url + "?ref=" + sponsor.referral_code.lower()
        guest = make_member("guest@example.com", kind="guest")
        renewals = {
            "fr": "Puis 720 CHF par an dès la deuxième année.",
            "de": "Ab dem zweiten Jahr 720 CHF pro Jahr.",
            "en": "Then CHF 720 per year from year two.",
        }
        for language in ("fr", "de", "en"):
            self.client.cookies["django_language"] = language
            for enabled in (True, False):
                with override_settings(REFERRAL_OFFER_ENABLED=enabled):
                    for route, eligible in (
                        (sponsored, True), (url, False), (url + "?ref=UNKNOWN", False),
                        (url + "?ref=" + guest.referral_code, False),
                    ):
                        for post in (False, True):
                            with self.subTest(language=language, enabled=enabled, route=route, post=post):
                                response = self.client.post(route, {"email": "invalid"}) if post else self.client.get(route)
                                assert_csp_clean(self, response)
                                self.assertContains(response, "720")
                                if enabled and eligible:
                                    self.assertContains(response, "490")
                                    self.assertContains(response, "<s ")
                                    self.assertContains(response, "<strong ")
                                    self.assertContains(response, renewals[language])
                                    self.assertNotContains(response, "350")
                                else:
                                    self.assertNotContains(response, "490")
                                    self.assertNotContains(response, "<s ")
            sponsor.user.is_active = False
            sponsor.user.save()
            with override_settings(REFERRAL_OFFER_ENABLED=True):
                response = self.client.get(sponsored)
                self.assertNotContains(response, "490")
                self.assertNotContains(response, "<s ")
            sponsor.user.is_active = True
            sponsor.user.save()
