from django.conf import settings
from django.utils import timezone


def site(request):
    return {"SITE_NAME": settings.SITE_NAME, "DEMO_MODE": settings.DEMO_MODE, "now": timezone.now()}
