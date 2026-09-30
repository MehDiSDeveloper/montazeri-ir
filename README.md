# montazeri.ir

The personal site of **Mahdi Montazeri** — portfolio, blog and digital business
card, in Persian, English and German.

Django 5 · SQLite · one container · no build step · no JavaScript framework.

---

## Run it

Only through Docker, on every machine, Windows included — never from a local
venv:

```bash
cp .env.example .env
docker compose up --build
```

Then open <http://localhost:8004>. `./data` is mounted as the volume — the
database, uploads and collected static all live there and nothing else needs
to persist, so recreating the container loses nothing.

Every `manage.py` command runs inside the running container:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_profile     # the real content
docker compose exec web python manage.py createsuperuser  # to edit content at /admin/
docker compose exec web python manage.py bale status
docker compose exec web python manage.py test tests
```

Locally, `docker compose up` also merges `docker-compose.override.yml`
(git-ignored, never deployed): the source is mounted over `/app`, runserver
replaces gunicorn so edits show on refresh, SQLite uses a rollback journal
instead of WAL (WAL cannot work on a Windows folder mounted into Docker), and a
second service, `bot`, runs `manage.py bale poll`, because there is no public
address for a webhook. To run exactly what production runs, bypass it:
`docker compose -f docker-compose.yml up --build`.

---

## The pages

| URL | What it answers |
|---|---|
| `/` | Who this is, in ten seconds: hero, current work, three projects, skills, career, two posts |
| `/projects/` | Everything built, filterable by tag without a page load |
| `/projects/<slug>/` | One project as a short case study: the problem, the build, the outcome, the links |
| `/blog/`, `/blog/<slug>/` | Writing — notes, things learned, things being chewed on |
| `/about/` | The long version, plus the full timeline |
| `/resume/` | The same data as a document — the print stylesheet makes it a real PDF |
| `/contact/` | Direct channels that copy with one tap, plus a form — name, company, email, an optional phone number, request type, timeline, subject, message |
| `/contact/track/` | Follow a request with its tracking code: its status, the whole conversation, and a box to write back |
| `/card/` | The digital business card: QR, vCard download, share |
| `/card/montazeri.vcf` | A real contact file a phone can save |
| `/en/…`, `/de/…` | The same site, English and German |
| `/sitemap.xml`, `/feed.xml`, `/robots.txt` | For machines |
| `/bot/<secret>/` | Where Bale posts a button press. Exists only when a secret is set |
| `/admin/` | Where the content is edited |

---

## Editing the content

Everything a visitor reads is in the database, so nothing here needs a deploy.
Sign in at `/admin/` and:

- **Profile** — name, headline, intro, bio, "right now", contact channels,
  avatar, résumé PDF. One row; it is already there.
- **Projects** — one row each. `is_featured` puts it on the home page; `order`
  sorts the list; `cover` is optional and the card looks right without one.
- **Experience** — work and education on one timeline. An empty `end` means
  "present".
- **Posts** — Markdown in the `body` fields. Reading time is counted, not typed.
- **Skill groups / Skills** — `is_primary` marks the ones worth emphasising.
- **Messages** — the requests people sent through the contact form. What they
  wrote is read-only; what you set is the **status** (new → read → answered,
  or rejected / archived) and the private **notes**, and you answer in the
  **reply** box — the answer appears on the visitor's tracking page. When they
  write back, the request is new again. The list opens on active requests
  (new + read); tick several statuses or «همه» in the filter, search by name,
  company, tracking code, `#12` or request type, and filter or sort by how
  close the visitor's deadline is. Opening one marks it read.

Every text field appears three times: `_fa`, `_en`, `_de`. **Only Persian is
required** — an empty English or German field falls back to Persian rather than
rendering blank, so you can translate the site gradually.

---

## Deploying

> **Live:** https://mohammadmahdimontazeri.ir on the VPS. Where and how it is deployed, and how to ship an update: [CLAUDE.md → Production](CLAUDE.md).

Any host that runs a container and gives you one writable directory.

1. Build and push the image, or point the host at this repository.
2. Mount a volume at `/app/data`.
3. Set the environment:

   | Variable | Why it matters |
   |---|---|
   | `DJANGO_SECRET_KEY` | Long and random. Rotating it logs out every admin session. |
   | `DJANGO_DEBUG` | `0` in production. |
   | `DJANGO_ALLOWED_HOSTS` | Your domain, comma separated. |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://yourdomain` — the contact form and admin need it. |
   | `DJANGO_SITE_URL` | The real domain. The canonical tag, the `hreflang` links, the sitemap **and the QR code** are built from it. |
   | `DJANGO_GEO_COUNTRY_HEADER` | The header your proxy puts the visitor's country in (Cloudflare: `HTTP_CF_IPCOUNTRY`). Without it, put a country `.mmdb` (DB-IP "IP to Country Lite" or GeoLite2-Country) at `data/geoip/country.mmdb` and set `DJANGO_GEO_CLIENT_IP_HEADER` (e.g. `HTTP_X_REAL_IP`) if a proxy sits in front. With neither, every first visit stays Persian. |

4. First boot only: `docker compose exec web python manage.py createsuperuser`.

`start.sh` runs `migrate`, then `collectstatic`, then registers the bot's
webhook if one is configured, then gunicorn — so a deploy needs no manual step.

---

## A new request arrives in Bale

Every contact-form submission can be delivered to a [Bale](https://bale.ai)
bot the moment it is saved — Bale rather than Telegram because Bale answers
inside Iran, though both work: they speak the same bot API and
`DJANGO_BOT_API` picks the service.

The notice carries **every field**, so the phone screen is enough to decide,
and the buttons under it set the same status the admin sets:

> 💬 پاسخ به درخواست‌کننده · 👁 خوانده شد · 📝 یادداشت · ❌ رد درخواست · 🗄 بایگانی · 🔗 رسیدگی در پنل

Whatever is already true offers its undo instead of itself, and the notice is
repainted in place after every change — from the phone *or* from `/admin/` —
so the two can never disagree. To leave a note, press «یادداشت» and send the
text, reply to a notice, or send `#12 the note` at any time. To answer the
visitor, press «پاسخ» and send the text: it lands on their tracking page and
the request becomes «پاسخ داده شده». When they write back, a fresh notice
arrives.

Setting it up takes about five minutes:

| Variable | What it is |
|---|---|
| `DJANGO_BOT_TOKEN` | From `@botfather` in Bale: `/newbot`. |
| `DJANGO_BOT_CHAT_ID` | Send `/id` to your bot and it answers with this. |
| `DJANGO_BOT_WEBHOOK_SECRET` | A long random string. Updates arrive at `https://<site>/bot/<secret>/`. |
| `DJANGO_BOT_API` | `https://tapi.bale.ai` (default) or `https://api.telegram.org`. |

```bash
docker compose exec web python manage.py bale status        # is the token right, where do updates go
docker compose exec web python manage.py bale set-webhook   # start.sh does this for you on deploy
docker compose exec web python manage.py bale test          # prove the chat id
docker compose logs -f bot                                  # the local poller (`bale poll`)
```

Locally the `bot` service polls by itself. Polling and a webhook are
exclusive, so if `bale status` shows a webhook, the poller is refused until
`bale delete-webhook` is run — and if that webhook is the live site on the same
token, deleting it cuts the live site off until its next boot.

Leave the token or the chat id empty and the feature is simply off: the form
saves exactly as before, nothing is sent, and `/bot/…` does not exist. A
messenger that is slow or down never costs a request — the row is committed
first and announced afterwards, off the request thread.

---

## What's here and what isn't

**Here:** three real languages with per-page URLs, Jalali dates for Persian
readers rendered server-side, light/dark/system theming with no flash, a
command palette on `Ctrl`/`⌘`+`K`, tag filtering with no page load,
one-tap copy, Web Share, a print stylesheet, `JSON-LD` structured data, an RSS
feed, a sitemap, a honeypot plus throttle on the contact form, and every
request delivered to Bale with its status and notes editable from there.

**Not here, on purpose:** a JavaScript framework, a CSS build, a CDN, an API, a
separate database server, and skill percentage bars.

**Coming later:** a lightweight custom admin panel to replace the stock Django
one.

Architecture, and the reasoning behind each decision, is in
[CLAUDE.md](CLAUDE.md).

---

## Licence

The code is Mahdi's. Vazirmatn and IBM Plex Mono are under the SIL Open Font
Licence 1.1 and Fraunces under the SIL OFL 1.1 — see `static/fonts/OFL.txt`.
