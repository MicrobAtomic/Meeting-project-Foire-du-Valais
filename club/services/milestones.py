"""Paliers: a visible next goal makes members want to meet — for the whole Club (federation index) and for each
member's album. The rewards are proposals to validate with the committee: change them here."""

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class Milestone:
    percent: int  # federation index to reach
    emoji: str
    title: str
    reward: str

    @property
    def ratio(self):
        return self.percent / 100


CLUB_MILESTONES = [
    Milestone(10, "🌱", _("Les premiers liens"), _("Le Club fait connaissance.")),
    Milestone(20, "🥂", _("La tournée du Club"), _("Une tournée de Petite Arvine offerte au prochain apéro.")),
    Milestone(35, "🧀", _("La raclette des membres"), _("Une raclette au feu de bois offerte à tout le Club.")),
    Milestone(50, "🍾", _("La cuvée du Club"), _("Une cuvée spéciale, avec le nom de chaque membre sur l'étiquette.")),
    Milestone(75, "🏔️", _("La sortie au sommet"), _("Une sortie surprise en montagne pour tout le Club.")),
    Milestone(100, "🎉", _("Plus jamais d'inconnus"), _("Tout le monde se connaît : la grande fête du Club.")),
]

ALBUM_GOALS = [(5, "🥉"), (15, "🥈"), (30, "🥇")]  # cards collected; the full album (💎) comes last


def connections_needed(percent: int, members: int) -> int:
    """Connections needed for the federation index to reach `percent` (integer arithmetic: no 0.2 * 1225 = 245.0000001)."""
    pairs = members * (members - 1) // 2
    return -(-percent * pairs // 100)


def club_progress(stats: dict) -> dict:
    """Milestones of the Club: one progress segment per milestone, the last one reached, the next one and
    how many connections it still needs. Welcoming new members lowers the index: there are new people to meet."""
    members, connections = stats["members"], stats["connections"]
    segments, current, upcoming, remaining, lower = [], None, None, 0, 0
    for milestone in CLUB_MILESTONES:
        needed = connections_needed(milestone.percent, members)
        reached = members > 1 and connections >= needed
        if reached:
            fill = 1.0
            current = milestone
        else:
            fill = min(max((stats["index"] * 100 - lower) / (milestone.percent - lower), 0.0), 1.0)
            if upcoming is None:
                upcoming, remaining = milestone, needed - connections
        segments.append({"milestone": milestone, "fill": fill, "reached": reached, "is_next": milestone is upcoming})
        lower = milestone.percent
    return {"segments": segments, "current": current, "next": upcoming, "remaining": remaining}


def album_goal(collected: int, total: int) -> dict | None:
    """Next personal goal: 5, 15 and 30 cards, then the full album. None once the album is complete."""
    goals = [(target, emoji) for target, emoji in ALBUM_GOALS if target < total] + [(total, "💎")]
    for target, emoji in goals:
        if collected < target:
            return {"target": target, "emoji": emoji, "remaining": target - collected, "full_album": target == total}
    return None
