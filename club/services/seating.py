"""Tables tournantes — pure Python (no Django import), unit-tested in club/tests/test_seating.py.

Variant of the Social Golfer Problem (NP-hard): local search (random swap of two guests
seated at different tables, kept if the cost does not increase) with random restarts.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from itertools import combinations

PENALTY_SEATED_TOGETHER_BEFORE = 10
PENALTY_NO_COMMON_LANGUAGE = 4
PENALTY_ALREADY_CONNECTED = 3
PENALTY_SAME_SECTOR = 1


@dataclass(frozen=True)
class Guest:
    id: int
    sector: str
    languages: frozenset[str]


@dataclass(frozen=True)
class SeatingResult:
    rounds: list[list[list[int]]]  # rounds[r][t] = sorted member ids at table t+1 during round r
    new_pairs: int  # distinct pairs seated together at least once who did not know each other before
    repeated_pairs: int  # extra co-seatings of a same pair across rounds (0 = never twice with the same person)


def table_sizes(guest_count: int, table_size: int) -> list[int]:
    """Balanced tables: never above table_size, sizes differ by at most one."""
    if guest_count == 0:
        return []
    tables = math.ceil(guest_count / table_size)
    base, extra = divmod(guest_count, tables)
    return [base + 1 if t < extra else base for t in range(tables)]


def compute_seating(
    guests: list[Guest],
    rounds: int = 3,
    table_size: int = 8,
    already_connected: frozenset[tuple[int, int]] = frozenset(),
    seed: int = 0,
    iterations: int | None = None,
    restarts: int = 4,
) -> SeatingResult:
    if rounds < 1 or table_size < 2:
        raise ValueError("rounds must be >= 1 and table_size >= 2")
    rng = random.Random(seed)
    guests = sorted(guests, key=lambda g: g.id)
    n = len(guests)
    if n == 0:
        return SeatingResult([[] for _ in range(rounds)], 0, 0)
    sizes = table_sizes(n, table_size)
    iterations = iterations or max(2000, 60 * n)

    def key(x: int, y: int) -> tuple[int, int]:
        return (min(guests[x].id, guests[y].id), max(guests[x].id, guests[y].id))

    static = [[0] * n for _ in range(n)]
    for x, y in combinations(range(n), 2):
        cost = 0
        if key(x, y) in already_connected:
            cost += PENALTY_ALREADY_CONNECTED
        if not (guests[x].languages & guests[y].languages):
            cost += PENALTY_NO_COMMON_LANGUAGE
        if guests[x].sector == guests[y].sector:
            cost += PENALTY_SAME_SECTOR
        static[x][y] = static[y][x] = cost
    together = [[0] * n for _ in range(n)]

    def pair_cost(x: int, y: int) -> int:
        return static[x][y] + PENALTY_SEATED_TOGETHER_BEFORE * together[x][y]

    def cost_at(x: int, table: list[int], leaving: int) -> int:
        return sum(pair_cost(x, y) for y in table if y != x and y != leaving)

    plan = []
    for _ in range(rounds):
        best, best_cost = None, None
        for _ in range(restarts):
            order = list(range(n))
            rng.shuffle(order)
            tables, start = [], 0
            for size in sizes:
                tables.append(order[start : start + size])
                start += size
            if len(tables) > 1:
                for _ in range(iterations):
                    t1, t2 = rng.sample(range(len(tables)), 2)
                    i, j = rng.randrange(len(tables[t1])), rng.randrange(len(tables[t2]))
                    x, y = tables[t1][i], tables[t2][j]
                    before = cost_at(x, tables[t1], x) + cost_at(y, tables[t2], y)
                    after = cost_at(x, tables[t2], y) + cost_at(y, tables[t1], x)
                    if after <= before:
                        tables[t1][i], tables[t2][j] = y, x
            total = sum(pair_cost(x, y) for table in tables for x, y in combinations(table, 2))
            if best_cost is None or total < best_cost:
                best, best_cost = [list(table) for table in tables], total
        for table in best:
            for x, y in combinations(table, 2):
                together[x][y] += 1
                together[y][x] += 1
        plan.append([sorted(guests[x].id for x in table) for table in best])

    pairs = list(combinations(range(n), 2))
    repeated = sum(together[x][y] - 1 for x, y in pairs if together[x][y] > 1)
    new_pairs = sum(1 for x, y in pairs if together[x][y] and key(x, y) not in already_connected)
    return SeatingResult(plan, new_pairs, repeated)
