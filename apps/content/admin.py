"""
Stock Django admin — the interim way to edit content.

The custom lightweight panel is a later piece of work (see CLAUDE.md). Until it
exists this is what makes the database writable, and it costs nothing: the
per-language columns render as three plain inputs side by side.

The post form is the one screen written for regular use, so it gets the most
care: one block per language, a body box big enough to write in, and images
uploaded on the same page with the Markdown line to paste already built.
"""

import re
from datetime import timedelta

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.template.defaultfilters import linebreaksbr
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
    normalise_tracking_code,
)

LANG_NAMES = {"fa": "فارسی — Persian", "en": "English", "de": "Deutsch — German"}


def _per_language(*names):
    return [
        (LANG_NAMES.get(code, code), {"fields": [f"{name}_{code}" for name in names]})
        for code in LANG_CODES
    ]


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg")


class UploadWidget(AdminFileWidget):
    """The stock file input, plus what it never tells you.

    A chosen file only reaches the server when the form is saved, and the stock
    input shows nothing but its name. This one shows the file that is live now,
    a preview of the one waiting, an undo for the choice, and — through
    admin-upload.js — a bar that stays on screen until «ذخیره» is pressed.
    """

    class Media:
        css = {"all": ["css/admin-upload.css"]}
        js = ["js/admin-upload.js"]

    def render(self, name, value, attrs=None, renderer=None):
        live = ""
        if value and getattr(value, "url", None) and value.name.lower().endswith(IMAGE_EXTENSIONS):
            live = format_html(
                '<a class="upload-live" href="{0}" target="_blank" rel="noopener" '
                'title="همین الان روی سایت است"><img src="{0}" alt=""></a>',
                value.url,
            )
        return format_html(
            '<div class="upload" data-upload>{}<div class="upload-field">{}'
            '<div class="upload-new" hidden><img alt="" hidden>'
            '<span><b class="upload-name"></b><small>با «ذخیره» اعمال می‌شود و روی سایت می‌نشیند</small></span>'
            '<button type="button" class="button" data-upload-undo>✕ منصرف شدم</button></div>'
            '<small class="upload-gone" hidden>با «ذخیره» از سایت حذف می‌شود</small>'
            "</div></div>",
            live,
            super().render(name, value, attrs, renderer),
        )


# Every admin with a file field uses these, inlines included. ImageField needs
# its own key: the admin matches a field's own class before its parent's.
UPLOADS = {
    models.ImageField: {"widget": UploadWidget(attrs={"accept": "image/*"})},
    models.FileField: {"widget": UploadWidget},
}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """One row, so the list is skipped and the pictures come first.

    The form is long — every text in three languages — and the file inputs used
    to sit somewhere in the middle with «ذخیره» far below, so a chosen photo
    looked taken while nothing had been sent.
    """

    formfield_overrides = UPLOADS
    save_on_top = True
    fieldsets = [
        (
            "عکس‌ها و فایل‌ها — pictures and files",
            {
                "fields": ("avatar", "og_image", "resume_file"),
                "description": "فایل را انتخاب کنید و «ذخیره» را بزنید؛ تا ذخیره نشود روی سایت نمی‌آید. "
                "برای برداشتن چیزی که الان روی سایت است، تیک «پاک کردن» کنارش را بزنید و ذخیره کنید.",
            },
        ),
        ("Contact", {"fields": ("email", "phone", "telegram", "github", "linkedin", "twitter", "website", "is_available")}),
        *_per_language(*Profile.I18N_FIELDS),
    ]

    def changelist_view(self, request, extra_context=None):
        # A list of one row is a detour, and «ذخیره» lands here: send it back
        # to the form, where the success message and the new picture show.
        return redirect("admin:content_profile_change", Profile.load().pk)

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
    formfield_overrides = UPLOADS
    save_on_top = True
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
    formfield_overrides = UPLOADS
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
    formfield_overrides = UPLOADS
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
    Message.Status.ANSWERED: "#c7a8f0",
    Message.Status.REJECTED: "#f2a2a2",
    Message.Status.ARCHIVED: "#c9c4bd",
}


def _fa(label: str) -> str:
    """The Persian half of a choice label: «جدید — new» → «جدید»."""
    return str(label).split(" — ")[0]


class StatusFilter(admin.SimpleListFilter):
    """Several statuses at once, not one at a time.

    No parameter is the inbox's resting state, «active»: what still needs the
    owner — new and read — and nothing that is answered, refused or put away.
    «All» is every status. Each status below is a toggle: clicking one adds
    it to what is shown or takes it away, so "new + answered" is two clicks.

    The value in the address is `?status=all` or `?status=new,answered`, so a
    filtered inbox is still a link that can be bookmarked.
    """

    title = "وضعیت — status"
    parameter_name = "status"
    ALL = "all"

    def lookups(self, request, model_admin):
        return Message.Status.choices  # unused by choices(); keeps has_output() true

    def selected(self) -> set[str]:
        value = self.value()
        if value is None:
            return set(Message.ACTIVE)
        if value == self.ALL:
            return set(Message.Status.values)
        picked = {part for part in value.split(",") if part in Message.Status.values}
        return picked or set(Message.ACTIVE)

    def queryset(self, request, queryset):
        if self.value() == self.ALL:
            return queryset
        return queryset.filter(status__in=self.selected())

    def _link(self, changelist, statuses: set[str]) -> str:
        if statuses == set(Message.ACTIVE):
            return changelist.get_query_string(remove=[self.parameter_name])
        if statuses == set(Message.Status.values):
            return changelist.get_query_string({self.parameter_name: self.ALL})
        ordered = [s for s in Message.Status.values if s in statuses]  # a stable address
        return changelist.get_query_string({self.parameter_name: ",".join(ordered)})

    def choices(self, changelist):
        counts = dict(
            Message.objects.values_list("status").annotate(n=Count("pk")).values_list("status", "n")
        )
        selected = self.selected()
        active_n = sum(counts.get(s, 0) for s in Message.ACTIVE)

        yield {
            "selected": self.value() is None,
            "query_string": self._link(changelist, set(Message.ACTIVE)),
            "display": f"فعال — جدید و خوانده‌شده ({active_n})",
        }
        yield {
            "selected": self.value() == self.ALL,
            "query_string": self._link(changelist, set(Message.Status.values)),
            "display": f"همه ({sum(counts.values())})",
        }
        for value, label in Message.Status.choices:
            on = value in selected
            toggled = selected - {value} if on else selected | {value}
            yield {
                "selected": on and self.value() not in (None, self.ALL),
                # The last one ticked cannot be unticked: an inbox filtered to
                # nothing is a screen that only looks broken.
                "query_string": self._link(changelist, toggled or selected),
                "display": f"{'☑' if on else '☐'} {_fa(label)} ({counts.get(value, 0)})",
            }


class DeadlineFilter(admin.SimpleListFilter):
    """How close the visitor's own deadline is. Choosing any of these also
    sorts the list closest-first — see MessageAdmin.get_ordering."""

    title = "مهلت — deadline"
    parameter_name = "due"

    def lookups(self, request, model_admin):
        return [
            ("overdue", "گذشته — overdue"),
            ("3", "تا ۳ روز — 3 days"),
            ("7", "تا ۷ روز — a week"),
            ("30", "تا ۳۰ روز — a month"),
            ("later", "بیش از ۳۰ روز — later"),
            ("none", "بدون مهلت — flexible"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        now = timezone.now()
        if value == "overdue":
            return queryset.filter(due_at__lt=now)
        if value in {"3", "7", "30"}:
            return queryset.filter(due_at__gte=now, due_at__lte=now + timedelta(days=int(value)))
        if value == "later":
            return queryset.filter(due_at__gt=now + timedelta(days=30))
        if value == "none":
            return queryset.filter(due_at__isnull=True)
        return queryset


class MessageAdminForm(forms.ModelForm):
    """Triage plus one box that is not a column: the answer to the visitor.
    Filled in, it becomes a `Reply` on save and the request «answered»."""

    reply = forms.CharField(
        required=False,
        label="پاسخ به درخواست‌کننده — reply",
        help_text="در صفحهٔ پیگیری او نمایش داده می‌شود و وضعیت «پاسخ داده شده» می‌شود. "
        "Shown on the visitor's tracking page; the request becomes «answered».",
        widget=forms.Textarea(attrs={"rows": 5, "dir": "auto", "style": "width:100%;max-width:48rem;line-height:1.8"}),
    )

    class Meta:
        model = Message
        fields = ("status", "notes")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """The inbox.

    What a visitor wrote is read-only — a request is a record, and editing it
    would make the notice already sitting in Bale a lie. What is editable is
    the triage — the status and the private notes, the same two things the
    bot's buttons write — and the conversation, which only ever grows.

    Finding a request: the search box takes a name, a company, an email or a
    phone, a tracking code (with or without the dash), `#12`, any word from
    the request or its replies, or a request type by name («مشاوره», «project»).
    The status filter decides which states the search looks in; the deadline
    filter narrows by how close the visitor's own deadline is.
    """

    form = MessageAdminForm
    list_display = ("state", "who", "reach", "kind_label", "deadline", "subject", "turns", "when", "note_preview")
    list_display_links = ("who",)
    list_filter = (StatusFilter, DeadlineFilter, "kind", "language")
    search_fields = (
        "name", "company", "email", "phone", "subject", "body", "notes", "tracking_code", "replies__body",
    )
    search_help_text = (
        "نام، شرکت، ایمیل، تلفن، کد پیگیری، ‎#شماره، نوع درخواست یا هر کلمه از متن — "
        "در وضعیت‌هایی که از فیلتر کنار صفحه انتخاب شده‌اند (پیش‌فرض: فعال)."
    )
    date_hierarchy = "created_at"
    actions = ("mark_read", "mark_rejected", "mark_archived")
    readonly_fields = (
        "name", "company", "email", "phone", "kind", "timeline", "deadline_full", "subject", "body",
        "tracking", "conversation", "language", "created_at", "read_at", "notified_at",
    )
    fieldsets = [
        ("What was sent", {"fields": (
            ("name", "company"), ("email", "phone"), ("kind", "timeline", "deadline_full"), "subject", "body",
        )}),
        ("Conversation", {"fields": ("tracking", "conversation", "reply")}),
        ("Triage", {"fields": ("status", "notes")}),
        ("When", {"fields": ("language", "created_at", "read_at", "notified_at"), "classes": ["collapse"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(reply_count=Count("replies"))

    def get_ordering(self, request):
        # Filtering by deadline is asking "what is due first", so answer it in
        # that order. A column the owner clicked (?o=) still wins.
        if request.GET.get(DeadlineFilter.parameter_name):
            return ("due_at", "-created_at")
        return super().get_ordering(request)

    def get_search_results(self, request, queryset, search_term):
        found, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        term = search_term.strip()
        if not term:
            return found, may_have_duplicates

        extra = Q()
        numbered = re.fullmatch(r"#?(\d+)", term)
        if numbered:
            extra |= Q(pk=int(numbered.group(1)))
        code = normalise_tracking_code(term)
        if code:
            extra |= Q(tracking_code=code)
        if len(term) >= 3:
            kinds = [value for value, label in Message.Kind.choices if term.lower() in label.lower()]
            if kinds:
                extra |= Q(kind__in=kinds)
        if extra:
            found = found | queryset.filter(extra)
        return found, may_have_duplicates

    # ── columns ────────────────────────────────────────────────────────────
    @admin.display(description="status", ordering="status")
    def state(self, obj):
        return format_html(
            '<b style="color:{}">●</b> {}',
            STATUS_COLOURS.get(obj.status, "#999"),
            _fa(obj.get_status_display()),
        )

    @admin.display(description="name · company", ordering="name")
    def who(self, obj):
        if not obj.company:
            return obj.name
        return format_html('{}<br><small style="color:var(--body-quiet-color)">{}</small>', obj.name, obj.company)

    @admin.display(description="reach")
    def reach(self, obj):
        # mailto and tel, because answering is the point of this screen.
        parts = [format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)]
        if obj.phone:
            parts.append(format_html('<a href="tel:{}" dir="ltr">{}</a>', obj.phone, obj.phone))
        return format_html_join(mark_safe("<br>"), "{}", ((p,) for p in parts))

    @admin.display(description="type", ordering="kind")
    def kind_label(self, obj):
        return _fa(obj.get_kind_display())

    @admin.display(description="deadline", ordering="due_at")
    def deadline(self, obj):
        days = obj.days_left()
        if days is None:
            return format_html('<span style="color:var(--body-quiet-color)">{}</span>', _fa(obj.get_timeline_display()))
        if days < 0:
            text, colour = f"{-days} روز گذشته", "#d9534f"
        elif days == 0:
            text, colour = "امروز", "#e8871e"
        elif days <= 3:
            text, colour = f"{days} روز مانده", "#e8871e"
        else:
            text, colour = f"{days} روز مانده", ""
        # A deadline stops being urgent once the request is no longer active.
        if not obj.is_active:
            colour = "var(--body-quiet-color)"
        return format_html('<span style="color:{};font-weight:600;white-space:nowrap">{}</span>', colour or "inherit", text)

    @admin.display(description="replies", ordering="reply_count")
    def turns(self, obj):
        return f"💬 {obj.reply_count}" if obj.reply_count else ""

    @admin.display(description="received", ordering="created_at")
    def when(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")

    @admin.display(description="notes")
    def note_preview(self, obj):
        text = obj.notes.strip().splitlines()
        return f"{text[-1][:60]}…" if text else ""

    # ── the change page ────────────────────────────────────────────────────
    @admin.display(description="deadline")
    def deadline_full(self, obj):
        if obj.due_at is None:
            return "—"
        return format_html("{} &nbsp;·&nbsp; {}", obj.due_at.strftime("%Y-%m-%d"), self.deadline(obj))

    @admin.display(description="tracking code")
    def tracking(self, obj):
        return format_html(
            '<code style="font-size:1.1em;letter-spacing:.08em;user-select:all">{}</code> &nbsp; '
            '<a href="{}" target="_blank" rel="noopener">صفحهٔ پیگیری — the visitor\'s page ↗</a>',
            obj.tracking_code,
            obj.get_absolute_url(),
        )

    @admin.display(description="conversation")
    def conversation(self, obj):
        replies = list(obj.replies.all())
        if not replies:
            return "هنوز پاسخی رد و بدل نشده — no replies yet."
        turns = []
        for reply in replies:
            if reply.from_owner:
                who, style = "شما — you", "background:var(--selected-bg);margin-inline-start:0;margin-inline-end:auto"
            else:
                who, style = obj.name, "background:var(--darkened-bg);margin-inline-start:auto;margin-inline-end:0"
            if reply.event == reply.Event.CANCELLED:
                body = "🚫 درخواست را از بله لغو کرد — cancelled the request from Bale"
            else:
                body = linebreaksbr(reply.body)
            turns.append((style, who, reply.created_at.strftime("%Y-%m-%d %H:%M"), body))
        return format_html(
            '<div style="display:grid;gap:10px;max-width:48rem">{}</div>',
            format_html_join(
                "",
                '<div style="{};max-width:85%;padding:10px 14px;border-radius:12px;'
                'border:1px solid var(--hairline-color)"><div style="font-size:.85em;'
                'color:var(--body-quiet-color);margin-bottom:4px"><b>{}</b> · {}</div>'
                '<div dir="auto" style="line-height:1.8">{}</div></div>',
                turns,
            ),
        )

    def has_add_permission(self, request):
        return False  # a request arrives from the form or it does not exist

    # ── triage writes ──────────────────────────────────────────────────────
    def save_model(self, request, obj, form, change):
        if "status" in form.changed_data:
            obj.read_at = None if obj.is_new else (obj.read_at or timezone.now())
        super().save_model(request, obj, form, change)
        answer = (form.cleaned_data.get("reply") or "").strip()
        if answer:
            obj.add_reply(answer, from_owner=True)
        if answer or {"status", "notes"} & set(form.changed_data):
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
