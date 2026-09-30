"""
Content models.

Everything a visitor reads comes from here, so the whole site is editable
without a deploy. Nothing else in the project holds copy.

── How translation works ──────────────────────────────────────────────────
A translated field is not one column plus a side table; it is one real column
per language, named `<field>_<lang>`. `@i18n_fields(...)` writes those columns
so the model body stays readable, and `Translatable.tr("title")` reads the
active language with a fallback chain.

Why this rather than django-modeltranslation or a per-language row: it is one
dependency fewer, every query stays a plain query with no joins, the stock
admin renders the three inputs side by side for free, and adding a fourth
language is one entry in settings.LANGUAGES plus one migration. The cost is
that a language you never fill in falls back — which is the behaviour a
personal site wants anyway.
"""

from __future__ import annotations

import secrets
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language

LANG_CODES: tuple[str, ...] = tuple(code for code, _ in settings.LANGUAGES)
DEFAULT_LANG: str = settings.LANGUAGE_CODE
# Order a missing translation falls back through. Persian first because it is
# the language every field is guaranteed to be filled in.
FALLBACK_CHAIN: tuple[str, ...] = (DEFAULT_LANG,) + tuple(
    c for c in LANG_CODES if c != DEFAULT_LANG
)


def i18n_fields(**fields):
    """Class decorator adding `<name>_<lang>` columns for every language.

    Usage:  @i18n_fields(title=lambda: models.CharField(max_length=200))

    The factory is called once per language because a Django field instance
    cannot be attached to two models (or two names) at once.

    Every language except Persian is optional. Persian is required too unless
    the factory itself says `blank=True`, which is how a field that is optional
    in every language (a post written only in English) stays optional.
    """

    def decorate(cls):
        for name, factory in fields.items():
            for code in LANG_CODES:
                field = factory()
                field.blank = field.blank or code != DEFAULT_LANG
                field.verbose_name = f"{name} [{code}]"
                cls.add_to_class(f"{name}_{code}", field)
        cls.I18N_FIELDS = tuple(fields)
        return cls

    return decorate


class Translatable(models.Model):
    """Mixin giving every translated model the same read path."""

    I18N_FIELDS: tuple[str, ...] = ()

    class Meta:
        abstract = True

    def tr(self, name: str) -> str:
        active = (get_language() or DEFAULT_LANG).split("-")[0]
        for code in (active, *FALLBACK_CHAIN):
            value = getattr(self, f"{name}_{code}", "")
            if value:
                return value
        return ""

    def languages_with(self, name: str) -> list[str]:
        """The languages `name` is really written in, fallback order first."""
        return [code for code in FALLBACK_CHAIN if getattr(self, f"{name}_{code}", "")]


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ── Profile: one row, the person ───────────────────────────────────────────
@i18n_fields(
    full_name=lambda: models.CharField(max_length=120),
    headline=lambda: models.CharField(max_length=160, help_text="One line under the name."),
    intro=lambda: models.TextField(help_text="Two or three sentences on the home hero."),
    bio=lambda: models.TextField(blank=True, help_text="Long form, Markdown. Shown on /about/."),
    location=lambda: models.CharField(max_length=80, blank=True),
    now=lambda: models.CharField(max_length=200, blank=True, help_text="What you are working on right now."),
    languages=lambda: models.CharField(
        max_length=160,
        blank=True,
        default="",
        help_text="Spoken languages and levels, e.g. 'Persian native · English C1 · German A1'. "
        "A German CV is expected to state these; the résumé page shows it in the fact bar.",
    ),
    availability=lambda: models.CharField(max_length=80, blank=True, help_text="e.g. open to work"),
    # ── search engines ──
    seo_title=lambda: models.CharField(
        max_length=70,
        blank=True,
        default="",
        help_text="The home page <title>, up to ~60 characters: name plus what you do. "
        "Falls back to the name.",
    ),
    seo_description=lambda: models.CharField(
        max_length=170,
        blank=True,
        default="",
        help_text="The home page meta description — the two lines under the link in "
        "search results. 120–160 characters. Falls back to the intro.",
    ),
    # ── project work, the /services/ page and the home band ──
    offer_title=lambda: models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Headline of the services offer. Empty hides the page, the nav link and the home band.",
    ),
    offer_lede=lambda: models.TextField(blank=True, default="", help_text="One or two sentences under it."),
    offer_body=lambda: models.TextField(
        blank=True,
        default="",
        help_text="Markdown. The long form on /services/ — what you build, how a project runs.",
    ),
)
class Profile(Translatable, TimeStamped):
    """Singleton. `Profile.load()` is the only way anything reads it."""

    avatar = models.ImageField(
        upload_to="profile/",
        blank=True,
        help_text="Your portrait: the home page hero, /about/, /resume/ and the business card /card/ — "
        "and the shared-link picture while the one below is empty. Square, at least 700×700 px.",
    )
    og_image = models.ImageField(
        upload_to="profile/",
        blank=True,
        help_text="The picture a shared link shows on LinkedIn, Telegram, WhatsApp or X, for every "
        "page without a picture of its own. 1200×630 px. Falls back to the avatar.",
    )
    resume_file = models.FileField(
        upload_to="profile/",
        blank=True,
        help_text="The file behind every «download résumé» button: the home hero, /resume/ and the "
        "footer. PDF. Empty hides the buttons.",
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    telegram = models.CharField(max_length=64, blank=True, help_text="username, no @")
    github = models.CharField(max_length=64, blank=True)
    linkedin = models.CharField(max_length=120, blank=True)
    twitter = models.CharField(max_length=64, blank=True)
    website = models.URLField(blank=True)

    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name = "profile"

    def __str__(self) -> str:
        return self.full_name_fa or "profile"

    @property
    def share_image(self):
        return self.og_image or self.avatar

    def save(self, *args, **kwargs):
        self.pk = 1  # there is exactly one person on a personal site
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "Profile":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def links(self) -> list[dict]:
        """The contact channels, in the order they should be offered."""
        out = []
        if self.email:
            out.append({"key": "email", "label": self.email, "href": f"mailto:{self.email}", "copy": self.email})
        if self.telegram:
            handle = self.telegram.lstrip("@")
            out.append({"key": "telegram", "label": f"@{handle}", "href": f"https://t.me/{handle}", "copy": f"@{handle}"})
        if self.github:
            handle = self.github.strip("/").split("/")[-1]
            out.append({"key": "github", "label": handle, "href": f"https://github.com/{handle}", "copy": f"https://github.com/{handle}"})
        if self.linkedin:
            handle = self.linkedin.strip("/").split("/")[-1]
            out.append({"key": "linkedin", "label": handle, "href": f"https://www.linkedin.com/in/{handle}", "copy": f"https://www.linkedin.com/in/{handle}"})
        if self.phone:
            out.append({"key": "phone", "label": self.phone, "href": f"tel:{self.phone}", "copy": self.phone})
        return out


# ── What a client gets: the cards on /services/ and the home band ──────────
@i18n_fields(
    title=lambda: models.CharField(max_length=80),
    body=lambda: models.CharField(max_length=280),
)
class Service(Translatable):
    """One promise to a client — end to end, fast delivery, agreed price.

    A row rather than a sentence in `offer_body` because each one is a card,
    and a card needs its own title, icon and place in the order.
    """

    class Icon(models.TextChoices):
        LAYERS = "layers", "layers"
        CLOCK = "clock", "clock"
        TARGET = "target", "target"
        BRIEFCASE = "briefcase", "briefcase"
        CODE = "code", "code"
        DATABASE = "database", "database"
        SPARKLE = "sparkle", "sparkle"
        CHECK = "check", "check"

    icon = models.CharField(max_length=16, choices=Icon.choices, default=Icon.SPARKLE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.title_fa or f"service {self.pk}"


# ── Skills ─────────────────────────────────────────────────────────────────
@i18n_fields(name=lambda: models.CharField(max_length=80))
class SkillGroup(Translatable):
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.name_fa or f"group {self.pk}"


class Skill(models.Model):
    """Deliberately has no percentage. A number nobody can verify buys nothing."""

    group = models.ForeignKey(SkillGroup, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=60, help_text="Technology names stay Latin in every language.")
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False, help_text="Shown in the home hero strip.")

    class Meta:
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.name


# ── Tags: shared by projects and posts ─────────────────────────────────────
@i18n_fields(name=lambda: models.CharField(max_length=60))
class Tag(Translatable):
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ("slug",)

    def __str__(self) -> str:
        return self.slug


# ── Projects ───────────────────────────────────────────────────────────────
@i18n_fields(
    title=lambda: models.CharField(max_length=140),
    summary=lambda: models.CharField(max_length=240, help_text="One sentence, shown on the card."),
    role=lambda: models.CharField(max_length=120, blank=True),
    problem=lambda: models.TextField(blank=True, help_text="Markdown. What needed solving."),
    body=lambda: models.TextField(blank=True, help_text="Markdown. What you built and why."),
    outcome=lambda: models.CharField(max_length=240, blank=True, help_text="The result, in one line."),
)
class Project(Translatable, TimeStamped):
    slug = models.SlugField(max_length=140, unique=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    stack = models.CharField(max_length=200, blank=True, help_text="Comma separated, Latin, e.g. Django, Postgres")
    cover = models.ImageField(
        upload_to="projects/",
        blank=True,
        help_text="The project's card on the home page and /projects/, the top of its own page, and "
        "the picture when its link is shared. Landscape, about 1600×1000 px.",
    )
    repo_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="projects")

    is_featured = models.BooleanField(default=False, help_text="Appears on the home page.")
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "-year", "-pk")

    def __str__(self) -> str:
        return self.slug

    def get_absolute_url(self) -> str:
        return reverse("project_detail", args=[self.slug])

    @property
    def stack_list(self) -> list[str]:
        return [part.strip() for part in self.stack.split(",") if part.strip()]


# ── Career and education ───────────────────────────────────────────────────
@i18n_fields(
    org=lambda: models.CharField(max_length=140),
    role=lambda: models.CharField(max_length=140),
    description=lambda: models.TextField(blank=True, help_text="Markdown. What you actually did."),
    location=lambda: models.CharField(max_length=80, blank=True),
)
class Experience(Translatable):
    class Kind(models.TextChoices):
        WORK = "work", "Work"
        EDUCATION = "education", "Education"

    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.WORK)
    start = models.DateField()
    end = models.DateField(null=True, blank=True, help_text="Leave empty if this is current.")
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "-start")

    def __str__(self) -> str:
        return f"{self.role_fa} @ {self.org_fa}"

    @property
    def is_current(self) -> bool:
        return self.end is None


# ── Writing ────────────────────────────────────────────────────────────────
# A post is written in whichever languages it is written in — a LinkedIn post
# is often English only — so no language is required here and `clean()` asks
# for one complete language instead. A language with no title of its own is
# served with the fallback but marked noindex, so a search engine never
# indexes a Persian article under /en/.
POST_BODY_HELP = (
    "Markdown. A line break stays a line break, so text pasted from LinkedIn keeps "
    "its shape. ## heading · **bold** · [text](https://…) for a link · a bare "
    "https://… link works too · ![description](/media/…) for an image — upload "
    "images at the bottom of this page and copy their line from there."
)


@i18n_fields(
    title=lambda: models.CharField(max_length=180, blank=True),
    excerpt=lambda: models.CharField(
        max_length=280,
        blank=True,
        help_text="One or two sentences. Shown in the list and used as the search "
        "result description, so 120–160 characters reads best.",
    ),
    body=lambda: models.TextField(blank=True, help_text=POST_BODY_HELP),
)
class Post(Translatable, TimeStamped):
    slug = models.SlugField(
        max_length=180,
        unique=True,
        help_text="The address: /blog/<slug>/. Latin, lowercase, hyphens — e.g. "
        "sql-server-locking. Keep it stable once published.",
    )
    cover = models.ImageField(
        upload_to="posts/",
        blank=True,
        help_text="Shown above the post and as the picture when the link is shared. 1200×630 px reads best.",
    )
    original_url = models.URLField(
        blank=True,
        max_length=500,
        help_text="Where this was first published — a LinkedIn post, X, Virgool, Medium. "
        "Shown under the post as a link to the original.",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)

    # host → (platform key, icon id). The key is `platform.<key>` in i18n.py.
    PLATFORMS = {
        "linkedin.com": ("linkedin", "linkedin"),
        "lnkd.in": ("linkedin", "linkedin"),
        "x.com": ("x", "external"),
        "twitter.com": ("x", "external"),
        "github.com": ("github", "github"),
        "t.me": ("telegram", "telegram"),
        "medium.com": ("medium", "external"),
        "virgool.io": ("virgool", "external"),
        "dev.to": ("devto", "external"),
    }

    class Meta:
        ordering = ("-published_at", "-pk")

    def __str__(self) -> str:
        return self.slug

    def clean(self):
        if not self.languages:
            raise ValidationError("Write the title and body in at least one language.")
        for code in LANG_CODES:
            if getattr(self, f"title_{code}") and not getattr(self, f"body_{code}"):
                raise ValidationError({f"body_{code}": "A title in this language needs a body too."})

    def get_absolute_url(self) -> str:
        return reverse("post_detail", args=[self.slug])

    @property
    def languages(self) -> list[str]:
        """Languages this post is actually written in: a title of its own."""
        return self.languages_with("title")

    @property
    def content_language(self) -> str:
        """The language the reader is shown: theirs if written, else the first there is."""
        active = (get_language() or DEFAULT_LANG).split("-")[0]
        langs = self.languages
        if active in langs or not langs:
            return active
        return langs[0]

    @property
    def lead_image(self):
        """The picture for a shared link: the cover, else the first body image."""
        if self.cover:
            return self.cover
        first = next(iter(self.images.all()), None)
        return first.image if first else None

    @property
    def original(self) -> dict | None:
        """{"key", "icon", "url"} for the original-post link, or None."""
        if not self.original_url:
            return None
        host = (urlsplit(self.original_url).hostname or "").lower().removeprefix("www.")
        for domain, (key, icon) in self.PLATFORMS.items():
            if host == domain or host.endswith("." + domain):
                return {"key": key, "icon": icon, "url": self.original_url}
        return {"key": "web", "icon": "external", "url": self.original_url}

    @property
    def reading_minutes(self) -> int:
        """Counted on the body the reader is actually being shown."""
        words = len(self.tr("body").split())
        return max(1, round(words / 200))


class PostImage(models.Model):
    """An image used inside a post body.

    Uploaded from the post's own admin page, which then shows the Markdown line
    to paste — so a picture in the middle of a post needs no second tool.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(
        upload_to="posts/body/",
        help_text="A picture inside the post's text. Save, then paste the Markdown line beside it "
        "where it should appear; the first one is also the shared-link picture when there is no cover.",
    )
    alt = models.CharField(
        max_length=200,
        blank=True,
        help_text="What the image shows, in a few words. Read aloud by screen readers and by Google Images.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.alt or self.image.name

    @property
    def markdown(self) -> str:
        return f"![{self.alt}]({self.image.url})" if self.image else ""


# ── Messages from the contact form ─────────────────────────────────────────
# Unambiguous on a screen and on a phone keyboard: no 0/O, 1/I/L. Eight of
# them is 31^8 ≈ 8.5 × 10^11 codes, and failed lookups are throttled on top.
TRACKING_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
TRACKING_LENGTH = 8


def new_tracking_code() -> str:
    raw = "".join(secrets.choice(TRACKING_ALPHABET) for _ in range(TRACKING_LENGTH))
    return f"{raw[:4]}-{raw[4:]}"


def normalise_tracking_code(value: str) -> str:
    """Whatever the visitor typed, in the shape the column stores: case,
    spaces and a missing or doubled dash do not matter."""
    raw = "".join(ch for ch in (value or "").upper() if ch in TRACKING_ALPHABET)
    return f"{raw[:4]}-{raw[4:]}" if len(raw) == TRACKING_LENGTH else ""


_PHONE_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalise_phone(value: str) -> str:
    """One number, however it was written: «۰۹۱۲ ۳۴۵ ۶۷۸۹», «+98 912…» and
    «00989123456789» all come out as «09123456789». A number from outside
    Iran keeps its country code and loses only the punctuation. Empty when
    there are too few digits to be a phone at all."""
    digits = "".join(ch for ch in (value or "").translate(_PHONE_DIGITS) if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "0" + digits
    return digits if len(digits) >= 7 else ""


class Message(models.Model):
    """What the contact form saves — and, when it is a project enquiry, a lead.

    A lead has a life cycle, so this carries a `status` rather than a handled
    flag: a request is new until it has been read, answered once a reply has
    gone back, and at any point it may be refused or put away. The same states
    are what the Bale bot's buttons set, so the phone and the admin can never
    disagree about where a request stands.

    A request is also a conversation. The visitor gets a `tracking_code`, and
    with it the page at /contact/track/<code>/ where both sides write `Reply`
    rows under the original message, as many as it takes. A reply from the
    visitor puts the request back to «new», whatever state it was in — someone
    is waiting again.

    `notes` is private. Nothing a visitor can reach renders it.
    """

    class Status(models.TextChoices):
        NEW = "new", "جدید — new"
        READ = "read", "خوانده‌شده — read"
        ANSWERED = "answered", "پاسخ داده شده — answered"
        REJECTED = "rejected", "رد شده — rejected"
        ARCHIVED = "archived", "بایگانی — archived"

    # «Active» is what still needs the owner: everything except a request that
    # is waiting on the visitor, refused, or put away.
    INACTIVE = (Status.ANSWERED, Status.REJECTED, Status.ARCHIVED)
    ACTIVE = (Status.NEW, Status.READ)

    class Kind(models.TextChoices):
        PROJECT = "project", "پروژه — project"
        JOB = "job", "پیشنهاد شغلی — job offer"
        CONSULT = "consult", "مشاوره — consulting"
        OTHER = "other", "سایر — other"

    class Timeline(models.TextChoices):
        """How soon the visitor needs it, relative to when they asked. The
        choice becomes a real date in `due_at`, which is what the admin sorts
        and filters by."""

        WEEK = "week", "تا یک هفته — within a week"
        MONTH = "month", "تا یک ماه — within a month"
        QUARTER = "quarter", "تا سه ماه — within three months"
        FLEXIBLE = "flexible", "انعطاف‌پذیر — flexible"

    TIMELINE_DAYS = {Timeline.WEEK: 7, Timeline.MONTH: 30, Timeline.QUARTER: 90}

    name = models.CharField(max_length=120)
    company = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    # Optional: a phone number is how most Iranian clients expect to be
    # answered, but asking for one as a requirement costs replies.
    phone = models.CharField(max_length=32, blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.OTHER)
    timeline = models.CharField(max_length=16, choices=Timeline.choices, default=Timeline.FLEXIBLE)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    subject = models.CharField(max_length=160, blank=True)
    body = models.TextField()
    language = models.CharField(max_length=8, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    tracking_code = models.CharField(max_length=9, unique=True, default=new_tracking_code, editable=False)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    read_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(
        blank=True,
        help_text="Private. Written here or from the bot's «یادداشت» button; never shown on the site.",
    )

    # Where the notice for this request landed, so a status change can go back
    # and repaint the same message instead of sending a second one.
    notified_at = models.DateTimeField(null=True, blank=True)
    bot_chat_id = models.CharField(max_length=64, blank=True)
    bot_message_id = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self) -> str:
        return f"#{self.pk} {self.name} — {self.created_at:%Y-%m-%d}"

    def save(self, *args, **kwargs):
        # The deadline is fixed when the request arrives: "within a week" means
        # a week from the day it was asked, not from whenever it was opened.
        if self.due_at is None and self.timeline in self.TIMELINE_DAYS:
            start = self.created_at or timezone.now()
            self.due_at = start + timedelta(days=self.TIMELINE_DAYS[self.timeline])
        super().save(*args, **kwargs)

    @property
    def is_new(self) -> bool:
        return self.status == self.Status.NEW

    @property
    def is_active(self) -> bool:
        return self.status in self.ACTIVE

    @property
    def admin_path(self) -> str:
        return reverse("admin:content_message_change", args=[self.pk])

    @property
    def admin_url(self) -> str:
        return f"{settings.SITE_URL}{self.admin_path}"

    def get_absolute_url(self) -> str:
        """The visitor's tracking page, in the language they wrote in."""
        from django.utils.translation import override  # local: the one caller

        with override(self.language or DEFAULT_LANG):
            return reverse("track_detail", args=[self.tracking_code])

    def days_left(self) -> int | None:
        """Whole days until the visitor's deadline; negative once it passed."""
        if self.due_at is None:
            return None
        return (timezone.localtime(self.due_at).date() - timezone.localdate()).days

    def set_status(self, status: str) -> bool:
        """Move to `status`. False when it was already there, so a double tap
        on the same button is a no-op rather than a second write."""
        if status not in self.Status.values or self.status == status:
            return False

        self.status = status
        # Back to «new» means genuinely unread again; every other move stamps
        # the first time this request was looked at.
        self.read_at = None if status == self.Status.NEW else (self.read_at or timezone.now())
        self.save(update_fields=["status", "read_at"])
        return True

    def add_reply(self, body: str, *, from_owner: bool) -> "Reply":
        """One more turn in the conversation, and the status that follows it.

        The owner answering makes it «answered»; the visitor writing back makes
        it «new» again, from any state — a refused or archived request someone
        has just written to is a request somebody is waiting on.
        """
        reply = self.replies.create(body=body.strip(), from_owner=from_owner)
        self.set_status(self.Status.ANSWERED if from_owner else self.Status.NEW)
        return reply

    @property
    def can_be_cancelled(self) -> bool:
        return self.status not in (self.Status.REJECTED, self.Status.ARCHIVED)

    def cancel_by_visitor(self) -> "Reply":
        """The visitor withdrew the request. It is put away like an archived
        one, and the withdrawal is a turn in the conversation rather than a
        flag, so it stays on the record after the visitor writes again —
        which, like any reply of theirs, makes the request «new»."""
        reply = self.replies.create(event=Reply.Event.CANCELLED, from_owner=False)
        self.set_status(self.Status.ARCHIVED)
        return reply

    @property
    def cancelled_by_visitor(self) -> bool:
        """Put away because the visitor withdrew it, and nothing said since."""
        if self.status != self.Status.ARCHIVED:
            return False
        last = self.replies.order_by("-created_at", "-pk").first()
        return last is not None and last.event == Reply.Event.CANCELLED

    def add_note(self, text: str) -> str:
        """Append one dated line to the private notes. Returns the line."""
        from apps.core.jalali import to_jalali  # local: keeps content free of core at import time

        stamped = timezone.localtime(timezone.now())
        jy, jm, jd = to_jalali(stamped.date())
        entry = f"{jy}/{jm:02d}/{jd:02d} {stamped:%H:%M} — {text.strip()}"
        self.notes = f"{self.notes.rstrip()}\n{entry}" if self.notes.strip() else entry
        self.save(update_fields=["notes"])
        return entry


class Reply(models.Model):
    """One turn in a request's conversation, from either side.

    Replies are a record, like the request itself: neither side edits or
    deletes one, they write another. That is what makes the thread something
    both people can point back to later.
    """

    class Event(models.TextChoices):
        """A turn that is something the visitor did rather than something
        they said. Empty for an ordinary reply."""

        CANCELLED = "cancelled", "لغو توسط درخواست‌کننده — cancelled by the visitor"

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="replies")
    from_owner = models.BooleanField(default=False)
    body = models.TextField(blank=True)
    event = models.CharField(max_length=16, choices=Event.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "pk")
        verbose_name_plural = "replies"

    def __str__(self) -> str:
        side = "owner" if self.from_owner else "visitor"
        return f"#{self.message_id} {side} — {self.created_at:%Y-%m-%d %H:%M}"


class BotState(models.Model):
    """The bot's memory. One row, because there is one bot and one owner.

    It holds the two things the messenger cannot hold for us:

    * `last_update_id` — the last update already acted on, so a webhook retry
      or a restarted poller can never archive the same request twice.
    * `awaiting_note_for` — which request a note is being written for, because
      «یادداشت» is a button press first and a text message second, and the two
      arrive as separate updates. `awaiting_reply` says the text that follows
      is an answer for the visitor rather than a private note — «پاسخ» works
      the same way.
    """

    last_update_id = models.BigIntegerField(default=0)
    awaiting_note_for = models.ForeignKey(
        Message, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    awaiting_since = models.DateTimeField(null=True, blank=True)
    awaiting_reply = models.BooleanField(default=False)

    class Meta:
        verbose_name = "bot state"

    def __str__(self) -> str:
        return f"bot state (update {self.last_update_id})"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "BotState":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def is_new_update(self, update_id: int) -> bool:
        """True the first time an update is seen; False for a replay."""
        if update_id and update_id <= self.last_update_id:
            return False
        if update_id:
            self.last_update_id = update_id
            self.save(update_fields=["last_update_id"])
        return True

    def await_note_for(self, message: "Message", *, reply: bool = False) -> None:
        self.awaiting_note_for = message
        self.awaiting_since = timezone.now()
        self.awaiting_reply = reply
        self.save(update_fields=["awaiting_note_for", "awaiting_since", "awaiting_reply"])

    def pending_note_target(self) -> "Message | None":
        """The request a plain text message should be filed under, if any."""
        if not self.awaiting_note_for_id or not self.awaiting_since:
            return None
        age = (timezone.now() - self.awaiting_since).total_seconds()
        if age > settings.BOT_NOTE_WINDOW_SECONDS:
            return None
        return self.awaiting_note_for

    def clear_note_target(self) -> None:
        if self.awaiting_note_for_id or self.awaiting_since or self.awaiting_reply:
            self.awaiting_note_for = None
            self.awaiting_since = None
            self.awaiting_reply = False
            self.save(update_fields=["awaiting_note_for", "awaiting_since", "awaiting_reply"])


# ── The visitor's side of the bot ──────────────────────────────────────────
def new_link_token() -> str:
    # URL-safe and well inside the 64 characters a /start payload may carry.
    return secrets.token_urlsafe(18)


class ChatLinkToken(models.Model):
    """The one-time key in a «get replies in Bale» deep link.

    It exists so the tracking code itself never travels through the messenger:
    the page mints one of these, the link carries it, and /start spends it.
    It is short-lived, it is claimed by the first chat that presents it — no
    other chat can use it after that — and it is spent by the first contact
    that chat shares, whether or not the number matched.
    """

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="link_tokens")
    token = models.CharField(max_length=64, unique=True, default=new_link_token, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    # The chat that opened the link, and so the only one whose contact counts.
    chat_id = models.CharField(max_length=64, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"link token for #{self.message_id}"

    @classmethod
    def issue(cls, message: Message) -> "ChatLinkToken":
        """A token for `message` — the one already waiting, if there is one,
        so reloading the page and pressing again does not pile rows up."""
        now = timezone.now()
        cls.objects.filter(expires_at__lt=now).delete()
        waiting = cls.objects.filter(message=message, chat_id="", used_at=None, expires_at__gt=now).first()
        if waiting is not None:
            return waiting
        return cls.objects.create(message=message, expires_at=now + timedelta(seconds=settings.BOT_LINK_TOKEN_SECONDS))

    @property
    def is_live(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()


class ChatLink(models.Model):
    """A request whose updates go to the visitor's own chat.

    Made only once the number the visitor shared from inside the messenger —
    their own, not somebody else's contact card — matched the number on the
    request. That chat is then allowed exactly three things for this request
    and nothing else: to be told, to reply, and to cancel. Every button checks
    this row, so knowing a request's id is worth nothing.

    `told_status` and `told_reply_id` are what the visitor was last told, so
    the same change is never sent twice and a private note — which changes
    neither — is never sent at all.
    """

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="chat_link")
    chat_id = models.CharField(max_length=64, db_index=True)
    phone = models.CharField(max_length=32, help_text="As shared from the messenger, normalised.")
    connected_at = models.DateTimeField(auto_now_add=True)

    told_status = models.CharField(max_length=16, blank=True)
    told_reply_id = models.BigIntegerField(default=0)
    # «پاسخ» is a press first and a text second, like the owner's.
    awaiting_reply_since = models.DateTimeField(null=True, blank=True)
    # The last reply or cancellation from the messenger: the same one-a-minute
    # throttle the site's form has.
    last_action_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "chat link"

    def __str__(self) -> str:
        return f"#{self.message_id} → chat {self.chat_id}"

    def mark_told(self) -> None:
        """Record the request's current state as already known to the visitor
        — for the changes they made themselves."""
        last = self.message.replies.filter(from_owner=True).order_by("-pk").values_list("pk", flat=True).first()
        self.told_status, self.told_reply_id = self.message.status, last or 0
        ChatLink.objects.filter(pk=self.pk).update(told_status=self.told_status, told_reply_id=self.told_reply_id)
