"""
Page views.

Every page is a plain function returning a rendered template. There is no API,
no JSON and no client-side router: the server sends finished HTML and the
JavaScript in static/js/app.js only improves what is already on the screen.
"""

from __future__ import annotations

import time

import segno
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import get_language

from apps.content.models import Experience, Post, Profile, Project, SkillGroup

from .forms import ContactForm
from .i18n import t


def _skill_groups():
    return SkillGroup.objects.prefetch_related("skills")


def _published_projects():
    return Project.objects.filter(is_published=True).prefetch_related("tags")


def _published_posts():
    return Post.objects.filter(is_published=True).prefetch_related("tags")


# ── pages ──────────────────────────────────────────────────────────────────
def home(request):
    profile = Profile.load()
    featured = list(_published_projects().filter(is_featured=True)[:3])
    if not featured:
        featured = list(_published_projects()[:3])
    return render(
        request,
        "pages/home.html",
        {
            "featured_projects": featured,
            "skill_groups": _skill_groups(),
            "primary_skills": [s for g in _skill_groups() for s in g.skills.all() if s.is_primary][:10],
            "experiences": Experience.objects.filter(kind=Experience.Kind.WORK)[:3],
            "posts": _published_posts()[:2],
            "profile": profile,
        },
    )


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
    form = ContactForm()
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
        lines.append(f"X-SOCIALPROFILE;TYPE=linkedin:https://linkedin.com/in/{p.linkedin.strip('/').split('/')[-1]}")
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
            f"Sitemap: {settings.SITE_URL}/sitemap.xml",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


class PostFeed(Feed):
    link = "/blog/"

    def title(self):
        return Profile.load().tr("full_name")

    def description(self):
        return Profile.load().tr("headline")

    def items(self):
        return Post.objects.filter(is_published=True)[:20]

    def item_title(self, item):
        return item.tr("title")

    def item_description(self, item):
        return item.tr("excerpt")

    def item_pubdate(self, item):
        return item.published_at


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
