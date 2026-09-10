#!/bin/sh
# Boot order matters: schema first, then static, then serve.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads 4 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
