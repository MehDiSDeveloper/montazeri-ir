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

**The app runs only through Docker — never from the Windows venv.** A
`runserver` or `bale poll` started from `.venv/` on the host is a second
writer on the same `data/db.sqlite3`, outside the container, and a second
poller on the same bot token.

```bash
docker compose up --build                                   # web on :8004, plus the bot poller
docker compose exec web python manage.py migrate            # after any model change
docker compose exec web python manage.py makemigrations content
docker compose exec web python manage.py seed_profile       # the REAL content, idempotent
docker compose exec web python manage.py seed_profile --wipe  # replace projects/skills/roles
docker compose exec web python manage.py seed_demo          # placeholder content — overwrites the real profile
docker compose exec web python manage.py seed_demo --wipe   # start the content over
docker compose exec web python manage.py createsuperuser    # to reach /admin/
docker compose exec web python manage.py check
docker compose exec web python manage.py bale status        # the request bot: token, chat, webhook
docker compose exec web python manage.py bale set-webhook   # start.sh does this on deploy
docker compose logs -f bot                                  # the dev poller (`bale poll`)
docker compose -f docker-compose.yml up --build             # production exactly, no override
```

`docker compose up` merges `docker-compose.override.yml` (git-ignored, never
deployed) over `docker-compose.yml`: the source is mounted over `/app`,
runserver replaces gunicorn, `DJANGO_SQLITE_JOURNAL_MODE=DELETE` (see "Things
that will bite"), and a second service, **`bot`**, runs `manage.py bale poll`
from the same image once `web` is healthy — locally there is no public address
for a webhook. Production is `docker-compose.yml` + `start.sh` alone: one
service, WAL, webhook.

Tests live in `tests/` and run inside the container with
`docker compose exec web python manage.py test tests`. Under `test`,
`settings.py` removes `DJANGO_BOT_*` from the environment — compose's
`env_file` has already put the real token there, so not reading `.env` is not
enough on its own.
They are stock Django test classes so `pytest-django` can pick them up
unchanged later. `test_geo_language.py` pins the redirect; `test_pages.py` pins
every route in all three languages, the services offer, per-language post SEO,
the sitemap and the Markdown rendering; `test_contact_requests.py` pins the
honeypot, the throttle, the phone field and the whole Bale bot — a fake in
place of `messenger.call` is why none of it touches the network;
`test_request_tracking.py` pins the tracking code, the conversation and the
status each reply leaves, and the inbox's filters and search.

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

**`seed_profile` is the real content and `seed_demo` will overwrite it.** Both
write `Profile.load()`, so running `seed_demo` on a live database replaces
Mahdi's biography with placeholders. `seed_profile` is the reviewed record of
every public claim — it is the file to edit when a claim changes, not the admin
form, because the admin leaves no diff. Its docstring lists the claims that are
retired and must not come back, and the reasons education and every private
fact are absent.

`apps/content/models.py` holds every word a visitor reads. Nothing else in the
project contains copy — if you find yourself typing a sentence about Mahdi into
a template, it belongs in a model field instead.

Twelve models: `Profile` (a singleton — `Profile.load()` is the only reader),
`Service`, `SkillGroup`/`Skill`, `Tag`, `Project`, `Experience`, `Post`/`PostImage`,
`Message`/`Reply`. The twelfth, `BotState`, is the one row nobody reads: it is the
request bot's memory and is documented with it below.

**Mahdi works on-site, hybrid or by the project — never fully remote.** The
copy states what he does, so the word "remote" appears nowhere a visitor reads.
**Project work is income, so it has its own page.** `Profile.offer_*` holds the
headline, lede and Markdown long form; `Service` rows are the promise cards
(end to end, quick start / fast delivery, agreed price, work modes). They show
as a peach band first on the home page and as `/services/`; "Start a project"
links to `/contact/?topic=project`, which pre-fills the subject. An empty
`offer_title` removes the page, the nav link, the band and the sitemap entry.

**Posts are written in the admin**, in whichever languages they exist in — no
language is required, `Post.clean()` asks for one complete title + body. The
body is Markdown rendered with `md_breaks` (a line break stays a line break, so
LinkedIn text pastes as-is; a bare `https://` becomes a link; off-site links open
in a new tab; images lazy-load). Images are uploaded as `PostImage` rows on the
post's own admin page, which shows the `![alt](url)` line to paste.
`original_url` renders a "originally posted on LinkedIn / X / …" link; the
platform comes from `Post.PLATFORMS`.

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
`feed.xml`, the `.vcf`, `/healthz` and the bot's `/bot/<secret>/`. There is
nothing to translate about a vCard or a bot update, the webhook's address must
stay exactly what `setWebhook` was told, and a crawler should find one sitemap
rather than three. That one
sitemap still lists every page in all three languages: `apps/core/sitemaps.py`
sets `i18n`, `alternates` and `x_default`, so each URL carries its hreflang
siblings — which is how the `/de/` pages get found by someone searching in
German.

**SEO lives in three places.** `base.html`'s head (title / description /
robots / canonical / hreflang / Open Graph blocks — `seo_title` and
`seo_description` on the profile are the home page's); the context processor
(`canonical_url` and `alternates`, both built from the path *without* its query
string); and `apps/core/seo.py`, which builds schema.org JSON-LD as dicts —
Person, WebSite, ProfilePage, BlogPosting, CreativeWork, Service, breadcrumbs —
emitted by `{% ld_* %}` from `seo_tags`. Never hand-write JSON-LD in a template.
A view can override with `seo_canonical`, `seo_alternates`, `seo_robots`. A
post opened in a language it is not written in keeps its fallback text but its
canonical names the language it has, its hreflang lists only real languages,
and the sitemap lists it only there (`get_languages_for_item`). The share image
is `Profile.og_image` → avatar, or a post's cover → first body image.

The header nav is in the order a reviewer reads a candidate — work, services,
résumé, about, writing — with contact as the one button in the bar. **The footer is the
site map**: every page grouped as explore / career / connect, plus the vCard,
RSS and `sitemap.xml`.

The switcher is built in `apps/core/context_processors.py` with Django's
`translate_url`, so it points at *this* page in the other language instead of
dumping the reader on the home page.

**A first visit picks its language by country.** `GeoLanguageMiddleware`
(`apps/core/middleware.py`) sends a first-time visitor on an unprefixed page
from Germany to `/de/…` and from any other *known* non-Iranian country to
`/en/…`; the mapping is `GEO_LANGUAGE_BY_COUNTRY` in settings. The country
comes from `apps/core/geo.py`: a proxy header (`DJANGO_GEO_COUNTRY_HEADER`)
first, then a MaxMind-format database at `data/geoip/country.mmdb`. The rules
that keep it from doing harm, all pinned in `tests/test_geo_language.py`:
it decides **once** (cookie `montazeri_geo`, set whether or not it redirected,
so the switcher's «فارسی» link sticks); it never redirects an explicit `/en/`
or `/de/` URL, a POST, a same-site Referer, or a **crawler** — redirecting
Googlebot (which crawls from the US) would de-index the Persian pages; and an
**unknown country changes nothing**, so a missing database never sends Iran to
English. `hreflang="x-default"` points at the unprefixed URL for this reason.

## The design system

**Colour lives in the three token blocks at the top of `static/css/site.css`
and nowhere else.** `:root` is the light theme; the two blocks after it restate
the same names for dark, once for `prefers-color-scheme` and once for an
explicit `[data-theme="dark"]`, so an explicit choice beats the device in both
directions. A rule that needs a tint writes `rgba(var(--mint-rgb), .12)`, never
a second hex. Re-theming the site is editing values in those blocks. The two
`--bg` values are also written in `base.html`'s `theme-color` meta tags and in
`THEME_COLOR` in `app.js`.

The palette is **four pastels, each with one meaning**:

| hue | means | where |
|---|---|---|
| mint (`--mint`) | the work, and anything actionable | projects, nav, primary buttons |
| sky (`--sky`) | the career | timeline, résumé, facts |
| peach (`--peach`) | the person | availability, «این روزها», contact |
| lilac (`--lilac`) | writing, and nothing else | posts, so a post tag never reads as a project |

A fifth hue would need a fifth meaning, which is the reason not to add one.

**Each hue is a five-step ramp, not one value**: `--x-tint`, `--x-soft`,
`--x`, `--x-strong`, `--x-deep`, plus `--x-rgb` for tints. A card, its border,
its icon and its label can be one colour at four intensities. What each step
is *for* is the rule to keep:

- `-tint` is a ground you can barely see, `-soft` is a fill, `--x` is the
  pastel itself (a button, a dot, a hover border).
- **Only `-strong` and `-deep` may colour a letterform**: `-strong` on
  `--surface` or `-tint` (≥ 4.5:1), and **on a `-soft` fill only `-deep`**
  (mint and peach `-strong` fall to 4.3–4.5:1 there).
- Text **on the pastel `--x` itself is `--on-accent`**, which is ink. That is
  why a primary button is a pastel with dark lettering rather than a saturated
  fill with white: it keeps the page pastel and still AA (8:1 or better).

In dark the ramp inverts — `-deep` is the *lightest* step — so a rule that
asked for `-deep` because it was drawing text keeps getting the readable step
without knowing about the theme.

**`--accent-*` is an indirection, not a fifth colour.** An element carrying
`data-accent="peach"` (or `"sky"`, `"lilac"`, `"mint"`) re-points the whole
ramp for itself and everything inside it, so every eyebrow, pill, chip, tag,
button and link in that subtree follows. Re-colouring a section is one
attribute in the template and no new CSS. Prefer `var(--accent-…)` over
`var(--mint-…)` in any component that could appear in more than one context.

**Where a hue *carries* something it means something; where it is only a
field it is rhythm.** Tags, links, buttons and post rows are the first kind and
keep the meanings above. Rows of near-identical boxes — case covers, project
cards, skill groups, fact tiles, contact channels, footer columns, the tech
ribbon — are the second: their container carries **`.rhythm`**, whose children
take turns through all four hues, so four boxes read as four boxes. Removing
the class is how a row goes back to one hue.

**A section can be a band.** `.sec.sec-band` paints the section edge to edge in
its own accent's `--wash-*` with a hairline dot texture. Bands alternate with
plain sections down the home page (work → *career band* → toolbox → *writing
band* → contact), which is what gives a long page a horizontal rhythm.

**Nothing may bleed sideways.** The hero aurora is an element with
`overflow: hidden`, and `.page-head::before` bleeds *up* behind the
transparent header but has `inset-inline: 0`. A negative inline inset or a
`left: -9999px` is scrollable overflow in RTL: the Persian page opens shifted
by exactly that much, while English looks fine. `html` carries
`overflow-x: clip` as the last line of defence, and **`<body>` must not carry
any `overflow-x`** — next to `clip` on `html` it turns `<body>` into its own
scroll container and the sticky header stops sticking.

**`[hidden]` always wins** (`display: none !important` in the base). Without
it a component's own `display: grid` beats the attribute, and a closed
popover, a filtered-out card and the pre-JS back-to-top button all show.

**Motion has one vocabulary.** Two easings, `--ease` (settle) and `--spring`
(a small overshoot, for things that pop); hover lifts use `transform`, arrivals
use the individual `translate`/`scale` properties, so the two never overwrite
each other. **The whole site sits on `.ambient`** (first child of `<body>`): a
fixed, self-clipped layer of four pastel lights drifting on 22–32 s cycles,
turned by scroll through a scroll-driven `rotate` (no JS), plus grain; over
them `initAmbient()` draws a canvas network (linked nodes, events travelling
the links, rising code tokens) in the `--x-rgb` colours. Strength is the
`--ambient` and `--net` tokens, set per theme. Every decorative loop —
the ambient field, the aurora drift, the portrait halo, the
floating skill chips, the tech ribbon — sits behind
`prefers-reduced-motion`, which also stops the ribbon and wraps it.

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

Thirteen concerns, each its own function started from `boot()`: theme; the
ambient network; header
(frosting, reading progress, back-to-top, mobile nav); nav indicator;
popovers; tooltips; reveal-on-scroll; pointer effects; tag filter;
copy-to-clipboard; share; the contact form's counter and sending state;
command palette.

**The search button carries no "Ctrl K" hint**, on purpose: in Chrome that
chord belongs to the address bar and searches Google, so a hint under the icon
promised something the page cannot deliver. The palette still opens on `/`.

The rules worth keeping:

- **Reveal-on-scroll's resting state is visible.** The hidden state exists only
  while `.js` is on the root element and motion is allowed. No observer, or
  `prefers-reduced-motion`, and everything is simply shown — content parked at
  `opacity: 0` waiting for a callback that never fires is the classic way this
  feature fails silently. The arrival is a CSS *animation* staggered by `--d`,
  not a transition with an inline `transition-delay`: that delay would also
  delay every hover on the card for the rest of the visit.
- **Tooltips are `data-tip="…"`, and they decorate a name the element already
  has.** One floating element, placed in viewport pixels, flipped below when
  there is no room above, clamped to both edges; mouse hover and keyboard focus
  only. An icon button still needs its `aria-label` — on touch that label is
  all there is.
- **Pointer effects are fine-pointer only and off under reduced motion.**
  `data-spot` is the soft light that follows the pointer inside a card (it uses
  the card's `::after`, so a spotlit component must not need its own);
  `data-tilt="n"` tilts by up to n degrees (the portrait, the business card).
- **The tag filter is client-side because the whole list is already on the
  page.** The query string is kept in step so a filtered view is still
  shareable, and the chip for `?tag=` is pressed on a cold load. If the list
  ever outgrows one render, this becomes a server-side filter and the chips
  become links. The count on each chip comes from `_tags_for()` in
  `apps/content/views.py`.

The command palette (Ctrl/⌘+K, or `/`) reads its index (`cmdk_index`) from the
context processor, shipped inside the page as JSON, so opening it costs no
request and it can never disagree with what the site actually has. Each entry
carries `i`, an icon id from `templates/partials/icons.html`. The language and
theme shortcuts are read from the header itself. It costs two small queries per
request; if the site grows past a few hundred rows, cache the list — do not
make the palette fetch.

## Dates: Jalali for Persian, Gregorian for the rest

Storage stays Gregorian and UTC. **Every date a Persian reader sees is rendered
Jalali by the server**, through `apps/core/jalali.py` (pure arithmetic, no
dependency) and the `smart_date` filter — so the first paint is already correct
and nothing has to be repaired by JavaScript a frame later. English and German
readers get the Gregorian date and their own month names. Persian digits come
from `fa_num`, which is a no-op in the other two languages.

How long a role ran is the `{% duration start end %}` tag: whole months counted
inclusively, the way a CV counts them — "2 yrs 5 mos", "2 J. 5 Mon.",
"۲ سال و ۵ ماه". It is arithmetic on the two dates printed beside it, not a
stored claim, so there is still no years-of-experience field anywhere.

## The contact form

`POST` → save → `redirect` with `?sent=1`, so a refresh can never resend.
Protection is a **honeypot** (`website`, invisible inside the form's own box
via `.hp` — never `left: -9999px`, which scrolls the Persian page sideways) plus a
per-session 60-second throttle from `settings.CONTACT_RATE_LIMIT_SECONDS`. No
captcha: for the volume a personal site attracts, a field a human never sees is
enough, and it costs the reader nothing.

A spam submission is answered **with the same redirect a real one gets**. A bot
that can tell the difference will tune around the trap.

The fields are name, an optional company, email, **an optional phone
number**, the request type (`Message.Kind`), the visitor's timeline
(`Message.Timeline`), subject and message. Type and timeline are radio chips
and optional too — nothing picked is "other" and "flexible". The timeline is
turned into a real date once, on arrival: `due_at` is `created_at` plus the
timeline's days, which is what the inbox sorts and filters by.
The phone is optional on purpose — most Iranian clients expect to be called
back, and requiring a number costs the replies of the ones who do not want to
be. `ContactForm.clean_phone` translates Persian and Arabic-Indic digits to
ASCII, so a number typed on a Persian keyboard is stored dialable.

Nothing is emailed. A message lands in the database, is announced in Bale (see
below) and is read at `/admin/content/message/`. Adding email means one
`send_mail` in `apps.core.views.contact` and SMTP settings — deliberately not
done, because an SMTP credential in a container is a real cost and there is
already a channel that reaches a phone.

## A request has a life cycle, and it reaches a phone

A message that only lands in `/admin/` is read when the admin is next opened,
which for a project enquiry is too late. So **`Message` carries a `status`**,
not a handled flag: `new → read → answered`, and at any point `rejected` or
`archived`. **Active** (`Message.ACTIVE`) is new and read — what still needs
the owner. `set_status()` stamps `read_at` the first time a request is looked
at and clears it again when it is put back to new. `notes` is a private, dated
log — appended to, never replaced, and rendered nowhere a visitor can reach.

**A request is a conversation.** Each one has a `tracking_code` (`XXXX-XXXX`
from an alphabet without 0/O/1/I/L), shown once on the thank-you page — from
the session, never in the redirect's URL — and it opens
`/contact/track/<code>/`, where both sides add `Reply` rows under the original
message, as many as it takes. Replies are never edited or deleted; a change is
another reply. **`Message.add_reply()` is the one place a reply's consequence
lives**: from the owner it makes the request `answered`; from the visitor it
makes it `new` again from *any* state — refused and archived included — and
`bot.notify_reply` sends a fresh notice, because a repaint makes no sound.
The owner answers from the admin's reply box or the bot's «پاسخ» button.

The tracking pages are `noindex, nofollow` and disallowed in `robots.txt`; the
URL is the key, like a private link. Guessing is throttled: wrong codes from
one address are counted in the cache (`TRACK_LOOKUP_LIMIT` per
`TRACK_LOOKUP_WINDOW_SECONDS`) and then the lookup answers 429. The cache is
the default per-process one, so the real limit is that times the gunicorn
workers — still hopeless for a guesser against 31⁸ codes. The reply box shares
the contact form's honeypot and throttle.

**The inbox** (`MessageAdmin`) opens on active requests. The status filter is
multi-select — each status is a toggle, `?status=new,answered`, plus «همه»
(`?status=all`) — and it scopes the search. The search box takes a name,
company, email, phone, tracking code (typed any way), `#12`, a word from the
request or any reply, or a request type by name («مشاوره», "project"). The
deadline filter (overdue / 3 / 7 / 30 days / later / flexible) also sorts
closest-first unless a column was clicked.

Three files, each with one job:

- **`apps/core/messenger.py`** — the transport. Bale (`tapi.bale.ai`) and
  Telegram speak the same bot API, so one client covers both and
  `DJANGO_BOT_API` picks the service; Bale is the default because it is the
  one that answers inside Iran. `urllib`, not a client library — the same
  reason there is no gettext toolchain. It knows nothing about messages.
- **`apps/core/bot.py`** — what to say. The notice carries **every field**,
  blanks shown as `—`, so the phone screen is enough to decide without opening
  anything. The buttons are drawn from the request's current state, so
  whatever is already true offers its undo instead of itself, and every change
  repaints the notice in place (`editMessageText`, falling back to replacing
  only the keyboard). A URL button opens the admin page; the address is in the
  text as well, for a client that will not draw one.
- **`apps/content/models.py: BotState`** — a singleton holding the last
  `update_id` handled, so a webhook retry can never archive a request twice,
  and which request a note (or, with `awaiting_reply`, an answer) is being
  written for, because «یادداشت» and «پاسخ» are a button press first and a
  text message second.

**A note can be filed three ways**, in order of how explicit the owner was:
`#12 text`, a reply to a notice (its `#12` is parsed back out), or the request
whose «یادداشت» button was pressed in the last `BOT_NOTE_WINDOW_SECONDS`.
Nothing matches, and the bot says how instead of guessing. **An answer to
the visitor only ever follows the «پاسخ» button** — a `#12` or a swiped
notice is always a private note, because an answer goes out to somebody.

**The transport is a webhook**, at `/bot/<secret>/` outside `i18n_patterns`
with the other machine endpoints. Long-polling would need a second process and
this site is one container with one process; `manage.py bale poll` covers
local work, where there is no public HTTPS address — it is the dev override's
`bot` service, so it exists only on a developer's machine. `start.sh` re-registers
the webhook on every boot, best effort, which is also what repairs a changed
`DJANGO_SITE_URL` by itself.

Three things guard the endpoint: a secret compared with
`constant_time_compare`, the route 404ing entirely when no secret is
configured, and **every action checking the update came from
`BOT_CHAT_ID`**. A malformed body is answered `200` and dropped — a messenger
told "error" redelivers the same update forever. `/start` and `/id` are the
exception that answers anybody: before `DJANGO_BOT_CHAT_ID` is filled in
nobody is the owner yet, and that is how the id is found.

**A notification may never cost a request.** The row is committed first and
announced second, from `transaction.on_commit` on a daemon thread, and
`bot.guarded` swallows and logs whatever comes back. Empty token or chat id
turns the whole feature off: the form behaves exactly as it did before.

The admin writes the same two fields the buttons write and calls
`bot.refresh_later()` afterwards, so the phone and `/admin/` cannot drift.
Opening a request marks it read, the way any other inbox does.

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

`start.sh` is the whole boot: `migrate`, then `collectstatic`, then — if a bot
token and webhook secret are set — `bale set-webhook`, then gunicorn. That one
is best effort: the site must come up when the messenger is unreachable.
WhiteNoise serves static with a one-year cache and a hashed manifest outside
`DEBUG`. Uploads under `data/media/` are served by Django in `DEBUG` and by the
front proxy or WhiteNoise in production — **if uploads 404 on the host, that is
the thing to check first.**

Environment variables are documented in `.env.example`. Only two matter:
`DJANGO_SECRET_KEY` (rotating it logs out every admin session) and
`DJANGO_ALLOWED_HOSTS`. Set `DJANGO_SITE_URL` to the real domain — the canonical
tag, the `hreflang` alternates, the sitemap, **the QR code** and the bot's own
webhook address all read it, so a wrong value ships a QR pointing at the wrong
host. `DJANGO_BOT_*` are the request bot's and are all optional — empty is off.

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
- **Every key in `Profile.links` needs two things**: an icon `#i-<key>` in
  `templates/partials/icons.html` and a label `channel.<key>` in
  `apps/core/i18n.py`. The key for mail is `email`, not `mail` — both icon ids
  exist for that reason. A missing icon is an empty button; a missing label
  renders as the key.
- **SQLite WAL does not work on the Windows bind mount.** WAL keeps its index
  in a memory-mapped `db.sqlite3-shm`, and a Windows folder mounted into
  Docker cannot share that mapping: `migrate` dies on `PRAGMA
  journal_mode=WAL` with `disk I/O error` and the dev container exits. So the
  dev override sets `DJANGO_SQLITE_JOURNAL_MODE=DELETE` (a rollback journal is
  an ordinary file), for `web` and `bot` alike; production, on a Linux disk,
  keeps the WAL default. The database stays in `data/` on the host either way,
  so recreating the container loses nothing. Two consequences: a database
  copied down from production is in WAL mode and must be checkpointed first
  (`PRAGMA wal_checkpoint(TRUNCATE); PRAGMA journal_mode=DELETE;`), and never
  delete a `-wal` file by hand — it can hold committed rows that are not in
  `db.sqlite3` yet.
- **A webhook and `bale poll` are exclusive.** While `setWebhook` is
  registered, `getUpdates` is refused — run `manage.py bale delete-webhook`
  before polling, and `set-webhook` again afterwards (`bale poll` says so when
  it starts, but never deletes the webhook itself: it may be the live site on
  the same token). Two pollers are just as wrong: each would handle half the
  presses — the dev `bot` service is the one poller, so nothing may run
  `bale poll` from the host venv beside it.
- **`DJANGO_SITE_URL` is the bot's address too.** `set-webhook` builds
  `<site>/bot/<secret>/` from it and the notice's admin link comes from the
  same place, so a wrong value ships a bot nobody can reach — alongside a QR
  pointing at the wrong host.
- **The QR plate is light in both themes** (`--qr-plate`, `--qr-ink`, defined
  once in `:root`). Do not "fix" it to follow dark mode: many phone cameras
  cannot read a light-on-dark code.
- **In the preview pane, a hidden or covered window pauses animation frames,
  CSS animations and `IntersectionObserver`.** Screenshots of a scrolled page
  then come back blank and the header never reports `is-stuck`. That is the
  pane, not the page — check with computed styles, or inject a style that
  zeroes animation and add `.is-in` to every `.reveal` before capturing.
