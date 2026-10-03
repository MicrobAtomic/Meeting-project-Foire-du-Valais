from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Count
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
    NotificationCampaign,
    NotificationDelivery,
    SeatAssignment,
    SeatingPlan,
    Substitute,
    Tag,
    new_qr_token,
)
from club.services.auth_links import email_language, send_login_link
from club.forms import MemberAdminForm
from club.services.photos import photo_write_scope, save_profile_photo
from club.services.membership import accept_invitation
from club.services.notifications import cancel_event, publish_event, queue_welcome, retry_confirmed_failures
from club.services.substitutions import approve_substitute, cancel_substitute, member_access_valid
from club.services.events import attendees as event_attendees
from django.core.exceptions import ValidationError
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
    list_display = ["full_name", "company", "communication_language", "sector", "member_since", "rank_display", "connections", "visible_in_directory"]
    list_filter = ["sector", "member_since", "is_founder", "speaks_de", "speaks_en", "visible_in_directory"]
    search_fields = ["first_name", "last_name", "company", "user__email"]
    readonly_fields = ["qr_token", "referral_code", "created_at", "admitted_at", "kind", "guest_access_until"]
    autocomplete_fields = ["user"]
    inlines = [MemberTagInline]
    actions = ["send_login_links", "rotate_qr_token"]

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        with photo_write_scope():
            return super().changeform_view(request, object_id, form_url, extra_context)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return fields if settings.PROFILE_PHOTO_UPLOADS_ENABLED else [field for field in fields if field not in ("photo", "remove_photo")]

    def save_model(self, request, obj, form, change):
        obj.photo = form.old_photo_name
        save_profile_photo(obj, form.cleaned_data.get("photo"), form.cleaned_data.get("remove_photo", False), form.old_photo_name)

    @admin.display(description=_("rang"))
    def rank_display(self, obj):
        return RANK_STYLE[obj.rank][0]

    @admin.display(description=_("Langue des communications"))
    def communication_language(self, obj):
        return dict(Member._meta.get_field("preferred_language").choices)[email_language(obj)]

    @admin.display(description=_("rencontres"))
    def connections(self, obj):
        return Connection.involving(obj).count()

    @admin.action(description=_("Envoyer un lien de connexion"))
    def send_login_links(self, request, queryset):
        sent = 0
        for member in queryset.select_related("user"):
            if not member_access_valid(member) or not member.user.email:
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
    list_display = ["title", "kind", "starts_at", "location", "has_seating", "has_bingo", "is_published", "attendees"]
    readonly_fields = ["is_published", "published_at", "cancelled_at"]
    list_filter = ["kind", "has_seating", "has_bingo"]
    fieldsets = [  # one box per language: the members read the text of the language they chose
        (_("L'événement"), {"fields": ["kind", "starts_at", "rsvp_deadline"]}),
        ("Français (FR)", {
            "fields": ["title", "location", "description"],
            "description": _("La version de référence, obligatoire : elle s'affiche aussi quand une traduction manque."),
        }),
        ("Deutsch (DE)", {"fields": ["title_de", "location_de", "description_de"]}),
        ("English (EN)", {"fields": ["title_en", "location_en", "description_en"]}),
        (_("Animations"), {
            "fields": ["has_seating", "has_bingo"],
            "description": _("Tables tournantes pour un dîner assis, bingo des rencontres pour un apéro debout. "
                             "Le reste se prépare depuis Tableau de bord → Préparer."),
        }),
        (_("Publication"), {"fields": ["is_published", "published_at", "cancelled_at"]}),
    ]
    search_fields = ["title", "location"]
    date_hierarchy = "starts_at"
    inlines = [RSVPInline]
    actions = ["make_matches", "make_seating", "publish", "cancel"]

    @admin.action(description=_("Publier et préparer l'annonce"))
    def publish(self, request, queryset):
        for event in queryset:
            try:
                publish_event(event.pk, request.user)
                self.message_user(request, _("Annonce préparée. L'envoi est traité par la commande périodique."))
            except ValidationError as error:
                self.message_user(request, " ".join(error.messages), level=messages.ERROR)

    @admin.action(description=_("Annuler l'événement"))
    def cancel(self, request, queryset):
        for event in queryset:
            cancel_event(event.pk, request.user)
        self.message_user(request, _("Événement annulé. Contacte les inscrits via le processus habituel de l'équipe."))

    def get_queryset(self, request):
        return super().get_queryset(request)

    @admin.display(description=_("inscrits"))
    def attendees(self, obj):
        return event_attendees(obj).count()

    @admin.action(description=_("Générer « Tes 3 rencontres »"))
    def make_matches(self, request, queryset):
        for event in queryset:
            count = generate_matches(event)
            self.message_user(request, _("%(event)s : %(count)s rencontres générées.") % {"event": event, "count": count})

    @admin.action(description=_("Générer le plan de tables (3 services, tables de 6)"))
    def make_seating(self, request, queryset):
        for event in queryset:
            if not event.has_seating:  # a standing drinks has no tables to rotate
                self.message_user(request, _("%(event)s : pas de repas assis, pas de plan de tables.") % {"event": event}, level=messages.WARNING)
                continue
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
    readonly_fields = ["status", "member", "welcome_sent_at", "created_at"]
    actions = ["accept_requests", "mark_contacted", "mark_declined", "send_access"]
    list_filter = ["status"]
    search_fields = ["first_name", "last_name", "company", "email"]
    autocomplete_fields = ["referred_by"]

    @admin.action(description=_("Accepter et créer le compte"))
    def accept_requests(self, request, queryset):
        for invitation in queryset:
            try:
                accept_invitation(invitation.pk, request.user)
                self.message_user(request, _("Compte créé ou déjà lié à la demande."))
            except ValidationError as error:
                self.message_user(request, " ".join(error.messages), level=messages.ERROR)

    @admin.action(description=_("Marquer comme contactée"))
    def mark_contacted(self, request, queryset):
        queryset.exclude(status=InvitationRequest.Status.ACCEPTED).filter(member__isnull=True).update(status=InvitationRequest.Status.CONTACTED)

    @admin.action(description=_("Marquer comme refusée"))
    def mark_declined(self, request, queryset):
        queryset.exclude(status=InvitationRequest.Status.ACCEPTED).filter(member__isnull=True).update(status=InvitationRequest.Status.DECLINED)

    @admin.action(description=_("Préparer l'accès au compte accepté"))
    def send_access(self, request, queryset):
        for invitation in queryset.filter(status=InvitationRequest.Status.ACCEPTED, member__isnull=False).select_related("member__user"):
            if invitation.member.user.is_active:
                queue_welcome(invitation)
                self.message_user(request, _("Accès préparé dans la file d'emails."))


class ReadOnlyNotificationAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Substitute)
class SubstituteAdmin(ReadOnlyNotificationAdmin):
    list_display = ["full_name", "company", "event", "member", "guest", "status", "approved_at"]
    list_filter = ["status", "event"]
    actions = ["approve", "cancel"]

    @admin.action(description=_("Valider l'identité et l'accès du remplaçant"))
    def approve(self, request, queryset):
        for substitute in queryset:
            try:
                approve_substitute(substitute.pk, request.user)
                self.message_user(request, _("Remplacement validé, accès invité préparé."))
            except ValidationError as error:
                self.message_user(request, " ".join(error.messages), level=messages.ERROR)

    @admin.action(description=_("Annuler ou refuser le remplacement"))
    def cancel(self, request, queryset):
        for substitute in queryset.select_related("member"):
            try:
                cancel_substitute(substitute.event_id, substitute.member, actor=request.user)
                self.message_user(request, _("Remplacement annulé. Tu peux répondre de nouveau."))
            except ValidationError as error:
                self.message_user(request, " ".join(error.messages), level=messages.ERROR)


@admin.register(NotificationCampaign)
class NotificationCampaignAdmin(ReadOnlyNotificationAdmin):
    list_display = ["scope_key", "kind", "created_at", "cancelled_at", "delivery_counts"]
    list_filter = ["kind"]

    @admin.display(description=_("États des envois"))
    def delivery_counts(self, obj):
        return ", ".join(f"{row['status']}: {row['count']}" for row in obj.deliveries.values("status").annotate(count=Count("pk")))


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(ReadOnlyNotificationAdmin):
    list_display = ["campaign", "recipient", "status", "attempts", "next_attempt_at", "sent_at", "last_error_code"]
    list_filter = ["status", "campaign__kind"]
    actions = ["retry_failed"]

    @admin.action(description=_("Réessayer les échecs confirmés uniquement"))
    def retry_failed(self, request, queryset):
        retry_confirmed_failures(queryset)
        self.message_user(request, _("Échecs confirmés replanifiés. Les résultats incertains nécessitent une revue manuelle."))
