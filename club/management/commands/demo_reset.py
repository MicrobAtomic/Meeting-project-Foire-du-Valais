"""Replay the demo: Camille goes back to her starting point (the 2 cards of the demo data, blank bingo grids) and
Lukas gets back the QR code printed in the README. Nothing else changes and nobody is logged out."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from club import demo_data
from club.models import BingoSquare, Connection, Member


class Command(BaseCommand):
    help = "Replay the demo meeting: remove Camille's new meetings and bingo ticks, restore Lukas's demo QR code."

    @transaction.atomic
    def handle(self, *args, **options):
        camille = Member.objects.filter(user__email=demo_data.CAMILLE["email"]).first()
        lukas = Member.objects.filter(user__email=demo_data.LUKAS["email"]).first()
        if camille is None or lukas is None:
            raise CommandError("Demo data not found: run `python manage.py seed_demo` first.")
        meetings, _ = Connection.involving(camille).exclude(source=Connection.Source.SEED).delete()
        squares = (
            BingoSquare.objects.filter(Q(player=camille) | Q(found=camille))
            .exclude(found=None)
            .update(found=None, found_at=None)
        )
        if lukas.qr_token != demo_data.LUKAS["qr_token"]:
            lukas.qr_token = demo_data.LUKAS["qr_token"]
            lukas.save(update_fields=["qr_token"])
        self.stdout.write(self.style.SUCCESS(
            f"Camille is back to her starting point: {meetings} meeting(s) removed, {squares} bingo square(s) cleared. "
            f"Lukas's QR code: /m/{lukas.qr_token}/"
        ))
