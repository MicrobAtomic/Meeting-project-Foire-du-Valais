from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from club.models import EmailPreferences, InvitationRequest, Member, Sector
from club.services.auth_links import email_language
from club.services.membership import accept_invitation
from club.tests.helpers import make_member, make_staff
from club.tests.test_join import valid_data


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MembershipTests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.invitation = InvitationRequest.objects.create(first_name="Marie", last_name="Fictive", company="Test SA",
            job_title="Direction", email="MARIE@example.com", language="de")

    def test_acceptance_is_linked_idempotent_and_not_an_email_success(self):
        member = accept_invitation(self.invitation.pk, self.staff)
        self.assertEqual(accept_invitation(self.invitation.pk, self.staff).pk, member.pk)
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(member.sector, Sector.OTHER)
        self.assertFalse(member.user.has_usable_password())
        self.assertFalse(member.onboarding_done)
        self.assertIsNotNone(member.admitted_at)
        self.assertEqual(member.preferred_language, "de")
        self.assertEqual(email_language(member), "de")
        self.assertTrue(EmailPreferences.objects.get(member=member).event_announcements)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "accepted")
        self.assertIsNone(self.invitation.welcome_sent_at)

    def test_existing_identity_and_nonstaff_cannot_create_accounts(self):
        other = make_member("marie@example.com")
        with self.assertRaises(PermissionDenied):
            accept_invitation(self.invitation.pk, other.user)
        with self.assertRaises(ValidationError):
            accept_invitation(self.invitation.pk, self.staff)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "new")
        self.assertIsNone(self.invitation.member_id)

    def test_failed_member_creation_rolls_back_user_and_invitation(self):
        count = get_user_model().objects.count()
        with patch("club.services.membership.Member.objects.create", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                accept_invitation(self.invitation.pk, self.staff)
        self.assertEqual(get_user_model().objects.count(), count)
        self.invitation.refresh_from_db()
        self.assertIsNone(self.invitation.member_id)

    def test_join_stores_active_language(self):
        for language in ("de", "en"):
            self.client.cookies["django_language"] = language
            self.client.post(reverse("club:join"), valid_data(email=f"{language}@example.com"))
            self.assertEqual(InvitationRequest.objects.get(email=f"{language}@example.com").language, language)
