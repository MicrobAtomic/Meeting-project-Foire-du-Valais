import secrets

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


def new_qr_token():
    return secrets.token_urlsafe(16)  # 128 random bits: impossible to guess or enumerate


def new_referral_code():
    return secrets.token_hex(4).upper()


class Sector(models.TextChoices):
    CONSTRUCTION = "construction", _("Construction & immobilier")
    FINANCE = "finance", _("Banque, finance & assurance")
    TOURISM = "tourism", _("Tourisme & hôtellerie")
    WINE_FOOD = "wine_food", _("Vins & agroalimentaire")
    ENERGY = "energy", _("Énergie & environnement")
    INDUSTRY = "industry", _("Industrie & artisanat")
    TECH = "tech", _("Tech & digital")
    HEALTH = "health", _("Santé")
    SERVICES = "services", _("Conseil, juridique & fiduciaire")
    RETAIL = "retail", _("Commerce & distribution")
    TRANSPORT = "transport", _("Transport & logistique")
    MEDIA = "media", _("Communication & médias")
    OTHER = "other", _("Autre secteur")  # accounts created from an invitation request, until the member picks theirs


class Member(models.Model):
    RANK_FOUNDER = "founder"
    RANK_PILLAR = "pillar"
    RANK_MEMBER = "member"
    RANK_NEWCOMER = "newcomer"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member")
    first_name = models.CharField(_("prénom"), max_length=80)
    last_name = models.CharField(_("nom"), max_length=80)
    company = models.CharField(_("entreprise"), max_length=120)
    job_title = models.CharField(_("fonction"), max_length=120)
    sector = models.CharField(_("secteur"), max_length=20, choices=Sector.choices)
    region = models.CharField(_("région"), max_length=80, blank=True)
    speaks_fr = models.BooleanField(_("parle français"), default=True)
    speaks_de = models.BooleanField(_("parle allemand"), default=False)
    speaks_en = models.BooleanField(_("parle anglais"), default=False)
    member_since = models.PositiveSmallIntegerField(
        _("membre depuis (année)"),
        help_text=_("Année d'entrée au Club. Elle donne le rang : nouvelle recrue la première année, pilier après 5 ans."),
    )
    is_founder = models.BooleanField(
        _("membre fondateur"), default=False, help_text=_("Membre depuis la création du Club : bordure dorée sur sa carte.")
    )
    fun_fact = models.CharField(_("anecdote"), max_length=200, blank=True)
    talk_to_me_about = models.CharField(_("parle-moi de…"), max_length=120, blank=True)
    phone = models.CharField(_("téléphone"), max_length=30, blank=True)
    linkedin_url = models.URLField(_("LinkedIn"), blank=True)
    visible_in_directory = models.BooleanField(
        _("visible dans l'album"), default=True, help_text=_("Décoché : seuls les membres déjà rencontrés voient sa carte.")
    )
    onboarding_done = models.BooleanField(
        _("profil complété"), default=False, help_text=_("Coché automatiquement quand le membre a choisi ses affinités.")
    )
    qr_token = models.CharField(max_length=32, unique=True, default=new_qr_token, editable=False)
    referral_code = models.CharField(max_length=12, unique=True, default=new_referral_code, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    demo_photo_key = models.CharField(max_length=32, blank=True, editable=False)
    photo = models.ImageField(upload_to="member_photos/", blank=True)
    preferred_language = models.CharField(_("Langue des emails"), max_length=2, choices=[("fr", _("Français")), ("de", _("Allemand")), ("en", _("Anglais"))], blank=True)
    admitted_at = models.DateTimeField(null=True, blank=True, editable=False)
    digest_teaser = models.CharField(_("Accroche pour le récapitulatif"), max_length=120, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = _("membre")

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        return (self.first_name[:1] + self.last_name[:1]).upper()

    @property
    def languages(self):
        return frozenset(
            code for code, spoken in (("fr", self.speaks_fr), ("de", self.speaks_de), ("en", self.speaks_en)) if spoken
        )

    @property
    def seniority_years(self):
        return max(0, timezone.localdate().year - self.member_since)

    @property
    def rank(self):
        if self.is_founder:
            return self.RANK_FOUNDER
        if self.seniority_years >= 5:
            return self.RANK_PILLAR
        if self.seniority_years == 0:
            return self.RANK_NEWCOMER
        return self.RANK_MEMBER


class EmailPreferences(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="email_preferences")
    event_announcements = models.BooleanField(_("Annonces des événements"), default=True)
    event_reminders = models.BooleanField(_("Relances sans réponse"), default=True)
    monthly_digest = models.BooleanField(_("Récapitulatif mensuel des nouveaux membres"), default=False)
    allow_member_spotlight = models.BooleanField(_("Autoriser ma présentation dans le récapitulatif"), default=False)


class PersonalNote(models.Model):
    owner = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="personal_notes")
    target = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notes_about")
    text = models.TextField(max_length=2000)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "target"], name="unique_personal_note"),
            models.CheckConstraint(condition=~Q(owner=F("target")), name="personal_note_not_self"),
        ]


class Tag(models.Model):
    class Category(models.TextChoices):
        HOBBY = "hobby", _("Loisirs")
        VALAIS = "valais", _("Valais & terroir")
        CULTURE = "culture", _("Culture & curiosités")
        WORK = "work", _("Vie de bureau")

    slug = models.SlugField(unique=True)
    emoji = models.CharField(max_length=8)
    category = models.CharField(max_length=10, choices=Category.choices)
    label_fr = models.CharField(max_length=80)
    label_de = models.CharField(max_length=80, blank=True)
    label_en = models.CharField(max_length=80, blank=True)
    icebreaker_fr = models.CharField(max_length=200, blank=True)
    icebreaker_de = models.CharField(max_length=200, blank=True)
    icebreaker_en = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "slug"]
        verbose_name = _("affinité")

    def __str__(self):
        return f"{self.emoji} {self.label_fr}"

    def _localized(self, field):
        lang = (get_language() or "fr")[:2]
        return getattr(self, f"{field}_{lang}", "") or getattr(self, f"{field}_fr")

    @property
    def label(self):
        return self._localized("label")

    @property
    def icebreaker(self):
        return self._localized("icebreaker")


class MemberTag(models.Model):
    class Sentiment(models.TextChoices):
        LIKE = "like", _("J'adore")
        NEUTRAL = "neutral", _("Bof")
        DISLIKE = "dislike", _("Je déteste")

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="tag_links")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="member_links")
    sentiment = models.CharField(max_length=8, choices=Sentiment.choices)

    class Meta:
        verbose_name = _("affinité du membre")
        verbose_name_plural = _("affinités du membre")
        constraints = [models.UniqueConstraint(fields=["member", "tag"], name="unique_member_tag")]


class Event(models.Model):
    class Kind(models.TextChoices):
        APERO = "apero", _("Apéro")
        DINNER = "dinner", _("Dîner / soirée")
        CONFERENCE = "conference", _("Conférence")
        VISIT = "visit", _("Visite")

    # Texts in French (the reference) + optional German and English versions: an empty translation shows the French.
    title = models.CharField(_("titre"), max_length=150)
    title_de = models.CharField(_("titre (allemand)"), max_length=150, blank=True, help_text=_("Facultatif : vide, le texte français s'affiche."))
    title_en = models.CharField(_("titre (anglais)"), max_length=150, blank=True, help_text=_("Facultatif : vide, le texte français s'affiche."))
    kind = models.CharField(_("type"), max_length=12, choices=Kind.choices)
    starts_at = models.DateTimeField(_("début"))
    is_published = models.BooleanField(_("Publié"), default=False, editable=False)
    published_at = models.DateTimeField(null=True, blank=True, editable=False)
    cancelled_at = models.DateTimeField(null=True, blank=True, editable=False)
    rsvp_deadline = models.DateTimeField(_("Fin des réponses"), null=True, blank=True)
    location = models.CharField(_("lieu"), max_length=150)
    location_de = models.CharField(_("lieu (allemand)"), max_length=150, blank=True, help_text=_("Facultatif : vide, le texte français s'affiche."))
    location_en = models.CharField(_("lieu (anglais)"), max_length=150, blank=True, help_text=_("Facultatif : vide, le texte français s'affiche."))
    description = models.TextField(_("description"), blank=True, help_text=_("Visible par les membres sur la page de l'événement."))
    description_de = models.TextField(_("description (allemand)"), blank=True, help_text=_("Facultatif : vide, le texte français s'affiche."))
    description_en = models.TextField(_("description (anglais)"), blank=True, help_text=_("Facultatif : vide, le texte français s'affiche."))
    has_seating = models.BooleanField(
        _("repas assis (tables tournantes)"),
        default=False,
        help_text=_("Pour un dîner assis : l'équipe génère un plan où chacun change de table à chaque service (Tableau de bord → Préparer)."),
    )
    has_bingo = models.BooleanField(
        _("bingo des rencontres"),
        default=False,
        help_text=_("Préparation du bingo : le modèle est disponible, le jeu n'est pas encore activé dans l'application."),
    )

    class Meta:
        ordering = ["starts_at"]
        verbose_name = _("événement")

    def __str__(self):
        return self.localized_title

    def _localized(self, field):
        """The text in the active language (de / en) when it was typed in, else the French one."""
        language = (get_language() or "fr")[:2]
        return (language != "fr" and getattr(self, f"{field}_{language}", "")) or getattr(self, field)

    @property
    def localized_title(self):
        return self._localized("title")

    @property
    def localized_location(self):
        return self._localized("location")

    @property
    def localized_description(self):
        return self._localized("description")

    @property
    def is_past(self):
        return self.starts_at < timezone.now()

    @property
    def responses_open(self):
        now = timezone.now()
        return self.is_published and not self.cancelled_at and now < min(self.rsvp_deadline or self.starts_at, self.starts_at)


class RSVP(models.Model):
    class Status(models.TextChoices):
        YES = "yes", _("Je viens")
        NO = "no", _("Je ne viens pas")

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="rsvps")
    status = models.CharField(_("réponse"), max_length=3, choices=Status.choices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("inscription")
        constraints = [models.UniqueConstraint(fields=["event", "member"], name="unique_rsvp")]


class Connection(models.Model):
    """Two members who met in person. Stored once per pair, always with member_a.pk < member_b.pk."""

    class Source(models.TextChoices):
        QR = "qr", _("Scan QR")
        ADMIN = "admin", _("Ajout admin")
        SEED = "seed", _("Données de démo")

    member_a = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="+")
    member_b = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="+")
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="connections")
    source = models.CharField(max_length=5, choices=Source.choices, default=Source.QR)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("rencontre")
        constraints = [
            models.UniqueConstraint(fields=["member_a", "member_b"], name="unique_connection"),
            models.CheckConstraint(condition=Q(member_a__lt=F("member_b")), name="connection_ordered_pair"),
        ]

    @classmethod
    def link(cls, first, second, *, source=Source.QR, event=None):
        if first.pk == second.pk:
            raise ValueError("A member cannot connect with themselves.")
        a, b = (first, second) if first.pk < second.pk else (second, first)
        return cls.objects.get_or_create(member_a=a, member_b=b, defaults={"source": source, "event": event})

    @classmethod
    def exists_between(cls, first, second):
        if first.pk == second.pk:
            return False
        a, b = sorted((first.pk, second.pk))
        return cls.objects.filter(member_a_id=a, member_b_id=b).exists()

    @classmethod
    def involving(cls, member):
        return cls.objects.filter(Q(member_a=member) | Q(member_b=member))


class Match(models.Model):
    """'Tes 3 rencontres': introduction proposed to two attendees of an event."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="matches")
    member_a = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="+")
    member_b = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="+")
    score = models.IntegerField()
    shared_likes = models.JSONField(default=list)
    shared_dislikes = models.JSONField(default=list)
    cross_sector = models.BooleanField(default=False)
    welcomes_newcomer = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("rencontre proposée")
        verbose_name_plural = _("rencontres proposées")
        constraints = [
            models.UniqueConstraint(fields=["event", "member_a", "member_b"], name="unique_match"),
            models.CheckConstraint(condition=Q(member_a__lt=F("member_b")), name="match_ordered_pair"),
        ]

    def other(self, member):
        return self.member_b if member.pk == self.member_a_id else self.member_a


class SeatingPlan(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="seating_plan")
    rounds = models.PositiveSmallIntegerField(default=3)
    table_size = models.PositiveSmallIntegerField(default=6)
    new_pairs = models.PositiveIntegerField(default=0)
    repeated_pairs = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("plan de tables")
        verbose_name_plural = _("plans de tables")


class SeatAssignment(models.Model):
    plan = models.ForeignKey(SeatingPlan, on_delete=models.CASCADE, related_name="assignments")
    round_index = models.PositiveSmallIntegerField()
    table_number = models.PositiveSmallIntegerField()
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="seats")

    class Meta:
        ordering = ["round_index", "table_number"]
        constraints = [
            models.UniqueConstraint(fields=["plan", "round_index", "member"], name="unique_seat_per_round"),
        ]


class InvitationRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", _("Nouvelle")
        CONTACTED = "contacted", _("Contactée")
        ACCEPTED = "accepted", _("Acceptée")
        DECLINED = "declined", _("Refusée")

    first_name = models.CharField(_("prénom"), max_length=80)
    last_name = models.CharField(_("nom"), max_length=80)
    company = models.CharField(_("entreprise"), max_length=120)
    job_title = models.CharField(_("fonction"), max_length=120)
    email = models.EmailField(_("e-mail"))
    message = models.TextField(_("message"), blank=True)
    language = models.CharField(_("langue"), max_length=2, choices=settings.LANGUAGES, default="fr")
    referred_by = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals", verbose_name=_("parrain ou marraine")
    )
    status = models.CharField(
        _("statut"),
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
        help_text=_("L'action d'acceptation crée le compte. L'accès est envoyé par lien de connexion, sans choix de mot de passe."),
    )
    member = models.OneToOneField(
        Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="invitation_request", verbose_name=_("compte créé")
    )
    welcome_sent_at = models.DateTimeField(_("e-mail de bienvenue envoyé le"), null=True, blank=True)
    created_at = models.DateTimeField(_("reçue le"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("demande d'invitation")
        verbose_name_plural = _("demandes d'invitation")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.company})"


class NotificationCampaign(models.Model):
    class Kind(models.TextChoices):
        WELCOME = "welcome", _("Bienvenue")
        ANNOUNCEMENT = "event_announcement", _("Annonce")
        REMINDER = "event_reminder", _("Relance")
        DIGEST = "new_members", _("Nouveaux membres")

    kind = models.CharField(max_length=24, choices=Kind.choices)
    scope_key = models.CharField(max_length=120, unique=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="notification_campaigns")
    invitation = models.ForeignKey(InvitationRequest, on_delete=models.SET_NULL, null=True, blank=True)
    month = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)


class NotificationDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        SENDING = "sending", _("En cours d'envoi")
        SENT = "sent", _("Accepté par SMTP")
        SKIPPED = "skipped", _("Ignoré")
        FAILED = "failed", _("Échec confirmé")
        UNCERTAIN = "uncertain", _("Résultat incertain")

    campaign = models.ForeignKey(NotificationCampaign, on_delete=models.PROTECT, related_name="deliveries")
    recipient = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notification_deliveries")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    claimed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["campaign", "recipient"], name="unique_campaign_recipient")]
        indexes = [models.Index(fields=["status", "next_attempt_at"], name="notification_due")]


class BingoSquare(models.Model):
    """One square of a member's 'Bingo des rencontres' grid for an event: « Trouve quelqu'un qui… ».
    It is ticked with the person whose QR code the player scanned; one person fills one square only."""

    class Kind(models.TextChoices):
        LIKE = "like", _("adore")
        DISLIKE = "dislike", _("déteste")
        LANGUAGE = "language", _("parle")
        SECTOR = "sector", _("secteur")
        RANK = "rank", _("rang")
        REGION = "region", _("région")
        JOKER = "joker", _("joker")

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bingo_squares")
    player = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="bingo_squares")
    position = models.PositiveSmallIntegerField()  # 0-8, row by row
    kind = models.CharField(max_length=10, choices=Kind.choices)
    value = models.CharField(max_length=80, blank=True)  # tag slug, language code, sector, rank or region ("" for the joker)
    found = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    found_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["event", "player", "position"]
        verbose_name = _("case de bingo")
        verbose_name_plural = _("cases de bingo")
        constraints = [
            models.UniqueConstraint(fields=["event", "player", "position"], name="unique_bingo_square"),
            models.UniqueConstraint(
                fields=["event", "player", "found"], condition=Q(found__isnull=False), name="one_bingo_square_per_person"
            ),
        ]


class Substitute(models.Model):
    """Someone who represents a member at an event they cannot attend, usually a colleague from the same company."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="substitutes", verbose_name=_("événement"))
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="substitutions", verbose_name=_("membre remplacé")
    )
    first_name = models.CharField(_("prénom"), max_length=80)
    last_name = models.CharField(_("nom"), max_length=80)
    email = models.EmailField(_("e-mail"))
    company = models.CharField(_("entreprise"), max_length=120)
    job_title = models.CharField(_("fonction"), max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["event", "last_name", "first_name"]
        verbose_name = _("remplaçant·e")
        verbose_name_plural = _("remplaçant·e·s")
        constraints = [models.UniqueConstraint(fields=["event", "member"], name="one_substitute_per_member")]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
