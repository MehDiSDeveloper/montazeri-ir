"""
Django settings — montazeri.ir

One process, one SQLite file, no external services. Everything that survives a
redeploy lives under DATA_DIR, which is the single mounted volume in production.
"""

from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Read KEY=value lines from .env into the environment, for runserver.

    docker compose already passes .env through `env_file`; this is so local
    work sees the same settings without python-dotenv. A variable that is
    already set always wins, so a real environment is never overridden.
    """
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


# Not for `manage.py test`: a developer's .env (a real bot token, above all)
# must never reach the test run, which has to behave the same on every machine.
TESTING = sys.argv[1:2] == ["test"]
if not TESTING:
    _load_dotenv(BASE_DIR / ".env")
else:
    # Inside Docker, compose's `env_file` has already put .env in the real
    # environment, so skipping the file is not enough: the bot is switched
    # off here too. Tests that need it turn it on with override_settings.
    for _key in ("DJANGO_BOT_TOKEN", "DJANGO_BOT_CHAT_ID", "DJANGO_BOT_WEBHOOK_SECRET"):
        os.environ.pop(_key, None)

# The one directory that is a volume in production: database, uploads, static.
DATA_DIR = Path(os.environ.get("DJANGO_DATA_DIR") or (BASE_DIR / "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


# ── Core ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS") or (
    ["localhost", "127.0.0.1", "[::1]"] if DEBUG else []
)
CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "apps.core",
    "apps.content",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # First-visit redirect from "/" to /en/ or /de/ by country — see
    # apps/core/middleware.py. Before LocaleMiddleware so a redirect costs nothing.
    "apps.core.middleware.GeoLanguageMiddleware",
    # LocaleMiddleware must sit after Session and before Common: it reads the
    # URL prefix written by i18n_patterns and activates that language, which is
    # what Translatable.tr() and the {% t %} tag both read.
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
            ],
        },
    },
]

# ── Database ───────────────────────────────────────────────────────────────
# SQLite on a mounted volume. WAL + a busy timeout is what makes it safe under
# a handful of gunicorn workers; anything heavier than this site would need
# Postgres, and swapping it in is one dict.
#
# WAL keeps its index in a memory-mapped -shm file, which a Windows folder
# bind-mounted into Docker cannot share ("disk I/O error"). The local dev
# override sets DJANGO_SQLITE_JOURNAL_MODE=DELETE for that reason; production,
# on a Linux disk, keeps WAL.
SQLITE_JOURNAL_MODE = os.environ.get("DJANGO_SQLITE_JOURNAL_MODE", "WAL").strip().upper() or "WAL"
if SQLITE_JOURNAL_MODE not in {"WAL", "DELETE", "TRUNCATE", "PERSIST"}:
    raise ValueError(f"DJANGO_SQLITE_JOURNAL_MODE={SQLITE_JOURNAL_MODE!r} is not a journal mode.")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
            "init_command": (
                "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;"
                if SQLITE_JOURNAL_MODE == "WAL"
                else f"PRAGMA journal_mode={SQLITE_JOURNAL_MODE};"
            ),
            "transaction_mode": "IMMEDIATE",
        },
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Language ───────────────────────────────────────────────────────────────
# Three real languages. Persian is the default and sits at "/" with no prefix;
# the other two are /en/ and /de/ via i18n_patterns in config/urls.py.
#
# Django's own gettext catalogues are deliberately NOT used for UI strings —
# see apps/core/i18n.py for why. LocaleMiddleware is still what activates the
# language, and everything downstream reads get_language().
LANGUAGE_CODE = "fa"
LANGUAGES = [
    ("fa", "Persian"),
    ("en", "English"),
    ("de", "German"),
]
LANGUAGE_COOKIE_NAME = "montazeri_lang"
LANGUAGE_COOKIE_SAMESITE = "Lax"
USE_I18N = True

# First-visit language by country (apps/core/middleware.py, apps/core/geo.py).
# Iran keeps Persian at "/", Germany goes to /de/, every other *known* country
# to /en/. An unknown country — no proxy header, no database — changes nothing.
GEO_LANGUAGE_ENABLED = _env_bool("DJANGO_GEO_LANGUAGE", default=True)
GEO_LANGUAGE_BY_COUNTRY = {"IR": "fa", "DE": "de"}
GEO_FALLBACK_LANGUAGE = "en"
# e.g. HTTP_CF_IPCOUNTRY behind Cloudflare. Django's META spelling.
GEO_COUNTRY_HEADER = os.environ.get("DJANGO_GEO_COUNTRY_HEADER", "")
# e.g. HTTP_X_REAL_IP or HTTP_X_FORWARDED_FOR behind nginx; empty means REMOTE_ADDR.
GEO_CLIENT_IP_HEADER = os.environ.get("DJANGO_GEO_CLIENT_IP_HEADER", "")
GEO_DATABASE_PATH = Path(
    os.environ.get("DJANGO_GEO_DATABASE") or (DATA_DIR / "geoip" / "country.mmdb")
)
GEO_COOKIE_NAME = "montazeri_geo"
GEO_COOKIE_AGE = 60 * 60 * 24 * 365
USE_TZ = True
TIME_ZONE = "Asia/Tehran"

# ── Static & media ─────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = DATA_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365

# ── Security (only bites outside DEBUG) ────────────────────────────────────
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ── Logging: one stream, stdout, because the container is the log ──────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(levelname)s %(name)s %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

# ── Site-level knobs the templates read ────────────────────────────────────
SITE_URL = os.environ.get("DJANGO_SITE_URL", "https://montazeri.ir").rstrip("/")
CONTACT_RATE_LIMIT_SECONDS = 60

# ── The messenger bot: a new request arrives in Bale ───────────────────────
# Bale (tapi.bale.ai) speaks the Telegram bot API, so one client covers both
# and DJANGO_BOT_API picks the service. Bale is the default because it is the
# one that answers inside Iran.
#
# Empty token or chat id = the whole feature is off: nothing is sent, the
# webhook 404s, and the contact form behaves exactly as it did before.
BOT_API = os.environ.get("DJANGO_BOT_API", "https://tapi.bale.ai").rstrip("/")
BOT_TOKEN = os.environ.get("DJANGO_BOT_TOKEN", "").strip()
# The one chat the bot talks to. Every button press is checked against it, so
# a stranger who finds the bot can press nothing.
BOT_CHAT_ID = os.environ.get("DJANGO_BOT_CHAT_ID", "").strip()
# The unguessable part of /bot/<secret>/, where Bale posts button presses.
# Empty means no webhook endpoint exists at all — use `manage.py bale poll`.
BOT_WEBHOOK_SECRET = os.environ.get("DJANGO_BOT_WEBHOOK_SECRET", "").strip()
BOT_TIMEOUT_SECONDS = 10
# How long after pressing «یادداشت» a plain message still counts as that note.
BOT_NOTE_WINDOW_SECONDS = 15 * 60
