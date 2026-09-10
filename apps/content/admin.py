"""
Stock Django admin — the interim way to edit content.

The custom lightweight panel is a later piece of work (see CLAUDE.md). Until it
exists this is what makes the database writable, and it costs nothing: the
per-language columns render as three plain inputs side by side.
"""

from django.contrib import admin

from .models import Experience, Message, Post, Profile, Project, Skill, SkillGroup, Tag


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


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


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("slug", "title_fa", "published_at", "is_published")
    list_filter = ("is_published", "tags")
    search_fields = ("slug", "title_fa", "title_en", "title_de")
    filter_horizontal = ("tags",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "is_handled")
    list_filter = ("is_handled", "language")
    readonly_fields = ("name", "email", "subject", "body", "language", "created_at")
    search_fields = ("name", "email", "body")
