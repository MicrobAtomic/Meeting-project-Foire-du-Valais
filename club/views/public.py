from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render


@login_not_required
def landing(request):
    return render(request, "public/landing.html")
