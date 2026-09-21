"""
The request bot: a new contact-form request arrives in Bale, and is triaged
from there.

Why this exists at all: a message that only lands in /admin/ is a message that
is read when the admin is next opened, which for a project enquiry is too
late. The notice carries every field, so the phone screen is enough to decide;
the buttons under it set the same `Message.status` the admin sets, so neither
side can drift from the other.

The whole feature is off when `DJANGO_BOT_TOKEN`/`DJANGO_BOT_CHAT_ID` are
empty: the form saves exactly as before and nothing is sent. A notification is
never allowed to affect the request — it is sent after the row is committed,
off the request thread, and a failure is logged and forgotten.

Updates reach `handle_update()` from either transport: the webhook at
/bot/<secret>/ in production, or `manage.py bale poll` where there is no
public HTTPS address. Both are thin; this is where the decisions live.
"""

from __future__ import annotations

import logging
import re
import threading

from django.conf import settings
from django.db import connections, transaction
from django.utils import timezone

from apps.content.models import BotState, Message
from apps.core import messenger, visitor
from apps.core.jalali import to_jalali

log = logging.getLogger("bot")

CALLBACK = re.compile(r"^req:([a-z]+):(\d+)$")
# "#12 note text" — the way to note a request other than the last one touched.
PREFIXED_NOTE = re.compile(r"^#(\d+)\s+(.+)$", re.S)
# The id inside a notice, so swipe-replying to one files the note correctly.
NOTICE_ID = re.compile(r"#(\d+)")

EMPTY = "—"

STATUS_LABEL = {
    Message.Status.NEW: "🆕 جدید",
    Message.Status.READ: "👁 خوانده‌شده",
    Message.Status.ANSWERED: "💬 پاسخ داده شده",
    Message.Status.REJECTED: "❌ رد شده",
    Message.Status.ARCHIVED: "🗄 بایگانی",
}
LANGUAGE_LABEL = {"fa": "فارسی", "en": "English", "de": "Deutsch"}

BUTTON_READ = "👁 خوانده شد"
BUTTON_UNREAD = "↩️ برگرداندن به جدید"
BUTTON_NOTE = "📝 یادداشت"
BUTTON_REPLY = "💬 پاسخ به درخواست‌کننده"
BUTTON_REJECT = "❌ رد درخواست"
BUTTON_UNREJECT = "↩️ لغو رد"
BUTTON_ARCHIVE = "🗄 بایگانی"
BUTTON_UNARCHIVE = "↩️ خروج از بایگانی"
BUTTON_PANEL = "🔗 رسیدگی در پنل"


# ── what the owner reads ───────────────────────────────────────────────────
def _host() -> str:
    return settings.SITE_URL.split("://")[-1].rstrip("/")


def _when(moment) -> str:
    """Jalali, because the person reading this reads Jalali."""
    local = timezone.localtime(moment)
    jy, jm, jd = to_jalali(local.date())
    return f"{jy}/{jm:02d}/{jd:02d} ساعت {local:%H:%M}"


def _label(message: Message, field: str) -> str:
    """The Persian half of a choice label: «پروژه — project» → «پروژه»."""
    return getattr(message, f"get_{field}_display")().split(" — ")[0]


def _deadline(message: Message) -> str:
    days = message.days_left()
    if days is None:
        return _label(message, "timeline")
    if days < 0:
        left = f"{-days} روز گذشته ⚠️"
    elif days == 0:
        left = "امروز ⏰"
    else:
        left = f"{days} روز مانده"
    return f"{_label(message, 'timeline')} — {left}"


# Enough of the conversation to answer from the phone, and no more: both
# services cap a message at 4096 characters.
THREAD_TURNS = 3
THREAD_CLIP = 600


def _thread(message: Message) -> list[str]:
    replies = list(message.replies.all())
    if not replies:
        return []
    lines = ["", f"💬 گفت‌وگو ({len(replies)} پاسخ):"]
    if len(replies) > THREAD_TURNS:
        lines.append("…")
    for reply in replies[-THREAD_TURNS:]:
        who = "شما" if reply.from_owner else (message.name or "درخواست‌کننده")
        body = reply.body.strip()
        if len(body) > THREAD_CLIP:
            body = body[:THREAD_CLIP].rstrip() + "…"
        lines += [f"— {who} · {_when(reply.created_at)}:", body]
    return lines


def notice_text(message: Message, headline: str = "📩 درخواست تازه") -> str:
    """The whole request in one message. Nothing is hidden behind a link: the
    point is to be able to decide without opening anything."""
    lines = [
        f"{headline} #{message.pk} — {_host()}",
        f"وضعیت: {STATUS_LABEL.get(message.status, message.status)}",
        "",
        f"نام: {message.name or EMPTY}",
        f"شرکت: {message.company or EMPTY}",
        f"ایمیل: {message.email or EMPTY}",
        f"تلفن: {message.phone or EMPTY}",
        f"نوع: {_label(message, 'kind')}",
        f"مهلت: {_deadline(message)}",
        f"موضوع: {message.subject or EMPTY}",
        f"زبان: {LANGUAGE_LABEL.get(message.language, message.language or EMPTY)}",
        f"زمان: {_when(message.created_at)}",
        f"کد پیگیری: {message.tracking_code}",
        "",
        "پیام:",
        message.body.strip(),
        *_thread(message),
    ]
    if message.notes.strip():
        lines += ["", "📝 یادداشت‌ها:", message.notes.strip()]
    lines += ["", f"پنل: {message.admin_url}"]
    return "\n".join(lines)


def keyboard(message: Message) -> messenger.Keyboard:
    """Buttons drawn from the request's current state, so pressing one and
    reading where it stands are the same thing. Whatever is already true
    offers its undo instead of itself."""
    pk = message.pk
    status = message.status

    if status == Message.Status.NEW:
        first = {"text": BUTTON_READ, "callback_data": f"req:read:{pk}"}
    else:
        first = {"text": BUTTON_UNREAD, "callback_data": f"req:unread:{pk}"}

    if status == Message.Status.REJECTED:
        reject = {"text": BUTTON_UNREJECT, "callback_data": f"req:unreject:{pk}"}
    else:
        reject = {"text": BUTTON_REJECT, "callback_data": f"req:reject:{pk}"}

    if status == Message.Status.ARCHIVED:
        archive = {"text": BUTTON_UNARCHIVE, "callback_data": f"req:unarchive:{pk}"}
    else:
        archive = {"text": BUTTON_ARCHIVE, "callback_data": f"req:archive:{pk}"}

    return [
        [{"text": BUTTON_REPLY, "callback_data": f"req:reply:{pk}"}],
        [first, {"text": BUTTON_NOTE, "callback_data": f"req:note:{pk}"}],
        [reject, archive],
        # A URL button opens the panel in one tap. The address is in the text
        # as well, for a client that will not draw one.
        [{"text": BUTTON_PANEL, "url": message.admin_url}],
    ]


# ── sending ────────────────────────────────────────────────────────────────
def guarded(fn, *args) -> None:
    """Run `fn` and let nothing out of it. A notification may not break the
    thing it is notifying about."""
    try:
        fn(*args)
    except Exception:  # noqa: BLE001 — logged, and then forgotten
        log.exception("bot: %s failed", getattr(fn, "__name__", fn))


def in_background(fn, *args) -> None:
    """The same, off the request thread. A visitor must never wait on — or
    fail because of — a messenger that is slow or down."""

    def run():
        try:
            guarded(fn, *args)
        finally:
            # This thread opened its own connection; nobody else will close it.
            connections.close_all()

    threading.Thread(target=run, name="bot", daemon=True).start()


def notify_new(message: Message) -> None:
    """Announce a new request, once the row is safely committed."""
    if not messenger.is_configured():
        return
    pk = message.pk
    transaction.on_commit(lambda: in_background(_send_notice, pk))


def notify_reply(message: Message) -> None:
    """The visitor wrote back. A fresh notice rather than a repaint of the old
    one: a repaint makes no sound, and somebody is waiting again."""
    if not messenger.is_configured():
        return
    pk = message.pk
    transaction.on_commit(lambda: in_background(_send_notice, pk, "💬 پاسخ تازه از درخواست‌کننده"))


def _send_notice(pk: int, headline: str = "📩 درخواست تازه") -> None:
    message = Message.objects.filter(pk=pk).first()
    if message is None:
        return
    sent = messenger.send(notice_text(message, headline), keyboard(message))
    if not sent:
        return
    Message.objects.filter(pk=pk).update(
        notified_at=timezone.now(),
        bot_chat_id=str((sent.get("chat") or {}).get("id") or settings.BOT_CHAT_ID),
        bot_message_id=str(sent.get("message_id") or ""),
    )


def refresh(message: Message) -> None:
    """Repaint the notice of a request whose state changed somewhere else —
    the admin, or another button press."""
    if not (messenger.is_configured() and message.bot_message_id):
        return
    messenger.edit(
        message.bot_chat_id or settings.BOT_CHAT_ID,
        message.bot_message_id,
        notice_text(message),
        keyboard(message),
    )


def refresh_later(message: Message) -> None:
    """The same, off the request thread — for the admin's save button."""
    if messenger.is_configured() and message.bot_message_id:
        in_background(_refresh, message.pk)


def _refresh(pk: int) -> None:
    message = Message.objects.filter(pk=pk).first()
    if message is not None:
        refresh(message)


# ── receiving ──────────────────────────────────────────────────────────────
ACTIONS = {
    "read": (Message.Status.READ, "علامت «خوانده‌شده» خورد."),
    "unread": (Message.Status.NEW, "دوباره «جدید» شد."),
    "reject": (Message.Status.REJECTED, "درخواست رد شد."),
    "unreject": (Message.Status.READ, "رد لغو شد."),
    "archive": (Message.Status.ARCHIVED, "بایگانی شد."),
    "unarchive": (Message.Status.READ, "از بایگانی خارج شد."),
}

HELP = (
    "این ربات درخواست‌های ثبت‌شده در سایت را می‌آورد.\n\n"
    "دکمه‌های زیر هر درخواست وضعیتش را عوض می‌کنند: خوانده‌شده، رد، بایگانی.\n"
    "برای پاسخ به درخواست‌کننده، دکمهٔ «پاسخ» را بزنید و بعد متن را بفرستید؛ "
    "پاسخ در صفحهٔ پیگیری او دیده می‌شود و درخواست «پاسخ داده شده» می‌شود.\n"
    "برای یادداشت، دکمهٔ «یادداشت» را بزنید و بعد متن را بفرستید — یا هر وقت "
    "خواستید پیامی به شکل «#12 متن یادداشت» بفرستید تا روی همان درخواست بنشیند.\n\n"
    "/new — درخواست‌های خوانده‌نشده\n"
    "/id — شناسهٔ این گفت‌وگو\n"
    "/help — همین راهنما"
)

NOTE_HINT = (
    "برای ثبت یادداشت، زیر درخواست دکمهٔ «یادداشت» را بزنید، "
    "یا پیام را به شکل «#12 متن یادداشت» بفرستید."
)


def handle_update(update: dict) -> None:
    """One update, from either transport. Anything unexpected is ignored."""
    state = BotState.load()
    if not state.is_new_update(int(update.get("update_id") or 0)):
        return  # a webhook retry, or a poller that restarted mid-batch

    if update.get("callback_query"):
        _on_button(state, update["callback_query"])
    elif update.get("message"):
        _on_text(state, update["message"])


def _on_button(state: BotState, query: dict) -> None:
    origin = ((query.get("message") or {}).get("chat") or {}).get("id")
    callback_id = str(query.get("id") or "")

    if not messenger.owns_chat(origin):
        messenger.answer(callback_id, "این دکمه برای شما نیست.")
        return

    match = CALLBACK.match(query.get("data") or "")
    if not match:
        messenger.answer(callback_id, "این دکمه معتبر نیست.")
        return

    action, pk = match.group(1), int(match.group(2))
    message = Message.objects.filter(pk=pk).first()
    if message is None:
        messenger.answer(callback_id, "این درخواست دیگر وجود ندارد.")
        return

    # The notice being pressed is the one to repaint, even when it is not the
    # one we had remembered — the bot may have been re-pointed, or /new may
    # have sent the request a second time.
    _remember_notice(message, query.get("message") or {})

    if action == "note":
        state.await_note_for(message)
        messenger.answer(callback_id, "متن یادداشت را بفرستید.")
        messenger.send(f"📝 یادداشت برای درخواست #{pk} ({message.name}) — متن را بفرستید.")
        return
    if action == "reply":
        state.await_note_for(message, reply=True)
        messenger.answer(callback_id, "متن پاسخ را بفرستید.")
        messenger.send(
            f"💬 پاسخ به {message.name} (درخواست #{pk}) — متن را بفرستید.\n"
            "این متن در صفحهٔ پیگیری درخواست‌کننده نمایش داده می‌شود."
        )
        return

    if action not in ACTIONS:
        messenger.answer(callback_id, "این دکمه معتبر نیست.")
        return

    status, done = ACTIONS[action]
    message.set_status(status)
    refresh(message)
    messenger.answer(callback_id, done)


def _on_text(state: BotState, incoming: dict) -> None:
    chat_id = (incoming.get("chat") or {}).get("id")
    owner = messenger.owns_chat(chat_id)
    # Anyone who is not the owner is, at most, a visitor — and only once the
    # visitor half is switched on. See apps/core/visitor.py.
    as_visitor = not owner and visitor.is_enabled()

    if incoming.get("contact"):
        if as_visitor:
            visitor.contact(incoming)
        return

    text = (incoming.get("text") or "").strip()
    if not text:
        return

    command = text.split()[0].split("@")[0].lower()

    # /id — and /start, until visitors are being let in — answer anyone:
    # before DJANGO_BOT_CHAT_ID is set nobody is the owner yet, and this is
    # how that id is found. They tell the asker their own chat id and nothing
    # else.
    if command == "/id" or (command == "/start" and not as_visitor):
        messenger.send(
            f"شناسهٔ این گفت‌وگو: {chat_id}\n\nآن را در DJANGO_BOT_CHAT_ID بگذارید.",
            chat_id=str(chat_id),
        )
        return

    if as_visitor:
        visitor.on_text(incoming, text)
        return
    if not owner:
        return  # a stranger found the bot: say nothing

    if command == "/new":
        _send_pending()
        return
    if command.startswith("/"):
        messenger.send(HELP)
        return

    _file_note(state, incoming, text)


def _file_note(state: BotState, incoming: dict, text: str) -> None:
    """A plain message is a note — or, straight after «پاسخ», an answer for the
    visitor. Which request it belongs to, in the order of how explicit the
    owner was being. A named request (#12, or a swiped notice) is always a
    note: an answer goes out to somebody, so it only ever follows the button."""
    named, note = None, text

    prefixed = PREFIXED_NOTE.match(text)
    if prefixed:
        named, note = int(prefixed.group(1)), prefixed.group(2).strip()
    else:
        replied = (incoming.get("reply_to_message") or {}).get("text") or ""
        found = NOTICE_ID.search(replied)
        if found:
            named = int(found.group(1))

    if named is not None:
        # A named request that is gone must not quietly become the pending
        # one: the note would land on somebody else's request.
        target = Message.objects.filter(pk=named).first()
        if target is None:
            messenger.send(f"درخواستی با شمارهٔ #{named} پیدا نشد.")
            return
    else:
        target = state.pending_note_target()
        if target is not None and state.awaiting_reply:
            target.add_reply(note, from_owner=True)
            state.clear_note_target()
            refresh(target)
            messenger.send(f"✅ پاسخ برای {target.name} (درخواست #{target.pk}) ثبت شد و در صفحهٔ پیگیری‌اش دیده می‌شود.")
            return

    if target is None:
        messenger.send(NOTE_HINT)
        return

    target.add_note(note)
    state.clear_note_target()
    refresh(target)
    messenger.send(f"✅ یادداشت روی درخواست #{target.pk} ثبت شد.")


def _send_pending() -> None:
    """/new — every request still marked new, in case a notice was missed."""
    pending = list(Message.objects.filter(status=Message.Status.NEW)[:10])
    if not pending:
        messenger.send("درخواست خوانده‌نشده‌ای نیست. ✅")
        return
    for message in pending:
        sent = messenger.send(notice_text(message), keyboard(message))
        if sent:
            _remember_notice(message, sent)


def _remember_notice(message: Message, notice: dict) -> None:
    """Point the stored notice at `notice`, so the next repaint finds it."""
    chat_id = str((notice.get("chat") or {}).get("id") or "")
    message_id = str(notice.get("message_id") or "")
    if not message_id or (message.bot_message_id == message_id and message.bot_chat_id == chat_id):
        return
    message.bot_chat_id, message.bot_message_id = chat_id, message_id
    Message.objects.filter(pk=message.pk).update(bot_chat_id=chat_id, bot_message_id=message_id)
