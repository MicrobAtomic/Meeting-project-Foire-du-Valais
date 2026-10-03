from django.core.management.base import BaseCommand

from club.models import Member
from club.services.substitutions import member_access_valid, recalculate_guest_access


class Command(BaseCommand):
    help = "Deactivate expired guest accounts while preserving genuine meetings. Never affects regular members."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        guests = Member.objects.filter(kind=Member.Kind.GUEST, user__is_active=True).select_related("user")
        expired = [guest for guest in guests if not member_access_valid(guest)]
        if not options["dry_run"]:
            for guest in expired:
                recalculate_guest_access(guest)
        self.stdout.write(f"Expired guest accounts: {len(expired)}; dry_run={options['dry_run']}")
