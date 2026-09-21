"""
The sitemap, in all three languages.

`i18n = True` writes one <url> per language — /, /en/ and /de/ — and
`alternates` links each to its siblings with xhtml:link hreflang, which is
what gets the German pages found by someone searching in German. x_default
is the unprefixed URL, matching the hreflang in base.html: it is the one that
picks a language by country.

A post is the exception: it is listed only in the languages it is written in
(`get_languages_for_item`), because the other language URLs are noindex.
"""

from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.content.models import Post, Profile, Project


class _Multilingual(Sitemap):
    i18n = True
    alternates = True
    x_default = True
    # The host comes from the request, but the scheme is pinned to SITE_URL's:
    # behind a TLS-terminating proxy the request itself looks like plain http.
    protocol = urlsplit(settings.SITE_URL).scheme or "https"


class StaticSitemap(_Multilingual):
    changefreq = "monthly"
    PRIORITY = {"home": 1.0, "services": 0.9, "project_list": 0.9}

    def items(self):
        profile = Profile.load()
        self._updated = profile.updated_at
        pages = ["home", "project_list", "resume", "about", "contact", "card"]
        # The services page 404s without an offer, so it is only listed with one.
        if profile.offer_title_fa or profile.offer_title_en or profile.offer_title_de:
            pages.insert(1, "services")
        # An empty blog is not offered in the nav, so it is not offered here.
        if Post.objects.filter(is_published=True).exists():
            pages.append("post_list")
        return pages

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.PRIORITY.get(item, 0.7)

    def lastmod(self, item):
        # Every one of these pages is mostly the profile.
        return self._updated


class ProjectSitemap(_Multilingual):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Project.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class PostSitemap(_Multilingual):
    changefreq = "weekly"
    priority = 0.7
    # x-default would name the Persian URL even for a post with no Persian.
    x_default = False

    def items(self):
        return Post.objects.filter(is_published=True)

    def get_languages_for_item(self, item):
        return item.languages

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "static": StaticSitemap,
    "projects": ProjectSitemap,
    "posts": PostSitemap,
}
