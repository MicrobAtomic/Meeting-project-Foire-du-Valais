from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from club.services.notifications import process_notifications


class Command(BaseCommand):
    help = "Prepare due campaigns and process a bounded notification batch. SMTP must be explicitly enabled."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        if not 1 <= options["limit"] <= 500:
            raise CommandError("limit must be between 1 and 500")
        try:
            result = process_notifications(limit=options["limit"], dry_run=options["dry_run"])
        except (ValidationError, OSError) as error:
            raise CommandError(type(error).__name__) from None
        self.stdout.write(str(result))
