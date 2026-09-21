"""
Structured data — the schema.org JSON-LD search engines read.

Built as Python dicts and serialised once instead of hand-written JSON in the
templates: a quote in a title can no longer break the block, and every page
describes the same Person under the same @id, so Google joins the home page,
the posts and the services page into one entity.

Rendered by the tags in apps/core/templatetags/seo_tags.py.
"""

from __future__ import annotations

import json

from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from apps.content.models import LANG_CODES, Skill


def absolute(path: str) -> str:
    return f"{settings.SITE_URL}{path}"


def _lang() -> str:
    return (get_language() or settings.LANGUAGE_CODE).split("-")[0]


def _person_ref() -> dict:
    return {"@id": absolute("/#person")}


def render(*nodes: dict | None) -> str:
    """One <script type="application/ld+json"> holding every node as a @graph."""
    data = {"@context": "https://schema.org", "@graph": [node for node in nodes if node]}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # "</script>" inside a string would end the block early.
    text = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{text}</script>')  # noqa: S308


# ── the site and the person ────────────────────────────────────────────────
def website(profile) -> dict:
    return {
        "@type": "WebSite",
        "@id": absolute("/#website"),
        "url": absolute("/"),
        "name": profile.tr("full_name"),
        "inLanguage": list(LANG_CODES),
        "publisher": _person_ref(),
    }


def person(profile) -> dict:
    name = profile.tr("full_name")
    node = {
        "@type": "Person",
        "@id": absolute("/#person"),
        "name": name,
        "url": absolute(reverse("about")),
        "jobTitle": profile.tr("headline"),
        "description": profile.tr("seo_description") or profile.tr("intro"),
    }
    others = sorted({v for v in (profile.full_name_fa, profile.full_name_en, profile.full_name_de) if v and v != name})
    if others:
        node["alternateName"] = others
    if profile.share_image:
        node["image"] = absolute(profile.share_image.url)
    if profile.email:
        node["email"] = f"mailto:{profile.email}"
    if profile.tr("location"):
        node["address"] = {"@type": "PostalAddress", "addressLocality": profile.tr("location")}
    same_as = [link["href"] for link in profile.links if link["key"] in ("github", "linkedin", "telegram")]
    if same_as:
        node["sameAs"] = same_as
    skills = list(Skill.objects.filter(is_primary=True).values_list("name", flat=True))
    if skills:
        node["knowsAbout"] = skills
    return node


def profile_page(profile) -> dict:
    return {
        "@type": "ProfilePage",
        "@id": absolute(reverse("about")),
        "url": absolute(reverse("about")),
        "inLanguage": _lang(),
        "dateModified": profile.updated_at.isoformat(),
        "mainEntity": _person_ref(),
    }


def breadcrumbs(*crumbs: tuple[str, str]) -> dict:
    """crumbs are (name, path) pairs, home first."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": absolute(path)}
            for i, (name, path) in enumerate(crumbs, start=1)
        ],
    }


# ── content ────────────────────────────────────────────────────────────────
def blog_posting(post) -> dict:
    url = absolute(post.get_absolute_url())
    node = {
        "@type": "BlogPosting",
        "@id": f"{url}#post",
        "url": url,
        "mainEntityOfPage": url,
        "headline": post.tr("title")[:110],
        "inLanguage": post.content_language,
        "datePublished": post.published_at.isoformat(),
        "dateModified": max(post.updated_at, post.published_at).isoformat(),
        "author": _person_ref(),
        "publisher": _person_ref(),
        "wordCount": len(post.tr("body").split()),
    }
    if post.tr("excerpt"):
        node["description"] = post.tr("excerpt")
    image = post.lead_image
    if image:
        node["image"] = absolute(image.url)
    keywords = [tag.tr("name") for tag in post.tags.all()]
    if keywords:
        node["keywords"] = keywords
    if post.original_url:
        node["sameAs"] = post.original_url
    return node


def creative_work(project) -> dict:
    url = absolute(project.get_absolute_url())
    node = {
        "@type": "CreativeWork",
        "@id": f"{url}#work",
        "url": url,
        "name": project.tr("title"),
        "description": project.tr("summary"),
        "inLanguage": _lang(),
        "author": _person_ref(),
        "dateModified": project.updated_at.isoformat(),
    }
    if project.year:
        node["dateCreated"] = str(project.year)
    if project.stack_list:
        node["keywords"] = project.stack_list
    if project.cover:
        node["image"] = absolute(project.cover.url)
    if project.demo_url or project.repo_url:
        node["sameAs"] = [u for u in (project.demo_url, project.repo_url) if u]
    return node


def service(profile, services) -> dict:
    url = absolute(reverse("services"))
    node = {
        "@type": "Service",
        "@id": f"{url}#service",
        "url": url,
        "name": profile.tr("offer_title"),
        "description": profile.tr("offer_lede"),
        "provider": _person_ref(),
        "inLanguage": _lang(),
    }
    if services:
        node["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": profile.tr("offer_title"),
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s.tr("title"), "description": s.tr("body")}}
                for s in services
            ],
        }
    return node
