"""
Project and post views.

Filtering is deliberately client-side: a personal site has tens of projects,
not thousands, so the whole list is rendered once and the tag chips hide rows
instantly with no request. The server still honours ?tag= so a filtered list is
a shareable URL and a crawler sees real pages.
"""

from __future__ import annotations

from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import translate_url
from django.utils.translation import get_language

from .models import Post, Project, Tag


def _tags_for(relation: str):
    """Tags in use by published rows of `relation`, each carrying its count `n`.

    The count is what the filter chip shows, so a reader knows before clicking
    whether a tag holds one project or five.
    """
    published = Q(**{f"{relation}__is_published": True})
    return Tag.objects.annotate(n=Count(relation, filter=published, distinct=True)).filter(n__gt=0)


def project_list(request):
    projects = Project.objects.filter(is_published=True).prefetch_related("tags")
    return render(
        request,
        "projects/list.html",
        {"projects": projects, "tags": _tags_for("projects"), "active_tag": request.GET.get("tag", "")},
    )


def project_detail(request, slug: str):
    project = get_object_or_404(
        Project.objects.prefetch_related("tags"), slug=slug, is_published=True
    )
    published = list(Project.objects.filter(is_published=True).values_list("slug", flat=True))
    index = published.index(slug)
    next_index = (index + 1) % len(published) if len(published) > 1 else None
    next_project = (
        Project.objects.prefetch_related("tags").filter(slug=published[next_index]).first()
        if next_index is not None
        else None
    )
    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
            "project_index": index + 1,
            "next_project": next_project,
            # The number on the next card is that project's place in the list,
            # so it matches the card it had on /projects/.
            "next_index": (next_index or 0) + 1,
        },
    )


def post_list(request):
    posts = Post.objects.filter(is_published=True).prefetch_related("tags")
    return render(
        request,
        "blog/list.html",
        {"posts": posts, "tags": _tags_for("posts"), "active_tag": request.GET.get("tag", "")},
    )


def post_detail(request, slug: str):
    """A post, with its search-engine story told per language.

    hreflang lists only the languages the post is written in. Opened in a
    language it is not written in, the page still reads (the fallback), but its
    canonical names the first language it does have — otherwise /en/blog/x/
    would be indexed as an English page full of Persian. Canonical alone, not
    noindex as well: Google reads the pair as a contradiction.
    """
    post = get_object_or_404(
        Post.objects.prefetch_related("tags", "images"), slug=slug, is_published=True
    )
    active = (get_language() or settings.LANGUAGE_CODE).split("-")[0]
    written = post.languages
    href = {code: f"{settings.SITE_URL}{translate_url(request.path, code)}" for code in written}
    alternates = [{"code": code, "href": href[code]} for code in written]
    if settings.LANGUAGE_CODE in href:
        alternates.append({"code": "x-default", "href": href[settings.LANGUAGE_CODE]})

    context = {"post": post, "related": _related(post), "seo_alternates": alternates}
    if written and active not in written:
        context.update(seo_canonical=href[written[0]], only_in=written)
    return render(request, "blog/detail.html", context)


def _related(post: Post, limit: int = 3) -> list[Post]:
    """Posts sharing a tag, topped up with the latest — a post is never a dead end."""
    others = Post.objects.filter(is_published=True).exclude(pk=post.pk).prefetch_related("tags")
    related = list(others.filter(tags__in=post.tags.all()).distinct()[:limit])
    if len(related) < limit:
        related += list(others.exclude(pk__in=[p.pk for p in related])[: limit - len(related)])
    return related
