from collections import Counter

from django.test import SimpleTestCase

from club.services.seating import Guest, compute_seating, table_sizes

FR = frozenset({"fr"})


def guests(count):
    return [Guest(i, f"sector{i % 5}", FR) for i in range(1, count + 1)]


class SeatingTests(SimpleTestCase):
    def test_table_sizes_are_balanced(self):
        self.assertEqual(table_sizes(40, 8), [8, 8, 8, 8, 8])
        self.assertEqual(table_sizes(41, 8), [7, 7, 7, 7, 7, 6])
        self.assertEqual(table_sizes(0, 8), [])

    def test_everybody_is_seated_exactly_once_per_round(self):
        result = compute_seating(guests(37), rounds=3, table_size=8)
        for tables in result.rounds:
            seated = Counter(member for table in tables for member in table)
            self.assertEqual(set(seated), set(range(1, 38)))
            self.assertEqual(max(seated.values()), 1)
            self.assertLessEqual(max(len(t) for t in tables), 8)

    def test_no_repeated_pairs_when_mathematically_possible(self):
        # 16 guests, 4 tables of 4, 2 rounds: a perfect rotation exists.
        result = compute_seating(guests(16), rounds=2, table_size=4, seed=1)
        self.assertEqual(result.repeated_pairs, 0)

    def test_beats_keeping_the_same_tables(self):
        result = compute_seating(guests(40), rounds=3, table_size=8)
        same_tables_repeats = 5 * 28 * 2  # 5 tables x 28 pairs, seen again in rounds 2 and 3
        self.assertLess(result.repeated_pairs, same_tables_repeats / 4)

    def test_deterministic_for_same_seed(self):
        self.assertEqual(compute_seating(guests(20), seed=3), compute_seating(guests(20), seed=3))
