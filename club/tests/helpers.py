import re

from django.contrib.auth import get_user_model

from club.models import Member

User = get_user_model()
PASSWORD = "Test-pass-2026!"


def make_member(email, **extra):
    user = User.objects.create_user(username=email, email=email, password=PASSWORD)
    fields = {
        "first_name": "Prénom",
        "last_name": email.split("@")[0],
        "company": "Test SA",
        "job_title": "CEO",
        "sector": "tech",
        "member_since": 2020,
    }
    fields.update(extra)
    return Member.objects.create(user=user, **fields)


def make_staff(email="staff@example.com"):
    return User.objects.create_user(username=email, email=email, password=PASSWORD, is_staff=True)


INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)(?![^>]*application/json)[^>]*>", re.I)
INLINE_STYLE = re.compile(r"(\sstyle=[\"']|<style)", re.I)
INLINE_HANDLER = re.compile(r"\son[a-z]+=[\"']", re.I)


def assert_csp_clean(testcase, response):
    """Page served with the strict CSP header and without any inline script/style/handler."""
    url = response.request["PATH_INFO"]
    testcase.assertEqual(response.status_code, 200, url)
    testcase.assertIn("script-src 'self'", response["Content-Security-Policy"], url)
    html = response.content.decode()
    testcase.assertIsNone(INLINE_SCRIPT.search(html), f"inline <script> in {url}")
    testcase.assertIsNone(INLINE_STYLE.search(html), f"inline style in {url}")
    testcase.assertIsNone(INLINE_HANDLER.search(html), f"inline on*= handler in {url}")
