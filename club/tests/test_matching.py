from collections import Counter

from django.test import SimpleTestCase

from club.services.matching import Profile, compute_matches, pair_key

FR = frozenset({"fr"})
DE = frozenset({"de"})


def people(count, **overrides):
    defaults = {"sector": "tech", "languages": FR}
    return [Profile(id=i, **{**defaults, **overrides}) for i in range(1, count + 1)]


class MatchingTests(SimpleTestCase):
    def test_never_matches_people_who_already_know_each_other(self):
        profiles = people(6)
        connected = {pair_key(1, 2), pair_key(3, 4)}
        result = compute_matches(profiles, connected)
        self.assertTrue(result)
        self.assertFalse({(m.a, m.b) for m in result} & connected)

    def test_never_matches_without_common_language(self):
        profiles = [Profile(1, "tech", FR), Profile(2, "tech", DE), Profile(3, "tech", FR)]
        pairs = {(m.a, m.b) for m in compute_matches(profiles, set())}
        self.assertNotIn((1, 2), pairs)
        self.assertNotIn((2, 3), pairs)

    def test_nobody_gets_more_than_per_person(self):
        counts = Counter()
        for m in compute_matches(people(20), set(), per_person=3):
            counts[m.a] += 1
            counts[m.b] += 1
        self.assertLessEqual(max(counts.values()), 3)

    def test_everybody_gets_at_least_one_when_possible(self):
        result = compute_matches(people(11), set(), per_person=3)
        matched = {m.a for m in result} | {m.b for m in result}
        self.assertEqual(matched, set(range(1, 12)))

    def test_shared_interests_win(self):
        profiles = [
            Profile(1, "tech", FR, likes=frozenset({"ski", "golf"})),
            Profile(2, "finance", FR, likes=frozenset({"ski", "golf"})),
            Profile(3, "tech", FR),
        ]
        best = compute_matches(profiles, set(), per_person=1)[0]
        self.assertEqual((best.a, best.b), (1, 2))
        self.assertEqual(best.shared_likes, ("golf", "ski"))

    def test_deterministic_for_same_seed(self):
        profiles = people(15)
        self.assertEqual(compute_matches(profiles, set(), seed=7), compute_matches(profiles, set(), seed=7))
