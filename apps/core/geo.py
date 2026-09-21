"""Which country a request comes from — and nothing else.

Two sources, tried in order, both optional:

1. **A header set by the front proxy** (`GEO_COUNTRY_HEADER`), e.g. Cloudflare's
   `CF-IPCountry` or nginx's geoip module. Free, no file, no lookup.
2. **A local country database** (`GEO_DATABASE_PATH`) in the MaxMind `.mmdb`
   format — GeoLite2-Country, or DB-IP's "IP to Country Lite", which needs no
   account. It lives under `data/geoip/` so it survives a redeploy with
   everything else.

Neither configured, or neither knows the address, and the answer is `None`.
Callers must treat `None` as "unknown", never as "abroad": a missing database
must not quietly send every Iranian visitor to English.
"""

from __future__ import annotations

import ipaddress
import logging
from functools import lru_cache
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


def country_for(request) -> str | None:
    """ISO 3166-1 alpha-2 code, upper case, or None when it cannot be known."""
    return _country_from_header(request) or _country_from_database(client_ip(request))


def client_ip(request) -> str | None:
    """The visitor's address. Behind a proxy, `GEO_CLIENT_IP_HEADER` names where
    the proxy put it; the left-most entry of a forwarded chain is the client."""
    header = settings.GEO_CLIENT_IP_HEADER
    raw = request.META.get(header) if header else None
    raw = (raw or request.META.get("REMOTE_ADDR") or "").split(",")[0].strip()
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return None


def _country_from_header(request) -> str | None:
    header = settings.GEO_COUNTRY_HEADER
    return _normalise(request.META.get(header)) if header else None


def _country_from_database(ip: str | None) -> str | None:
    if ip is None or not ipaddress.ip_address(ip).is_global:
        return None
    reader = _reader(str(settings.GEO_DATABASE_PATH or ""))
    if reader is None:
        return None
    try:
        record = reader.get(ip) or {}
    except ValueError:
        return None
    return _normalise((record.get("country") or {}).get("iso_code"))


@lru_cache(maxsize=1)
def _reader(path: str):
    """Opened once per process; the file is memory-mapped, so this is cheap."""
    if not path or not Path(path).is_file():
        return None
    try:
        import maxminddb
    except ImportError:
        logger.warning("GEO_DATABASE_PATH is set but maxminddb is not installed")
        return None
    try:
        return maxminddb.open_database(path)
    except (OSError, maxminddb.InvalidDatabaseError):
        logger.exception("Could not open the geo database at %s", path)
        return None


def _normalise(code: str | None) -> str | None:
    """Two letters or nothing. Cloudflare sends `XX` and `T1` for "unknown" and Tor."""
    code = (code or "").strip().upper()
    if len(code) != 2 or not code.isalpha() or code == "XX":
        return None
    return code
