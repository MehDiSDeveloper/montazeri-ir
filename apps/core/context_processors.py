"""Everything every template needs, resolved once per request."""

from __future__ import annotations

from django.conf import settings
from django.urls import translate_url
from django.utils.translation import get_language

from django.urls import reverse

from apps.content.models import Post, Profile, Project

from .i18n import t

RTL_LANGUAGES = {"fa", "ar", "he"}


def _command_index() -> list[dict]:
    """What Ctrl+K can jump to. Ships inside the page, so opening costs nothing.

    Two small queries per request. If this site ever grows past a few hundred
    rows, the answer is to cache this list, not to make the palette fetch.
    """
    pages = [
        ("nav.home", "home"),
        ("nav.projects", "project_list"),
        ("nav.writing", "post_list"),
        ("nav.about", "about"),
        ("nav.resume", "resume"),
        ("nav.card", "card"),
        ("nav.contact", "contact"),
    ]
    index = [{"t": t(key), "u": reverse(name), "k": ""} for key, name in pages]
    for project in Project.objects.filter(is_published=True):
        index.append({"t": project.tr("title"), "u": project.get_absolute_url(), "k": t("projects.title")})
    for post in Post.objects.filter(is_published=True)[:30]:
        index.append({"t": post.tr("title"), "u": post.get_absolute_url(), "k": t("blog.title")})
    return index


def site(request):
    lang = (get_language() or settings.LANGUAGE_CODE).split("-")[0]
    path = request.get_full_path()
    return {
        "profile": Profile.load(),
        "cmdk_index": _command_index(),
        "lang": lang,
        "text_dir": "rtl" if lang in RTL_LANGUAGES else "ltr",
        "site_url": settings.SITE_URL,
        # One entry per language, each pointing at *this* page in that language,
        # so switching never dumps the reader back on the home page.
        "language_links": [
            {
                "code": code,
                "label": label,
                "native": {"fa": "فارسی", "en": "English", "de": "Deutsch"}.get(code, label),
                "url": translate_url(path, code),
                "is_active": code == lang,
            }
            for code, label in settings.LANGUAGES
        ],
    }
