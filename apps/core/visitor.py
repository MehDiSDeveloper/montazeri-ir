"""
The request bot, from the visitor's side: their request's updates in their
own chat, and — from there — a reply or a cancellation.

The same bot and the same webhook as the owner's half in `bot.py`; which half
answers is decided by the chat. The owner is `BOT_CHAT_ID` and nobody else;
a visitor is a chat that a `ChatLink` row names, and only for the requests it
names. Every visitor action looks that row up again, so a request's id in a
button is a label, never a key.

How a chat gets linked — the messenger cannot write to a phone number, so the
visitor has to come to the bot:

1. The tracking page mints a `ChatLinkToken` and sends the visitor to
   ble.ir/<bot>?start=<token>. The tracking code never leaves the site.
2. /start <token> claims the token for that chat and asks for the phone
   number with a request_contact button.
3. The contact must be the sender's own (contact.user_id == from.id), and its
   number must be the one on the request. Then — and only then — the link is
   made. Either way the token is spent.

Off unless the owner's half is configured and `BOT_USERNAME` is set.
"""

from __future__ import annotations

import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.content.models import ChatLink, ChatLinkToken, Message, normalise_phone
from apps.core import bot, messenger
from apps.core.i18n import t

# What a /start payload may be: our tokens are URL-safe base64.
TOKEN_SHAPE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def is_enabled() -> bool:
    return messenger.is_configured() and bool(settings.BOT_USERNAME)


def _lang(message: Message) -> str:
    return message.language or settings.LANGUAGE_CODE


def _say(chat_id, key: str, lang: str, markup: dict | None = None, **values) -> None:
    messenger.send(t(key, lang).format(**values), chat_id=str(chat_id), markup=markup)


def _everyone(key: str) -> str:
    """For a chat whose language nobody knows yet: all three, Persian first."""
    return "\n\n".join(t(key, code) for code, _ in settings.LANGUAGES)


REMOVE_KEYBOARD = {"remove_keyboard": True}


def _contact_keyboard(lang: str) -> dict:
    return {
        "keyboard": [[{"text": t("bale.share_phone", lang), "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


# ── linking ────────────────────────────────────────────────────────────────
def start(chat_id, payload: str) -> None:
    """/start from a chat that is not the owner's."""
    payload = payload.strip()
    if not payload:
        messenger.send(_everyone("bale.welcome"), chat_id=str(chat_id))
        return

    now = timezone.now()
    token = (
        ChatLinkToken.objects.select_related("message").filter(token=payload).first()
        if TOKEN_SHAPE.match(payload)
        else None
    )
    # Claim it for this chat, atomically: the first chat to present a token
    # is the only one it will ever work for.
    claimed = token is not None and (
        ChatLinkToken.objects.filter(pk=token.pk, used_at=None, expires_at__gt=now, chat_id__in=("", str(chat_id)))
        .update(chat_id=str(chat_id))
    )
    if not claimed:
        messenger.send(_everyone("bale.bad_link"), chat_id=str(chat_id))
        return

    lang = _lang(token.message)
    _say(chat_id, "bale.ask_contact", lang, _contact_keyboard(lang), code=token.message.tracking_code)


def contact(incoming: dict) -> None:
    """A shared contact: the answer to the request_contact button."""
    chat_id = str((incoming.get("chat") or {}).get("id") or "")
    sender = str((incoming.get("from") or {}).get("id") or "")
    card = incoming.get("contact") or {}

    token = (
        ChatLinkToken.objects.select_related("message")
        .filter(chat_id=chat_id, used_at=None, expires_at__gt=timezone.now())
        .order_by("-created_at")
        .first()
    )
    if token is None:
        messenger.send(_everyone("bale.bad_link"), chat_id=chat_id, markup=REMOVE_KEYBOARD)
        return
    message = token.message
    lang = _lang(message)

    # Somebody else's contact card proves nothing about who is typing. Not
    # spent: pressing the button, rather than attaching a card, still works.
    if not sender or sender != chat_id or str(card.get("user_id") or "") != sender:
        _say(chat_id, "bale.own_contact", lang, _contact_keyboard(lang))
        return

    # One try per link, matched or not.
    if not ChatLinkToken.objects.filter(pk=token.pk, used_at=None).update(used_at=timezone.now()):
        messenger.send(_everyone("bale.bad_link"), chat_id=chat_id, markup=REMOVE_KEYBOARD)
        return

    shared = normalise_phone(card.get("phone_number") or "")
    if not message.phone:
        _say(chat_id, "bale.no_phone", lang, REMOVE_KEYBOARD)
        return
    if not shared or shared != normalise_phone(message.phone):
        _say(chat_id, "bale.mismatch", lang, REMOVE_KEYBOARD)
        return

    link, _ = ChatLink.objects.update_or_create(
        message=message,
        defaults={"chat_id": chat_id, "phone": shared, "awaiting_reply_since": None},
    )
    link.mark_told()
    _say(chat_id, "bale.linked", lang, REMOVE_KEYBOARD, code=message.tracking_code)


def stop(chat_id) -> None:
    """/stop — this chat hears nothing more about any request."""
    links = list(ChatLink.objects.filter(chat_id=str(chat_id)).select_related("message"))
    if not links:
        messenger.send(_everyone("bale.welcome"), chat_id=str(chat_id))
        return
    codes = "، ".join(link.message.tracking_code for link in links)
    lang = _lang(links[0].message)
    ChatLink.objects.filter(chat_id=str(chat_id)).delete()
    _say(chat_id, "bale.stopped", lang, codes=codes)


def disconnect(message: Message) -> None:
    """The tracking page's «disconnect»: drop the link, and say so in the
    chat once the row is really gone."""
    link = ChatLink.objects.filter(message=message).first()
    if link is None:
        return
    chat_id = link.chat_id
    link.delete()
    if is_enabled():
        lang, code = _lang(message), message.tracking_code
        transaction.on_commit(lambda: bot.in_background(_say_stopped, chat_id, lang, code))


def _say_stopped(chat_id, lang: str, codes: str) -> None:
    _say(chat_id, "bale.stopped", lang, codes=codes)


# ── routing ────────────────────────────────────────────────────────────────
def on_text(incoming: dict, text: str) -> None:
    """A text from a chat that is not the owner's."""
    chat_id = (incoming.get("chat") or {}).get("id")
    command, _, rest = text.partition(" ")
    command = command.split("@")[0].lower()

    if command == "/start":
        start(chat_id, rest)
    elif command == "/stop":
        stop(chat_id)
    else:
        messenger.send(_everyone("bale.welcome"), chat_id=str(chat_id))
