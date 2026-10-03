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
    member_since = models.PositiveSmallIntegerField(_("membre depuis (année)"))
    is_founder = models.BooleanField(_("membre fondateur"), default=False)
    fun_fact = models.CharField(_("anecdote"), max_length=200, blank=True)
    talk_to_me_about = models.CharField(_("parle-moi de…"), max_length=120, blank=True)
    phone = models.CharField(_("téléphone"), max_length=30, blank=True)
    linkedin_url = models.URLField(_("LinkedIn"), blank=True)
    visible_in_directory = models.BooleanField(_("visible dans l'album"), default=True)
    onboarding_done = models.BooleanField(default=False)
    qr_token = models.CharField(max_length=32, unique=True, default=new_qr_token, editable=False)
    referral_code = models.CharField(max_length=12, unique=True, default=new_referral_code, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

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
        constraints = [models.UniqueConstraint(fields=["member", "tag"], name="unique_member_tag")]


class Event(models.Model):
    class Kind(models.TextChoices):
        APERO = "apero", _("Apéro")
        DINNER = "dinner", _("Dîner / soirée")
        CONFERENCE = "conference", _("Conférence")
        VISIT = "visit", _("Visite")

    title = models.CharField(_("titre"), max_length=150)
    kind = models.CharField(_("type"), max_length=12, choices=Kind.choices)
    starts_at = models.DateTimeField(_("début"))
    location = models.CharField(_("lieu"), max_length=150)
    description = models.TextField(_("description"), blank=True)
    has_seating = models.BooleanField(_("repas assis (tables tournantes)"), default=False)

    class Meta:
        ordering = ["starts_at"]
        verbose_name = _("événement")

    def __str__(self):
        return self.title

    @property
    def is_past(self):
        return self.starts_at < timezone.now()


class RSVP(models.Model):
    class Status(models.TextChoices):
        YES = "yes", _("Je viens")
        NO = "no", _("Je ne viens pas")

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="rsvps")
    status = models.CharField(max_length=3, choices=Status.choices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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
    referred_by = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
