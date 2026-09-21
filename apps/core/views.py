"""
Page views.

Every page is a plain function returning a rendered template. There is no API,
no JSON and no client-side router: the server sends finished HTML and the
JavaScript in static/js/app.js only improves what is already on the screen.
"""

from __future__ import annotations

import json
import logging
import time

import segno
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.translation import get_language
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.content.models import Experience, Post, Profile, Project, Service, SkillGroup

from . import bot
from .forms import ContactForm
from .i18n import t

log = logging.getLogger("bot")


def _skill_groups():
    return SkillGroup.objects.prefetch_related("skills")


def _published_projects():
    return Project.objects.filter(is_published=True).prefetch_related("tags")


def _published_posts():
    return Post.objects.filter(is_published=True).prefetch_related("tags")


# ── pages ──────────────────────────────────────────────────────────────────
HERO_EXTRA_SKILLS = ("PostgreSQL",)


def home(request):
    profile = Profile.load()
    featured = list(_published_projects().filter(is_featured=True)[:3])
    if not featured:
        featured = list(_published_projects()[:3])
    groups = list(_skill_groups())
    # The chips floating round the portrait: the first primary skill of each
    # group, so four chips say four different things instead of "C#" three ways,
    # plus the named extras — PostgreSQL is the database of the recent projects
    # and would otherwise lose its group's slot to SQL Server.
    firsts = [next((s for s in g.skills.all() if s.is_primary), None) for g in groups]
    extras = [s for g in groups for s in g.skills.all() if s.name in HERO_EXTRA_SKILLS]
    return render(
        request,
        "pages/home.html",
        {
            "featured_projects": featured,
            "skill_groups": groups,
            "primary_skills": [s for g in groups for s in g.skills.all() if s.is_primary][:10],
            "hero_skills": [s for s in firsts if s][:4] + [s for s in extras if s not in firsts],
            "experiences": Experience.objects.filter(kind=Experience.Kind.WORK)[:3],
            "posts": _published_posts()[:2],
            "services": list(Service.objects.all()),
            "profile": profile,
        },
    )


def services(request):
    """Project work: what a client gets, and the one button that starts it.

    It is the page that earns, so it is a real indexed URL in all three
    languages rather than a section only the home page has. No offer written,
    no page — the nav link and the home band disappear with it.
    """
    if not Profile.load().tr("offer_title"):
        raise Http404
    return render(request, "pages/services.html", {"services": list(Service.objects.all())})


def about(request):
    return render(
        request,
        "pages/about.html",
        {
            "work": Experience.objects.filter(kind=Experience.Kind.WORK),
            "education": Experience.objects.filter(kind=Experience.Kind.EDUCATION),
            "skill_groups": _skill_groups(),
        },
    )


def contact(request):
    """POST -> save -> redirect. A refresh must never resend a message."""
    sent = request.GET.get("sent") == "1"
    # "Start a project" links here with ?topic=project, so the subject is
    # already filled in and the message is easy to spot in the admin list.
    initial = {"subject": t("services.subject")} if request.GET.get("topic") == "project" else {}
    form = ContactForm(initial=initial)
    throttled = False

    if request.method == "POST":
        form = ContactForm(request.POST)
        last = request.session.get("contact_last_sent", 0)
        throttled = (time.time() - last) < settings.CONTACT_RATE_LIMIT_SECONDS

        if form.is_valid() and not throttled:
            if form.is_spam():
                return redirect(f"{reverse('contact')}?sent=1")  # answer a bot the same way
            message = form.save(commit=False)
            message.language = get_language() or settings.LANGUAGE_CODE
            message.save()
            # The request is stored first and announced second: a messenger
            # that is slow or down may not cost a lead. See apps/core/bot.py.
            bot.notify_new(message)
            request.session["contact_last_sent"] = time.time()
            return redirect(f"{reverse('contact')}?sent=1")

    return render(request, "pages/contact.html", {"form": form, "sent": sent, "throttled": throttled})


def card(request):
    """The digital business card: one screen, made to be scanned."""
    profile = Profile.load()
    card_url = f"{settings.SITE_URL}{reverse('card')}"
    # segno will not take "currentColor", so the QR is drawn in a sentinel hex
    # and swapped for the keyword here. That is what lets one SVG be legible in
    # both themes without rendering the code twice.
    qr = segno.make(card_url, error="m")
    qr_svg = qr.svg_inline(border=0, omitsize=True, dark="#000000").replace('stroke="#000"', 'stroke="currentColor"')
    return render(
        request,
        "pages/card.html",
        {
            "card_url": card_url,
            "qr_svg": qr_svg,
            "vcard_url": reverse("vcard"),
            "profile": profile,
        },
    )


def resume(request):
    return render(
        request,
        "pages/resume.html",
        {
            "work": Experience.objects.filter(kind=Experience.Kind.WORK),
            "education": Experience.objects.filter(kind=Experience.Kind.EDUCATION),
            "skill_groups": _skill_groups(),
            "projects": _published_projects().filter(is_featured=True)[:4],
        },
    )


# ── machine endpoints ──────────────────────────────────────────────────────
def vcard(request):
    """A real .vcf, so a phone can save the contact instead of a screenshot."""
    p = Profile.load()
    name = p.tr("full_name") or p.full_name_en or "Mahdi Montazeri"
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{name}",
        f"N:{name.split()[-1] if ' ' in name else name};{name.split()[0]};;;",
        f"TITLE:{p.tr('headline')}",
    ]
    if p.email:
        lines.append(f"EMAIL;TYPE=INTERNET,PREF:{p.email}")
    if p.phone:
        lines.append(f"TEL;TYPE=CELL:{p.phone}")
    if p.tr("location"):
        lines.append(f"ADR;TYPE=WORK:;;;{p.tr('location')};;;")
    lines.append(f"URL:{settings.SITE_URL}")
    if p.github:
        lines.append(f"X-SOCIALPROFILE;TYPE=github:https://github.com/{p.github.strip('/').split('/')[-1]}")
    if p.linkedin:
        lines.append(f"X-SOCIALPROFILE;TYPE=linkedin:https://www.linkedin.com/in/{p.linkedin.strip('/').split('/')[-1]}")
    lines.append("END:VCARD")

    body = "\r\n".join(lines) + "\r\n"
    response = HttpResponse(body, content_type="text/vcard; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="montazeri.vcf"'
    return response


def robots(request):
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /i18n/",
            "Disallow: /healthz",
            "Disallow: /bot/",
            f"Sitemap: {settings.SITE_URL}/sitemap.xml",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


@csrf_exempt
@require_POST
def bot_webhook(request, secret: str):
    """Where Bale posts a button press or a note.

    A webhook rather than long-polling because this site is one container with
    one process: a poller would need a second one, and a public HTTPS address
    already exists. `manage.py bale poll` covers the case where it does not —
    local work, mostly.

    Three things guard it: an unguessable path compared in constant time, the
    endpoint not existing at all when no secret is configured, and every
    action in bot.py checking the update really came from the owner's chat.
    A malformed body is answered 200 and dropped, because a messenger that is
    told "error" will send the same update again, forever.
    """
    if not settings.BOT_WEBHOOK_SECRET or not constant_time_compare(secret, settings.BOT_WEBHOOK_SECRET):
        raise Http404

    try:
        update = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return HttpResponse("ok", content_type="text/plain")

    if isinstance(update, dict):
        try:
            bot.handle_update(update)
        except Exception:  # noqa: BLE001 — never ask for a redelivery
            log.exception("bot: handling update %s failed", update.get("update_id"))

    return HttpResponse("ok", content_type="text/plain")


class PostFeed(Feed):
    link = "/blog/"

    def title(self):
        return Profile.load().tr("full_name")

    def description(self):
        return Profile.load().tr("headline")

    def author_name(self):
        return Profile.load().tr("full_name")

    def items(self):
        return Post.objects.filter(is_published=True).prefetch_related("tags")[:20]

    def item_title(self, item):
        return item.tr("title")

    def item_description(self, item):
        return item.tr("excerpt")

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_categories(self, item):
        return [tag.tr("name") for tag in item.tags.all()]


# ── error pages ────────────────────────────────────────────────────────────
def not_found(request, exception=None):
    return render(
        request,
        "pages/error.html",
        {"code": "404", "title": t("err.404_title"), "body": t("err.404_body")},
        status=404,
    )


def server_error(request):
    return render(
        request,
        "pages/error.html",
        {"code": "500", "title": t("err.500_title"), "body": t("err.500_body")},
        status=500,
    )
