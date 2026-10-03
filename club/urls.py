from django.urls import path

from club.views import member, public, staff

app_name = "club"
urlpatterns = [
    path("", public.landing, name="landing"),
    path("accueil/", member.home, name="home"),
    path("moi/qr/", member.my_qr, name="my_qr"),
    path("membres/<int:pk>/", member.member_detail, name="member_detail"),
    path("membres/<int:pk>/vcard/", member.member_vcard, name="member_vcard"),
    path("m/<str:token>/", member.scan, name="scan"),
    path("staff/", staff.dashboard, name="staff_dashboard"),
]
