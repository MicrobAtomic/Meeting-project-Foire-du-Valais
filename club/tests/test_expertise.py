"""« Je peux aider sur… / Je cherche… »: the themes of mutual help, their bonus in « Tes 3 rencontres » and their display.

A discreet door, never the core: affinities still weigh more than a synergy (see SynergyScoreTests)."""

from datetime import timedelta
from html import unescape
from io import StringIO
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.html import escape

from club import demo_data
from club.management.commands import seed_demo
from club.models import RSVP, Connection, Event, Expertise, Match, Member, MemberExpertise
from club.services.events import generate_matches
from club.services.expertise import MAX_PER_KIND, save_expertise
from club.services.intros import intros_for
from club.services.matching import (
    MAX_SYNERGIES_PER_PAIR, WEIGHT_CROSS_SECTOR, WEIGHT_SHARED_LIKE, WEIGHT_SYNERGY, Profile, Proposal, compute_matches,
    pair_key, score_pair,
)
from club.tests.helpers import PASSWORD, assert_csp_clean, make_member, make_staff

FR = frozenset({"fr"})
DE = frozenset({"de"})
OFFER, NEED = MemberExpertise.Kind.OFFER, MemberExpertise.Kind.NEED


def theme(slug, label_fr=None, **extra):
    return Expertise.objects.create(slug=slug, emoji=extra.pop("emoji", "🧰"), label_fr=label_fr or slug.capitalize(), **extra)


def profile(member_id, offers=(), needs=(), sector="tech", **extra):
    return Profile(member_id, sector, extra.pop("languages", FR), offers=frozenset(offers), needs=frozenset(needs), **extra)


class SynergyScoreTests(SimpleTestCase):
    """Score of a pair: +4 per need of one covered by the other (both directions), at most 2 per pair."""

    def base_score(self):
        return score_pair(profile(1), profile(2, sector="finance")).score  # the same pair, without any theme

    def test_the_weights_keep_affinities_at_the_centre(self):
        self.assertEqual((WEIGHT_SYNERGY, MAX_SYNERGIES_PER_PAIR), (4, 2))
        self.assertLess(WEIGHT_SYNERGY, 2 * WEIGHT_SHARED_LIKE)  # two shared passions beat one synergy

    def test_a_need_covered_by_the_other_adds_four_points(self):
        without = score_pair(profile(1), profile(2, sector="finance"))
        helper_is_second = score_pair(profile(1, needs={"digital"}), profile(2, offers={"digital"}, sector="finance"))
        helper_is_first = score_pair(profile(1, offers={"digital"}), profile(2, needs={"digital"}, sector="finance"))
        self.assertEqual(without.synergies, ())
        self.assertEqual(helper_is_second.score, without.score + WEIGHT_SYNERGY)
        self.assertEqual(helper_is_second.synergies, ((2, 1, "digital"),))  # (helper id, seeker id, slug)
        self.assertEqual(helper_is_first.score, without.score + WEIGHT_SYNERGY)
        self.assertEqual(helper_is_first.synergies, ((1, 2, "digital"),))

    def test_a_synergy_in_each_direction_adds_eight_points(self):
        p = profile(1, offers={"digital"}, needs={"marche-alemanique"})
        q = profile(2, offers={"marche-alemanique"}, needs={"digital"}, sector="construction")
        proposal = score_pair(p, q)
        self.assertEqual(proposal.score, score_pair(profile(1), profile(2, sector="construction")).score + 2 * WEIGHT_SYNERGY)
        self.assertEqual(set(proposal.synergies), {(1, 2, "digital"), (2, 1, "marche-alemanique")})

    def test_at_most_two_synergies_are_counted_per_pair(self):
        three = {"digital", "marketing", "financement"}
        one_way = score_pair(profile(1, offers=three), profile(2, needs=three, sector="finance"))
        self.assertEqual(len(one_way.synergies), 2)
        self.assertEqual(one_way.score, self.base_score() + 2 * WEIGHT_SYNERGY)
        # when they can help each other, one of each direction is kept before a second one the same way
        mixed = score_pair(profile(1, offers=three, needs={"export"}), profile(2, needs=three, offers={"export"}, sector="finance"))
        self.assertEqual(len(mixed.synergies), 2)
        self.assertEqual({(helper, seeker) for helper, seeker, _slug in mixed.synergies}, {(1, 2), (2, 1)})

    def test_no_synergy_without_a_need_covered_by_an_offer(self):
        cases = {
            "no themes": (profile(1), profile(2)),
            "offers only": (profile(1, offers={"digital"}), profile(2, offers={"digital"})),
            "needs only": (profile(1, needs={"digital"}), profile(2, needs={"digital"})),
            "other themes": (profile(1, offers={"digital"}), profile(2, needs={"export"})),
            "own offer is not a need": (profile(1, offers={"digital"}, needs={"digital"}), profile(2)),
        }
        for name, (p, q) in cases.items():
            proposal = score_pair(p, q)
            self.assertEqual(proposal.synergies, (), name)
            self.assertEqual(proposal.score, score_pair(profile(1), profile(2)).score, name)

    def test_existing_callers_still_build_profiles_and_proposals_without_themes(self):
        self.assertEqual(Profile(1, "tech", FR).offers, frozenset())
        self.assertEqual(Profile(1, "tech", FR).needs, frozenset())
        self.assertEqual(Proposal(1, 2, 0, (), (), False, False).synergies, ())

    def test_the_absolute_rules_do_not_change(self):
        helper, seeker = profile(1, offers={"digital"}, languages=FR), profile(2, needs={"digital"}, languages=DE)
        self.assertIsNone(score_pair(helper, seeker))  # no common language: never, whatever the synergy
        friends = [profile(1, offers={"digital"}), profile(2, needs={"digital"}), profile(3)]
        pairs = {(m.a, m.b) for m in compute_matches(friends, {pair_key(1, 2)}, per_person=2)}
        self.assertNotIn((1, 2), pairs)  # they already know each other: never, whatever the synergy

    def test_a_synergy_is_a_bonus_two_shared_passions_still_win(self):
        profiles = [
            profile(1, needs={"digital"}, likes=frozenset({"ski", "golf"})),
            profile(2, offers={"digital"}),  # synergy with 1 (+4)
            profile(3, likes=frozenset({"ski", "golf"})),  # two shared passions with 1 (+6)
        ]
        best = compute_matches(profiles, set(), per_person=1)[0]
        self.assertEqual((best.a, best.b), (1, 3))

    def test_the_proposal_carries_its_synergies_and_stays_deterministic(self):
        profiles = [profile(1, offers={"digital"}), profile(2, needs={"digital"}), profile(3), profile(4, needs={"digital"})]
        first = compute_matches(profiles, set(), seed=7)
        self.assertEqual(first, compute_matches(profiles, set(), seed=7))
        by_pair = {(m.a, m.b): m.synergies for m in first}
        self.assertEqual(by_pair[(1, 2)], ((1, 2, "digital"),))
        self.assertEqual(by_pair[(1, 4)], ((1, 4, "digital"),))
        self.assertEqual(by_pair[(2, 4)], ())


class SaveExpertiseTests(TestCase):
    def setUp(self):
        self.alice = make_member("alice@example.com")
        self.bob = make_member("bob@example.com")
        self.themes = {slug: theme(slug) for slug in ("digital", "marketing", "export", "financement", "juridique")}

    def slugs(self, member, kind):
        return set(MemberExpertise.objects.filter(member=member, kind=kind).values_list("expertise__slug", flat=True))

    def test_saves_and_replaces_the_themes_of_that_member_only(self):
        t = self.themes
        save_expertise(self.bob, [t["export"]], [t["juridique"]])
        save_expertise(self.alice, [t["digital"], t["marketing"]], [t["financement"]])
        self.assertEqual((self.slugs(self.alice, OFFER), self.slugs(self.alice, NEED)), ({"digital", "marketing"}, {"financement"}))
        save_expertise(self.alice, [t["marketing"], t["export"]], [])
        self.assertEqual((self.slugs(self.alice, OFFER), self.slugs(self.alice, NEED)), ({"marketing", "export"}, set()))
        self.assertEqual((self.slugs(self.bob, OFFER), self.slugs(self.bob, NEED)), ({"export"}, {"juridique"}))

    def test_saving_the_same_themes_twice_changes_nothing(self):
        save_expertise(self.alice, [self.themes["digital"]], [self.themes["export"]])
        before = set(MemberExpertise.objects.values_list("pk", flat=True))
        save_expertise(self.alice, [self.themes["digital"], self.themes["digital"]], [self.themes["export"]])
        self.assertEqual(set(MemberExpertise.objects.values_list("pk", flat=True)), before)

    def test_at_most_three_themes_per_kind_and_nothing_is_written_beyond(self):
        t = self.themes
        save_expertise(self.alice, [t["digital"]], [t["export"]])
        save_expertise(self.alice, [t["digital"], t["marketing"], t["export"]], [t["financement"], t["juridique"], t["digital"]])
        self.assertEqual(MAX_PER_KIND, 3)
        self.assertEqual(MemberExpertise.objects.filter(member=self.alice).count(), 6)  # 3 + 3 is allowed
        for too_many in (
            ([t["digital"], t["marketing"], t["export"], t["financement"]], []),
            ([], [t["digital"], t["marketing"], t["export"], t["financement"]]),
        ):
            with self.assertRaises(ValidationError):
                save_expertise(self.alice, *too_many)
            self.assertEqual(MemberExpertise.objects.filter(member=self.alice).count(), 6)  # untouched

    def test_the_database_refuses_the_same_theme_twice_in_the_same_kind(self):
        MemberExpertise.objects.create(member=self.alice, expertise=self.themes["digital"], kind=OFFER)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MemberExpertise.objects.create(member=self.alice, expertise=self.themes["digital"], kind=OFFER)
        MemberExpertise.objects.create(member=self.alice, expertise=self.themes["digital"], kind=NEED)  # the other kind is fine


class ExpertiseLabelTests(TestCase):
    def test_label_follows_the_active_language_and_falls_back_to_french(self):
        full = Expertise.objects.create(slug="digital", emoji="💻", label_fr="Digital & IA", label_de="Digitalisierung & KI",
                                        label_en="Digital & AI")
        partial = Expertise.objects.create(slug="export", emoji="🌍", label_fr="Export & international")
        for language, expected in (("fr", "Digital & IA"), ("de", "Digitalisierung & KI"), ("en", "Digital & AI")):
            with translation.override(language):
                self.assertEqual(full.label, expected, language)
        for language in ("fr", "de", "en"):
            with translation.override(language):
                self.assertEqual(partial.label, "Export & international", language)  # no translation typed in: French
        self.assertEqual(str(full), "💻 Digital & IA")
        self.assertEqual([t.slug for t in Expertise.objects.all()], ["digital", "export"])  # ordered by (order, slug)


class GenerateMatchesSynergyTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(is_published=True, title="Dîner", kind="dinner", location="Martigny",
                                          starts_at=timezone.now() + timedelta(days=5))
        self.alice = make_member("alice@example.com", first_name="Alice", sector="tech")
        self.bob = make_member("bob@example.com", first_name="Bob", sector="finance")
        self.carla = make_member("carla@example.com", first_name="Carla", sector="health")
        for member in (self.alice, self.bob, self.carla):
            RSVP.objects.create(event=self.event, member=member, status=RSVP.Status.YES)
        self.digital, self.export = theme("digital"), theme("export")

    def match(self, first, second):
        a, b = sorted((first.pk, second.pk))
        return Match.objects.get(event=self.event, member_a_id=a, member_b_id=b)

    def test_the_synergies_are_stored_as_helper_seeker_slug(self):
        save_expertise(self.alice, [self.digital], [self.export])
        save_expertise(self.bob, [self.export], [self.digital])
        generate_matches(self.event)
        self.assertCountEqual(self.match(self.alice, self.bob).synergies,
                              [[self.alice.pk, self.bob.pk, "digital"], [self.bob.pk, self.alice.pk, "export"]])
        self.assertEqual(self.match(self.alice, self.carla).synergies, [])
        # tech / finance / health: different sectors, no shared affinity, nobody is a newcomer
        self.assertEqual(self.match(self.alice, self.carla).score, WEIGHT_CROSS_SECTOR)
        self.assertEqual(self.match(self.alice, self.bob).score, WEIGHT_CROSS_SECTOR + 2 * WEIGHT_SYNERGY)

    def test_without_any_theme_nothing_changes(self):
        generate_matches(self.event)
        self.assertEqual(Match.objects.count(), 3)
        self.assertTrue(all(m.synergies == [] for m in Match.objects.all()))

    def test_people_who_already_met_get_no_synergy_introduction(self):
        save_expertise(self.alice, [self.digital], [])
        save_expertise(self.bob, [], [self.digital])
        Connection.link(self.alice, self.bob)
        generate_matches(self.event)
        a, b = sorted((self.alice.pk, self.bob.pk))
        self.assertFalse(Match.objects.filter(event=self.event, member_a_id=a, member_b_id=b).exists())


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SeededSynergyTests(TestCase):
    """The demo storyline: Camille and Lukas help each other, in both directions."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.camille = Member.objects.get(user__email="camille.rey@example.com")
        cls.lukas = Member.objects.get(user__email="lukas.imboden@example.com")
        cls.dinner = Event.objects.get(title="Dîner d'automne")

    def slugs(self, member, kind):
        return set(MemberExpertise.objects.filter(member=member, kind=kind).values_list("expertise__slug", flat=True))

    def test_fourteen_themes_in_three_languages(self):
        self.assertEqual(Expertise.objects.count(), 14)
        self.assertFalse(Expertise.objects.filter(Q(label_de="") | Q(label_en="")).exists())
        digital = Expertise.objects.get(slug="digital")
        self.assertEqual((digital.emoji, digital.label_fr, digital.label_de, digital.label_en),
                         ("💻", "Digital & IA", "Digitalisierung & KI", "Digital & AI"))

    def test_camille_and_lukas_are_a_synergy_in_both_directions(self):
        self.assertEqual((self.slugs(self.camille, OFFER), self.slugs(self.camille, NEED)), ({"digital"}, {"marche-alemanique"}))
        self.assertEqual((self.slugs(self.lukas, OFFER), self.slugs(self.lukas, NEED)), ({"marche-alemanique"}, {"digital"}))
        a, b = sorted((self.camille.pk, self.lukas.pk))
        match = Match.objects.get(event=self.dinner, member_a_id=a, member_b_id=b)
        self.assertCountEqual(match.synergies, [[self.camille.pk, self.lukas.pk, "digital"],
                                                [self.lukas.pk, self.camille.pk, "marche-alemanique"]])

    def test_lukas_stays_at_the_top_of_camilles_introductions(self):
        intros = intros_for(self.camille, self.dinner)
        self.assertEqual(len(intros), 3)
        self.assertEqual(intros[0]["other"], self.lukas)
        self.assertGreater(intros[0]["score"], intros[1]["score"])

    def test_every_other_member_has_one_or_two_offers_and_at_most_two_needs(self):
        for member in Member.objects.exclude(pk__in=[self.camille.pk, self.lukas.pk]):
            self.assertIn(len(self.slugs(member, OFFER)), (1, 2), member)
            self.assertLessEqual(len(self.slugs(member, NEED)), 2, member)
            self.assertFalse(self.slugs(member, OFFER) & self.slugs(member, NEED), member)

    def test_the_offers_are_coherent_with_the_sector(self):
        for member in Member.objects.exclude(pk__in=[self.camille.pk, self.lukas.pk]):
            allowed = set(demo_data.SECTOR_EXPERTISE[member.sector]) | ({"marche-alemanique"} if member.speaks_de else set())
            self.assertTrue(self.slugs(member, OFFER) <= allowed, (member, self.slugs(member, OFFER)))

    def test_the_help_themes_do_not_move_the_existing_draws(self):
        """Own generator for the themes: the connections (hence the 15 % index) are the same with or without them."""
        def connections():
            return sorted(Connection.objects.values_list("member_a__user__email", "member_b__user__email", "event_id"))

        with mock.patch.object(seed_demo.Command, "assign_expertise", lambda *args, **kwargs: None), \
                mock.patch.object(seed_demo.Command, "check_storyline", lambda *args, **kwargs: None):
            call_command("seed_demo", reset=True, stdout=StringIO())
        self.assertFalse(MemberExpertise.objects.exists())
        without_themes = connections()
        call_command("seed_demo", reset=True, stdout=StringIO())
        self.assertTrue(MemberExpertise.objects.exists())
        self.assertEqual(connections(), without_themes)

    def test_seeding_again_with_reset_recreates_the_same_themes(self):
        before = sorted(MemberExpertise.objects.values_list("member__user__email", "expertise__slug", "kind"))
        call_command("seed_demo", reset=True, stdout=StringIO())
        self.assertEqual(Expertise.objects.count(), 14)
        self.assertEqual(sorted(MemberExpertise.objects.values_list("member__user__email", "expertise__slug", "kind")), before)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SynergyDisplayTests(TestCase):
    """« Tes rencontres » shows the synergy as a discreet 🤝 line, on the home page (short) and on the event page."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.camille = Member.objects.get(user__email="camille.rey@example.com")
        cls.lukas = Member.objects.get(user__email="lukas.imboden@example.com")
        cls.dinner = Event.objects.get(title="Dîner d'automne")

    def page(self, name, *args, member=None, language=None):
        self.client.force_login((member or self.camille).user)
        if language:
            self.addCleanup(translation.activate, settings.LANGUAGE_CODE)
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
        response = self.client.get(reverse(name, args=args))
        self.assertEqual(response.status_code, 200)
        return response, unescape(response.content.decode())

    def test_intros_for_gives_the_synergies_as_the_member_sees_them(self):
        camille_view = next(i for i in intros_for(self.camille, self.dinner) if i["other"] == self.lukas)
        self.assertEqual([s["text"] for s in camille_view["synergies"]], [
            "Tu cherches « Marché alémanique » : Lukas peut t'aider.",
            "Lukas cherche « Digital & IA » : c'est ton domaine.",
        ])
        self.assertEqual([s["topic"].slug for s in camille_view["synergies"]], ["marche-alemanique", "digital"])
        lukas_view = next(i for i in intros_for(self.lukas, self.dinner) if i["other"] == self.camille)
        self.assertEqual([s["text"] for s in lukas_view["synergies"]], [
            "Tu cherches « Digital & IA » : Camille peut t'aider.",
            "Camille cherche « Marché alémanique » : c'est ton domaine.",
        ])

    def test_an_introduction_without_synergy_has_an_empty_list(self):
        without = [i for i in intros_for(self.camille, self.dinner) if i["other"] != self.lukas]
        self.assertTrue(any(i["synergies"] == [] for i in without))

    def test_home_shows_only_the_first_synergy(self):
        response, html = self.page("club:home")
        self.assertIn("Tu cherches « Marché alémanique » : Lukas peut t'aider.", html)
        self.assertNotIn("Lukas cherche « Digital & IA »", html)  # short version: the first one only
        self.assertIn("🤝", html)
        assert_csp_clean(self, response)

    def test_event_page_shows_every_synergy_under_the_affinities(self):
        response, html = self.page("club:event_detail", self.dinner.pk)
        self.assertIn("Tu cherches « Marché alémanique » : Lukas peut t'aider.", html)
        self.assertIn("Lukas cherche « Digital & IA » : c'est ton domaine.", html)
        self.assertLess(html.index("Vous aimez tous les deux"), html.index("Tu cherches « Marché alémanique »"))
        self.assertLess(html.index("Tu cherches « Marché alémanique »"), html.index("💬"))
        assert_csp_clean(self, response)

    def test_the_other_side_sees_it_too(self):
        _response, html = self.page("club:event_detail", self.dinner.pk, member=self.lukas)
        self.assertIn("Tu cherches « Digital & IA » : Camille peut t'aider.", html)
        self.assertIn("Camille cherche « Marché alémanique » : c'est ton domaine.", html)

    def test_the_topic_is_named_in_the_language_of_the_page(self):
        _response, german = self.page("club:event_detail", self.dinner.pk, language="de")
        self.assertIn("Deutschschweizer Markt", german)
        self.assertIn("Digitalisierung & KI", german)
        _response, english = self.page("club:event_detail", self.dinner.pk, language="en")
        self.assertIn("Swiss German market", english)
        self.assertIn("Digital & AI", english)

    def test_staff_sees_the_synergies_as_chips_in_the_list_of_introductions(self):
        self.client.force_login(make_staff("chef@example.com"))
        response = self.client.get(reverse("club:staff_event", args=[self.dinner.pk]))
        html = unescape(response.content.decode())
        self.assertIn("🤝 💻 Digital & IA", html)
        self.assertIn("🤝 🇨🇭 Marché alémanique", html)
        assert_csp_clean(self, response)


def chip(topic):
    """The pill a card shows for a theme, as it appears in the HTML (labels are escaped there)."""
    return f'<span class="chip">{topic.emoji} {escape(topic.label)}</span>'


class ThemesTestCase(TestCase):
    """Base: two members, five themes (in this display order), and Alice logged in."""

    def setUp(self):
        self.alice = make_member("alice@example.com", first_name="Alice", company="Alice SA")
        self.bob = make_member("bob@example.com", first_name="Bob", company="Bob SA")
        self.themes = {
            slug: theme(slug, label_fr=label_fr, label_de=label_de, label_en=label_en, emoji=emoji, order=order)
            for order, (slug, emoji, label_fr, label_de, label_en) in enumerate([
                ("digital", "💻", "Digital & IA", "Digitalisierung & KI", "Digital & AI"),
                ("marketing", "📣", "Marketing & communication", "Marketing & Kommunikation", "Marketing & communications"),
                ("financement", "💰", "Financement", "Finanzierung", "Funding"),
                ("export", "🌍", "Export & international", "Export & international", "Export & international"),
                ("logistique", "🚚", "Logistique & transport", "Logistik & Transport", "Logistics & transport"),
            ])
        }
        self.client.force_login(self.alice.user)

    def give(self, member, offers=(), needs=()):
        save_expertise(member, [self.themes[s] for s in offers], [self.themes[s] for s in needs])

    def slugs(self, member, kind):
        return set(MemberExpertise.objects.filter(member=member, kind=kind).values_list("expertise__slug", flat=True))

    def html(self, response):
        return unescape(response.content.decode())


class ProfileExpertiseTests(ThemesTestCase):
    """« 🧰 Je peux aider sur… » and « 🔎 Je cherche… » in the profile form: optional, 3 at most, mine only."""

    def setUp(self):
        super().setUp()
        self.url = reverse("club:profile_edit")

    def data(self, offers=(), needs=(), **extra):
        data = {
            "first_name": "Alice", "last_name": "Martin", "company": "Alice SA", "job_title": "CEO", "sector": "finance",
            "region": "Sion", "speaks_fr": "on", "fun_fact": "", "talk_to_me_about": "", "phone": "", "linkedin_url": "",
            "visible_in_directory": "on",
            "offers": [self.themes[s].pk for s in offers], "needs": [self.themes[s].pk for s in needs],
        }
        data.update(extra)
        return data

    def ticked(self, response, field):
        return {w.data["label"] for w in response.context["form"][field] if w.data["selected"]}

    def test_the_form_offers_both_groups_with_the_discreet_help_text(self):
        response = self.client.get(self.url)
        assert_csp_clean(self, response)
        html = self.html(response)
        for text in ("Entraide entre membres", "Je peux aider sur…", "Je cherche…", "🧰", "🔎",
                     "Facultatif, 3 au plus. C'est une porte ouverte, pas une vitrine commerciale."):
            self.assertIn(text, html)
        for field in ("offers", "needs"):
            self.assertEqual(html.count(f'name="{field}"'), 5)  # one checkbox per theme
        self.assertIn("💻 Digital & IA", html)
        self.assertIn("🚚 Logistique & transport", html)

    def test_my_current_themes_are_ticked(self):
        self.give(self.alice, offers=["digital", "export"], needs=["financement"])
        self.give(self.bob, offers=["logistique"], needs=["marketing"])
        response = self.client.get(self.url)
        self.assertEqual(self.ticked(response, "offers"), {"💻 Digital & IA", "🌍 Export & international"})
        self.assertEqual(self.ticked(response, "needs"), {"💰 Financement"})

    def test_posting_saves_my_themes_for_me_only(self):
        self.give(self.bob, offers=["logistique"], needs=["marketing"])
        response = self.client.post(self.url, self.data(offers=["digital", "marketing"], needs=["financement"]))
        self.assertRedirects(response, reverse("club:member_detail", args=[self.alice.pk]), fetch_redirect_response=False)
        self.assertEqual(self.slugs(self.alice, OFFER), {"digital", "marketing"})
        self.assertEqual(self.slugs(self.alice, NEED), {"financement"})
        self.assertEqual((self.slugs(self.bob, OFFER), self.slugs(self.bob, NEED)), ({"logistique"}, {"marketing"}))
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.last_name, "Martin")  # the rest of the profile is saved in the same step

    def test_three_themes_per_group_are_fine_and_replace_the_previous_ones(self):
        self.give(self.alice, offers=["digital"], needs=["export"])
        response = self.client.post(self.url, self.data(offers=["marketing", "financement", "export"],
                                                         needs=["digital", "logistique", "export"]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.slugs(self.alice, OFFER), {"marketing", "financement", "export"})
        self.assertEqual(self.slugs(self.alice, NEED), {"digital", "logistique", "export"})

    def test_a_fourth_theme_is_refused_with_a_clear_message_and_nothing_is_saved(self):
        self.give(self.alice, offers=["digital"])
        four = ["digital", "marketing", "financement", "export"]
        for field, kind_label, payload in (
            ("offers", "Je peux aider sur", {"offers": four}),
            ("needs", "Je cherche", {"needs": four}),
        ):
            response = self.client.post(self.url, self.data(company="Changée SA", **payload))
            self.assertEqual(response.status_code, 200, field)
            self.assertContains(response, 'role="alert"')
            self.assertIn(f"Choisis 3 thèmes au plus pour « {kind_label} ».", self.html(response), field)
            self.alice.refresh_from_db()
            self.assertEqual(self.alice.company, "Alice SA", field)  # nothing of the form was saved
            self.assertEqual((self.slugs(self.alice, OFFER), self.slugs(self.alice, NEED)), ({"digital"}, set()), field)

    def test_what_was_ticked_is_kept_when_the_form_is_shown_again(self):
        response = self.client.post(self.url, self.data(offers=["digital", "marketing", "financement", "export"], needs=["logistique"]))
        self.assertEqual(len(self.ticked(response, "offers")), 4)
        self.assertEqual(self.ticked(response, "needs"), {"🚚 Logistique & transport"})

    def test_an_unknown_theme_is_refused(self):
        response = self.client.post(self.url, self.data(offers=["digital"], needs=[]) | {"needs": [987654]})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="alert"')
        self.assertFalse(MemberExpertise.objects.exists())

    def test_unticking_everything_clears_my_themes(self):
        self.give(self.alice, offers=["digital", "export"], needs=["financement"])
        self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)
        self.assertFalse(MemberExpertise.objects.filter(member=self.alice).exists())

    def test_a_member_cannot_reach_the_themes_of_somebody_else(self):
        self.give(self.bob, offers=["logistique"], needs=["marketing"])
        before = sorted(MemberExpertise.objects.filter(member=self.bob).values_list("pk", "expertise__slug", "kind"))
        self.client.post(self.url, self.data(
            offers=["digital"], member=self.bob.pk, member_id=self.bob.pk, user=self.bob.user_id, pk=self.bob.pk,
            **{"expertise_links-0-member": self.bob.pk, "expertise_links-0-expertise": self.themes["export"].pk,
               "expertise_links-0-kind": "offer", "expertise_links-TOTAL_FORMS": "1"}))
        self.assertEqual(sorted(MemberExpertise.objects.filter(member=self.bob).values_list("pk", "expertise__slug", "kind")), before)
        self.assertEqual(self.slugs(self.alice, OFFER), {"digital"})

    def test_a_get_never_writes(self):
        self.client.get(self.url, {"offers": self.themes["digital"].pk, "needs": self.themes["export"].pk})
        self.assertFalse(MemberExpertise.objects.exists())

    def test_without_any_theme_in_the_database_the_section_is_simply_absent(self):
        Expertise.objects.all().delete()
        response = self.client.get(self.url)
        assert_csp_clean(self, response)
        self.assertNotContains(response, "Entraide entre membres")
        self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)

    def test_the_themes_are_named_in_german_and_english(self):
        self.addCleanup(translation.activate, settings.LANGUAGE_CODE)
        for language, expected in (("de", "💻 Digitalisierung & KI"), ("en", "💻 Digital & AI"), ("fr", "💻 Digital & IA")):
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
            response = self.client.get(self.url)
            self.assertIn(expected, self.html(response), language)


class CardExpertiseTests(ThemesTestCase):
    """The full card lists « Je peux aider sur » and « Je cherche »; the compact one at most 2 offers."""

    def setUp(self):
        super().setUp()
        self.give(self.bob, offers=["digital", "marketing", "financement"], needs=["export", "logistique"])

    def test_the_full_card_shows_both_lines_of_pills(self):
        response = self.client.get(reverse("club:member_detail", args=[self.bob.pk]))
        assert_csp_clean(self, response)
        html = response.content.decode()
        self.assertIn("Je peux aider sur", html)
        self.assertIn("Je cherche", html)
        for slug in ("digital", "marketing", "financement", "export", "logistique"):
            self.assertIn(chip(self.themes[slug]), html, slug)
        self.assertLess(html.index("Je peux aider sur"), html.index(chip(self.themes["digital"])))
        self.assertLess(html.index(chip(self.themes["financement"])), html.index("Je cherche"))

    def test_nothing_is_shown_when_nothing_is_filled_in(self):
        response = self.client.get(reverse("club:member_detail", args=[self.alice.pk]))
        self.assertNotContains(response, "Je peux aider sur")
        self.assertNotContains(response, "Je cherche")

    def test_each_line_only_appears_when_it_is_filled_in(self):
        url = reverse("club:member_detail", args=[self.alice.pk])
        self.give(self.alice, offers=["export"])
        html = self.client.get(url).content.decode()
        self.assertIn("Je peux aider sur", html)
        self.assertNotIn("Je cherche", html)
        self.give(self.alice, needs=["export"])
        html = self.client.get(url).content.decode()
        self.assertNotIn("Je peux aider sur", html)
        self.assertIn("Je cherche", html)

    def test_the_compact_card_shows_two_offers_at_most_and_no_needs(self):
        html = self.client.get(reverse("club:album")).content.decode()
        self.assertIn(chip(self.themes["digital"]), html)
        self.assertIn(chip(self.themes["marketing"]), html)
        self.assertNotIn(chip(self.themes["financement"]), html)  # the 3rd offer only shows on the full card
        self.assertNotIn(chip(self.themes["export"]), html)  # needs only show on the full card
        self.assertNotIn(chip(self.themes["logistique"]), html)
        self.assertIn("🧰", html)

    def test_the_card_of_an_attendee_on_the_event_page_shows_the_themes_too(self):
        event = Event.objects.create(is_published=True, title="Dîner", kind="dinner", location="Martigny",
                                     starts_at=timezone.now() + timedelta(days=5))
        for member in (self.alice, self.bob):
            RSVP.objects.create(event=event, member=member, status=RSVP.Status.YES)
        response = self.client.get(reverse("club:event_detail", args=[event.pk]))
        assert_csp_clean(self, response)
        self.assertIn(chip(self.themes["digital"]), response.content.decode())

    def test_the_album_does_not_query_the_themes_once_per_card(self):
        def album_queries():
            with CaptureQueriesContext(connection) as queries:
                self.assertEqual(self.client.get(reverse("club:album")).status_code, 200)
            return len(queries)

        few = album_queries()
        for number in range(10):
            member = make_member(f"extra{number}@example.com")
            self.give(member, offers=["digital", "export"], needs=["logistique"])
        self.assertEqual(album_queries(), few)

    def test_the_template_tag_costs_one_query_per_card_without_prefetch_and_none_with_it(self):
        template = Template('{% load club_ui %}{% expertise_with member "offer" as offers %}'
                            '{% expertise_with member "need" as needs %}{{ offers|length }}-{{ needs|length }}')
        member = Member.objects.get(pk=self.bob.pk)  # nothing prefetched on this instance
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(template.render(Context({"member": member})), "3-2")
        self.assertEqual(len(queries), 1)  # both lines at once, themes included
        member = Member.objects.prefetch_related("expertise_links__expertise").get(pk=self.bob.pk)
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(template.render(Context({"member": member})), "3-2")
        self.assertEqual(len(queries), 0)

    def test_the_themes_are_listed_in_display_order_whatever_the_order_they_were_picked_in(self):
        self.give(self.alice, offers=["logistique", "financement", "digital"])
        html = self.client.get(reverse("club:member_detail", args=[self.alice.pk])).content.decode()
        positions = [html.index(chip(self.themes[slug])) for slug in ("digital", "financement", "logistique")]
        self.assertEqual(positions, sorted(positions))

    def test_a_single_card_fetches_its_themes_in_a_constant_number_of_queries(self):
        url = reverse("club:member_detail", args=[self.bob.pk])

        def queries_for_the_card():
            with CaptureQueriesContext(connection) as queries:
                self.client.get(url)
            return len(queries)

        many = queries_for_the_card()
        save_expertise(self.bob, [self.themes["digital"]], [])
        self.assertEqual(queries_for_the_card(), many)


class AlbumHelpFilterTests(ThemesTestCase):
    """« Peut m'aider sur… » (?aide=<slug>): the members who offer the theme, other filters untouched."""

    def setUp(self):
        super().setUp()
        self.carla = make_member("carla@example.com", first_name="Carla", sector="finance", speaks_de=True)
        self.dan = make_member("dan@example.com", first_name="Dan", sector="tech")
        self.give(self.bob, offers=["digital"], needs=["financement"])
        self.give(self.carla, offers=["digital", "financement"])
        self.give(self.dan, offers=["export"], needs=["digital"])  # NEEDS digital: not somebody who can help on it

    def album(self, **params):
        response = self.client.get(reverse("club:album"), params)
        self.assertEqual(response.status_code, 200)
        return response

    def names(self, response):
        return sorted(m.first_name for m in response.context["members"])

    def test_without_the_filter_everybody_is_listed(self):
        self.assertEqual(self.names(self.album()), ["Bob", "Carla", "Dan"])

    def test_the_filter_keeps_the_members_who_offer_the_theme(self):
        self.assertEqual(self.names(self.album(aide="digital")), ["Bob", "Carla"])
        self.assertEqual(self.names(self.album(aide="financement")), ["Carla"])  # Bob only LOOKS for it
        self.assertEqual(self.names(self.album(aide="export")), ["Dan"])
        self.assertEqual(self.names(self.album(aide="logistique")), [])  # nobody offers it: an empty result, not an error

    def test_unknown_values_are_ignored_like_the_other_filters(self):
        for junk in ("<hack>", "xx", "digital' OR '1'='1", "DIGITAL"):
            self.assertEqual(self.names(self.album(aide=junk)), ["Bob", "Carla", "Dan"], junk)

    def test_the_existing_filters_still_work_and_combine_with_it(self):
        self.assertEqual(self.names(self.album(aide="digital", secteur="finance")), ["Carla"])
        self.assertEqual(self.names(self.album(aide="digital", langue="de")), ["Carla"])
        self.assertEqual(self.names(self.album(aide="digital", q="Bob")), ["Bob"])
        self.assertEqual(self.names(self.album(secteur="tech")), ["Bob", "Dan"])
        Connection.link(self.alice, self.bob)
        self.assertEqual(self.names(self.album(aide="digital", statut="album")), ["Bob"])
        self.assertEqual(self.names(self.album(aide="digital", statut="a-rencontrer")), ["Carla"])

    def test_the_select_lists_the_themes_and_keeps_the_choice(self):
        response = self.album(aide="export")
        assert_csp_clean(self, response)
        html = self.html(response)
        self.assertIn('name="aide"', html)
        self.assertIn("Peut m'aider sur…", html)
        for slug in self.themes:
            self.assertIn(f'<option value="{slug}"', html)
        self.assertIn('<option value="export" selected>', html)
        self.assertEqual(response.context["filters"]["help"], "export")

    def test_without_any_theme_the_filter_is_not_offered(self):
        Expertise.objects.all().delete()
        response = self.album()
        assert_csp_clean(self, response)
        self.assertNotContains(response, 'name="aide"')

    def test_hidden_cards_stay_hidden_whatever_they_offer(self):
        self.carla.visible_in_directory = False
        self.carla.save()
        self.assertEqual(self.names(self.album(aide="digital")), ["Bob"])
        Connection.link(self.alice, self.carla)
        self.assertEqual(self.names(self.album(aide="digital")), ["Bob", "Carla"])


class AdminExpertiseTests(ThemesTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = get_user_model().objects.create_superuser("admin@example.com", "admin@example.com", PASSWORD)
        self.client.force_login(self.superuser)
        self.url = reverse("admin:club_member_change", args=[self.bob.pk])

    def inline_data(self, rows):
        data = {"tag_links-TOTAL_FORMS": "0", "tag_links-INITIAL_FORMS": "0", "tag_links-MIN_NUM_FORMS": "0",
                "tag_links-MAX_NUM_FORMS": "1000", "expertise_links-TOTAL_FORMS": str(len(rows)),
                "expertise_links-INITIAL_FORMS": "0", "expertise_links-MIN_NUM_FORMS": "0", "expertise_links-MAX_NUM_FORMS": "1000"}
        for index, (slug, kind) in enumerate(rows):
            data[f"expertise_links-{index}-expertise"] = self.themes[slug].pk
            data[f"expertise_links-{index}-kind"] = kind
        return data

    def member_data(self, rows):
        data = {field.name: getattr(self.bob, field.name) for field in self.bob._meta.fields
                if not field.is_relation and field.name not in {"id", "photo", "created_at", "admitted_at", "guest_access_until"}}
        data.update(user=self.bob.user_id, **self.inline_data(rows))
        return data

    def test_the_member_page_has_the_inline_and_the_themes_page_lists_the_labels(self):
        self.give(self.bob, offers=["digital"])
        page = self.client.get(self.url)
        self.assertContains(page, "expertise_links-TOTAL_FORMS")
        changelist = self.client.get(reverse("admin:club_expertise_changelist"))
        self.assertEqual(changelist.status_code, 200)
        for label in ("Digital &amp; IA", "Digitalisierung &amp; KI", "Digital &amp; AI"):
            self.assertContains(changelist, label)
        self.assertContains(changelist, 'name="form-0-order"')  # the order is editable in the list

    def test_the_staff_can_set_up_to_three_themes_per_kind(self):
        rows = [("digital", "offer"), ("marketing", "offer"), ("export", "offer"),
                ("financement", "need"), ("logistique", "need"), ("digital", "need")]
        response = self.client.post(self.url, self.member_data(rows))
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["errors"])
        self.assertEqual(self.slugs(self.bob, OFFER), {"digital", "marketing", "export"})
        self.assertEqual(self.slugs(self.bob, NEED), {"financement", "logistique", "digital"})

    def test_a_fourth_theme_of_one_kind_is_refused_in_the_admin_too(self):
        rows = [("digital", "need"), ("marketing", "offer"), ("export", "offer"), ("financement", "offer"), ("logistique", "offer")]
        response = self.client.post(self.url, self.member_data(rows))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Choisis 3 thèmes au plus pour « Je peux aider sur ».", self.html(response))
        self.assertFalse(MemberExpertise.objects.exists())

    def test_the_same_theme_twice_in_the_same_kind_is_refused(self):
        response = self.client.post(self.url, self.member_data([("digital", "offer"), ("digital", "offer")]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MemberExpertise.objects.exists())
