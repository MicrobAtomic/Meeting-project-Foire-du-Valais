from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class EmailAuthenticationForm(AuthenticationForm):
    """Login with the e-mail address (stored lowercase as username), whatever the case typed."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("E-mail ou mot de passe incorrect."),
    }
    username = forms.CharField(label=_("E-mail"), widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()
