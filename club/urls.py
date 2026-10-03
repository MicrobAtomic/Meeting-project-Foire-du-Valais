from django.urls import path

from club.views import events, member, public, staff

app_name = "club"
urlpatterns = [
    path("", public.landing, name="landing"),
    path("accueil/", member.home, name="home"),
    path("album/", member.album, name="album"),
    path("moi/", member.profile_edit, name="profile_edit"),
    path("moi/qr/", member.my_qr, name="my_qr"),
    path("membres/<int:pk>/", member.member_detail, name="member_detail"),
    path("membres/<int:pk>/vcard/", member.member_vcard, name="member_vcard"),
    path("evenements/", events.event_list, name="event_list"),
    path("evenements/<int:pk>/", events.event_detail, name="event_detail"),
    path("evenements/<int:pk>/rsvp/", events.event_rsvp, name="event_rsvp"),
    path("m/<str:token>/", member.scan, name="scan"),
    path("staff/", staff.dashboard, name="staff_dashboard"),
]
