# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## What this is

The personal site of **Mahdi Montazeri** — a portfolio, a blog and a digital
business card in one Django app, in **three languages** (Persian, English,
German). It is also the link and the QR code he hands people, so the two things
it must never be are slow and ugly.

The stance of the whole project: **a strong front end over a deliberately
small back end.** Nine views, one SQLite file, no API, no build step, no
JavaScript framework. Every design decision below exists to keep it that way
while still allowing the site to grow.

## Commands

Everything runs through the venv at `.venv/` (`.venv/Scripts/` on Windows).

```bash
.venv/Scripts/python manage.py runserver 8021       # local dev
.venv/Scripts/python manage.py migrate               # after any model change
.venv/Scripts/python manage.py makemigrations content
.venv/Scripts/python manage.py seed_demo             # placeholder content, idempotent
.venv/Scripts/python manage.py seed_demo --wipe      # start the content over
.venv/Scripts/python manage.py createsuperuser       # to reach /admin/
.venv/Scripts/python manage.py check
docker compose up --build                            # the real thing, port 8000
```

There is **no test suite yet**. When one arrives it belongs in `tests/` with
`pytest-django`, and the first three things worth pinning are named at the foot
of this file.

## The shape of the project

```
config/        settings, urls, wsgi          — the whole Django configuration
apps/core/     views, forms, i18n strings, template tags, jalali
apps/content/  models, admin, seed command   — everything a visitor reads
templates/     base.html + one file per page
static/        site.css, app.js, self-hosted fonts
data/          db.sqlite3, media/, staticfiles/  — THE one volume in production
```

`data/` is the only directory that survives a redeploy, and everything
persistent is inside it on purpose: the database, uploads and collected static
are one mount, so hosting is one container and one disk.

## Content lives in the database, not in the code

`apps/content/models.py` holds every word a visitor reads. Nothing else in the
project contains copy — if you find yourself typing a sentence about Mahdi into
a template, it belongs in a model field instead.

Eight models: `Profile` (a singleton — `Profile.load()` is the only reader),
`SkillGroup`/`Skill`, `Tag`, `Project`, `Experience`, `Post`, `Message`.

Two deliberate absences:

- **`Skill` has no percentage.** A "90% Python" bar is a number nobody can
  verify and every reviewer discounts. `is_primary` is the only emphasis there
  is, and it means "show this in the hero strip".
- **There is no view counter and no "years of experience" field.** Both are
  claims a personal site cannot back up.

## Translation: one column per language

A translated field is **one real column per language**, named `<field>_<lang>`.
`@i18n_fields(...)` in `models.py` writes those columns so the model body stays
readable, and `Translatable.tr("title")` reads the active language with a
fallback chain that ends at Persian.

Why not `django-modeltranslation` or a per-language row: one dependency fewer,
every query stays a plain query with no join, the stock admin renders the three
inputs side by side for free, and **a fourth language is one entry in
`settings.LANGUAGES` plus one migration**. The cost is that an unfilled
language falls back rather than 404s, which is the behaviour a personal site
wants anyway.

In templates it is `{{ project|tr:"title" }}` and, for a Markdown field,
`{{ project|md:"body" }}`.

**UI strings are a different problem and have a different answer.** Buttons,
labels and section headings live in `apps/core/i18n.py` as one Python dict,
read with `{% t "nav.projects" %}`. Django's gettext catalogues need `.po`
files compiled by the `msgfmt` binary, which turns "reword a button" into a
build step that has to run on Windows, in CI and inside the image; this
vocabulary is about a hundred short strings. `LocaleMiddleware` is still what
activates the language — only the catalogue is ours.

**An unknown key renders as the key**, visibly, rather than as an empty string.

## URLs, and the language prefix

`i18n_patterns` with `prefix_default_language=False`: Persian is at `/`,
English at `/en/`, German at `/de/`. Everything a reader can see is inside that
block so a language switch is a real, shareable, indexable URL.

Machine endpoints stay **outside** it — `sitemap.xml`, `robots.txt`,
`feed.xml`, the `.vcf` and `/healthz`. There is nothing to translate about a
vCard, and a crawler should find one sitemap rather than three.

The switcher is built in `apps/core/context_processors.py` with Django's
`translate_url`, so it points at *this* page in the other language instead of
dumping the reader on the home page.

## The design system

**Colour lives in the three token blocks at the top of `static/css/site.css`
and nowhere else.** `:root` is the light theme; the two blocks after it restate
the same names for dark, once for `prefers-color-scheme` and once for an
explicit `[data-theme="dark"]`, so an explicit choice beats the device in both
directions. A rule that needs a tint writes `rgba(var(--sage-rgb), .12)`, never
a second hex. Re-theming the site is editing values in those blocks.

The palette is **actpact's «شن و مریم‌گلی» run pastel**: sage (`--sage`) is the
primary voice, clay (`--clay`) is the signature accent used sparingly, and a
third lilac (`--lilac`) is reserved for *writing* — a tag on a post is lilac so
it never reads as a project. Adding a fourth hue means adding a fourth meaning,
which is the reason not to.

**Logical properties only.** The site runs RTL in Persian and LTR in English
and German from the same rules: `padding-inline-start`, never `padding-left`.
A rule with a physical side in it is a bug in one of the three languages.

**Three typefaces, all self-hosted.** Vazirmatn for everything Persian and all
UI, Fraunces for Latin display (the name, the card index, the error code) and
IBM Plex Mono for labels, dates and technology names. Nothing this page draws
with comes off a CDN — inside Iran `fonts.googleapis.com` is slow at best.
Latin runs inside Persian text carry `.lat` or `.mono`, which set
`direction: ltr; unicode-bidi: isolate`, or a Latin word flips inside a Persian
sentence.

**The theme has three states**, not two: `system` / `light` / `dark`, stored
under `localStorage["montazeri-theme"]`. That key is read **twice**: by
`app.js`, and by a small blocking script in `base.html`'s `<head>`. The second
one is pre-paint on purpose — deferring it to `app.js` repaints one frame in,
which is exactly the flash it prevents. **If you rename the key, rename it in
both places.**

## JavaScript is enhancement, and only enhancement

`static/js/app.js` is one file, no dependency, no build. Turn JavaScript off
and every link, form and page still works; what is lost is polish.

Eight concerns, each its own function: theme, sticky header and mobile nav,
popovers, reveal-on-scroll, tag filter, copy-to-clipboard, share, command
palette.

Two of them have a rule worth keeping:

- **Reveal-on-scroll's resting state is visible.** The hidden state exists only
  while `.js` is on the root element and an `IntersectionObserver` is coming.
  No observer, or `prefers-reduced-motion`, and everything is simply shown —
  content parked at `opacity: 0` waiting for a callback that never fires is the
  classic way this feature fails silently.
- **The tag filter is client-side because the whole list is already on the
  page.** The query string is kept in step so a filtered view is still
  shareable, and the server honours `?tag=` on a cold load, so a crawler sees
  real pages. If the list ever outgrows one render, this becomes a server-side
  filter and the chips become links.

The command palette's index (`cmdk_index`) is built in the context processor
and shipped inside the page as JSON, so opening it costs no request and it can
never disagree with what the site actually has. It costs two small queries per
request; if the site grows past a few hundred rows, cache the list — do not
make the palette fetch.

## Dates: Jalali for Persian, Gregorian for the rest

Storage stays Gregorian and UTC. **Every date a Persian reader sees is rendered
Jalali by the server**, through `apps/core/jalali.py` (pure arithmetic, no
dependency) and the `smart_date` filter — so the first paint is already correct
and nothing has to be repaired by JavaScript a frame later. English and German
readers get the Gregorian date and their own month names. Persian digits come
from `fa_num`, which is a no-op in the other two languages.

## The contact form

`POST` → save → `redirect` with `?sent=1`, so a refresh can never resend.
Protection is a **honeypot** (`website`, positioned off-screen) plus a
per-session 60-second throttle from `settings.CONTACT_RATE_LIMIT_SECONDS`. No
captcha: for the volume a personal site attracts, a field a human never sees is
enough, and it costs the reader nothing.

A spam submission is answered **with the same redirect a real one gets**. A bot
that can tell the difference will tune around the trap.

Nothing is emailed. Messages land in the database and are read at
`/admin/content/message/`. Adding email means one `send_mail` in
`apps.core.views.contact` and SMTP settings — deliberately not done, because an
SMTP credential in a container is a real cost and the admin list already works.

## The digital business card

`/card/` is one screen made to be handed over, and `/card/montazeri.vcf` is a
real vCard so a phone saves the contact rather than a screenshot. The QR is
rendered **server-side** by `segno` as inline SVG: it prints, it survives a
screenshot, and it needs no JavaScript to exist.

`segno` will not accept `currentColor`, so the code is drawn in a sentinel hex
and swapped in `apps/core/views.py`. That is what lets one SVG be legible in
both themes without rendering the QR twice.

## The admin, and the panel that is coming

`django.contrib.admin` is registered and is the **interim** way to edit
content. The lightweight custom panel is a later piece of work; when it is
built it belongs in `apps/panel/` as its own app with its own templates,
reusing `site.css`'s tokens, and the stock admin can then be switched off in
one line. Until then, do not build admin-shaped branches into the public pages
— the two audiences are different and the panel is a screen of its own.

## Deployment

One container, one process, one volume:

```
docker compose up --build     # or: docker build -t montazeri . && docker run …
```

`start.sh` is the whole boot: `migrate`, then `collectstatic`, then gunicorn.
WhiteNoise serves static with a one-year cache and a hashed manifest outside
`DEBUG`. Uploads under `data/media/` are served by Django in `DEBUG` and by the
front proxy or WhiteNoise in production — **if uploads 404 on the host, that is
the thing to check first.**

Environment variables are documented in `.env.example`. Only two matter:
`DJANGO_SECRET_KEY` (rotating it logs out every admin session) and
`DJANGO_ALLOWED_HOSTS`. Set `DJANGO_SITE_URL` to the real domain — the canonical
tag, the `hreflang` alternates, the sitemap and **the QR code** all read it, so
a wrong value ships a QR pointing at the wrong host.

## Where this grows, and how

Each of these is a small, contained change. None needs the design above
rewritten:

- **A fourth language.** One entry in `settings.LANGUAGES`, one migration, one
  column in `apps/core/i18n.py`'s dict, one entry in `templatetags`' month names.
- **The lightweight admin panel.** `apps/panel/`, see above.
- **Email on a new message.** One `send_mail` call in `contact`.
- **Photos on projects.** The field is already there (`Project.cover`); the
  card and the detail page already render it when present.
- **A `/now` page.** `Profile.now_*` already holds the sentence; a page would
  be a longer version of the same field.
- **Postgres.** One dict in `settings.DATABASES` and `psycopg` in
  `requirements.txt`. Nothing in the app knows which backend it is on. Do this
  when concurrent writes get heavy or a second machine needs the same data —
  not before, because a separate database is the single biggest line on the
  hosting bill.
- **Tests.** The three worth writing first: every route answers 200 in all
  three languages; `Translatable.tr` falls back rather than returning empty;
  and the contact form's honeypot and throttle both refuse without saving.

## Things that will bite

- **`{# … #}` in a Django template is single-line only.** A multi-line one
  leaks into the rendered page as visible text. Use `{% comment %}` for
  anything over one line — every long comment in `templates/` already does.
- **Every views module that renders a translated field must load `site_tags`.**
  `{% load site_tags %}` at the top; forgetting it is a render-time error, not
  a silent miss.
- **`Profile.save()` forces `pk = 1`.** There is one person on a personal site.
  Do not try to create a second row.
- **`data/` is in `.gitignore` and `.dockerignore`.** The database is never
  committed and never baked into the image.
