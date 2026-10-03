from django import forms
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from club.models import EmailPreferences, InvitationRequest, Member, Substitute
from club.services.photos import normalize_member_photo, save_profile_photo


class EmailAuthenticationForm(AuthenticationForm):
    """Login with the e-mail address (stored lowercase as username), whatever the case typed."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("E-mail ou mot de passe incorrect."),
    }
    username = forms.CharField(label=_("E-mail"), widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class PhotoForm(forms.ModelForm):
    photo = forms.FileField(label=_("Photo de profil"), required=False, widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp,image/heic,image/heif,image/avif,.heic,.heif,.hif", "class": "input"}))
    remove_photo = forms.BooleanField(label=_("Retirer ma photo"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_photo_name = self.instance.photo.name or ""
        if not settings.PROFILE_PHOTO_UPLOADS_ENABLED:
            self.fields.pop("photo", None)
            self.fields.pop("remove_photo", None)

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        return normalize_member_photo(photo) if photo and not isinstance(photo, FieldFile) else None

    def clean(self):
        data = super().clean()
        if data.get("photo") and data.get("remove_photo"):
            raise forms.ValidationError(_("Choisis une nouvelle photo ou son retrait, pas les deux."))
        return data

    def save(self, commit=True):
        member = super().save(commit=False)
        member.photo = self.old_photo_name
        if commit:
            save_profile_photo(member, self.cleaned_data.get("photo"), self.cleaned_data.get("remove_photo", False), self.old_photo_name)
            self.save_m2m()
        return member


class MemberAdminForm(PhotoForm):
    class Meta:
        model = Member
        fields = "__all__"


class MemberProfileForm(PhotoForm):
    """What a member may edit about THEIR card. member_since, is_founder, qr_token, referral_code and user
    are deliberately absent: only the staff manages them (the form ignores them even if posted)."""

    class Meta:
        model = Member
        fields = [
            "first_name", "last_name", "company", "job_title", "sector", "region",
            "speaks_fr", "speaks_de", "speaks_en", "fun_fact", "talk_to_me_about",
            "phone", "linkedin_url", "visible_in_directory",
            "preferred_language", "digest_teaser",
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


class EmailPreferencesForm(forms.ModelForm):
    class Meta:
        model = EmailPreferences
        fields = ["event_announcements", "event_reminders", "monthly_digest", "allow_member_spotlight"]
        widgets = {field: forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-stone-300 text-red-700"})
                   for field in fields}


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


class SubstituteForm(forms.ModelForm):
    class Meta:
        model = Substitute
        fields = ["first_name", "last_name", "email", "job_title", "speaks_fr", "speaks_de", "speaks_en", "preferred_language"]
        labels = {"first_name": _("Prénom"), "last_name": _("Nom"), "email": _("E-mail"), "job_title": _("Fonction")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "h-5 w-5 rounded border-stone-300 text-red-700" if isinstance(field.widget, forms.CheckboxInput) else "input"

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        data = super().clean()
        if not any(data.get(key) for key in ("speaks_fr", "speaks_de", "speaks_en")):
            raise forms.ValidationError(_("Choisis au moins une langue parlée."))
        return data


class PersonalNoteForm(forms.Form):
    text = forms.CharField(label=_("Ma note personnelle"), required=False, max_length=2000,
                           widget=forms.Textarea(attrs={"class": "input", "rows": 4, "maxlength": 2000}))


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
