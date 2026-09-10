"""
Template tags — the only bridge between the Python side and the templates.

Four jobs: look up a UI string, read a translated model field, render Markdown,
and write a date the way the active language writes dates.
"""

from __future__ import annotations

import datetime as dt
import re

import markdown as md
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from apps.core import jalali
from apps.core.i18n import t as lookup

register = template.Library()

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

_MD = md.Markdown(
    extensions=["extra", "codehilite", "sane_lists", "toc"],
    extension_configs={"codehilite": {"guess_lang": False, "css_class": "code"}},
    output_format="html",
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


@register.filter(name="markdown")
def markdown_text(value: str):
    return _render_markdown(value or "")


def _render_markdown(text: str):
    if not text:
        return ""
    _MD.reset()
    return mark_safe(_MD.convert(text))  # noqa: S308 — input is our own content


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
