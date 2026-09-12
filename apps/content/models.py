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

from django.conf import settings
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
    """

    def decorate(cls):
        for name, factory in fields.items():
            for code in LANG_CODES:
                field = factory()
                field.blank = code != DEFAULT_LANG
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
)
class Profile(Translatable, TimeStamped):
    """Singleton. `Profile.load()` is the only way anything reads it."""

    avatar = models.ImageField(upload_to="profile/", blank=True)
    resume_file = models.FileField(upload_to="profile/", blank=True)

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
            out.append({"key": "linkedin", "label": handle, "href": f"https://linkedin.com/in/{handle}", "copy": f"https://linkedin.com/in/{handle}"})
        if self.phone:
            out.append({"key": "phone", "label": self.phone, "href": f"tel:{self.phone}", "copy": self.phone})
        return out


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
    cover = models.ImageField(upload_to="projects/", blank=True)
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
@i18n_fields(
    title=lambda: models.CharField(max_length=180),
    excerpt=lambda: models.CharField(max_length=280, blank=True),
    body=lambda: models.TextField(blank=True, help_text="Markdown."),
)
class Post(Translatable, TimeStamped):
    slug = models.SlugField(max_length=180, unique=True)
    cover = models.ImageField(upload_to="posts/", blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("-published_at", "-pk")

    def __str__(self) -> str:
        return self.slug

    def get_absolute_url(self) -> str:
        return reverse("post_detail", args=[self.slug])

    @property
    def reading_minutes(self) -> int:
        """Counted on the body the reader is actually being shown."""
        words = len(self.tr("body").split())
        return max(1, round(words / 200))


# ── Messages from the contact form ─────────────────────────────────────────
class Message(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=160, blank=True)
    body = models.TextField()
    language = models.CharField(max_length=8, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_handled = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} — {self.created_at:%Y-%m-%d}"
