"""
Structured-data tags. Each emits one finished JSON-LD block from apps/core/seo.py.

    {% load seo_tags %}
    {% ld_site %}               WebSite + Person — every page, from base.html
    {% ld_profile_page %}       /about/
    {% ld_post post %}          a post, with its breadcrumb
    {% ld_project project %}    a case study, with its breadcrumb
    {% ld_services services %}  /services/, with its breadcrumb
"""

from __future__ import annotations

from django import template
from django.urls import reverse

from apps.core import seo
from apps.core.i18n import t

register = template.Library()


@register.simple_tag(takes_context=True)
def ld_site(context):
    profile = context["profile"]
    return seo.render(seo.website(profile), seo.person(profile))


@register.simple_tag(takes_context=True)
def ld_profile_page(context):
    profile = context["profile"]
    return seo.render(
        seo.profile_page(profile),
        seo.breadcrumbs((t("nav.home"), reverse("home")), (t("nav.about"), reverse("about"))),
    )


@register.simple_tag
def ld_post(post):
    return seo.render(
        seo.blog_posting(post),
        seo.breadcrumbs(
            (t("nav.home"), reverse("home")),
            (t("blog.title"), reverse("post_list")),
            (post.tr("title"), post.get_absolute_url()),
        ),
    )


@register.simple_tag
def ld_project(project):
    return seo.render(
        seo.creative_work(project),
        seo.breadcrumbs(
            (t("nav.home"), reverse("home")),
            (t("projects.title"), reverse("project_list")),
            (project.tr("title"), project.get_absolute_url()),
        ),
    )


@register.simple_tag(takes_context=True)
def ld_services(context, services):
    return seo.render(
        seo.service(context["profile"], services),
        seo.breadcrumbs((t("nav.home"), reverse("home")), (t("nav.services"), reverse("services"))),
    )
