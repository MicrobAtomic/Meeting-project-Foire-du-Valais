"""Bingo des rencontres : la grille, la case la plus rare, les cases cochées, les pages, le scan et les outils staff."""

from collections import Counter
from datetime import timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone, translation

from club.models import RSVP, BingoSquare, Connection, Event, Match, MemberTag, Tag
from club.services import bingo
from club.tests.helpers import make_member

DUMMY = ("region", "Atlantis")  # a square nobody can fill: it pads the nine positions of a hand-made grid
THIS_YEAR = timezone.localdate().year


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BingoTestCase(TestCase):
    """Accounts are created by the dozen in these tests: a fast hasher keeps the suite quick (as in the seeded tests)."""


def make_tags(count=8, prefix="tag"):
    return [
        Tag.objects.create(
            slug=f"{prefix}{i}", emoji="🎲", category="hobby", label_fr=f"Sujet {i}", label_de=f"Thema {i}", label_en=f"Topic {i}"
        )
        for i in range(count)
    ]


def make_bingo_event(days=5, **extra):
    fields = {
        "title": "Apéro bingo", "kind": "apero", "location": "Martigny", "has_bingo": True, "is_published": True,
        "starts_at": timezone.now() + timedelta(days=days),
    }
    fields.update(extra)
    return Event.objects.create(**fields)


def register(event, *members, status="yes"):
    for member in members:
        RSVP.objects.create(event=event, member=member, status=status)


def likes(member, *tags, sentiment="like"):
    for tag in tags:
        MemberTag.objects.create(member=member, tag=tag, sentiment=sentiment)


def make_match(event, first, second, likes=(), dislikes=(), score=10):
    a, b = sorted((first, second), key=lambda m: m.pk)
    return Match.objects.create(
        event=event, member_a=a, member_b=b, score=score, shared_likes=list(likes), shared_dislikes=list(dislikes)
    )


def make_crowd(event, tags, count=14):
    """`count` registered members who differ by sector, region, languages, seniority and tastes."""
    crowd = []
    for i in range(count):
        member = make_member(
            f"p{i}@example.com", first_name=f"Prénom{i}", last_name=f"Nom{i}",
            sector=["tech", "finance", "health", "tourism"][i % 4], region=["Martigny", "Sion", "Brig"][i % 3],
            speaks_fr=i % 5 != 4, speaks_de=i % 3 == 0, speaks_en=i % 2 == 0,
            member_since=[2016, 2019, 2022, THIS_YEAR][i % 4], is_founder=i % 8 == 0,
        )
        likes(member, *(tags[(i + k) % len(tags)] for k in range(3)))
        likes(member, tags[(i + 5) % len(tags)], sentiment="dislike")
        crowd.append(member)
    register(event, *crowd)
    return crowd


def make_quiet_members(count, *, prefix="q", sectors=None, **extra):
    """Members who share nothing but French: one region each, a seniority without any rank (member)."""
    sectors = sectors or ["tech", "finance", "health", "retail", "transport", "media", "energy", "industry", "services"]
    return [
        make_member(
            f"{prefix}{i}@example.com", first_name=f"{prefix.upper()}{i}", sector=sectors[i % len(sectors)],
            region=f"Ville {prefix}{i}", member_since=THIS_YEAR - 2, **extra,
        )
        for i in range(count)
    ]


def give_grid(event, player, specs):
    """A hand-made grid: nine (kind, value) pairs, by position."""
    return [
        BingoSquare.objects.create(event=event, player=player, position=i, kind=kind, value=value)
        for i, (kind, value) in enumerate(specs)
    ]


def hand_grid(**by_position):
    """Nine squares, DUMMY except the given ones: hand_grid(p0=("like", "tag1"), p2=("language", "de"))."""
    specs = [DUMMY] * 9
    specs[4] = ("joker", "")
    for name, spec in by_position.items():
        specs[int(name[1:])] = spec
    return specs


def tick_by_hand(grid, positions, people):
    """Tick these positions with these (different) people, as the scans would have."""
    for position, person in zip(positions, people):
        BingoSquare.objects.filter(pk=grid[position].pk).update(found=person, found_at=timezone.now())


def shape(grid):
    return [(s.position, s.kind, s.value) for s in grid]


def can_pair_everybody(options):
    """Independent check (plain backtracking): can each item get a person of its own among `options`, a list of lists?"""
    order = sorted(range(len(options)), key=lambda i: len(options[i]))

    def solve(k, used):
        if k == len(order):
            return True
        return any(solve(k + 1, used | {person}) for person in options[order[k]] if person not in used)

    return solve(0, frozenset())


def fillers_of(grid, player, people, met=()):
    """For each square of the grid, the ids of the other attendees who could tick it."""
    return [
        [m.pk for m in people if m.pk != player.pk and bingo.satisfies(m, square, m.pk not in met)] for square in grid
    ]


class GridTests(BingoTestCase):
    def setUp(self):
        self.event = make_bingo_event()
        self.tags = make_tags()
        self.crowd = make_crowd(self.event, self.tags)
        self.player = self.crowd[1]

    def grid(self, player=None):
        return bingo.generate_grid(self.event, player or self.player)

    def test_nine_squares_with_the_joker_in_the_middle(self):
        grid = self.grid()
        self.assertEqual([s.position for s in grid], list(range(9)))
        self.assertEqual(grid[4].kind, "joker")
        self.assertEqual([s.kind for s in grid].count("joker"), 1)  # a real crowd needs no other joker
        self.assertTrue(all(s.found_id is None and s.found_at is None for s in grid))
        self.assertEqual(BingoSquare.objects.filter(event=self.event, player=self.player).count(), 9)

    def test_the_grid_is_idempotent_and_deterministic(self):
        first = self.grid()
        self.assertEqual([s.pk for s in self.grid()], [s.pk for s in first])  # the second call reads, never rebuilds
        self.assertEqual(BingoSquare.objects.count(), 9)
        BingoSquare.objects.all().delete()
        self.assertEqual(shape(self.grid()), shape(first))  # same people, same tastes: same grid
        self.assertNotEqual(shape(self.grid(self.crowd[2])), shape(first))  # but each player has their own

    def test_two_requests_opening_the_grid_at_once_keep_one_grid(self):
        first = self.grid()
        with mock.patch.object(bingo, "existing_grid", side_effect=[[], list(first)]):  # the 2nd request raced the 1st
            again = bingo.generate_grid(self.event, self.player)
        self.assertEqual([s.pk for s in again], [s.pk for s in first])
        self.assertEqual(BingoSquare.objects.filter(event=self.event, player=self.player).count(), 9)

    def test_every_square_can_be_filled_by_at_least_two_other_attendees(self):
        for player in self.crowd:
            grid = self.grid(player)
            for square, people in zip(grid, fillers_of(grid, player, self.crowd)):
                if square.kind != "joker":
                    self.assertGreaterEqual(len(people), 2, bingo.square_label(square))

    def test_a_full_card_stays_possible(self):
        for player in self.crowd:
            grid = self.grid(player)
            self.assertTrue(can_pair_everybody(fillers_of(grid, player, self.crowd)), player.first_name)

    def test_variety_caps(self):
        for player in self.crowd:
            kinds = Counter(s.kind for s in self.grid(player))
            self.assertLessEqual(kinds["like"], 3)
            self.assertLessEqual(kinds["dislike"], 2)
            self.assertLessEqual(kinds["language"], 1)
            self.assertLessEqual(kinds["sector"], 2)
            self.assertLessEqual(kinds["rank"], 1)
            self.assertLessEqual(kinds["region"], 1)
            self.assertGreaterEqual(len(kinds), 4)  # a mix of questions, not eight times the same one

    def test_only_the_people_who_come_are_considered(self):
        ghosts = make_tags(2, prefix="ghost")  # each liked by three people, who would make it a very popular square
        for i in range(3):
            absent, gone = make_member(f"absent{i}@example.com"), make_member(f"gone{i}@example.com")
            likes(absent, ghosts[0])
            likes(gone, ghosts[1])
            register(self.event, absent, status="no")  # said no
            register(self.event, gone)  # said yes, but the account is closed since
            gone.user.is_active = False
            gone.user.save()
        for player in self.crowd:
            self.assertFalse({"ghost0", "ghost1"} & {s.value for s in self.grid(player)})

    def make_rare_member(self, name, tag_slug):
        """Somebody nobody resembles (own sector, own region, own affinity): only an introduction can bring them in."""
        sectors = {"Rita": "retail", "Remo": "transport", "Rosa": "media"}
        member = make_member(
            f"{name.lower()}@example.com", first_name=name, sector=sectors[name], region=f"Rareville {name}",
            member_since=THIS_YEAR - 2,
        )
        likes(member, Tag.objects.create(slug=tag_slug, emoji="🦄", category="hobby", label_fr=f"Rare {name}"))
        register(self.event, member)
        return member

    def test_each_introduction_gets_its_own_square(self):
        partners = [self.make_rare_member("Rita", "rare-rita"), self.make_rare_member("Remo", "rare-remo"),
                    self.make_rare_member("Rosa", "rare-rosa")]
        for partner in partners:
            make_match(self.event, self.player, partner)
        grid = self.grid()
        supply = [[s.position for s in grid if s.kind != "joker" and bingo.satisfies(p, s, False)] for p in partners]
        self.assertTrue(all(supply), supply)  # each partner fills something, although nobody else shares their tastes
        self.assertTrue(can_pair_everybody(supply))  # and three partners have three different squares

    def test_an_introduction_prefers_a_like_both_people_share(self):
        rita = self.make_rare_member("Rita", "rare-rita")
        shared = Tag.objects.create(slug="rare-shared", emoji="🤝", category="hobby", label_fr="Rare commun")
        likes(rita, shared)
        likes(self.player, shared)
        make_match(self.event, self.player, rita, likes=["rare-shared"])
        grid = self.grid()
        self.assertIn(("like", "rare-shared"), {(s.kind, s.value) for s in grid})  # rather than her sector or her region
        self.assertNotIn("rare-rita", {s.value for s in grid})

    def test_an_introduction_without_shared_like_falls_back_on_one_of_her_likes(self):
        rita = self.make_rare_member("Rita", "rare-rita")
        make_match(self.event, self.player, rita)
        self.assertIn(("like", "rare-rita"), {(s.kind, s.value) for s in self.grid()})

    def test_an_introduction_to_somebody_who_is_not_coming_any_more_is_ignored(self):
        rita = self.make_rare_member("Rita", "rare-rita")
        make_match(self.event, self.player, rita)
        RSVP.objects.filter(event=self.event, member=rita).update(status="no")
        grid = self.grid()
        self.assertEqual(len(grid), 9)
        self.assertNotIn("rare-rita", {s.value for s in grid})  # no square nobody could fill


class SmallEventTests(BingoTestCase):
    def sector_squares(self, player, others, events=6):
        """The sector squares of the player's grid at several events (another event: another draw)."""
        result = []
        for _ in range(events):
            event = make_bingo_event()
            register(event, player, *others)
            result.append({s.value for s in bingo.generate_grid(event, player) if s.kind == "sector"})
        return result

    def test_squares_nobody_has_met_come_before_squares_of_old_acquaintances(self):
        player = make_member("player@example.com", sector="services", region="Aigle", member_since=THIS_YEAR - 2)
        others = make_quiet_members(8, sectors=["tech", "tech", "retail", "retail", "finance", "finance", "health", "health"])
        for other in others[:4]:
            Connection.link(player, other)  # the whole tech and retail sectors are already in the album
        for sectors in self.sector_squares(player, others):
            self.assertEqual(sectors, {"finance", "health"})  # only two sector squares are allowed: the new faces win

    def test_your_own_sector_is_the_last_one_asked(self):
        player = make_member("player@example.com", sector="tech", region="Aigle", member_since=THIS_YEAR - 2)
        others = make_quiet_members(6, sectors=["tech", "tech", "finance", "finance", "health", "health"])
        for sectors in self.sector_squares(player, others):
            self.assertEqual(sectors, {"finance", "health"})

    def test_french_is_only_asked_to_people_who_do_not_speak_it(self):
        event = make_bingo_event()
        speaker = make_member("speaker@example.com", sector="services", speaks_fr=True)
        german = make_member("german@example.com", sector="services", speaks_fr=False, speaks_de=True)
        others = make_quiet_members(3)  # they speak French only and share nothing else
        register(event, speaker, german, *others)
        self.assertNotIn(("language", "fr"), {(s.kind, s.value) for s in bingo.generate_grid(event, speaker)})
        self.assertIn(("language", "fr"), {(s.kind, s.value) for s in bingo.generate_grid(event, german)})

    def test_the_placeholder_sector_is_never_a_square(self):
        event = make_bingo_event()
        player = make_member("player@example.com", sector="services", region="Aigle", member_since=THIS_YEAR - 2)
        others = make_quiet_members(3, sectors=["other"])  # accounts that have not chosen their sector yet
        register(event, player, *others)
        self.assertNotIn("sector", {s.kind for s in bingo.generate_grid(event, player)})

    def test_a_small_event_is_completed_with_jokers(self):
        event = make_bingo_event()
        trio = [make_member(f"t{i}@example.com", sector="tech", region="Sion", member_since=2010) for i in range(3)]
        likes(trio[0], make_tags(1, prefix="mine")[0])  # nobody else likes it: it can never be a square
        register(event, *trio)
        grid = bingo.generate_grid(event, trio[0])
        self.assertEqual([s.position for s in grid], list(range(9)))
        kinds = Counter(s.kind for s in grid)
        self.assertEqual(kinds["sector"] + kinds["rank"] + kinds["region"], 3)  # all the two others have in common
        self.assertEqual(kinds["like"], 0)
        self.assertEqual(kinds["joker"], 6)
        self.assertEqual(grid[4].kind, "joker")

    def test_a_square_only_one_person_can_fill_is_better_than_a_joker(self):
        event = make_bingo_event()
        player = make_member("player@example.com", sector="services", region="Aigle", member_since=THIS_YEAR - 2)
        others = make_quiet_members(4, sectors=["tech", "finance", "health", "retail"])
        register(event, player, *others)
        grid = bingo.generate_grid(event, player)  # sector and region have 1 filler each: weak, but still squares
        kinds = Counter(s.kind for s in grid)
        self.assertEqual(kinds["sector"], 2)
        self.assertEqual(kinds["region"], 1)
        self.assertEqual(kinds["joker"], 6)

    def test_alone_at_the_event_the_grid_is_nothing_but_jokers(self):
        event = make_bingo_event()
        loner = make_member("loner@example.com")
        register(event, loner)
        self.assertEqual({s.kind for s in bingo.generate_grid(event, loner)}, {"joker"})

    def test_an_unlucky_crowd_cannot_break_the_full_card(self):
        """Two twins fill five squares between them and nobody else shares anything: a naive draw would make a full
        card impossible (five squares, two people). The grid is repaired with squares the other people can fill."""
        event = make_bingo_event()
        tags = make_tags(3, prefix="twin")
        player = make_member("player@example.com", sector="services", region="Aigle", member_since=THIS_YEAR - 2)
        twins = [make_member(f"twin{i}@example.com", sector="tech", region="Sion", member_since=THIS_YEAR - 2) for i in range(2)]
        for twin in twins:
            likes(twin, *tags)
        solos = make_quiet_members(7, prefix="solo", sectors=["finance", "health", "retail", "transport", "media", "energy", "industry"])
        for i, solo in enumerate(solos):
            likes(solo, make_tags(1, prefix=f"hobby{i}-")[0])
        crowd = [player, *twins, *solos]  # nine other people for the player
        register(event, *crowd)
        grid = bingo.generate_grid(event, player)
        supply = fillers_of(grid, player, crowd)
        self.assertTrue(can_pair_everybody(supply))
        self.assertTrue(can_pair_everybody([people for square, people in zip(grid, supply) if square.kind != "joker"]))


class LabelTests(BingoTestCase):
    def setUp(self):
        Tag.objects.create(
            slug="ski", emoji="⛷️", category="hobby", label_fr="Ski de randonnée", label_de="Skitouren", label_en="Ski touring"
        )

    def label(self, kind, value=""):
        return bingo.square_label(BingoSquare(kind=kind, value=value))

    def test_french_texts(self):
        self.assertEqual(self.label("like", "ski"), "adore ⛷️ Ski de randonnée")
        self.assertEqual(self.label("dislike", "ski"), "déteste ⛷️ Ski de randonnée")
        self.assertEqual(self.label("language", "de"), "parle allemand")
        self.assertEqual(self.label("language", "en"), "parle anglais")
        self.assertEqual(self.label("language", "fr"), "parle français")
        self.assertEqual(self.label("sector", "finance"), "travaille dans 🏦 Banque, finance & assurance")
        self.assertEqual(self.label("rank", "founder"), "est membre fondateur")
        self.assertEqual(self.label("rank", "pillar"), "est au Club depuis plus de 5 ans")
        self.assertEqual(self.label("rank", "newcomer"), "vient d'entrer au Club")
        self.assertEqual(self.label("region", "Brig"), "vient de Brig")
        self.assertEqual(self.label("joker"), "🃏 Joker : quelqu'un que tu n'avais jamais rencontré")

    def test_affinities_follow_the_active_language(self):
        for language, expected in (("de", "Skitouren"), ("en", "Ski touring")):
            with translation.override(language):
                self.assertIn(expected, self.label("like", "ski"))

    def test_an_affinity_deleted_since_does_not_break_the_page(self):
        self.assertIn("vanished", self.label("like", "vanished"))

    def test_the_labels_of_a_whole_grid_cost_a_single_query(self):
        squares = [BingoSquare(kind="like", value="ski"), BingoSquare(kind="dislike", value="ski"), BingoSquare(kind="joker")]
        with self.assertNumQueries(1):
            self.assertEqual(len(bingo.square_labels(squares)), 3)


class SatisfiesAndLinesTests(BingoTestCase):
    def setUp(self):
        self.tags = make_tags(2)
        self.member = make_member(
            "brigitte@example.com", sector="finance", region=" brig ", speaks_de=True, speaks_en=False,
            member_since=2010, is_founder=True,
        )
        likes(self.member, self.tags[0])
        likes(self.member, self.tags[1], sentiment="dislike")

    def check(self, kind, value, new_meeting=False):
        return bingo.satisfies(self.member, BingoSquare(kind=kind, value=value), new_meeting)

    def test_each_kind_of_square(self):
        self.assertTrue(self.check("like", "tag0"))
        self.assertFalse(self.check("like", "tag1"))  # she hates this one
        self.assertTrue(self.check("dislike", "tag1"))
        self.assertFalse(self.check("dislike", "tag0"))
        self.assertTrue(self.check("language", "de"))
        self.assertFalse(self.check("language", "en"))
        self.assertTrue(self.check("sector", "finance"))
        self.assertFalse(self.check("sector", "tech"))
        self.assertTrue(self.check("rank", "founder"))
        self.assertFalse(self.check("rank", "newcomer"))
        self.assertTrue(self.check("region", "Brig"))  # regions are typed by hand: case and spaces do not matter
        self.assertTrue(self.check("region", "BRIG"))
        self.assertFalse(self.check("region", "Sion"))

    def test_the_joker_is_for_somebody_new_only(self):
        self.assertFalse(self.check("joker", "", new_meeting=False))
        self.assertTrue(self.check("joker", "", new_meeting=True))

    def test_a_member_without_region_never_fills_a_region(self):
        self.member.region = ""
        self.member.save()
        self.assertFalse(self.check("region", ""))

    def test_lines_rows_columns_and_diagonals(self):
        def ticked(*positions):
            return [BingoSquare(position=p, found_id=1 if p in positions else None) for p in range(9)]

        self.assertEqual(bingo.lines(ticked()), 0)
        self.assertEqual(bingo.lines(ticked(0, 1)), 0)
        for line in bingo.LINES:
            self.assertEqual(bingo.lines(ticked(*line)), 1, line)
        self.assertEqual(bingo.lines(ticked(0, 1, 2, 3, 4, 5)), 2)  # two rows
        self.assertEqual(bingo.lines(ticked(0, 4, 8, 2, 6)), 2)  # both diagonals
        self.assertEqual(bingo.lines(ticked(*range(9))), 8)  # a full card: 3 rows + 3 columns + 2 diagonals
        self.assertEqual(len(bingo.LINES), 8)
        self.assertEqual(bingo.complete_lines(ticked(6, 7, 8)), [(6, 7, 8)])


class PlayTests(BingoTestCase):
    """find_square and tick on hand-made grids: the rarest square, one person per square, the joker, closed games."""

    def setUp(self):
        self.event = make_bingo_event()
        self.tags = make_tags(3)
        self.player = make_member("player@example.com", first_name="Pia", sector="services", member_since=THIS_YEAR - 2)
        # Xavier: likes tag0, speaks German, finance, founder. Yara and Zoé: health, speak German (Yara likes tag0 too).
        self.xavier = make_member("xavier@example.com", first_name="Xavier", sector="finance", speaks_de=True, member_since=2010, is_founder=True)
        self.yara = make_member("yara@example.com", first_name="Yara", sector="health", speaks_de=True, member_since=THIS_YEAR - 2)
        self.zoe = make_member("zoe@example.com", first_name="Zoé", sector="health", speaks_de=True, member_since=THIS_YEAR - 2)
        likes(self.xavier, self.tags[0])
        likes(self.yara, self.tags[0])
        register(self.event, self.player, self.xavier, self.yara, self.zoe)

    def grid(self, **by_position):
        return give_grid(self.event, self.player, hand_grid(**by_position))

    def test_the_rarest_square_is_chosen(self):
        # fillers: tag0 = Xavier + Yara (2), German = all three (3), finance = Xavier only (1)
        grid = self.grid(p0=("like", "tag0"), p1=("language", "de"), p2=("sector", "finance"))
        event, square = bingo.find_square(self.player, self.xavier, False)
        self.assertEqual((event, square.pk), (self.event, grid[2].pk))

    def test_when_squares_are_equally_rare_the_lowest_position_wins(self):
        grid = self.grid(p5=("like", "tag0"), p1=("sector", "health"), p7=("language", "de"))  # both 2 people for Yara
        self.assertEqual(bingo.find_square(self.player, self.yara, False)[1].pk, grid[1].pk)
        BingoSquare.objects.all().delete()
        grid = self.grid(p1=("like", "tag0"), p5=("sector", "health"), p7=("language", "de"))
        self.assertEqual(bingo.find_square(self.player, self.yara, False)[1].pk, grid[1].pk)

    def test_finding_a_square_ticks_nothing(self):
        self.grid(p0=("like", "tag0"))
        self.assertIsNotNone(bingo.find_square(self.player, self.xavier, False))
        self.assertFalse(BingoSquare.objects.filter(found__isnull=False).exists())

    def test_the_grid_is_created_when_it_does_not_exist_yet(self):
        self.assertFalse(BingoSquare.objects.exists())
        bingo.find_square(self.player, self.xavier, True)
        self.assertEqual(BingoSquare.objects.filter(player=self.player).count(), 9)

    def test_one_person_fills_one_square_only(self):
        grid = self.grid(p0=("like", "tag0"), p1=("language", "de"))
        first = bingo.tick(self.player, self.xavier, False)
        self.assertEqual(first.square.pk, grid[0].pk)  # tag0 is rarer than German
        self.assertIsNone(bingo.find_square(self.player, self.xavier, False))  # Xavier also speaks German: too late
        self.assertIsNone(bingo.tick(self.player, self.xavier, False))
        second = bingo.tick(self.player, self.yara, False)  # tag0 is taken: Yara gets the German square
        self.assertEqual(second.square.pk, grid[1].pk)

    def test_the_joker_is_only_for_somebody_never_met(self):
        grid = self.grid()  # nothing but the joker is fillable
        self.assertIsNone(bingo.find_square(self.player, self.xavier, False))
        event, square = bingo.find_square(self.player, self.xavier, True)
        self.assertEqual(square.pk, grid[4].pk)

    def test_the_joker_is_the_last_square_used(self):
        grid = self.grid(p0=("like", "tag0"))
        self.assertEqual(bingo.find_square(self.player, self.xavier, True)[1].pk, grid[0].pk)
        bingo.tick(self.player, self.yara, True)  # Yara takes the tag0 square...
        self.assertEqual(bingo.find_square(self.player, self.xavier, True)[1].pk, grid[4].pk)  # ...so Xavier gets the joker

    def test_nothing_to_tick_when_the_person_fills_no_free_square(self):
        self.grid(p0=("sector", "tourism"))
        self.assertIsNone(bingo.find_square(self.player, self.xavier, False))
        self.assertIsNone(bingo.tick(self.player, self.xavier, False))

    def test_no_square_without_a_bingo_a_game_still_on_and_two_registered_people(self):
        self.grid(p0=("language", "de"))
        self.assertIsNotNone(bingo.find_square(self.player, self.xavier, False))
        Event.objects.filter(pk=self.event.pk).update(has_bingo=False)
        self.assertIsNone(bingo.find_square(self.player, self.xavier, False))
        Event.objects.filter(pk=self.event.pk).update(has_bingo=True, starts_at=timezone.now() - timedelta(days=2))
        self.assertIsNone(bingo.find_square(self.player, self.xavier, False))  # over
        Event.objects.filter(pk=self.event.pk).update(starts_at=timezone.now() + timedelta(days=1))
        RSVP.objects.filter(event=self.event, member=self.xavier).update(status="no")
        self.assertIsNone(bingo.find_square(self.player, self.xavier, False))  # Xavier is not coming
        RSVP.objects.filter(event=self.event, member=self.xavier).update(status="yes")
        RSVP.objects.filter(event=self.event, member=self.player).delete()
        self.assertIsNone(bingo.find_square(self.player, self.xavier, False))  # the player never answered
        self.assertIsNone(bingo.tick(self.player, self.xavier, True))

    def test_scanning_yourself_gives_nothing(self):
        self.assertIsNone(bingo.open_bingo_event(self.player, self.player))

    def test_tick_records_who_and_when_and_counts_lines(self):
        grid = self.grid(p0=("like", "tag0"), p1=("language", "de"), p2=("sector", "health"))
        tick_by_hand(grid, [1, 2], [self.zoe, self.yara])  # two squares of the top row already ticked
        before = timezone.now()
        result = bingo.tick(self.player, self.xavier, False)
        self.assertEqual(result.square.pk, grid[0].pk)
        self.assertEqual((result.lines_before, result.lines_after, result.filled), (0, 1, 3))
        self.assertTrue(result.new_bingo)
        self.assertFalse(result.full_card)
        stored = BingoSquare.objects.get(pk=grid[0].pk)
        self.assertEqual(stored.found, self.xavier)
        self.assertGreaterEqual(stored.found_at, before)
        self.assertEqual(result.event, self.event)

    def test_a_full_card_is_reported(self):
        grid = self.grid(p0=("like", "tag0"))
        others = [make_member(f"other{i}@example.com") for i in range(7)]
        tick_by_hand(grid, [1, 2, 3, 4, 5, 6, 7, 8], others + [self.zoe])
        result = bingo.tick(self.player, self.xavier, False)
        self.assertEqual(result.filled, 9)
        self.assertTrue(result.full_card)
        self.assertEqual(result.lines_after, 8)

    def test_a_double_post_ticks_once(self):
        self.grid(p0=("like", "tag0"), p1=("language", "de"))
        self.assertIsNotNone(bingo.tick(self.player, self.xavier, True))
        self.assertIsNone(bingo.tick(self.player, self.xavier, False))
        self.assertEqual(BingoSquare.objects.filter(player=self.player, found=self.xavier).count(), 1)

    def test_a_parallel_request_on_another_square_is_refused_by_the_database(self):
        grid = self.grid(p0=("like", "tag0"), p1=("language", "de"))
        stale = bingo._find(self.player, self.xavier, False)  # what the 2nd request saw before the 1st one wrote
        self.assertEqual(stale[2].pk, grid[0].pk)
        tick_by_hand(grid, [1], [self.xavier])  # ...the 1st request ticked Xavier on the German square meanwhile
        with mock.patch.object(bingo, "_find", return_value=stale):
            self.assertIsNone(bingo.tick(self.player, self.xavier, False))
        self.assertEqual(BingoSquare.objects.filter(player=self.player, found=self.xavier).count(), 1)
        self.assertIsNone(BingoSquare.objects.get(pk=grid[0].pk).found_id)

    def test_a_parallel_request_on_the_same_square_loses_quietly(self):
        grid = self.grid(p0=("like", "tag0"))
        stale = bingo._find(self.player, self.xavier, False)
        tick_by_hand(grid, [0], [self.yara])  # Yara got there first
        with mock.patch.object(bingo, "_find", return_value=stale):
            self.assertIsNone(bingo.tick(self.player, self.xavier, False))
        self.assertEqual(BingoSquare.objects.get(pk=grid[0].pk).found, self.yara)


class OpenEventTests(BingoTestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        self.midnight = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)

    def test_the_next_unfinished_bingo_where_both_are_registered(self):
        later = make_bingo_event(days=30, title="Plus tard")
        sooner = make_bingo_event(days=3, title="Bientôt")
        other = make_bingo_event(days=1, title="Sans Bob")
        no_bingo = make_bingo_event(days=2, title="Sans bingo", has_bingo=False)
        register(later, self.alice, self.bob)
        register(sooner, self.alice, self.bob)
        register(other, self.alice)
        register(no_bingo, self.alice, self.bob)
        self.assertEqual(bingo.open_bingo_event(self.alice, self.bob), sooner)
        self.assertEqual(bingo.open_bingo_event(self.bob, self.alice), sooner)

    def test_both_must_have_said_yes(self):
        event = make_bingo_event()
        register(event, self.alice)
        register(event, self.bob, status="no")
        self.assertIsNone(bingo.open_bingo_event(self.alice, self.bob))

    def test_the_game_lasts_until_midnight_of_the_day_of_the_event(self):
        today = make_bingo_event(title="Ce soir", starts_at=self.midnight + timedelta(minutes=1))
        register(today, self.alice, self.bob)
        self.assertEqual(bingo.open_bingo_event(self.alice, self.bob), today)  # even once it has started
        self.assertTrue(bingo.is_open(today))
        yesterday = make_bingo_event(title="Hier", starts_at=self.midnight - timedelta(minutes=1))
        self.assertFalse(bingo.is_open(yesterday))
        today.delete()
        register(yesterday, self.alice, self.bob)
        self.assertIsNone(bingo.open_bingo_event(self.alice, self.bob))

    def test_an_event_without_bingo_is_never_open(self):
        self.assertFalse(bingo.is_open(make_bingo_event(has_bingo=False)))


class StatsTests(BingoTestCase):
    def test_grids_ticks_winners_and_full_cards(self):
        event = make_bingo_event()
        players = [make_member(f"player{i}@example.com", first_name=f"Joueur{i}", last_name=f"Nom{i}") for i in range(5)]
        crowd = [make_member(f"crowd{i}@example.com") for i in range(9)]
        grids = [give_grid(event, player, hand_grid()) for player in players]
        tick_by_hand(grids[0], [0, 1, 2, 3], crowd)  # one line, 4 squares
        tick_by_hand(grids[1], range(9), crowd)  # full card: 8 lines
        tick_by_hand(grids[2], [0, 3, 6, 1], crowd)  # one line, 4 squares: after player 0 (same score, name order)
        tick_by_hand(grids[3], [0, 1], crowd)  # no line
        # players[4]: grid opened, nothing ticked
        stats = bingo.event_stats(event)
        self.assertEqual((stats.grids, stats.ticked, stats.bingos, stats.full_cards), (5, 4 + 9 + 4 + 2, 3, 1))
        self.assertEqual(
            [(w.member.first_name, w.lines, w.squares) for w in stats.winners],
            [("Joueur1", 8, 9), ("Joueur0", 1, 4), ("Joueur2", 1, 4)],
        )
        self.assertEqual(stats.total, 9)

    def test_other_events_and_closed_accounts_are_left_out(self):
        event, other = make_bingo_event(), make_bingo_event(title="Un autre")
        player, closed = make_member("a@example.com"), make_member("b@example.com")
        crowd = [make_member(f"c{i}@example.com") for i in range(3)]
        tick_by_hand(give_grid(event, player, hand_grid()), [0, 1, 2], crowd)
        tick_by_hand(give_grid(other, player, hand_grid()), [0, 1, 2], crowd)
        tick_by_hand(give_grid(event, closed, hand_grid()), [0, 1, 2], crowd)
        closed.user.is_active = False
        closed.user.save()
        stats = bingo.event_stats(event)
        self.assertEqual((stats.grids, stats.ticked, stats.bingos), (1, 3, 1))

    def test_an_event_nobody_played(self):
        stats = bingo.event_stats(make_bingo_event())
        self.assertEqual((stats.grids, stats.ticked, stats.bingos, stats.full_cards, stats.winners), (0, 0, 0, 0, []))


# --------------------------------------------------------------------------------------------------------------
# Pages: the grid, the scan, the event page and the staff tools
# --------------------------------------------------------------------------------------------------------------

from io import StringIO  # noqa: E402

from django.core.management import call_command  # noqa: E402
from django.urls import reverse  # noqa: E402

from club.models import Member, SeatingPlan  # noqa: E402
from club.tests.helpers import assert_csp_clean, make_staff  # noqa: E402


class BingoPagesTests(BingoTestCase):
    def setUp(self):
        self.event = make_bingo_event(title="Apéro des vendanges")
        self.tags = make_tags()
        self.crowd = make_crowd(self.event, self.tags)
        self.player = self.crowd[1]
        self.url = reverse("club:event_bingo", args=[self.event.pk])

    def test_the_grid_page_shows_nine_squares_and_the_rules(self):
        self.client.force_login(self.player.user)
        response = self.client.get(self.url)
        assert_csp_clean(self, response)
        self.assertContains(response, "Bingo des rencontres")
        self.assertContains(response, "0 / 9")
        self.assertEqual(response.content.decode().count("<li class=\"flex min-h-28"), 9)
        self.assertContains(response, "Joker : quelqu&#x27;un que tu n&#x27;avais jamais rencontré")
        self.assertContains(response, "Une personne ne remplit qu'une seule case.")

    def test_somebody_not_registered_is_invited_to_answer_first(self):
        outsider = make_member("outsider@example.com")
        self.client.force_login(outsider.user)
        response = self.client.get(self.url)
        self.assertContains(response, "Ta grille t'attend")
        self.assertFalse(BingoSquare.objects.filter(player=outsider).exists())

    def test_no_bingo_no_page(self):
        plain = make_bingo_event(has_bingo=False)
        self.client.force_login(self.player.user)
        self.assertEqual(self.client.get(reverse("club:event_bingo", args=[plain.pk])).status_code, 404)

    def test_an_unpublished_event_stays_hidden(self):
        draft = make_bingo_event(is_published=False)
        register(draft, self.player)
        self.client.force_login(self.player.user)
        self.assertEqual(self.client.get(reverse("club:event_bingo", args=[draft.pk])).status_code, 404)

    def test_event_page_and_list_announce_the_game(self):
        self.client.force_login(self.player.user)
        detail = self.client.get(reverse("club:event_detail", args=[self.event.pk]))
        self.assertContains(detail, "Animations de la soirée")
        self.assertContains(detail, "Voir ma grille · 0 / 9")
        self.assertContains(detail, self.url)
        self.assertContains(self.client.get(reverse("club:event_list")), "🎯 Bingo des rencontres")


class BingoScanTests(BingoTestCase):
    def setUp(self):
        self.event = make_bingo_event()
        self.tags = make_tags()
        self.crowd = make_crowd(self.event, self.tags)
        self.player, self.other = self.crowd[1], self.crowd[2]
        self.scan_url = reverse("club:scan", args=[self.other.qr_token])
        self.client.force_login(self.player.user)

    def test_scanning_somebody_new_adds_the_card_and_ticks_a_square(self):
        expected = bingo.find_square(self.player, self.other, new_meeting=True)
        self.assertIsNotNone(expected)
        page = self.client.get(self.scan_url)
        self.assertContains(page, "peut valider la case")
        self.assertFalse(BingoSquare.objects.filter(player=self.player, found__isnull=False).exists())  # GET ticks nothing
        response = self.client.post(self.scan_url, follow=True)
        self.assertContains(response, "Carte ajoutée à ton album")
        self.assertContains(response, "🎯 Bingo : case")
        square = BingoSquare.objects.get(player=self.player, found=self.other)
        self.assertEqual(square.pk, expected[1].pk)

    def test_an_old_acquaintance_can_still_validate_a_square_but_not_the_joker(self):
        Connection.link(self.player, self.other)
        page = self.client.get(self.scan_url)
        self.assertContains(page, "Valider ma case de bingo")
        self.client.post(self.scan_url)
        square = BingoSquare.objects.get(player=self.player, found=self.other)
        self.assertNotEqual(square.kind, "joker")

    def test_already_met_and_nothing_to_tick_goes_straight_to_the_card(self):
        Connection.link(self.player, self.other)
        BingoSquare.objects.filter(event=self.event).delete()
        give_grid(self.event, self.player, hand_grid())  # only squares nobody fills, and a joker
        response = self.client.get(self.scan_url)
        self.assertRedirects(response, reverse("club:member_detail", args=[self.other.pk]))

    def test_a_line_shouts_bingo(self):
        BingoSquare.objects.filter(event=self.event).delete()
        a, b, c = self.crowd[3], self.crowd[4], self.crowd[5]
        grid = give_grid(self.event, self.player, hand_grid(p1=("like", self.tags[0].slug)))
        tick_by_hand(grid, [0, 2], [a, b])
        BingoSquare.objects.filter(pk=grid[0].pk).update(kind="region", value="Atlantis")
        likes(c, self.tags[0])
        response = self.client.post(reverse("club:scan", args=[c.qr_token]), follow=True)
        self.assertContains(response, "BINGO ! Montre ton écran au bar")


class BingoStaffTests(BingoTestCase):
    def setUp(self):
        self.bingo_event = make_bingo_event(title="Apéro debout")
        self.dinner = make_bingo_event(title="Dîner assis", has_bingo=False, has_seating=True)
        self.client.force_login(make_staff())

    def test_no_seating_plan_for_a_standing_drinks(self):
        url = reverse("club:staff_event", args=[self.bingo_event.pk])
        page = self.client.get(url)
        self.assertContains(page, "Pas de repas assis pour cet événement")
        self.assertNotContains(page, "Générer le plan de tables")
        response = self.client.post(url, {"action": "seating", "rounds": "3", "table_size": "6"}, follow=True)
        self.assertContains(response, "pas de plan de tables")
        self.assertFalse(SeatingPlan.objects.filter(event=self.bingo_event).exists())

    def test_a_seated_dinner_keeps_its_seating_form(self):
        page = self.client.get(reverse("club:staff_event", args=[self.dinner.pk]))
        self.assertContains(page, "Générer le plan de tables")
        self.assertNotContains(page, "liste des gagnants")

    def test_the_bingo_card_lists_the_winners_for_the_bar(self):
        tags = make_tags()
        crowd = make_crowd(self.bingo_event, tags, count=6)
        grid = give_grid(self.bingo_event, crowd[0], hand_grid())
        tick_by_hand(grid, [0, 1, 2], crowd[1:4])
        page = self.client.get(reverse("club:staff_event", args=[self.bingo_event.pk]))
        self.assertContains(page, "1 grille ouverte")
        self.assertContains(page, "3 cases cochées")
        self.assertContains(page, "1 bingo")
        self.assertContains(page, crowd[0].full_name)
        self.assertContains(page, "1 ligne · 3 / 9")


class BingoDemoStoryTests(TestCase):
    """The pitch: Camille scans Lukas at the autumn dinner, and a square of her bingo is ticked."""

    def test_camille_ticks_a_square_by_scanning_lukas(self):
        call_command("seed_demo", stdout=StringIO())
        camille = Member.objects.get(user__email="camille.rey@example.com")
        lukas = Member.objects.get(user__email="lukas.imboden@example.com")
        dinner = Event.objects.get(title="Dîner d'automne")
        grid = bingo.generate_grid(dinner, camille)
        self.assertTrue(any(bingo.satisfies(lukas, square, new_meeting=False) for square in grid if square.kind != "joker"))
        self.client.force_login(camille.user)
        self.client.post(reverse("club:scan", args=[lukas.qr_token]))
        self.assertTrue(BingoSquare.objects.filter(event=dinner, player=camille, found=lukas).exists())
