"""Shared profile visibility checks. Notes never grant visibility or contact access."""
from django.http import Http404
from django.shortcuts import get_object_or_404

from club.models import Connection, Member


def visible_target(viewer, pk):
    target = get_object_or_404(
        Member.objects.select_related("user").prefetch_related("tag_links__tag"),
        pk=pk, user__is_active=True,
    )
    if not target.visible_in_directory and target.pk != viewer.pk and not Connection.exists_between(viewer, target):
        raise Http404
    return target
