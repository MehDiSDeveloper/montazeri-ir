<!-- Moved out of CLAUDE.md so it loads only when needed. Keep it current. -->

## The contact form

`POST` → save → `redirect` with `?sent=1`, so a refresh can never resend.
Protection is a **honeypot** (`website`, invisible inside the form's own box
via `.hp` — never `left: -9999px`, which scrolls the Persian page sideways) plus a
per-session 60-second throttle from `settings.CONTACT_RATE_LIMIT_SECONDS`. No
captcha: for the volume a personal site attracts, a field a human never sees is
enough, and it costs the reader nothing.

A spam submission is answered **with the same redirect a real one gets**. A bot
that can tell the difference will tune around the trap.

The fields are name, an optional company, email, **an optional phone
number**, the request type (`Message.Kind`), the visitor's timeline
(`Message.Timeline`), subject and message. Type and timeline are radio chips
and optional too — nothing picked is "other" and "flexible". The timeline is
turned into a real date once, on arrival: `due_at` is `created_at` plus the
timeline's days, which is what the inbox sorts and filters by.
The phone is optional on purpose — most Iranian clients expect to be called
back, and requiring a number costs the replies of the ones who do not want to
be. `ContactForm.clean_phone` translates Persian and Arabic-Indic digits to
ASCII, so a number typed on a Persian keyboard is stored dialable.

Nothing is emailed. A message lands in the database, is announced in Bale (see
below) and is read at `/admin/content/message/`. Adding email means one
`send_mail` in `apps.core.views.contact` and SMTP settings — deliberately not
done, because an SMTP credential in a container is a real cost and there is
already a channel that reaches a phone.

## A request has a life cycle, and it reaches a phone

A message that only lands in `/admin/` is read when the admin is next opened,
which for a project enquiry is too late. So **`Message` carries a `status`**,
not a handled flag: `new → read → answered`, and at any point `rejected` or
`archived`. **Active** (`Message.ACTIVE`) is new and read — what still needs
the owner. `set_status()` stamps `read_at` the first time a request is looked
at and clears it again when it is put back to new. `notes` is a private, dated
log — appended to, never replaced, and rendered nowhere a visitor can reach.

**A request is a conversation.** Each one has a `tracking_code` (`XXXX-XXXX`
from an alphabet without 0/O/1/I/L), shown once on the thank-you page — from
the session, never in the redirect's URL — and it opens
`/contact/track/<code>/`, where both sides add `Reply` rows under the original
message, as many as it takes. Replies are never edited or deleted; a change is
another reply. **`Message.add_reply()` is the one place a reply's consequence
lives**: from the owner it makes the request `answered`; from the visitor it
makes it `new` again from *any* state — refused and archived included — and
`bot.notify_reply` sends a fresh notice, because a repaint makes no sound.
The owner answers from the admin's reply box or the bot's «پاسخ» button.

The tracking pages are `noindex, nofollow` and disallowed in `robots.txt`; the
URL is the key, like a private link. Guessing is throttled: wrong codes from
one address are counted in the cache (`TRACK_LOOKUP_LIMIT` per
`TRACK_LOOKUP_WINDOW_SECONDS`) and then the lookup answers 429. The cache is
the default per-process one, so the real limit is that times the gunicorn
workers — still hopeless for a guesser against 31⁸ codes. The reply box shares
the contact form's honeypot and throttle.

**The inbox** (`MessageAdmin`) opens on active requests. The status filter is
multi-select — each status is a toggle, `?status=new,answered`, plus «همه»
(`?status=all`) — and it scopes the search. The search box takes a name,
company, email, phone, tracking code (typed any way), `#12`, a word from the
request or any reply, or a request type by name («مشاوره», "project"). The
deadline filter (overdue / 3 / 7 / 30 days / later / flexible) also sorts
closest-first unless a column was clicked.

Three files, each with one job:

- **`apps/core/messenger.py`** — the transport. Bale (`tapi.bale.ai`) and
  Telegram speak the same bot API, so one client covers both and
  `DJANGO_BOT_API` picks the service; Bale is the default because it is the
  one that answers inside Iran. `urllib`, not a client library — the same
  reason there is no gettext toolchain. It knows nothing about messages.
- **`apps/core/bot.py`** — what to say. The notice carries **every field**,
  blanks shown as `—`, so the phone screen is enough to decide without opening
  anything. The buttons are drawn from the request's current state, so
  whatever is already true offers its undo instead of itself, and every change
  repaints the notice in place (`editMessageText`, falling back to replacing
  only the keyboard). A URL button opens the admin page; the address is in the
  text as well, for a client that will not draw one.
- **`apps/content/models.py: BotState`** — a singleton holding the last
  `update_id` handled, so a webhook retry can never archive a request twice,
  and which request a note (or, with `awaiting_reply`, an answer) is being
  written for, because «یادداشت» and «پاسخ» are a button press first and a
  text message second.

**A note can be filed three ways**, in order of how explicit the owner was:
`#12 text`, a reply to a notice (its `#12` is parsed back out), or the request
whose «یادداشت» button was pressed in the last `BOT_NOTE_WINDOW_SECONDS`.
Nothing matches, and the bot says how instead of guessing. **An answer to
the visitor only ever follows the «پاسخ» button** — a `#12` or a swiped
notice is always a private note, because an answer goes out to somebody.

**The transport is a webhook**, at `/bot/<secret>/` outside `i18n_patterns`
with the other machine endpoints. Long-polling would need a second process and
this site is one container with one process; `manage.py bale poll` covers
local work, where there is no public HTTPS address — it is the dev override's
`bot` service, so it exists only on a developer's machine. `start.sh` re-registers
the webhook on every boot, best effort, which is also what repairs a changed
`DJANGO_SITE_URL` by itself.

Three things guard the endpoint: a secret compared with
`constant_time_compare`, the route 404ing entirely when no secret is
configured, and **every action checking the update came from
`BOT_CHAT_ID`**. A malformed body is answered `200` and dropped — a messenger
told "error" redelivers the same update forever. `/id` (and `/start`, while
the visitor half below is off) is the exception that answers anybody: before
`DJANGO_BOT_CHAT_ID` is filled in nobody is the owner yet, and that is how the
id is found.

**A notification may never cost a request.** The row is committed first and
announced second, from `transaction.on_commit` on a daemon thread, and
`bot.guarded` swallows and logs whatever comes back. Empty token or chat id
turns the whole feature off: the form behaves exactly as it did before.

The admin writes the same two fields the buttons write and calls
`bot.refresh_later()` afterwards, so the phone and `/admin/` cannot drift.
Opening a request marks it read, the way any other inbox does.

## The same bot, from the visitor's side

A visitor can have their request's updates sent to their own Bale, and reply
or cancel from there. **Same bot, same webhook; the role comes from the
chat.** The owner is `BOT_CHAT_ID` and nothing else; a visitor is a chat a
`ChatLink` row names, and only for the request that row names. The owner's
`req:` buttons still check `BOT_CHAT_ID` exactly as before; the visitor's
`vis:` buttons are routed to `apps/core/visitor.py` before that check and
look the `ChatLink` up again for *that chat and that request* on every
press — the id in `callback_data` is a label, never a key. The owner's chat
never becomes a visitor.

**A bot cannot write to a phone number, so the visitor comes to the bot.**
The tracking page's «دریافت پاسخ‌ها در بله» is a POST (a link preview must
not mint anything) that issues a `ChatLinkToken` and redirects to
`ble.ir/<DJANGO_BOT_USERNAME>?start=<token>`. The token, not the tracking
code, is what travels through the messenger; it lives
`BOT_LINK_TOKEN_SECONDS`, is claimed by the first chat that sends
`/start <token>`, and is spent by the first contact that chat shares. The bot
asks for the number with a `request_contact` button, and links the chat only
if **the card is the sender's own** (`contact.user_id == from.id == chat.id`
— a forwarded card proves nothing, and a card without `user_id` is refused)
**and its number is the request's**, both through `normalise_phone` (Persian
digits, `+98`, `0098`, `9…` all become `09…`). A request without a phone
cannot be linked; the page says so instead of offering the button. `/stop`
unlinks every request of the chat; the page has its own «disconnect».

**What the visitor is told** is decided in one place: `bot.refresh()` — which
every owner-side change already passes through, from the bot or the admin —
calls `visitor.tell_later()`. `ChatLink.told_status`/`told_reply_id` hold
what the visitor last heard, so a change is sent once, a repaint with nothing
new sends nothing, and a private note, which changes neither, is never sent.
The claim is made before sending and undone if the send fails, so a missed
answer rides along with the next change. The text is in `Message.language`
with the same `status.*` labels as the tracking page; every bot string for
visitors is `bale.*` in `apps/core/i18n.py`. Changes the visitor made
themselves call `visitor_acted()` so they are not echoed back.

**A reply from Bale is a reply** — «پاسخ», then text, then
`add_reply(from_owner=False)` and `notify_reply`, identical to the page. A
visitor's `#12 text` is never a note; only the owner files notes. **Cancel
asks twice** (the second press is `vis:confirm`), then `cancel_by_visitor()`
archives the request and writes a `Reply` with `event="cancelled"` — a turn in
the conversation rather than a flag, so it stays on the record after the
visitor writes again, which reopens the request like any reply.
`cancelled_by_visitor` (archived, and the last turn is that event) is what
puts «لغو شده توسط مشتری» in the owner's notice. Reply and cancel share the
form's one-a-minute throttle, per chat (`ChatLink.last_action_at`).

Sending follows the owner's rules: after commit, on a daemon thread, through
`bot.guarded`. The half is off — no button on the page, `/start` answers with
the chat id as before — unless the owner's half is configured **and**
`DJANGO_BOT_USERNAME` is set.

## The digital business card

`/card/` is one screen made to be handed over, and `/card/montazeri.vcf` is a
real vCard so a phone saves the contact rather than a screenshot. The QR is
rendered **server-side** by `segno` as inline SVG: it prints, it survives a
screenshot, and it needs no JavaScript to exist.

`segno` will not accept `currentColor`, so the code is drawn in a sentinel hex
and swapped in `apps/core/views.py`. That is what lets one SVG be legible in
both themes without rendering the QR twice.
