"""
Template tags — the only bridge between the Python side and the templates.

Four jobs: look up a UI string, read a translated model field, render Markdown,
and write a date the way the active language writes dates.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import xml.etree.ElementTree as etree

import markdown as md
from django import template
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.util import AtomicString

from apps.core import jalali
from apps.core.i18n import t as lookup

register = template.Library()


@register.simple_tag
def static_v(path: str) -> str:
    """`{% static %}` plus a cache-buster where the URL does not carry one.

    Outside DEBUG the manifest storage already hashes every file name. Under
    DEBUG (the dev container behind the Cloudflare tunnel) `site.css` is one
    fixed URL, so Cloudflare's edge and the phone kept the old copy after an
    edit; the file's mtime in the query makes each edit a new URL.
    """
    from django.contrib.staticfiles import finders
    from django.templatetags.static import static

    url = static(path)
    if settings.DEBUG:
        found = finders.find(path)
        if found:
            import os
            url += f"?v={int(os.path.getmtime(found))}"
    return url

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

JALALI_MONTHS = (
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
)
EN_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
DE_MONTHS = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)

# A bare https://… becomes a link, as it does on LinkedIn. Not when it follows
# a quote, "=" or "(" — that is a URL already inside raw HTML or a Markdown
# link — and trailing punctuation, Latin or Persian, stays outside the link.
BARE_URL = r"(?<![\w/\"'=(\]])(https?://[^\s<>\"]+[^\s<>\".,;:!?)\]'»«،؛])"


class _BareLink(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element("a")
        el.set("href", m.group(1))
        el.text = AtomicString(m.group(1))
        return el, m.start(0), m.end(0)


class _WebDefaults(Treeprocessor):
    """Images load lazily; a link off the site opens in a new tab."""

    def run(self, root):
        for img in root.iter("img"):
            img.set("loading", "lazy")
            img.set("decoding", "async")
        for a in root.iter("a"):
            href = a.get("href", "")
            if href.startswith(("http://", "https://")) and not href.startswith(settings.SITE_URL):
                a.set("target", "_blank")
                a.set("rel", "noopener")


class _WebExtension(Extension):
    def extendMarkdown(self, md_instance):
        # 105: after <autolink> (120), before line breaks (100) and raw HTML (90).
        md_instance.inlinePatterns.register(_BareLink(BARE_URL, md_instance), "bare_link", 105)
        # After the inline pass (20), so the links exist to be looked at.
        md_instance.treeprocessors.register(_WebDefaults(md_instance), "web_defaults", 5)


_EXTENSIONS = ["extra", "codehilite", "sane_lists", "toc"]
_CONFIG = {"codehilite": {"guess_lang": False, "css_class": "code"}}

_MD = md.Markdown(extensions=[*_EXTENSIONS, _WebExtension()], extension_configs=_CONFIG, output_format="html")
# Posts keep single line breaks. The long seeded fields (bio, case studies) are
# hard-wrapped at 80 columns in seed_profile.py and must not.
_MD_BREAKS = md.Markdown(
    extensions=[*_EXTENSIONS, "nl2br", _WebExtension()], extension_configs=_CONFIG, output_format="html"
)


def _lang() -> str:
    return (get_language() or "fa").split("-")[0]


# ── UI strings ─────────────────────────────────────────────────────────────
@register.simple_tag
def t(key: str) -> str:
    return lookup(key)


# ── translated model fields ────────────────────────────────────────────────
@register.filter(name="tr")
def tr(obj, field: str) -> str:
    """{{ project|tr:"title" }} — the active language, with fallback."""
    if obj is None:
        return ""
    getter = getattr(obj, "tr", None)
    return getter(field) if callable(getter) else ""


@register.filter(name="md")
def md_field(obj, field: str):
    """{{ project|md:"body" }} — a translated Markdown field, rendered."""
    return _render_markdown(tr(obj, field))


@register.filter(name="md_breaks")
def md_breaks_field(obj, field: str):
    """{{ post|md_breaks:"body" }} — as `md`, but a line break stays a line break."""
    return _render_markdown(tr(obj, field), _MD_BREAKS)


@register.filter(name="markdown")
def markdown_text(value: str):
    return _render_markdown(value or "")


@register.filter(name="plain")
def plain(value: str) -> str:
    """Markdown flattened to one line of text — for a meta description."""
    text = html.unescape(strip_tags(_render_markdown(value or "")))
    return re.sub(r"\s+", " ", text).strip()


def _render_markdown(text: str, renderer: md.Markdown = _MD):
    if not text:
        return ""
    renderer.reset()
    return mark_safe(renderer.convert(text))  # noqa: S308 — input is our own content


# ── numbers and dates ──────────────────────────────────────────────────────
@register.filter(name="fa_num")
def fa_num(value) -> str:
    """Persian digits, but only for a Persian reader."""
    text = "" if value is None else str(value)
    return text.translate(PERSIAN_DIGITS) if _lang() == "fa" else text


@register.filter(name="smart_date")
def smart_date(value, fmt: str = "month-year") -> str:
    """A date in the calendar the active language actually uses.

    fmt: "month-year" | "day-month-year" | "year"
    """
    if not value:
        return ""
    if isinstance(value, dt.datetime):
        value = value.date()

    lang = _lang()
    if lang == "fa":
        year, month, day = jalali.to_jalali(value)
        name = JALALI_MONTHS[month - 1]
        if fmt == "year":
            out = str(year)
        elif fmt == "day-month-year":
            out = f"{day} {name} {year}"
        else:
            out = f"{name} {year}"
        return out.translate(PERSIAN_DIGITS)

    months = DE_MONTHS if lang == "de" else EN_MONTHS
    name = months[value.month - 1]
    if fmt == "year":
        return str(value.year)
    if fmt == "day-month-year":
        return f"{value.day} {name} {value.year}" if lang == "de" else f"{name} {value.day}, {value.year}"
    return f"{name} {value.year}"


@register.simple_tag
def duration(start, end=None) -> str:
    """How long a role ran, written the way a CV writes it: "2 yrs 5 mos".

    Counted inclusively by month, as LinkedIn and a German Lebenslauf both do,
    so Nov 2023 – Mar 2026 is 2 yrs 5 mos. It is arithmetic on the two dates
    already printed beside it, not a new claim. A missing end means today.
    """
    if not start:
        return ""
    end = end or dt.date.today()
    total = max(1, (end.year - start.year) * 12 + (end.month - start.month) + 1)
    years, months = divmod(total, 12)
    parts = []
    if years:
        parts.append(f"{years} {lookup('dur.year' if years == 1 else 'dur.years')}")
    if months:
        parts.append(f"{months} {lookup('dur.month' if months == 1 else 'dur.months')}")
    return fa_num(lookup("dur.and").join(parts))


@register.filter(name="iso")
def iso(value) -> str:
    """Machine-readable date for <time datetime="…">."""
    if not value:
        return ""
    return value.isoformat()


# ── misc ───────────────────────────────────────────────────────────────────
@register.filter(name="initials")
def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", (name or "").strip()) if p]
    return "".join(p[0] for p in parts[:2]).upper()


@register.simple_tag(takes_context=True)
def active(context, *url_names) -> str:
    """"is-active" when the current view is one of these, for nav links."""
    match = context.get("request").resolver_match if context.get("request") else None
    return "is-active" if match and match.url_name in url_names else ""
