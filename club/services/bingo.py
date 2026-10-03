"""« Bingo des rencontres » : une grille 3×3 « Trouve quelqu'un qui… » par inscrit et par événement.

On trouve la personne, on discute, on scanne son QR code : la case se coche avec son prénom. Une personne ne
remplit qu'une case par grille. Une ligne (horizontale, verticale ou diagonale) = BINGO, la grille pleine = tirage
au sort. La case centrale est un joker : « quelqu'un que tu n'avais jamais rencontré ».

Testé dans club/tests/test_bingo.py. Rien à préparer côté staff : la grille se crée à la première ouverture
(page du bingo ou scan d'un QR code), de façon déterministe, et reste la même ensuite.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import NamedTuple

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from club.models import RSVP, BingoSquare, Event, Match, Member, MemberTag, Sector, Tag
from club.services.events import attendees
from club.services.federation import collected_ids
from club.ui import SECTOR_STYLE

Kind = BingoSquare.Kind

GRID_SIZE = 9
CENTER = 4  # the joker
LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),  # diagonals
)
# Variety: at most this many squares of each kind in a grid (3 + 2 + 1 + 2 + 1 + 1 = 10 >= the 8 squares to fill).
CAPS = {Kind.LIKE: 3, Kind.DISLIKE: 2, Kind.LANGUAGE: 1, Kind.SECTOR: 2, Kind.RANK: 1, Kind.REGION: 1}
LANGUAGES = ("de", "en")  # "fr" is added for the players who do not speak French
RANKS = (Member.RANK_FOUNDER, Member.RANK_PILLAR, Member.RANK_NEWCOMER)

LANGUAGE_LABELS = {
    "fr": gettext_lazy("parle français"),
    "de": gettext_lazy("parle allemand"),
    "en": gettext_lazy("parle anglais"),
}
RANK_LABELS = {
    Member.RANK_FOUNDER: gettext_lazy("est membre fondateur"),
    Member.RANK_PILLAR: gettext_lazy("est au Club depuis plus de 5 ans"),
    Member.RANK_NEWCOMER: gettext_lazy("vient d'entrer au Club"),
}


# --------------------------------------------------------------------------------------------------------------
# What a person is, as far as the game is concerned
# --------------------------------------------------------------------------------------------------------------


def norm_region(text: str) -> str:
    """Regions are typed by hand ("Brig", "brig ", "BRIG"): compare them without case nor extra spaces."""
    return " ".join(text.split()).casefold()


@dataclass(frozen=True)
class Person:
    """Snapshot of one member: everything a square can ask about, loaded once for the whole attendee list."""

    id: int
    sector: str
    region: str  # normalised, "" when unknown
    region_label: str  # as typed, for display
    languages: frozenset[str]
    rank: str
    likes: frozenset[str]  # tag slugs
    dislikes: frozenset[str]

    def fills(self, kind: str, value: str) -> bool:
        """True when this person answers « Trouve quelqu'un qui… <kind> <value> ». The joker depends on the meeting."""
        if kind == Kind.LIKE:
            return value in self.likes
        if kind == Kind.DISLIKE:
            return value in self.dislikes
        if kind == Kind.LANGUAGE:
            return value in self.languages
        if kind == Kind.SECTOR:
            return self.sector == value
        if kind == Kind.RANK:
            return self.rank == value
        if kind == Kind.REGION:
            return bool(self.region) and self.region == norm_region(value)
        return False


def _people(members) -> dict[int, Person]:
    """{member id: Person} for a queryset of members, in two queries, ordered by id."""
    rows = sorted(members, key=lambda m: m.pk)
    likes, dislikes = defaultdict(set), defaultdict(set)
    links = MemberTag.objects.filter(
        member__in=members, sentiment__in=(MemberTag.Sentiment.LIKE, MemberTag.Sentiment.DISLIKE)
    ).values_list("member_id", "tag__slug", "sentiment")
    for member_id, slug, sentiment in links:
        (likes if sentiment == MemberTag.Sentiment.LIKE else dislikes)[member_id].add(slug)
    return {
        m.pk: Person(
            id=m.pk,
            sector=m.sector,
            region=norm_region(m.region),
            region_label=" ".join(m.region.split()),
            languages=m.languages,
            rank=m.rank,
            likes=frozenset(likes[m.pk]),
            dislikes=frozenset(dislikes[m.pk]),
        )
        for m in rows
    }


def _attendee_people(event) -> dict[int, Person]:
    return _people(attendees(event))


def _person(member) -> Person:
    return _people(Member.objects.filter(pk=member.pk))[member.pk]


def _fills(person: Person, square, new_meeting: bool) -> bool:
    return bool(new_meeting) if square.kind == Kind.JOKER else person.fills(square.kind, square.value)


def satisfies(member, square, new_meeting) -> bool:
    """Does `member` answer this square? The joker only counts for someone the player had never met."""
    if square.kind == Kind.JOKER:
        return bool(new_meeting)
    return _fills(_person(member), square, new_meeting)


# --------------------------------------------------------------------------------------------------------------
# Building a grid
# --------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    kind: str
    value: str
    fillers: frozenset[int]  # ids of the OTHER attendees who answer it

    @property
    def key(self) -> tuple[str, str]:
        return (self.kind, self.value)


def _candidates(player, others) -> list[Candidate]:
    """Every square the other attendees could fill, in a stable order (the same event gives the same grid)."""
    languages = LANGUAGES if player.speaks_fr else LANGUAGES + ("fr",)
    fillers: dict[tuple[str, str], set[int]] = defaultdict(set)
    region_names: dict[str, str] = {}
    for p in others:
        for slug in p.likes:
            fillers[(Kind.LIKE, slug)].add(p.id)
        for slug in p.dislikes:
            fillers[(Kind.DISLIKE, slug)].add(p.id)
        for code in languages:
            if code in p.languages:
                fillers[(Kind.LANGUAGE, code)].add(p.id)
        if p.sector != Sector.OTHER:  # "Autre secteur" says nothing: the member has not chosen theirs yet
            fillers[(Kind.SECTOR, p.sector)].add(p.id)
        if p.rank in RANKS:
            fillers[(Kind.RANK, p.rank)].add(p.id)
        if p.region:
            region_names.setdefault(p.region, p.region_label)
            fillers[(Kind.REGION, p.region)].add(p.id)
    result = []
    for (kind, value), ids in sorted(fillers.items()):
        result.append(Candidate(kind, region_names[value] if kind == Kind.REGION else value, frozenset(ids)))
    return result


def _unmatched(supply: list[frozenset[int]]) -> list[int]:
    """Squares left without a person when each person fills at most one square (maximum bipartite matching,
    augmenting paths). Empty list = a full card is possible: every square can have its own person."""
    owner: dict[int, int] = {}  # person id -> index of the square they fill

    def assign(square: int, seen: set[int]) -> bool:
        for person in sorted(supply[square]):
            if person in seen:
                continue
            seen.add(person)
            if person not in owner or assign(owner[person], seen):
                owner[person] = square
                return True
        return False

    return [square for square in range(len(supply)) if not assign(square, set())]


def _choose(player, others: dict[int, Person], met: set[int], matches, rng: random.Random) -> list[tuple[str, str]]:
    """The 8 (kind, value) pairs around the joker, shuffled. Priorities, in this order:
    1. for each introduction proposed to the player ("Tes 3 rencontres"), a square that partner fills, preferably a
       "like" they share (a conversation topic for sure);
    2. squares that people the player has not met yet fill;
    3. variety (CAPS).
    Candidates filled by at least 2 other attendees come first; squares only one person can fill only complete
    what is missing. Then we check a full card is still possible, and finally pad with jokers (small events)."""
    pool = _candidates(player, others.values())
    strong = [c for c in pool if len(c.fillers) >= 2]
    weak = [c for c in pool if len(c.fillers) == 1]
    draw = {c.key: rng.random() for c in pool}  # one random number per candidate: stable tie-breaks
    own_region = norm_region(player.region)
    squares_to_fill = GRID_SIZE - 1

    def order(c: Candidate):  # lower = chosen first
        unmet = len(c.fillers - met)
        like_me = (c.kind == Kind.SECTOR and c.value == player.sector) or (
            c.kind == Kind.REGION and norm_region(c.value) == own_region
        )  # the point is to meet people unlike yourself
        return (0 if unmet >= 2 else 1 if unmet == 1 else 2, like_me, draw[c.key])

    ranked = sorted(strong, key=order) + sorted(weak, key=order)
    chosen: list[Candidate] = []
    taken: set[tuple[str, str]] = set()
    protected: set[tuple[str, str]] = set()  # the squares of the introductions: never swapped out
    counts: Counter = Counter()

    def take(c: Candidate) -> None:
        chosen.append(c)
        taken.add(c.key)
        counts[c.kind] += 1

    def has_room(c: Candidate) -> bool:
        return c.key not in taken and counts[c.kind] < CAPS[c.kind]

    for match in matches:  # best introduction first
        if len(chosen) >= squares_to_fill:
            break
        partner = match.other(player).pk
        if partner not in others:
            continue
        options = [c for c in ranked if partner in c.fillers and c.key not in taken]
        options = [c for c in options if has_room(c)] or options  # the caps give way before the introduction does
        if not options:
            continue

        def partner_rank(c: Candidate, match=match):
            if c.kind == Kind.LIKE and c.value in match.shared_likes:
                topic = 0
            elif c.kind == Kind.DISLIKE and c.value in match.shared_dislikes:
                topic = 1
            else:
                topic = 2 if c.kind == Kind.LIKE else 3
            return (topic, len(c.fillers) < 2, order(c))

        pick = min(options, key=partner_rank)
        take(pick)
        protected.add(pick.key)

    for c in ranked:
        if len(chosen) >= squares_to_fill:
            break
        if has_room(c):
            take(c)

    if len(others) >= len(chosen):  # with fewer people than squares, a full card is out of reach anyway
        dropped: set[tuple[str, str]] = set()
        while True:
            failing = _unmatched([c.fillers for c in chosen])
            victims = [i for i, c in enumerate(chosen) if c.key not in protected]
            if not failing or not victims:
                break
            # swap the least supplied square (preferably one of those left without a person)
            victim = min(victims, key=lambda i: (i not in failing, len(chosen[i].fillers), i))
            old = chosen[victim]

            def fits(c: Candidate) -> bool:
                if c.key in taken or c.key in dropped:
                    return False
                return counts[c.kind] - (1 if c.kind == old.kind else 0) < CAPS[c.kind]

            replacement = next((c for c in ranked if fits(c)), None)
            if replacement is None:
                break
            dropped.add(old.key)
            taken.discard(old.key)
            counts[old.kind] -= 1
            taken.add(replacement.key)
            counts[replacement.kind] += 1
            chosen[victim] = replacement

    picks = [(c.kind, c.value) for c in chosen]
    picks += [(Kind.JOKER, "")] * (squares_to_fill - len(picks))  # small event: jokers complete the grid
    rng.shuffle(picks)
    return picks


def existing_grid(event, player) -> list[BingoSquare]:
    """The player's squares for this event, by position ([] when the grid was never opened). Writes nothing."""
    return list(BingoSquare.objects.filter(event=event, player=player).select_related("found").order_by("position"))


def generate_grid(event, player) -> list[BingoSquare]:
    """The player's 3×3 grid for this event: created on first call, the existing one afterwards (idempotent).
    Deterministic: the same attendees, tastes and introductions always give the same grid."""
    grid = existing_grid(event, player)
    if grid:
        return grid
    others = _attendee_people(event)
    others.pop(player.pk, None)  # « Trouve quelqu'un qui… » : somebody else
    matches = Match.objects.filter(event=event).filter(Q(member_a=player) | Q(member_b=player)).order_by("-score", "pk")
    rng = random.Random(event.pk * 100_003 + player.pk)
    picks = _choose(player, others, collected_ids(player), list(matches), rng)
    positions = [p for p in range(GRID_SIZE) if p != CENTER]
    squares = [BingoSquare(event=event, player=player, position=CENTER, kind=Kind.JOKER, value="")]
    squares += [BingoSquare(event=event, player=player, position=p, kind=k, value=v) for p, (k, v) in zip(positions, picks)]
    # Two requests may open the same grid at once: the second insert is simply ignored, and we read what is stored.
    BingoSquare.objects.bulk_create(squares, ignore_conflicts=True)
    return existing_grid(event, player)


# --------------------------------------------------------------------------------------------------------------
# Texts
# --------------------------------------------------------------------------------------------------------------


def _label(square, tags: dict[str, Tag]) -> str:
    kind, value = square.kind, square.value
    if kind in (Kind.LIKE, Kind.DISLIKE):
        tag = tags.get(value)
        subject = f"{tag.emoji} {tag.label}" if tag else value
        return (_("adore %(tag)s") if kind == Kind.LIKE else _("déteste %(tag)s")) % {"tag": subject}
    if kind == Kind.LANGUAGE:
        return str(LANGUAGE_LABELS.get(value, value))
    if kind == Kind.SECTOR:
        emoji = SECTOR_STYLE.get(value, ("🏢", ""))[0]
        name = Sector(value).label if value in Sector.values else value
        return _("travaille dans %(sector)s") % {"sector": f"{emoji} {name}"}
    if kind == Kind.RANK:
        return str(RANK_LABELS.get(value, value))
    if kind == Kind.REGION:
        return _("vient de %(region)s") % {"region": value}
    return _("🃏 Joker : quelqu'un que tu n'avais jamais rencontré")


def square_labels(squares) -> list[str]:
    """Texts of several squares in the active language, with a single query for the affinities."""
    slugs = {s.value for s in squares if s.kind in (Kind.LIKE, Kind.DISLIKE)}
    tags = {tag.slug: tag for tag in Tag.objects.filter(slug__in=slugs)} if slugs else {}
    return [_label(square, tags) for square in squares]


def square_label(square) -> str:
    """« adore ⛷️ Ski de randonnée », « parle allemand », « vient de Brig »… (reads as the end of « Trouve quelqu'un qui… »)."""
    return square_labels([square])[0]


# --------------------------------------------------------------------------------------------------------------
# Playing
# --------------------------------------------------------------------------------------------------------------


def _start_of_today():
    return timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)


def is_open(event) -> bool:
    """The game runs for the whole day of the event (local time), then the grids become read-only."""
    return event.has_bingo and not event.cancelled_at and event.starts_at >= _start_of_today()


def open_bingo_event(player, other):
    """The next published bingo event, not cancelled nor over yet, where both people are expected (see
    events.attendees: a member who sent a substitute no longer plays, an approved guest does), or None."""
    if player.pk == other.pk:
        return None
    candidates = (
        Event.objects.filter(has_bingo=True, is_published=True, cancelled_at__isnull=True, starts_at__gte=_start_of_today())
        .filter(rsvps__member=player, rsvps__status=RSVP.Status.YES)
        .filter(rsvps__member=other, rsvps__status=RSVP.Status.YES)
        .order_by("starts_at", "pk")
        .distinct()
    )
    for event in candidates:
        if attendees(event).filter(pk__in=(player.pk, other.pk)).count() == 2:
            return event
    return None


def _rarity(square, people: dict[int, Person], player_pk: int, met: set[int]) -> int:
    """How many other attendees could fill this square (the joker: everybody the player has not met)."""
    if square.kind == Kind.JOKER:
        return sum(1 for pk in people if pk != player_pk and pk not in met)
    return sum(1 for pk, person in people.items() if pk != player_pk and person.fills(square.kind, square.value))


def _find(player, other, new_meeting):
    event = open_bingo_event(player, other)
    if event is None:
        return None
    squares = generate_grid(event, player)
    if any(s.found_id == other.pk for s in squares):  # one person fills one square only
        return None
    free = [s for s in squares if s.found_id is None]
    people = _attendee_people(event)
    them = people.get(other.pk)
    if not free or them is None:
        return None
    met = collected_ids(player)
    options = [
        (_rarity(s, people, player.pk, met), s.position, s) for s in free if _fills(them, s, new_meeting)
    ]
    if not options:
        return None
    return event, squares, min(options, key=lambda option: option[:2])[2]


def find_square(player, other, new_meeting):
    """(event, square) the player would tick by scanning `other`, or None. Ticks nothing.
    Among the free squares `other` fills: the rarest one (fewest attendees fill it), then the lowest position."""
    hit = _find(player, other, new_meeting)
    return None if hit is None else (hit[0], hit[2])


def complete_lines(squares) -> list[tuple[int, int, int]]:
    """The lines (3 rows, 3 columns, 2 diagonals) whose three squares are ticked."""
    ticked = {s.position for s in squares if s.found_id is not None}
    return [line for line in LINES if all(position in ticked for position in line)]


def lines(squares) -> int:
    return len(complete_lines(squares))


@dataclass(frozen=True)
class TickResult:
    event: Event
    square: BingoSquare
    lines_before: int
    lines_after: int
    filled: int  # ticked squares, this one included

    @property
    def new_bingo(self) -> bool:
        return self.lines_after > self.lines_before

    @property
    def full_card(self) -> bool:
        return self.filled == GRID_SIZE


def tick(player, other, new_meeting) -> TickResult | None:
    """Tick the square `other` fills for `player` (see find_square). None when there is nothing to tick, or when a
    parallel request (double POST) got there first."""
    hit = _find(player, other, new_meeting)
    if hit is None:
        return None
    event, squares, square = hit
    before = lines(squares)
    now = timezone.now()
    try:
        with transaction.atomic():
            updated = BingoSquare.objects.filter(pk=square.pk, found__isnull=True).update(found=other, found_at=now)
    except IntegrityError:  # `other` already fills another square of this grid
        return None
    if not updated:  # somebody else just ticked this very square
        return None
    square.found, square.found_at = other, now
    return TickResult(event, square, before, lines(squares), sum(1 for s in squares if s.found_id is not None))


def found_count(player, event) -> int:
    return BingoSquare.objects.filter(event=event, player=player, found__isnull=False).count()


# --------------------------------------------------------------------------------------------------------------
# For the staff
# --------------------------------------------------------------------------------------------------------------


class Winner(NamedTuple):
    member: Member
    lines: int
    squares: int  # ticked squares


@dataclass(frozen=True)
class EventStats:
    grids: int  # grids opened
    ticked: int  # squares ticked, all grids together
    full_cards: int
    winners: list[Winner]  # at least one line, best first
    total: int = GRID_SIZE

    @property
    def bingos(self) -> int:
        return len(self.winners)


def event_stats(event) -> EventStats:
    by_player: dict[int, list[BingoSquare]] = defaultdict(list)
    for square in BingoSquare.objects.filter(event=event, player__user__is_active=True).select_related("player"):
        by_player[square.player_id].append(square)
    winners: list[Winner] = []
    ticked = full_cards = 0
    for squares in by_player.values():
        found = sum(1 for s in squares if s.found_id is not None)
        ticked += found
        if found == GRID_SIZE:
            full_cards += 1
        complete = lines(squares)
        if complete:
            winners.append(Winner(squares[0].player, complete, found))
    winners.sort(key=lambda w: (-w.lines, -w.squares, w.member.last_name, w.member.first_name))
    return EventStats(len(by_player), ticked, full_cards, winners)
