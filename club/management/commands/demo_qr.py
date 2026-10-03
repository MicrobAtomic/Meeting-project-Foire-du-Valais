"""Write the QR code of Lukas, the member Camille meets in the demo, for a site address (the image of the README)."""

from pathlib import Path

import segno
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from club import demo_data


class Command(BaseCommand):
    help = "Write docs/demo/qr-lukas.svg: the QR code that opens Lukas's card, for a site address (default: local)."

    def add_arguments(self, parser):
        parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8000", help="e.g. https://xxx.onrender.com")
        parser.add_argument("--output", default=str(Path(settings.BASE_DIR, "docs", "demo", "qr-lukas.svg")))

    def handle(self, *args, base_url, output, **options):
        url = base_url.rstrip("/") + reverse("club:scan", args=[demo_data.LUKAS["qr_token"]])
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        segno.make_qr(url, error="m").save(str(path), scale=8, border=2, dark="#1c1917", light="#ffffff")
        self.stdout.write(f"{url}\n→ {path}")
