"""
Stock Django admin — the interim way to edit content.

The custom lightweight panel is a later piece of work (see CLAUDE.md). Until it
exists this is what makes the database writable, and it costs nothing: the
per-language columns render as three plain inputs side by side.

The post form is the one screen written for regular use, so it gets the most
care: one block per language, a body box big enough to write in, and images
uploaded on the same page with the Markdown line to paste already built.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from apps.core import bot

from .models import (
    LANG_CODES,
    Experience,
    Message,
    Post,
    PostImage,
    Profile,
    Project,
    Service,
    Skill,
    SkillGroup,
    Tag,
)

LANG_NAMES = {"fa": "فارسی — Persian", "en": "English", "de": "Deutsch — German"}


def _per_language(*names):
    return [
        (LANG_NAMES.get(code, code), {"fields": [f"{name}_{code}" for name in names]})
        for code in LANG_CODES
    ]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "title_en", "icon", "order")
    list_editable = ("icon", "order")


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1


@admin.register(SkillGroup)
class SkillGroupAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "name_en", "order")
    inlines = [SkillInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("slug", "name_fa", "name_en", "name_de")
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("slug", "title_fa", "year", "is_featured", "is_published", "order")
    list_filter = ("is_featured", "is_published", "tags")
    list_editable = ("is_featured", "is_published", "order")
    search_fields = ("slug", "title_fa", "title_en", "title_de")
    filter_horizontal = ("tags",)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("org_fa", "role_fa", "kind", "start", "end")
    list_filter = ("kind",)


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ("image", "alt", "order", "snippet")
    readonly_fields = ("snippet",)

    @admin.display(description="Markdown to paste into the body")
    def snippet(self, obj):
        if not obj.pk or not obj.image:
            return "Save (and continue editing) to get the line to paste."
        return format_html(
            '<code style="user-select:all;direction:ltr;unicode-bidi:isolate">{}</code> '
            '<button type="button" class="button" '
            "onclick=\"navigator.clipboard.writeText(this.previousElementSibling.textContent)"
            ".then(()=>{{this.textContent='✓ copied'}})\">copy</button>",
            obj.markdown,
        )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("slug", "title", "written_in", "published_at", "is_published")
    list_filter = ("is_published", "tags")
    list_editable = ("is_published",)
    search_fields = ("slug", *[f"title_{code}" for code in LANG_CODES])
    date_hierarchy = "published_at"
    filter_horizontal = ("tags",)
    prepopulated_fields = {"slug": ("title_en",)}
    save_on_top = True
    inlines = [PostImageInline]
    fieldsets = [
        (None, {"fields": ("slug", ("published_at", "is_published"), "cover", "original_url", "tags")}),
        *_per_language("title", "excerpt", "body"),
    ]

    @admin.display(description="title")
    def title(self, obj):
        return obj.tr("title")

    @admin.display(description="written in")
    def written_in(self, obj):
        return " · ".join(code.upper() for code in obj.languages)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        # dir="auto" lets a Persian paragraph sit right-to-left in the same box
        # an English one sits left-to-right in.
        if db_field.name.startswith(("title_", "excerpt_", "body_")):
            field.widget.attrs["dir"] = "auto"
        if db_field.name.startswith("body_"):
            field.widget.attrs.update(rows=20, style="width:100%;max-width:60rem;line-height:1.7")
        return field


STATUS_COLOURS = {
    Message.Status.NEW: "#7fb3ff",
    Message.Status.READ: "#8fd6b4",
    Message.Status.REJECTED: "#f2a2a2",
    Message.Status.ARCHIVED: "#c9c4bd",
}


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """The inbox.

    What a visitor wrote is read-only — a request is a record, and editing it
    would make the notice already sitting in Bale a lie. What is editable is
    the triage: the status and the private notes, the same two things the
    bot's buttons write, so neither side is the special one.
    """

    list_display = ("state", "name", "reach", "subject", "when", "note_preview")
    list_display_links = ("name",)
    list_filter = ("status", "language")
    search_fields = ("name", "email", "phone", "subject", "body", "notes")
    date_hierarchy = "created_at"
    actions = ("mark_read", "mark_rejected", "mark_archived")
    readonly_fields = ("name", "email", "phone", "subject", "body", "language", "created_at", "read_at", "notified_at")
    fieldsets = [
        ("Triage", {"fields": ("status", "notes")}),
        ("What was sent", {"fields": ("name", "email", "phone", "subject", "body")}),
        ("When", {"fields": ("language", "created_at", "read_at", "notified_at"), "classes": ["collapse"]}),
    ]

    @admin.display(description="status", ordering="status")
    def state(self, obj):
        return format_html(
            '<b style="color:{}">●</b> {}',
            STATUS_COLOURS.get(obj.status, "#999"),
            obj.get_status_display().split(" — ")[0],
        )

    @admin.display(description="reach")
    def reach(self, obj):
        # mailto and tel, because answering is the point of this screen.
        parts = [format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)]
        if obj.phone:
            parts.append(format_html('<a href="tel:{}" dir="ltr">{}</a>', obj.phone, obj.phone))
        return format_html_join(mark_safe("<br>"), "{}", ((p,) for p in parts))

    @admin.display(description="received", ordering="created_at")
    def when(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")

    @admin.display(description="notes")
    def note_preview(self, obj):
        text = obj.notes.strip().splitlines()
        return f"{text[-1][:60]}…" if text else ""

    def has_add_permission(self, request):
        return False  # a request arrives from the form or it does not exist

    # ── triage writes ──────────────────────────────────────────────────────
    def save_model(self, request, obj, form, change):
        if "status" in form.changed_data:
            obj.read_at = None if obj.is_new else (obj.read_at or timezone.now())
        super().save_model(request, obj, form, change)
        if {"status", "notes"} & set(form.changed_data):
            # Repaint the notice in Bale, so the phone and this screen never
            # disagree about where a request stands.
            bot.refresh_later(obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Opening a request is reading it — the same as any other inbox."""
        if request.method == "GET":
            message = self.get_object(request, object_id)
            if message is not None and message.is_new:
                message.set_status(Message.Status.READ)
                bot.refresh_later(message)
        return super().change_view(request, object_id, form_url, extra_context)

    def _move(self, request, queryset, status, label):
        moved = [message for message in queryset if message.set_status(status)]
        for message in moved:  # only the ones that actually changed
            bot.refresh_later(message)
        self.message_user(request, f"{len(moved)} message(s) moved to {label}.")

    @admin.action(description="Mark as read")
    def mark_read(self, request, queryset):
        self._move(request, queryset, Message.Status.READ, "read")

    @admin.action(description="Reject")
    def mark_rejected(self, request, queryset):
        self._move(request, queryset, Message.Status.REJECTED, "rejected")

    @admin.action(description="Archive")
    def mark_archived(self, request, queryset):
        self._move(request, queryset, Message.Status.ARCHIVED, "archived")
