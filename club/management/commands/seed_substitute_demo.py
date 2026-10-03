from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from club.models import Member, Substitute
from club.services.events import visible_events
from club.services.substitutions import approve_substitute, request_substitute


class Command(BaseCommand):
    help = "Opt-in fictitious substitute scenario, independent of Camille and Lukas. No email is sent."

    @transaction.atomic
    def handle(self, *args, **options):
        principal = Member.objects.filter(user__email="joelle.luisier@example.com", kind=Member.Kind.MEMBER).first()
        event = visible_events().filter(pk=5, title="Apéro de Noël").first()
        staff = get_user_model().objects.filter(email="equipe@example.com", is_staff=True, is_active=True).first()
        if not principal or not event or not event.responses_open or not staff:
            raise CommandError("Run seed_demo first on a dedicated demo database.")
        existing = Substitute.objects.filter(event=event, member=principal, status="approved").first()
        if existing:
            if existing.email != "invite.demo@example.com":
                raise CommandError("A different substitution already exists; no changes made.")
            self.stdout.write("Substitute demo already prepared.")
            return
        request = request_substitute(event.pk, principal, {
            "first_name": "Alex", "last_name": "Exemple", "email": "invite.demo@example.com", "job_title": "Collègue",
            "speaks_fr": True, "speaks_de": True, "speaks_en": False, "preferred_language": "fr",
        })
        approve_substitute(request.pk, staff)
        self.stdout.write("Fictitious substitute prepared; email queued only. Camille and Lukas unchanged.")
