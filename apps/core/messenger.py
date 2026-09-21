"""
A Telegram-compatible bot API client. Bale by default, because Bale is the one
that answers inside Iran.

Bale (https://tapi.bale.ai) and Telegram (https://api.telegram.org) expose the
same methods under the same names, so one client covers both and
`DJANGO_BOT_API` picks the service.

`urllib` rather than a client library: this is a handful of POSTs and the site
has no other use for the dependency — the same reason there is no gettext
toolchain and no build step.

This module knows nothing about messages, statuses or the database. It moves
text and buttons; `apps/core/bot.py` decides what to say.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

log = logging.getLogger("bot")

# Both services refuse a message longer than 4096 characters.
MAX_LENGTH = 4000

# An inline keyboard is a list of rows; a row is a list of buttons. A button
# carries either `callback_data` (it posts an update back) or `url` (it opens).
Keyboard = list[list[dict]]


class BotError(RuntimeError):
    """The API answered, and said no."""


def is_configured() -> bool:
    return bool(settings.BOT_TOKEN and settings.BOT_CHAT_ID)


def owns_chat(chat_id) -> bool:
    """Only the configured chat may press a button or file a note."""
    return bool(settings.BOT_CHAT_ID) and str(chat_id) == str(settings.BOT_CHAT_ID)


def call(method: str, payload: dict | None = None, timeout: float | None = None) -> dict | list:
    """Call one bot method and return its `result`. Raises BotError."""
    if not settings.BOT_TOKEN:
        raise BotError("no bot token is configured")

    url = f"{settings.BOT_API}/bot{settings.BOT_TOKEN}/{method}"
    body = json.dumps(payload or {}).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=timeout or settings.BOT_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # The token is in the URL, so never let the URL into a log line.
        detail = error.read().decode("utf-8", "replace")[:200]
        raise BotError(f"{method} answered {error.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        raise BotError(f"{method} failed: {error}") from None

    if not data.get("ok"):
        raise BotError(f"{method} refused: {str(data.get('description'))[:200]}")
    return data.get("result")


# ── talking ────────────────────────────────────────────────────────────────
def _chunks(text: str) -> list[str]:
    """Split on line breaks so no piece is over the API's limit."""
    out: list[str] = []
    current = ""
    for line in text.split("\n"):
        for start in range(0, max(len(line), 1), MAX_LENGTH):
            piece = line[start : start + MAX_LENGTH]
            if current and len(current) + 1 + len(piece) > MAX_LENGTH:
                out.append(current)
                current = piece
            else:
                current = f"{current}\n{piece}" if current else piece
    if current.strip():
        out.append(current)
    return out


def send(text: str, keyboard: Keyboard | None = None, chat_id: str | None = None) -> dict | None:
    """Send `text`, split if it is long. The buttons go on the last piece, so
    they sit under the whole notice. Returns that last message, or None when
    there is nobody to send to.

    An explicit `chat_id` needs only a token, not a configured owner: that is
    what lets the bot answer /id before DJANGO_BOT_CHAT_ID has been filled in.
    """
    destination = chat_id or settings.BOT_CHAT_ID
    if not (settings.BOT_TOKEN and destination):
        return None

    sent = None
    pieces = _chunks(text)
    for index, piece in enumerate(pieces):
        payload = {"chat_id": destination, "text": piece}
        # No parse_mode: whatever a visitor typed can then never break the
        # formatting, or worse, turn into markup.
        if keyboard and index == len(pieces) - 1:
            payload["reply_markup"] = {"inline_keyboard": keyboard}
        sent = call("sendMessage", payload)
    return sent


def edit(chat_id: str, message_id: str, text: str, keyboard: Keyboard | None = None) -> None:
    """Repaint a notice in place. Falls back to replacing only the buttons —
    a request's whole state is legible from them either way."""
    markup = {"inline_keyboard": keyboard} if keyboard else None
    try:
        call(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                **({"reply_markup": markup} if markup else {}),
            },
        )
    except BotError as error:
        log.info("editMessageText unavailable (%s) — replacing the buttons only.", error)
        if markup:
            call("editMessageReplyMarkup", {"chat_id": chat_id, "message_id": message_id, "reply_markup": markup})


def answer(callback_id: str, text: str = "") -> None:
    """The little toast over the button that was just pressed. Best effort:
    the action has already happened and must not be undone by a failed toast."""
    try:
        call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text[:180]})
    except BotError as error:
        log.info("answerCallbackQuery failed: %s", error)


# ── plumbing ───────────────────────────────────────────────────────────────
def get_me() -> dict:
    return call("getMe")


def set_webhook(url: str) -> dict:
    return call("setWebhook", {"url": url})


def delete_webhook() -> dict:
    return call("deleteWebhook", {})


def webhook_info() -> dict:
    return call("getWebhookInfo", {})


def get_updates(offset: int, poll_seconds: int) -> list[dict]:
    result = call(
        "getUpdates",
        {"offset": offset, "timeout": poll_seconds},
        timeout=poll_seconds + settings.BOT_TIMEOUT_SECONDS,
    )
    return result or []
