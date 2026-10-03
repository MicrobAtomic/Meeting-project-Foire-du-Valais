from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from club.models import (
    RSVP,
    Connection,
    Event,
    InvitationRequest,
    Match,
    Member,
    MemberTag,
    SeatAssignment,
    SeatingPlan,
    Tag,
    new_qr_token,
)
from club.services.auth_links import send_login_link
from club.forms import MemberAdminForm
from club.services.photos import save_profile_photo
from club.services.events import generate_matches, generate_seating
from club.ui import RANK_STYLE

admin.site.site_header = f"{settings.SITE_NAME} — administration"
admin.site.site_title = settings.SITE_NAME
admin.site.index_title = _("Club des Affaires")


class MemberTagInline(admin.TabularInline):
    model = MemberTag
    extra = 0
    autocomplete_fields = ["tag"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    form = MemberAdminForm
    list_display = ["full_name", "company", "sector", "member_since", "rank_display", "connections", "visible_in_directory"]
    list_filter = ["sector", "member_since", "is_founder", "speaks_de", "speaks_en", "visible_in_directory"]
    search_fields = ["first_name", "last_name", "company", "user__email"]
    readonly_fields = ["qr_token", "referral_code", "created_at"]
    autocomplete_fields = ["user"]
    inlines = [MemberTagInline]
    actions = ["send_login_links", "rotate_qr_token"]

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return fields if settings.PROFILE_PHOTO_UPLOADS_ENABLED else [field for field in fields if field not in ("photo", "remove_photo")]

    def save_model(self, request, obj, form, change):
        obj.photo = form.old_photo_name
        save_profile_photo(obj, form.cleaned_data.get("photo"), form.cleaned_data.get("remove_photo", False), form.old_photo_name)

    @admin.display(description=_("rang"))
    def rank_display(self, obj):
        return RANK_STYLE[obj.rank][0]

    @admin.display(description=_("rencontres"))
    def connections(self, obj):
        return Connection.involving(obj).count()

    @admin.action(description=_("Envoyer un lien de connexion"))
    def send_login_links(self, request, queryset):
        sent = 0
        for member in queryset.select_related("user"):
            if not member.user.is_active or not member.user.email:
                continue
            try:
                send_login_link(request, member)
                sent += 1
            except Exception as error:  # mail server down, bad SMTP settings…
                self.message_user(request, f"{member}: {error}", level=messages.ERROR)
        self.message_user(request, ngettext("%(count)s lien envoyé.", "%(count)s liens envoyés.", sent) % {"count": sent})

    @admin.action(description=_("Régénérer le QR code (l'ancien ne fonctionnera plus)"))
    def rotate_qr_token(self, request, queryset):
        for member in queryset:
            member.qr_token = new_qr_token()
            member.save(update_fields=["qr_token"])
        self.message_user(request, _("%(count)s QR code(s) régénéré(s).") % {"count": queryset.count()})


class RSVPInline(admin.TabularInline):
    model = RSVP
    extra = 0
    autocomplete_fields = ["member"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "starts_at", "location", "has_seating", "attendees"]
    list_filter = ["kind", "has_seating"]
    search_fields = ["title", "location"]
    date_hierarchy = "starts_at"
    inlines = [RSVPInline]
    actions = ["make_matches", "make_seating"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            yes_count=Count("rsvps", filter=Q(rsvps__status=RSVP.Status.YES))
        )

    @admin.display(description=_("inscrits"), ordering="yes_count")
    def attendees(self, obj):
        return obj.yes_count

    @admin.action(description=_("Générer « Tes 3 rencontres »"))
    def make_matches(self, request, queryset):
        for event in queryset:
            count = generate_matches(event)
            self.message_user(request, _("%(event)s : %(count)s rencontres générées.") % {"event": event, "count": count})

    @admin.action(description=_("Générer le plan de tables (3 services, tables de 6)"))
    def make_seating(self, request, queryset):
        for event in queryset:
            plan = generate_seating(event)
            self.message_user(
                request,
                _("%(event)s : %(new)s nouvelles paires, %(repeated)s répétition(s).")
                % {"event": event, "new": plan.new_pairs, "repeated": plan.repeated_pairs},
            )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["emoji", "label_fr", "label_de", "label_en", "category", "order"]
    list_editable = ["order"]
    list_filter = ["category"]
    search_fields = ["slug", "label_fr", "label_de", "label_en"]


class ConnectionAdminForm(forms.ModelForm):
    class Meta:
        model = Connection
        fields = ["member_a", "member_b", "event", "source", "created_at"]

    def clean(self):
        cleaned = super().clean()
        first, second = cleaned.get("member_a"), cleaned.get("member_b")
        if first and second:
            if first.pk == second.pk:
                raise forms.ValidationError(_("Choisis deux membres différents."))
            if first.pk > second.pk:  # the database stores each pair once, smallest id first
                cleaned["member_a"], cleaned["member_b"] = second, first
        return cleaned


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    form = ConnectionAdminForm
    list_display = ["member_a", "member_b", "event", "source", "created_at"]
    list_filter = ["source", "event"]
    search_fields = ["member_a__first_name", "member_a__last_name", "member_b__first_name", "member_b__last_name"]
    autocomplete_fields = ["member_a", "member_b"]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ["event", "member_a", "member_b", "score", "shared_likes", "shared_dislikes", "welcomes_newcomer"]
    list_filter = ["event", "welcomes_newcomer", "cross_sector"]
    search_fields = ["member_a__first_name", "member_a__last_name", "member_b__first_name", "member_b__last_name"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class SeatAssignmentInline(admin.TabularInline):
    model = SeatAssignment
    extra = 0
    can_delete = False
    readonly_fields = ["round_index", "table_number", "member"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SeatingPlan)
class SeatingPlanAdmin(admin.ModelAdmin):
    list_display = ["event", "rounds", "table_size", "new_pairs", "repeated_pairs", "updated_at"]
    readonly_fields = ["event", "rounds", "table_size", "new_pairs", "repeated_pairs", "updated_at"]
    inlines = [SeatAssignmentInline]

    def has_add_permission(self, request):
        return False


@admin.register(InvitationRequest)
class InvitationRequestAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "company", "email", "referred_by", "status", "created_at"]
    list_editable = ["status"]
    list_filter = ["status"]
    search_fields = ["first_name", "last_name", "company", "email"]
    autocomplete_fields = ["referred_by"]
