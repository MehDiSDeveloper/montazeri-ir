# ── one image, one process, one SQLite file on one mounted volume ───────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ is the volume mount point: db.sqlite3, media/ and staticfiles/ all live here.
RUN mkdir -p data/media data/staticfiles

RUN chmod +x start.sh
EXPOSE 8000
CMD ["./start.sh"]
