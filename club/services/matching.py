"""'Tes 3 rencontres' — pure Python (no Django import), unit-tested in club/tests/test_matching.py."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from itertools import combinations, zip_longest

WEIGHT_SHARED_LIKE = 3
WEIGHT_SHARED_DISLIKE = 2
WEIGHT_CROSS_SECTOR = 2
WEIGHT_NEWCOMER_WITH_PILLAR = 3
WEIGHT_SYNERGY = 4  # a need of one covered by the other: a discreet bonus, the human affinities stay the core
MAX_SYNERGIES_PER_PAIR = 2


@dataclass(frozen=True)
class Profile:
    id: int
    sector: str
    languages: frozenset[str]
    likes: frozenset[str] = frozenset()
    dislikes: frozenset[str] = frozenset()
    is_newcomer: bool = False
    is_pillar: bool = False
    offers: frozenset[str] = frozenset()  # themes of mutual help the person can help on
    needs: frozenset[str] = frozenset()  # themes the person is looking for


@dataclass(frozen=True)
class Proposal:
    a: int  # always a < b
    b: int
    score: int
    shared_likes: tuple[str, ...]
    shared_dislikes: tuple[str, ...]
    cross_sector: bool
    welcomes_newcomer: bool
    synergies: tuple[tuple[int, int, str], ...] = ()  # (helper id, seeker id, theme slug)


def pair_key(first: int, second: int) -> tuple[int, int]:
    return (first, second) if first < second else (second, first)


def synergies_between(p: Profile, q: Profile) -> tuple[tuple[int, int, str], ...]:
    """Needs of one covered by the offers of the other, in both directions, at most MAX_SYNERGIES_PER_PAIR.

    When both can help each other, one of each direction is kept before a second one in the same direction."""
    p_helps_q = [(p.id, q.id, slug) for slug in sorted(p.offers & q.needs)]
    q_helps_p = [(q.id, p.id, slug) for slug in sorted(q.offers & p.needs)]
    interleaved = [synergy for pair in zip_longest(p_helps_q, q_helps_p) for synergy in pair if synergy is not None]
    return tuple(interleaved[:MAX_SYNERGIES_PER_PAIR])


def score_pair(p: Profile, q: Profile) -> Proposal | None:
    """None when the two people share no language (they could not talk)."""
    if not (p.languages & q.languages):
        return None
    shared_likes = tuple(sorted(p.likes & q.likes))
    shared_dislikes = tuple(sorted(p.dislikes & q.dislikes))
    cross_sector = p.sector != q.sector
    welcomes_newcomer = (p.is_newcomer and q.is_pillar) or (q.is_newcomer and p.is_pillar)
    synergies = synergies_between(p, q)
    score = (
        WEIGHT_SHARED_LIKE * len(shared_likes)
        + WEIGHT_SHARED_DISLIKE * len(shared_dislikes)
        + (WEIGHT_CROSS_SECTOR if cross_sector else 0)
        + (WEIGHT_NEWCOMER_WITH_PILLAR if welcomes_newcomer else 0)
        + WEIGHT_SYNERGY * len(synergies)
    )
    a, b = pair_key(p.id, q.id)
    return Proposal(a, b, score, shared_likes, shared_dislikes, cross_sector, welcomes_newcomer, synergies)


def compute_matches(
    profiles: list[Profile],
    already_connected: set[tuple[int, int]],
    per_person: int = 3,
    seed: int = 0,
) -> list[Proposal]:
    """Up to `per_person` introductions per attendee.

    Rules: never two people who already know each other, never two people without a common
    language. Fair greedy: everybody gets a 1st introduction before anybody gets a 2nd, etc.
    Deterministic for a given seed. Complexity O(n^2) pairs: 200 attendees -> ~20k pairs.
    """
    rng = random.Random(seed)
    candidates = []
    for p, q in combinations(sorted(profiles, key=lambda x: x.id), 2):
        if pair_key(p.id, q.id) in already_connected:
            continue
        proposal = score_pair(p, q)
        if proposal is not None:
            candidates.append((proposal.score, rng.random(), proposal))
    candidates.sort(key=lambda item: (-item[0], item[1]))

    taken = Counter()
    chosen: dict[tuple[int, int], Proposal] = {}
    for cap in range(1, per_person + 1):
        for _, _, proposal in candidates:
            key = (proposal.a, proposal.b)
            if key not in chosen and taken[proposal.a] < cap and taken[proposal.b] < cap:
                chosen[key] = proposal
                taken[proposal.a] += 1
                taken[proposal.b] += 1
    return sorted(chosen.values(), key=lambda m: (-m.score, m.a, m.b))
