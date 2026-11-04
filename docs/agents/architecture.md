<!-- Moved out of CLAUDE.md so it loads only when needed. Keep it current. -->

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

Fourteen models: `Profile` (a singleton — `Profile.load()` is the only reader),
`Service`, `SkillGroup`/`Skill`, `Tag`, `Project`, `Experience`, `Post`/`PostImage`,
`Message`/`Reply`. The other three are rows nobody reads: `BotState` is the
request bot's memory, and `ChatLink`/`ChatLinkToken` are which visitor's chat
a request reaches. All three are documented with the bot below.

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

## The admin, and the panel that is coming

`django.contrib.admin` is registered and is the **interim** way to edit
content. The lightweight custom panel is a later piece of work; when it is
built it belongs in `apps/panel/` as its own app with its own templates,
reusing `site.css`'s tokens, and the stock admin can then be switched off in
one line. Until then, do not build admin-shaped branches into the public pages
— the two audiences are different and the panel is a screen of its own.

**Every file field in the admin uses `UploadWidget`** (`formfield_overrides =
UPLOADS` in `apps/content/admin.py`, inlines included, plus
`static/js/admin-upload.js` and `static/css/admin-upload.css`, which only the
admin loads). The stock input shows nothing but a file name, and a chosen file
is sent only when the form is saved, so on the long profile form a photo looked
applied when it was not. The widget shows the picture that is live now, a
preview of the one waiting (name and size, «با ذخیره اعمال می‌شود») with a
«منصرف شدم» undo, dims the live picture when «پاک کردن» is ticked — choosing
a file and ticking clear undo each other, because Django refuses both — and
keeps a fixed bar with «ذخیره» (it submits as "save and continue") until the
form is sent; leaving with a file waiting asks first. `ProfileAdmin` puts the
pictures first, has `save_on_top`, and its list redirects to the one profile,
so «ذخیره» comes back to the form. Each file field's `help_text` says where on
the site it shows — keep that true when a template starts or stops using one.

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
