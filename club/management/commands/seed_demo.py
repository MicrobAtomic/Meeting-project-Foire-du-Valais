import os
import random
import secrets
import unicodedata
from datetime import timedelta
from itertools import combinations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from club import demo_data
from club.models import RSVP, Connection, Event, InvitationRequest, Match, Member, MemberTag, Sector, Tag
from club.services.events import generate_matches
from club.services.federation import club_stats

User = get_user_model()
DEMO_DOMAIN = "@example.com"


def ascii_slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return "".join(c if c.isalnum() else "-" for c in text).strip("-")


class Command(BaseCommand):
    help = "Create fictitious demo data: tags, ~50 members, events, connections, introductions."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo data (users @example.com, events, tags) first.")
        parser.add_argument("--if-empty", action="store_true", help="Do nothing when members already exist (used at deploy).")

    @transaction.atomic
    def handle(self, *args, reset=False, if_empty=False, **options):
        if if_empty and Member.objects.exists():
            self.stdout.write("Members already exist: seed skipped.")
            return
        if reset:
            User.objects.filter(email__endswith=DEMO_DOMAIN).delete()
            Event.objects.all().delete()
            Tag.objects.all().delete()
            InvitationRequest.objects.all().delete()
        elif Member.objects.exists():
            raise CommandError("Members already exist. Use --reset to recreate the demo data.")

        rng = random.Random(42)
        password = os.environ.get("DEMO_PASSWORD") or ("club-demo-2026" if settings.DEBUG else secrets.token_urlsafe(12))
        year = timezone.localdate().year
        tags = self.create_tags()

        staff = User.objects.create_user(
            username=demo_data.STAFF["email"], email=demo_data.STAFF["email"], password=password,
            first_name=demo_data.STAFF["first_name"], last_name=demo_data.STAFF["last_name"],
            is_staff=True, is_superuser=True,
        )
        camille = self.create_member(tags, password=password, **{**demo_data.CAMILLE, "member_since": year})
        lukas = self.create_member(tags, password=password, **demo_data.LUKAS)
        others = self.create_other_members(rng, tags, year)
        members = [camille, lukas, *others]

        past, upcoming, later = self.create_events()
        self.create_rsvps(rng, members, past, upcoming, later, camille, lukas)
        self.create_connections(rng, members, past, camille, lukas)
        intros = generate_matches(upcoming)

        self.check_storyline(upcoming, camille, lukas)
        stats = club_stats()
        self.stdout.write(self.style.SUCCESS(
            f"{stats['members']} members, {stats['connections']} connections, "
            f"federation index {stats['index']:.0%}, {intros} introductions for '{upcoming.title}'."
        ))
        self.stdout.write(f"Demo accounts (password: {password}):")
        for user in (staff, camille.user, lukas.user):
            self.stdout.write(f"  - {user.email}{' (staff)' if user.is_staff else ''}")

    def create_tags(self):
        tags = {}
        for order, row in enumerate(demo_data.TAGS):
            slug, emoji, category, label_fr, label_de, label_en, ice_fr, ice_de, ice_en = row
            tags[slug] = Tag.objects.create(
                slug=slug, emoji=emoji, category=category, order=order,
                label_fr=label_fr, label_de=label_de, label_en=label_en,
                icebreaker_fr=ice_fr, icebreaker_de=ice_de, icebreaker_en=ice_en,
            )
        return tags

    def create_member(self, tags, *, email, likes, dislikes, password=None, **fields):
        user = User.objects.create_user(username=email, email=email, password=password)  # None -> unusable password
        member = Member.objects.create(user=user, onboarding_done=True, **fields)
        MemberTag.objects.bulk_create(
            [MemberTag(member=member, tag=tags[s], sentiment=MemberTag.Sentiment.LIKE) for s in likes]
            + [MemberTag(member=member, tag=tags[s], sentiment=MemberTag.Sentiment.DISLIKE) for s in dislikes]
        )
        return member

    def create_other_members(self, rng, tags, year):
        work = [t for t in tags.values() if t.category == Tag.Category.WORK]
        fun = [t for t in tags.values() if t.category != Tag.Category.WORK]
        years = [2016] * 4 + [rng.randint(2017, 2019) for _ in range(10)] + [rng.randint(2020, 2023) for _ in range(18)]
        years += [rng.randint(year - 2, year - 1) for _ in range(11)] + [year] * 5
        used_names, members = set(), []
        for i, member_since in enumerate(years):
            german = i % 4 == 3
            first_names, last_names = (
                (demo_data.FIRST_NAMES_DE, demo_data.LAST_NAMES_DE) if german
                else (demo_data.FIRST_NAMES_FR, demo_data.LAST_NAMES_FR)
            )
            while True:
                first, last = rng.choice(first_names), rng.choice(last_names)
                if (first, last) not in used_names:
                    used_names.add((first, last))
                    break
            sector = rng.choice(Sector.values)
            likes = rng.sample(fun, rng.randint(3, 6))
            dislikes = rng.sample(work, rng.randint(1, 2))
            members.append(self.create_member(
                tags,
                email=f"{ascii_slug(first)}.{ascii_slug(last)}{DEMO_DOMAIN}",
                likes=[t.slug for t in likes],
                dislikes=[t.slug for t in dislikes],
                first_name=first,
                last_name=last,
                company=" ".join([
                    rng.choice(demo_data.COMPANY_PREFIXES),
                    rng.choice(demo_data.COMPANY_SUFFIXES[sector]),
                    rng.choice(demo_data.LEGAL_FORMS_DE if german else demo_data.LEGAL_FORMS_FR),
                ]),
                job_title=rng.choice(demo_data.JOB_TITLES_DE if german else demo_data.JOB_TITLES_FR),
                sector=sector,
                region=rng.choice(demo_data.REGIONS_DE if german else demo_data.REGIONS_FR),
                speaks_fr=(not german) or rng.random() < 0.6,
                speaks_de=german or rng.random() < 0.2,
                speaks_en=rng.random() < 0.25,
                member_since=member_since,
                is_founder=member_since == 2016,
                fun_fact=demo_data.FUN_FACTS[i % len(demo_data.FUN_FACTS)],
                talk_to_me_about=rng.choice(demo_data.TALK_TOPICS),
                phone=f"+41 79 000 {(i + 3) // 100:02d} {(i + 3) % 100:02d}",
            ))
        return members

    def create_events(self):
        now = timezone.localtime()

        def at(days, hour=18, minute=30):
            return (now + timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Fixed primary keys on purpose: generate_matches() seeds its randomness with event.pk, so the
        # introductions of the demo storyline stay identical after every --reset.
        past = [
            Event.objects.create(pk=1, title="Conférence de presse de la Foire", kind=Event.Kind.CONFERENCE,
                                 starts_at=at(-120, 10, 0), location="CERM, Martigny"),
            Event.objects.create(pk=2, title="Apéro des membres", kind=Event.Kind.APERO,
                                 starts_at=at(-60), location="Caveau du Club, Martigny"),
            Event.objects.create(pk=3, title="Soirée Wow", kind=Event.Kind.DINNER,
                                 starts_at=at(-3, 19, 0), location="CERM, Martigny"),
        ]
        upcoming = Event.objects.create(
            pk=4, title="Dîner d'automne", kind=Event.Kind.DINNER, starts_at=at(12, 19, 0),
            location="Salle des Bisses, Martigny", has_seating=True,
            description="Trois services, trois tables différentes : on se mélange !",
        )
        later = Event.objects.create(pk=5, title="Apéro de Noël", kind=Event.Kind.APERO,
                                     starts_at=at(75), location="Caveau du Club, Martigny")
        self.realign_event_sequence()
        return past, upcoming, later

    @staticmethod
    def realign_event_sequence():
        """PostgreSQL does not advance its sequence on explicit pks: realign it so events created later
        (from the admin) do not collide with ours. No-op on SQLite."""
        with connection.cursor() as cursor:
            for statement in connection.ops.sequence_reset_sql(no_style(), [Event]):
                cursor.execute(statement)

    def create_rsvps(self, rng, members, past, upcoming, later, camille, lukas):
        rsvps = []
        for event in past:
            for member in members:
                if member.member_since <= event.starts_at.year and member is not camille:
                    status = RSVP.Status.YES if rng.random() < 0.8 else RSVP.Status.NO
                    rsvps.append(RSVP(event=event, member=member, status=status))
        others = [m for m in members if m not in (camille, lukas)]
        rng.shuffle(others)
        for member in [camille, lukas, *others[:36]]:
            rsvps.append(RSVP(event=upcoming, member=member, status=RSVP.Status.YES))
        for member in others[36:41]:
            rsvps.append(RSVP(event=upcoming, member=member, status=RSVP.Status.NO))
        for member in rng.sample(members, 10):
            rsvps.append(RSVP(event=later, member=member, status=RSVP.Status.YES))
        RSVP.objects.bulk_create(rsvps)

    def create_connections(self, rng, members, past, camille, lukas):
        def seniority(m):
            return m.seniority_years

        links = []
        for a, b in combinations(members, 2):
            if camille in (a, b):
                continue
            if Member.RANK_NEWCOMER in (a.rank, b.rank):
                probability = 0.02
            elif seniority(a) >= 5 and seniority(b) >= 5:
                probability = 0.45
            elif a.region == b.region:
                probability = 0.2
            else:
                probability = 0.04
            if rng.random() < probability:
                links.append((a, b, rng.choice(past)))
        friends = [m for m in members if m not in (camille, lukas) and m.speaks_fr]
        for friend in rng.sample(friends, 2):
            links.append((camille, friend, past[-1]))
        Connection.objects.bulk_create(
            Connection(
                member_a=min(a, b, key=lambda m: m.pk), member_b=max(a, b, key=lambda m: m.pk),
                event=event, source=Connection.Source.SEED, created_at=event.starts_at,
            )
            for a, b, event in links
        )

    def check_storyline(self, upcoming, camille, lukas):
        pair = sorted((camille.pk, lukas.pk))
        if not Match.objects.filter(event=upcoming, member_a_id=pair[0], member_b_id=pair[1]).exists():
            raise CommandError("Storyline broken: Camille must be introduced to Lukas for the upcoming dinner.")
        if Connection.involving(camille).count() != 2:
            raise CommandError("Storyline broken: Camille must start with exactly 2 connections.")
        index = club_stats()["index"]
        if not 0.08 <= index <= 0.30:
            raise CommandError(f"Federation index {index:.0%} outside the 8–30% range expected for the demo.")
