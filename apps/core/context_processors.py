"""Everything every template needs, resolved once per request."""

from __future__ import annotations

from django.conf import settings
from django.urls import translate_url
from django.utils.translation import get_language

from django.urls import reverse

from apps.content.models import Post, Profile, Project

from .i18n import t

RTL_LANGUAGES = {"fa", "ar", "he"}
# Open Graph wants a territory as well as a language.
OG_LOCALES = {"fa": "fa_IR", "en": "en_US", "de": "de_DE"}


def _has_writing() -> bool:
    """Whether the writing section is worth offering at all.

    An empty blog behind a nav link reads worse than no blog: a reader who
    clicks "Writing" and lands on nothing concludes the site is unfinished.
    The link, the palette entry and the section come back on their own the
    moment a post is published.
    """
    return Post.objects.filter(is_published=True).exists()


def _command_index(has_offer: bool, has_writing: bool) -> list[dict]:
    """What Ctrl+K can jump to. Ships inside the page, so opening costs nothing.

    Two small queries per request. If this site ever grows past a few hundred
    rows, the answer is to cache this list, not to make the palette fetch.
    """
    # "i" is the icon id in templates/partials/icons.html, without the "i-".
    pages = [
        ("nav.home", "home", "home", True),
        ("nav.projects", "project_list", "grid", True),
        ("nav.services", "services", "briefcase", has_offer),
        ("nav.resume", "resume", "doc", True),
        ("nav.about", "about", "user", True),
        ("nav.writing", "post_list", "pen", has_writing),
        ("nav.contact", "contact", "mail", True),
        ("nav.card", "card", "qr", True),
    ]
    index = [{"t": t(key), "u": reverse(name), "k": "", "i": icon} for key, name, icon, shown in pages if shown]
    for project in Project.objects.filter(is_published=True):
        index.append({"t": project.tr("title"), "u": project.get_absolute_url(), "k": t("projects.title"), "i": "code"})
    for post in Post.objects.filter(is_published=True)[:30]:
        index.append({"t": post.tr("title"), "u": post.get_absolute_url(), "k": t("blog.title"), "i": "pen"})
    return index


def _alternates(path: str) -> list[dict]:
    """hreflang for this page: every language, plus x-default.

    Built from the path without its query string, so a filtered list
    (?tag=python) points search engines at the one real list, the same URL the
    canonical tag names. x-default is the unprefixed URL, the one that picks a
    language by country. A view that knows better (a post written in one
    language) passes `seo_alternates` instead.
    """
    out = [
        {"code": code, "href": f"{settings.SITE_URL}{translate_url(path, code)}"}
        for code, _ in settings.LANGUAGES
    ]
    out.append({"code": "x-default", "href": f"{settings.SITE_URL}{translate_url(path, settings.LANGUAGE_CODE)}"})
    return out


def site(request):
    lang = (get_language() or settings.LANGUAGE_CODE).split("-")[0]
    path = request.get_full_path()
    profile = Profile.load()
    has_offer = bool(profile.tr("offer_title"))
    has_writing = _has_writing()
    return {
        "profile": profile,
        "has_offer": has_offer,
        "has_writing": has_writing,
        "cmdk_index": _command_index(has_offer, has_writing),
        "lang": lang,
        "text_dir": "rtl" if lang in RTL_LANGUAGES else "ltr",
        "site_url": settings.SITE_URL,
        "canonical_url": f"{settings.SITE_URL}{request.path}",
        "alternates": _alternates(request.path),
        "og_locale": OG_LOCALES.get(lang, lang),
        "og_locale_alternates": [OG_LOCALES.get(code, code) for code, _ in settings.LANGUAGES if code != lang],
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
