from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from club.decorators import member_required
from club.models import Connection, Member
from club.services.events import current_event
from club.services.federation import collection_progress
from club.services.qr import qr_svg
from club.services.vcard import build_vcard


@member_required
def home(request):
    collected, total = collection_progress(request.member)
    return render(request, "club/home.html", {"collected": collected, "total": total})


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
    context = {"target": target, "is_me": is_me, "connected": connected, "can_see_contact": is_me or connected}
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
