from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path
from django.views.i18n import set_language
from sesame.views import LoginView as MagicLinkLoginView

from club.forms import EmailAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("connexion/", auth_views.LoginView.as_view(authentication_form=EmailAuthenticationForm, redirect_authenticated_user=True), name="login"),
    path("connexion/lien/", login_not_required(MagicLinkLoginView.as_view()), name="magic_login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("i18n/setlang/", login_not_required(set_language), name="set_language"),
    path("", include("club.urls")),
]
