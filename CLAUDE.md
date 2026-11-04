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

Both dev services are `restart: "no"`. The bot used to be `on-failure:3`, and
Docker counted Docker Desktop shutting down as a failure, so it started the
bot by itself every time Docker Desktop opened. It runs only when `compose up`
is run.

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
status each reply leaves, and the inbox's filters and search;
`test_visitor_bot.py` pins the visitor's side of the bot — linking a chat,
every way linking must fail, the updates it receives, and reply and cancel,
including that a visitor can never press anything that is not theirs;
`test_admin_upload.py` pins the admin's file fields — the widget on every
one, the profile's pictures first, save, and clear.

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

## Detailed docs (read only the one your task touches)

Details live in `docs/agents/`. Before changing an area, read its file; after changing it, update that file in the same commit.

- `docs/agents/architecture.md`: content in the database, translation columns, URLs and the language prefix, Jalali/Gregorian dates, JavaScript as enhancement, the admin, where the site grows. Read before changing models, content, routes or JS.
- `docs/agents/design.md`: the design system (tokens, typography, components, layout). Read before any template or CSS change.
- `docs/agents/contact.md`: the contact form, the request life cycle and its Bale/phone notifications, the bot from the visitor side, the digital business card.

## Production: where and how this site is live

> A deploy changes the **live** site. Ask the user before deploying.

| | |
|---|---|
| URL | https://mohammadmahdimontazeri.ir (`www.` and `http://` redirect here) |
| Server | VPS `91.207.18.218` (Webdade, Ubuntu 24.04). From Windows: `ssh vps` → user `deploy` (key login, passwordless sudo, in the `docker` group) |
| App dir | `/srv/montazeri-ir/`: code (replaced on every deploy), `.env` (production secrets, only on the server), `data/` (the volume; deploy never touches it) |
| Container | published on `127.0.0.1:8004` → 8000. Only Caddy is public (ports 80/443) |
| Reverse proxy | Caddy on the host, automatic Let's Encrypt HTTPS. Config source `G:\Repos\devops\server\caddy\Caddyfile`, applied with `bash /g/Repos/devops/caddy-apply.sh` |
| Runbook | `G:\Repos\devops\RUNBOOK.md` (server layout, logs, restart, backups, DNS). Keep it updated after any server change |

**Deploy** (Windows PowerShell; takes the **local working copy**, uncommitted changes included, git is not involved):

```
G:\Repos\devops\deploy.ps1 montazeri-ir
```

It uploads the repo without `.git`, `.venv`, `node_modules`, `.next`, `.env*`, `data/` and the dev-only compose file,
strips CRLF from `*.sh`, rsyncs into `/srv/montazeri-ir/` (keeping `.env` and `data/`), runs `docker compose up -d --build`
and waits for a 200 on `http://127.0.0.1:8004/healthz`. Migrations run in the container's start script, so there is no manual step.

**Compose on the server.** The server `.env` sets `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`, so a plain `docker compose …` in `/srv/montazeri-ir` uses the prod override. `docker-compose.prod.yml` is not in this repo; it lives in `G:\Repos\devops\server\montazeri-ir\` and is shipped by `deploy.sh`. It replaces the port with `127.0.0.1:8004`. `docker-compose.override.yml` (runserver, DEBUG, the polling `bot` service) is dev-only and is never uploaded.
If you change the service name, the container port or the published port here, update `G:\Repos\devops\`
(`deploy.sh`, `server/montazeri-ir/`, the Caddyfile) in the same change, or the live site breaks.

**Production environment** lives only in `/srv/montazeri-ir/.env` (mode 600). A new variable the code needs must be added there too,
not only to `.env.example`. Change a key without opening the file (it backs up `.env` and re-creates the container):
`printf 'KEY=value\n' | bash /g/Repos/devops/env-set.sh montazeri-ir`. Never print, copy into chat or commit its values.

**Look at the live app:**

```
ssh vps "cd /srv/montazeri-ir && docker compose ps && docker compose logs --tail 100"
```

**Backups:** `data/` is backed up every night (03:30) to `/var/backups/apps/` on the server and pulled daily to `G:\apps backup` on Windows; 14 days are kept in each place. How to restore: RUNBOOK → Backups.

**Specific to this app:**

- Uploads (`/media/`) are served by **Caddy** from `/srv/montazeri-ir/data/media`, because Django serves them only with `DEBUG` on.
- Admin user `admin` was created once with `createsuperuser --noinput` from `DJANGO_SUPERUSER_*` in the server `.env`.
- The bot `@invt4mntbot` is the **production** bot (token in the server `.env`, `DJANGO_BOT_WEBHOOK_SECRET` generated on the server).
  `start.sh` registers `https://mohammadmahdimontazeri.ir/bot/<secret>/` on every boot; check with
  `docker compose exec -T web python manage.py bale status`. Don't run this token locally (the local `bot` service would poll it):
  use a separate test bot in the local `.env`.
- SQLite runs in WAL mode on the server (the default); back it up with `sqlite3 .backup`, never by copying the file alone.
- The live database started empty on 2026-09-30 with `seed_profile`. **Never run `seed_demo` on the server.**

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
host. `DJANGO_BOT_*` are the request bot's and are all optional — empty is off;
`DJANGO_BOT_USERNAME` alone switches the visitor half on or off.

## Things that will bite

- **Persian text on an `/en/` or `/de/` page is an empty `_en`/`_de`
  column, not a code bug** — `tr()` falls back to Persian. From 2026-09-30
  the live profile's name, headline, intro, bio, location, now and
  availability had no English or German, and on 2026-10-15 they were filled
  from `seed_profile` (only the empty columns). The likely cause was a
  scripted POST to the profile's admin form: Django saves every field the
  POST leaves out, unless it has a default, as empty. Edit in the admin from
  a browser (it sends every field) or in `manage.py shell`; never POST part
  of an admin form.
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
- **Bale's deep link is not in its API reference.** `ble.ir/<bot>?start=<x>`
  arriving as `/start <x>` is what Bale does in practice and what its own
  bot course teaches, but the reference at docs.bale.ai does not specify it,
  nor a payload's length or alphabet. The token is 24 URL-safe characters to
  stay inside Telegram's limits; if Bale ever drops the payload, the visitor
  gets the welcome text instead of the phone prompt.
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
