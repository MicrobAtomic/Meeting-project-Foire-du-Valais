"""Presentation constants for member cards. Always FULL Tailwind class names (Tailwind scans this file)."""

from django.utils.translation import gettext_lazy as _

SECTOR_STYLE = {  # sector -> (emoji, avatar classes)
    "construction": ("🏗️", "bg-amber-500 text-white"),
    "finance": ("🏦", "bg-sky-700 text-white"),
    "tourism": ("🏨", "bg-teal-600 text-white"),
    "wine_food": ("🍇", "bg-rose-800 text-white"),
    "energy": ("⚡", "bg-yellow-400 text-stone-900"),
    "industry": ("🏭", "bg-stone-600 text-white"),
    "tech": ("💻", "bg-indigo-600 text-white"),
    "health": ("🩺", "bg-emerald-600 text-white"),
    "services": ("⚖️", "bg-slate-700 text-white"),
    "retail": ("🛍️", "bg-pink-600 text-white"),
    "transport": ("🚚", "bg-orange-600 text-white"),
    "media": ("📣", "bg-violet-600 text-white"),
    "other": ("🧩", "bg-stone-500 text-white"),
}

RANK_STYLE = {  # rank -> (label, card ring classes, badge classes)
    "founder": (_("Membre fondateur"), "ring-4 ring-amber-400", "bg-amber-400 text-stone-900"),
    "pillar": (_("Pilier du Club"), "ring-2 ring-stone-400", "bg-stone-700 text-white"),
    "member": (_("Membre"), "ring-1 ring-stone-200", "bg-stone-100 text-stone-700"),
    "newcomer": (_("Nouvelle recrue"), "ring-4 ring-emerald-400", "bg-emerald-500 text-white"),
}

EVENT_KIND_EMOJI = {"apero": "🥂", "dinner": "🍽️", "conference": "🎤", "visit": "🏭"}

ROUND_LABELS = [_("Entrée"), _("Plat"), _("Dessert"), _("Café")]  # tables tournantes: one label per service

GENERIC_ICEBREAKER = _("Demande-lui comment a commencé son aventure au Club.")


def round_label(index):
    return ROUND_LABELS[index] if index < len(ROUND_LABELS) else _("Service %(number)s") % {"number": index + 1}
