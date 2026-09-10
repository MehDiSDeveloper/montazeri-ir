"""
Project and post views.

Filtering is deliberately client-side: a personal site has tens of projects,
not thousands, so the whole list is rendered once and the tag chips hide rows
instantly with no request. The server still honours ?tag= so a filtered list is
a shareable URL and a crawler sees real pages.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404, render

from .models import Post, Project, Tag


def project_list(request):
    projects = Project.objects.filter(is_published=True).prefetch_related("tags")
    tags = Tag.objects.filter(projects__is_published=True).distinct()
    return render(
        request,
        "projects/list.html",
        {"projects": projects, "tags": tags, "active_tag": request.GET.get("tag", "")},
    )


def project_detail(request, slug: str):
    project = get_object_or_404(
        Project.objects.prefetch_related("tags"), slug=slug, is_published=True
    )
    published = list(Project.objects.filter(is_published=True).values_list("slug", flat=True))
    index = published.index(slug)
    next_slug = published[(index + 1) % len(published)] if len(published) > 1 else None
    next_project = Project.objects.filter(slug=next_slug).first() if next_slug else None
    return render(request, "projects/detail.html", {"project": project, "next_project": next_project})


def post_list(request):
    posts = Post.objects.filter(is_published=True).prefetch_related("tags")
    tags = Tag.objects.filter(posts__is_published=True).distinct()
    return render(
        request,
        "blog/list.html",
        {"posts": posts, "tags": tags, "active_tag": request.GET.get("tag", "")},
    )


def post_detail(request, slug: str):
    post = get_object_or_404(Post.objects.prefetch_related("tags"), slug=slug, is_published=True)
    return render(request, "blog/detail.html", {"post": post})
