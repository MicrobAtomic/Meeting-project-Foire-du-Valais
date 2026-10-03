from django.shortcuts import render

from club.decorators import staff_required
from club.services.federation import club_stats


@staff_required
def dashboard(request):
    return render(request, "staff/dashboard.html", {"stats": club_stats()})
