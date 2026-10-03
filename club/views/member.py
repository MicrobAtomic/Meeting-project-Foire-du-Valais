from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_http_methods

from club.decorators import member_required
from club.forms import MemberProfileForm
from club.models import RSVP, Connection, Event, Member, MemberTag, Sector, Tag
from club.services.events import current_event
from club.services.federation import club_stats, collected_ids, collection_progress
from club.services.intros import intros_for
from club.services.milestones import album_goal, club_progress
from club.services.profile import common_tags, save_tag_answers
from club.services.qr import qr_svg
from club.services.vcard import build_vcard

LANGUAGE_FIELDS = {"fr": "speaks_fr", "de": "speaks_de", "en": "speaks_en"}
STATUS_CHOICES = [
    ("toutes", gettext_lazy("Toutes les cartes")),
    ("album", gettext_lazy("Dans mon album")),
    ("a-rencontrer", gettext_lazy("À rencontrer")),
    ("nouveaux", gettext_lazy("Nouvelles recrues")),
]


@member_required
def home(request):
    collected, total = collection_progress(request.member)
    stats = club_stats()
    next_event = Event.objects.filter(starts_at__gte=timezone.now()).order_by("starts_at").first()
    answer = None
    next_intros = []
    if next_event:
        answer = RSVP.objects.filter(event=next_event, member=request.member).values_list("status", flat=True).first()
        if answer == RSVP.Status.YES:  # people who hide their card are never introduced
            next_intros = [i for i in intros_for(request.member, next_event) if i["other"].visible_in_directory]
    context = {
        "collected": collected,
        "total": total,
        "album_goal": album_goal(collected, total),
        "stats": stats,
        "club_progress": club_progress(stats),
        "next_event": next_event,
        "next_status": answer,
        "next_intros": next_intros,
    }
    return render(request, "club/home.html", context)


@member_required
def my_qr(request):
    url = request.build_absolute_uri(reverse("club:scan", args=[request.member.qr_token]))
    return render(request, "club/my_qr.html", {"qr_svg": qr_svg(url), "scan_url": url})


@member_required
def member_detail(request, pk):
    target = get_object_or_404(
        Member.objects.select_related("user").prefetch_related("tag_links__tag"), pk=pk, user__is_active=True
    )
    is_me = target.pk == request.member.pk
    connected = Connection.exists_between(request.member, target)
    if not target.visible_in_directory and not (is_me or connected):
        raise Http404
    context = {
        "target": target,
        "is_me": is_me,
        "connected": connected,
        "can_see_contact": is_me or connected,
        "card_collected": None if is_me else connected,  # None hides the "À rencontrer" footer on my own card
        "common": None if is_me else common_tags(request.member, target),
    }
    return render(request, "club/member_detail.html", context)


@member_required
def member_vcard(request, pk):
    target = get_object_or_404(Member.objects.select_related("user"), pk=pk, user__is_active=True)
    if target.pk != request.member.pk and not Connection.exists_between(request.member, target):
        raise PermissionDenied
    response = HttpResponse(build_vcard(target), content_type="text/vcard; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{slugify(target.full_name) or "contact"}.vcf"'
    return response


@member_required
@require_http_methods(["GET", "POST"])
def scan(request, token):
    """QR code target. GET only shows a confirmation (no side effect); POST (CSRF-protected) connects."""
    target = get_object_or_404(Member, qr_token=token, user__is_active=True)
    me = request.member
    if target.pk == me.pk:
        messages.info(request, _("C'est ta propre carte 😉"))
        return redirect("club:member_detail", pk=me.pk)
    if request.method == "POST":
        _connection, created = Connection.link(me, target, source=Connection.Source.QR, event=current_event())
        if created:
            messages.success(request, _("Carte ajoutée à ton album ! 🎉"))
        return redirect("club:member_detail", pk=target.pk)
    if Connection.exists_between(me, target):
        return redirect("club:member_detail", pk=target.pk)
    return render(request, "club/scan_confirm.html", {"target": target})


@member_required
def album(request):
    me = request.member
    collected = collected_ids(me)
    members = (
        Member.objects.filter(user__is_active=True)
        .filter(Q(visible_in_directory=True) | Q(pk__in=collected))  # a card already collected stays in the album
        .exclude(pk=me.pk)
        .select_related("user")
        .prefetch_related("tag_links__tag")
    )
    query = request.GET.get("q", "").strip()
    sector = request.GET.get("secteur", "")
    language = request.GET.get("langue", "")
    status = request.GET.get("statut", "toutes")
    if query:
        members = members.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(company__icontains=query)
        )
    if sector in Sector.values:
        members = members.filter(sector=sector)
    if language in LANGUAGE_FIELDS:
        members = members.filter(**{LANGUAGE_FIELDS[language]: True})
    if status == "album":
        members = members.filter(pk__in=collected)
    elif status == "a-rencontrer":
        members = members.exclude(pk__in=collected)
    elif status == "nouveaux":
        members = members.filter(member_since=timezone.localdate().year)
    members = list(members)
    context = {
        "members": members,
        "cards": [(m, m.pk in collected) for m in members],
        "collected": collected,
        "progress": collection_progress(me),
        "stats": club_stats(),
        "sectors": Sector.choices,
        "statuses": STATUS_CHOICES,
        "filters": {"q": query, "sector": sector, "language": language, "status": status},
    }
    return render(request, "club/album.html", context)


@member_required
@require_http_methods(["GET", "POST"])
def profile_edit(request):
    member = request.member  # always MY card, never an id taken from the URL
    if request.method == "POST":
        form = MemberProfileForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            save_tag_answers(member, request.POST)
            messages.success(request, _("Profil enregistré ✅"))
            return redirect("club:member_detail", pk=member.pk)
    else:
        form = MemberProfileForm(instance=member)
    answers = {link.tag.slug: link.sentiment for link in member.tag_links.select_related("tag")}
    if request.method == "POST":  # keep what was just ticked if the form has to be shown again
        for key, value in request.POST.items():
            if key.startswith("tag_") and value in MemberTag.Sentiment.values:
                answers[key[4:]] = value
    tags = list(Tag.objects.all())
    groups = []
    for value, label in Tag.Category.choices:
        items = [(tag, answers.get(tag.slug, MemberTag.Sentiment.NEUTRAL)) for tag in tags if tag.category == value]
        if items:
            groups.append((label, items))
    return render(request, "club/profile_edit.html", {"form": form, "groups": groups})


@member_required
@require_http_methods(["GET", "POST"])
def onboarding(request):
    """'Swipe tes affinités': one card per tag, answered like / neutral / dislike (progressively enhanced by swipe.js)."""
    member = request.member
    if request.method == "POST":
        save_tag_answers(member, request.POST)
        if not member.onboarding_done:
            member.onboarding_done = True
            member.save(update_fields=["onboarding_done"])
        messages.success(request, _("Profil complété 🎉"))
        return redirect("club:home")
    answers = {link.tag.slug: link.sentiment for link in member.tag_links.select_related("tag")}
    items = [(tag, answers.get(tag.slug, MemberTag.Sentiment.NEUTRAL)) for tag in Tag.objects.all()]
    return render(request, "club/onboarding.html", {"items": items})


@member_required
def invite(request):
    """My personal referral link (?ref=CODE), its QR code, the offer, and the people I invited."""
    me = request.member
    link = request.build_absolute_uri(reverse("club:join")) + "?ref=" + me.referral_code
    context = {
        "invite_link": link,
        "qr_svg": qr_svg(link),
        "referrals": me.referrals.order_by("-created_at"),
        "membership_price": settings.MEMBERSHIP_PRICE,
        "new_member_price": settings.REFERRAL_NEW_MEMBER_PRICE,
        "sponsor_discount": settings.REFERRAL_SPONSOR_DISCOUNT,
    }
    return render(request, "club/invite.html", context)
