"""
URL map.

Persian is the default language and is served without a prefix; English and
German live under /en/ and /de/. Everything the reader can see goes inside
i18n_patterns so a language switch is a real URL, shareable and indexable.
Machine endpoints (sitemap, feed, the vCard, the admin) stay outside it —
there is nothing to translate about a .vcf file.
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core import views as core_views
from apps.core.sitemaps import SITEMAPS

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", core_views.robots, name="robots"),
    path("feed.xml", core_views.PostFeed(), name="feed"),
    path("card/montazeri.vcf", core_views.vcard, name="vcard"),
    path("healthz", core_views.healthz, name="healthz"),
    # Where the Bale bot posts button presses. Outside i18n_patterns with the
    # rest of the machine endpoints: there is nothing to translate about an
    # update, and the address must stay exactly what setWebhook was told.
    path("bot/<str:secret>/", core_views.bot_webhook, name="bot_webhook"),
]

urlpatterns += i18n_patterns(
    path("", core_views.home, name="home"),
    path("about/", core_views.about, name="about"),
    path("services/", core_views.services, name="services"),
    path("contact/", core_views.contact, name="contact"),
    path("card/", core_views.card, name="card"),
    path("resume/", core_views.resume, name="resume"),
    path("", include("apps.content.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.not_found"
handler500 = "apps.core.views.server_error"
