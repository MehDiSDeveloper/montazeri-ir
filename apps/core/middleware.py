"""Pick a first-visit language from the visitor's country.

Persian stays the language of the unprefixed URLs; this only decides whether a
*first-time* visitor on one of them is better served by /en/ or /de/. The rules
are narrow on purpose, because a wrong redirect is worse than none:

- **Only unprefixed (Persian) pages.** A reader who opened /en/ or /de/ chose it.
- **Only once.** The first answer sets `GEO_COOKIE_NAME`, whether it redirected
  or not, so a German visitor who then picks «فارسی» in the switcher stays there.
- **Never from inside the site.** A same-host Referer means a click on our own
  link — this is what keeps the switcher working when cookies are off.
- **Never for crawlers.** Search engines crawl mostly from the US; redirecting
  them would leave the Persian pages unindexed. hreflang already tells them
  which URL is which language.
- **Unknown country, no redirect.** No header and no database is "don't know".
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import translate_url
from django.utils.cache import patch_cache_control, patch_vary_headers
from django.utils.translation import get_language_from_path

from .geo import country_for

BOT_PATTERN = re.compile(
    r"bot|crawl|spider|slurp|preview|facebookexternalhit|embedly|whatsapp|telegram|lighthouse",
    re.IGNORECASE,
)


def language_for_country(country: str | None) -> str | None:
    if country is None:
        return None
    return settings.GEO_LANGUAGE_BY_COUNTRY.get(country, settings.GEO_FALLBACK_LANGUAGE)


class GeoLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._is_candidate(request):
            return self.get_response(request)

        redirect_to = self._redirect_target(request)
        response = HttpResponseRedirect(redirect_to) if redirect_to else self.get_response(request)
        if redirect_to:
            # The answer depends on who asked; no shared cache may keep it.
            patch_cache_control(response, private=True, no_cache=True)
        patch_vary_headers(response, ["Cookie"])
        self._remember(response)
        return response

    def _is_candidate(self, request) -> bool:
        return (
            settings.GEO_LANGUAGE_ENABLED
            and request.method in ("GET", "HEAD")
            and settings.GEO_COOKIE_NAME not in request.COOKIES
            and not BOT_PATTERN.search(request.headers.get("User-Agent", ""))
            and not self._from_this_site(request)
        )

    def _redirect_target(self, request) -> str | None:
        if get_language_from_path(request.path_info) is not None:
            return None  # an explicit /en/ or /de/ URL
        language = language_for_country(country_for(request))
        if language is None or language == settings.LANGUAGE_CODE:
            return None
        path = request.get_full_path()
        target = translate_url(path, language)
        # translate_url hands the path back untouched for anything outside
        # i18n_patterns (admin, sitemap, vCard, a 404) — leave those alone.
        return target if target != path else None

    @staticmethod
    def _from_this_site(request) -> bool:
        referer = request.headers.get("Referer")
        return bool(referer) and urlsplit(referer).netloc == request.get_host()

    @staticmethod
    def _remember(response) -> None:
        response.set_cookie(
            settings.GEO_COOKIE_NAME,
            "1",
            max_age=settings.GEO_COOKIE_AGE,
            samesite="Lax",
            secure=not settings.DEBUG,
            httponly=True,
        )
