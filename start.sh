#!/bin/sh
# Boot order matters: schema first, then static, then serve.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

# Point Bale at this deployment's /bot/<secret>/ endpoint. Best effort: the
# site must still come up when the messenger is unreachable, and re-running it
# on every boot is what repairs a changed DJANGO_SITE_URL by itself.
if [ -n "${DJANGO_BOT_TOKEN:-}" ] && [ -n "${DJANGO_BOT_WEBHOOK_SECRET:-}" ]; then
  python manage.py bale set-webhook || echo "bale: webhook not registered — run 'manage.py bale set-webhook'."
fi
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads 4 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
