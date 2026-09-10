# montazeri.ir

The personal site of **Mahdi Montazeri** — portfolio, blog and digital business
card, in Persian, English and German.

Django 5 · SQLite · one container · no build step · no JavaScript framework.

---

## Run it locally

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
cp .env.example .env

.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py seed_demo        # placeholder content in all three languages
.venv/Scripts/python manage.py createsuperuser  # to edit content at /admin/
.venv/Scripts/python manage.py runserver 8021
```

Then open <http://localhost:8021>.

## Run it in Docker

```bash
docker compose up --build
```

Port 8000. `./data` is mounted as the volume — the database, uploads and
collected static all live there and nothing else needs to persist.

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
| `/contact/` | Direct channels that copy with one tap, plus a form |
| `/card/` | The digital business card: QR, vCard download, share |
| `/card/montazeri.vcf` | A real contact file a phone can save |
| `/en/…`, `/de/…` | The same site, English and German |
| `/sitemap.xml`, `/feed.xml`, `/robots.txt` | For machines |
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
- **Messages** — what people sent through the contact form. Read-only.

Every text field appears three times: `_fa`, `_en`, `_de`. **Only Persian is
required** — an empty English or German field falls back to Persian rather than
rendering blank, so you can translate the site gradually.

---

## Deploying

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

4. First boot only: `python manage.py createsuperuser`.

`start.sh` runs `migrate` then `collectstatic` then gunicorn, so a deploy needs
no manual step.

---

## What's here and what isn't

**Here:** three real languages with per-page URLs, Jalali dates for Persian
readers rendered server-side, light/dark/system theming with no flash, a
command palette on `Ctrl`/`⌘`+`K`, tag filtering with no page load,
one-tap copy, Web Share, a print stylesheet, `JSON-LD` structured data, an RSS
feed, a sitemap, and a honeypot plus throttle on the contact form.

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
