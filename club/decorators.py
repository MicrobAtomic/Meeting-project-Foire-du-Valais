from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from club.services.substitutions import member_access_valid


def member_required(view):
    """Logged-in user WITH a Member profile. Sets request.member. Staff without profile -> staff dashboard."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        member = getattr(request.user, "member", None)
        if member is None:
            if request.user.is_staff:
                return redirect("club:staff_dashboard")
            raise PermissionDenied
        request.member = member
        if not member_access_valid(member):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper
