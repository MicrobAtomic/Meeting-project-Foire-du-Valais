from django.urls import path

from club.views import events, member, public, staff

app_name = "club"
urlpatterns = [
    path("", public.landing, name="landing"),
    path("connexion/recevoir-un-lien/", public.magic_link_request, name="magic_link_request"),
    path("rejoindre/", public.join, name="join"),
    path("rejoindre/merci/", public.join_thanks, name="join_thanks"),
    path("emails/desabonnement/<str:token>/", public.email_unsubscribe, name="email_unsubscribe"),
    path("accueil/", member.home, name="home"),
    path("bienvenue/", member.onboarding, name="onboarding"),
    path("album/", member.album, name="album"),
    path("moi/", member.profile_edit, name="profile_edit"),
    path("moi/photo/apercu/", member.profile_photo_preview, name="profile_photo_preview"),
    path("moi/qr/", member.my_qr, name="my_qr"),
    path("moi/inviter/", member.invite, name="invite"),
    path("membres/<int:pk>/", member.member_detail, name="member_detail"),
    path("membres/<int:pk>/note/", member.member_note, name="member_note"),
    path("membres/<int:pk>/photo/", member.member_photo, name="member_photo"),
    path("membres/<int:pk>/vcard/", member.member_vcard, name="member_vcard"),
    path("evenements/", events.event_list, name="event_list"),
    path("evenements/<int:pk>/", events.event_detail, name="event_detail"),
    path("evenements/<int:pk>/rsvp/", events.event_rsvp, name="event_rsvp"),
    path("evenements/<int:pk>/remplacant/", events.member_substitute, name="member_substitute"),
    path("evenements/<int:pk>/remplacant/annuler/", events.member_substitute_cancel, name="member_substitute_cancel"),
    path("m/<str:token>/", member.scan, name="scan"),
    path("staff/", staff.dashboard, name="staff_dashboard"),
    path("staff/evenements/<int:pk>/", staff.event_tools, name="staff_event"),
    path("staff/evenements/<int:pk>/badges/", staff.badges, name="staff_badges"),
]
