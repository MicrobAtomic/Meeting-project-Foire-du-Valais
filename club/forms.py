from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from club.models import InvitationRequest, Member


class EmailAuthenticationForm(AuthenticationForm):
    """Login with the e-mail address (stored lowercase as username), whatever the case typed."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("E-mail ou mot de passe incorrect."),
    }
    username = forms.CharField(label=_("E-mail"), widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class MemberProfileForm(forms.ModelForm):
    """What a member may edit about THEIR card. member_since, is_founder, qr_token, referral_code and user
    are deliberately absent: only the staff manages them (the form ignores them even if posted)."""

    class Meta:
        model = Member
        fields = [
            "first_name", "last_name", "company", "job_title", "sector", "region",
            "speaks_fr", "speaks_de", "speaks_en", "fun_fact", "talk_to_me_about",
            "phone", "linkedin_url", "visible_in_directory",
        ]
        labels = {
            "first_name": _("Prénom"),
            "last_name": _("Nom"),
            "company": _("Entreprise"),
            "job_title": _("Fonction"),
            "sector": _("Secteur"),
            "region": _("Région"),
            "speaks_fr": _("Français"),
            "speaks_de": _("Allemand"),
            "speaks_en": _("Anglais"),
            "fun_fact": _("Une anecdote sur toi"),
            "talk_to_me_about": _("Parle-moi de…"),
            "phone": _("Téléphone"),
            "linkedin_url": _("Profil LinkedIn"),
            "visible_in_directory": _("Apparaître dans l'album du Club"),
        }
        help_texts = {
            "fun_fact": _("Elle servira de phrase d'accroche aux autres membres."),
            "talk_to_me_about": _("Un sujet dont tu adores parler."),
            "phone": _("Visible uniquement par les membres que tu as rencontrés."),
            "linkedin_url": _("Visible uniquement par les membres que tu as rencontrés."),
            "visible_in_directory": _("Si tu décoches, seuls les membres que tu as déjà rencontrés pourront voir ta carte."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "h-5 w-5 rounded border-stone-300 text-red-700 focus:ring-red-700"
            else:
                field.widget.attrs["class"] = "input"
        self.fields["region"].widget.attrs["placeholder"] = "Martigny, Sion, Brig…"
        self.fields["phone"].widget.input_type = "tel"
        self.fields["phone"].widget.attrs.update({"autocomplete": "tel", "placeholder": "+41 79 000 00 00"})
        self.fields["linkedin_url"].widget.attrs["placeholder"] = "https://www.linkedin.com/in/…"


class InvitationRequestForm(forms.ModelForm):
    """Public mini-form 'Demander une invitation'. `website` is a honeypot: humans never see it, bots fill it."""

    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = InvitationRequest
        fields = ["first_name", "last_name", "email", "company", "job_title"]
        labels = {
            "first_name": _("Prénom"),
            "last_name": _("Nom"),
            "email": _("E-mail"),
            "company": _("Entreprise"),
            "job_title": _("Poste"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "website":
                field.widget.attrs["class"] = "input"
        self.fields["first_name"].widget.attrs.update({"autocomplete": "given-name", "autofocus": True})
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "autocapitalize": "none"})
        self.fields["company"].widget.attrs["autocomplete"] = "organization"
        self.fields["job_title"].widget.attrs["autocomplete"] = "organization-title"

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    @property
    def is_bot(self):
        return bool(self.cleaned_data.get("website"))


class SeatingForm(forms.Form):
    """Settings of the rotating tables (staff). Tables of 6 over 3 services is the tested sweet spot."""

    rounds = forms.IntegerField(label=_("Nombre de services"), min_value=1, max_value=4, initial=3)
    table_size = forms.IntegerField(label=_("Places par table"), min_value=4, max_value=10, initial=6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class MagicLinkRequestForm(forms.Form):
    email = forms.EmailField(
        label=_("E-mail"),
        widget=forms.EmailInput(attrs={"class": "input", "autocomplete": "email", "autocapitalize": "none", "autofocus": True}),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
