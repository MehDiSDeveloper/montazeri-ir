"""The contact form's guards, and the request bot that triages what it saves.

Nothing here touches the network: `apps.core.messenger.call` is the one place
the outside world is reached, so a fake in its place makes every button press,
note and repaint an ordinary, fast assertion.
"""

from __future__ import annotations

import time
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.content.models import BotState, Message
from apps.core import bot, messenger

BOT = dict(
    BOT_TOKEN="test-token",
    BOT_CHAT_ID="555",
    BOT_WEBHOOK_SECRET="s3cret",
    SITE_URL="https://montazeri.ir",
    GEO_LANGUAGE_ENABLED=False,
)

FORM = {"name": "سارا", "email": "sara@example.com", "body": "یک پروژه دارم."}


class FakeBale:
    """Stands in for the API. Records every call and answers plausibly."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.next_message_id = 100

    def __call__(self, method, payload=None, timeout=None):
        payload = payload or {}
        self.calls.append((method, payload))
        if method == "sendMessage":
            self.next_message_id += 1
            return {"message_id": self.next_message_id, "chat": {"id": "555"}}
        return {}

    def of(self, method: str) -> list[dict]:
        return [payload for name, payload in self.calls if name == method]

    @property
    def texts(self) -> list[str]:
        return [payload.get("text", "") for _, payload in self.calls]


def callback(data: str, chat_id: str = "555", update_id: int = 1) -> dict:
    return {
        "update_id": update_id,
        "callback_query": {
            "id": "cb1",
            "data": data,
            "message": {"message_id": 101, "chat": {"id": chat_id}},
        },
    }


def written(text: str, chat_id: str = "555", update_id: int = 1, reply_to: str | None = None) -> dict:
    message = {"message_id": 7, "chat": {"id": chat_id}, "text": text}
    if reply_to is not None:
        message["reply_to_message"] = {"message_id": 101, "text": reply_to}
    return {"update_id": update_id, "message": message}


# ── the form ───────────────────────────────────────────────────────────────
@override_settings(GEO_LANGUAGE_ENABLED=False)
class ContactFormTests(TestCase):
    def test_a_message_is_saved_and_the_redirect_prevents_a_resend(self):
        response = self.client.post("/contact/", FORM)
        self.assertRedirects(response, "/contact/?sent=1")
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.get().status, Message.Status.NEW)

    def test_the_honeypot_saves_nothing_and_looks_identical(self):
        response = self.client.post("/contact/", {**FORM, "website": "http://spam.example"})
        self.assertRedirects(response, "/contact/?sent=1")
        self.assertEqual(Message.objects.count(), 0)

    def test_the_throttle_refuses_a_second_message_inside_a_minute(self):
        self.client.post("/contact/", FORM)
        self.client.post("/contact/", {**FORM, "body": "دوباره"})
        self.assertEqual(Message.objects.count(), 1)

    def test_the_throttle_lets_go_after_its_window(self):
        self.client.post("/contact/", FORM)
        session = self.client.session
        session["contact_last_sent"] = time.time() - 120
        session.save()
        self.client.post("/contact/", {**FORM, "body": "دوباره"})
        self.assertEqual(Message.objects.count(), 2)

    def test_the_phone_is_optional(self):
        self.client.post("/contact/", FORM)
        self.assertEqual(Message.objects.get().phone, "")

    def test_a_phone_typed_in_persian_digits_is_stored_dialable(self):
        self.client.post("/contact/", {**FORM, "phone": "۰۹۱۲۳۴۵۶۷۸۹"})
        self.assertEqual(Message.objects.get().phone, "09123456789")

    def test_a_phone_that_is_not_one_is_refused_without_losing_the_message(self):
        response = self.client.post("/contact/", {**FORM, "phone": "بزنگید"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)
        self.assertContains(response, "شمارهٔ تماس معتبر نیست")

    def test_the_form_offers_a_phone_field_in_every_language(self):
        for prefix in ("/", "/en/", "/de/"):
            with self.subTest(prefix=prefix):
                self.assertContains(self.client.get(f"{prefix}contact/"), 'name="phone"')


# ── the notice ─────────────────────────────────────────────────────────────
@override_settings(**BOT)
class NoticeTests(TestCase):
    def setUp(self):
        self.bale = FakeBale()
        patcher = patch.object(messenger, "call", self.bale)
        patcher.start()
        self.addCleanup(patcher.stop)
        # In production the notice goes out on its own thread. Here it runs
        # inline — but through the same guard, so "a failure never reaches the
        # visitor" is the real code being tested and not the stand-in.
        inline = patch.object(bot, "in_background", bot.guarded)
        inline.start()
        self.addCleanup(inline.stop)

    def _submit(self, **extra):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post("/contact/", {**FORM, **extra})
        return Message.objects.get()

    def test_a_new_request_arrives_with_every_field_and_a_panel_link(self):
        message = self._submit(phone="09123456789", subject="پروژه")
        text = self.bale.of("sendMessage")[0]["text"]

        self.assertIn("سارا", text)
        self.assertIn("sara@example.com", text)
        self.assertIn("09123456789", text)
        self.assertIn("پروژه", text)
        self.assertIn("یک پروژه دارم.", text)
        self.assertIn(f"https://montazeri.ir/admin/content/message/{message.pk}/change/", text)

    def test_an_empty_field_is_shown_as_empty_rather_than_left_out(self):
        self._submit()
        self.assertIn("تلفن: —", self.bale.of("sendMessage")[0]["text"])

    def test_the_notice_is_remembered_so_it_can_be_repainted(self):
        message = self._submit()
        self.assertEqual(message.bot_message_id, "101")
        self.assertIsNotNone(message.notified_at)

    def test_nothing_is_sent_when_no_bot_is_configured(self):
        with override_settings(BOT_TOKEN="", BOT_CHAT_ID=""):
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post("/contact/", FORM)
        self.assertEqual(self.bale.calls, [])
        self.assertEqual(Message.objects.count(), 1)

    def test_a_messenger_that_is_down_never_costs_the_request(self):
        with patch.object(messenger, "call", side_effect=messenger.BotError("boom")):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post("/contact/", FORM)
        self.assertRedirects(response, "/contact/?sent=1")
        self.assertEqual(Message.objects.count(), 1)

    def test_the_buttons_offer_the_undo_of_whatever_is_already_true(self):
        message = self._submit()
        labels = [button["text"] for row in bot.keyboard(message) for button in row]
        self.assertIn(bot.BUTTON_READ, labels)

        message.set_status(Message.Status.ARCHIVED)
        labels = [button["text"] for row in bot.keyboard(message) for button in row]
        self.assertIn(bot.BUTTON_UNARCHIVE, labels)
        self.assertNotIn(bot.BUTTON_ARCHIVE, labels)

    def test_the_panel_button_is_a_link_not_a_callback(self):
        message = self._submit()
        panel = bot.keyboard(message)[-1][0]
        self.assertEqual(panel["url"], message.admin_url)


# ── the buttons ────────────────────────────────────────────────────────────
@override_settings(**BOT)
class TriageTests(TestCase):
    def setUp(self):
        self.bale = FakeBale()
        patcher = patch.object(messenger, "call", self.bale)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.message = Message.objects.create(
            name="سارا", email="sara@example.com", body="یک پروژه دارم.", bot_message_id="101", bot_chat_id="555"
        )

    def press(self, action: str, **kwargs):
        bot.handle_update(callback(f"req:{action}:{self.message.pk}", **kwargs))
        self.message.refresh_from_db()

    def test_read_reject_and_archive_each_move_the_request(self):
        for action, expected in [
            ("read", Message.Status.READ),
            ("reject", Message.Status.REJECTED),
            ("unreject", Message.Status.READ),
            ("archive", Message.Status.ARCHIVED),
            ("unarchive", Message.Status.READ),
            ("unread", Message.Status.NEW),
        ]:
            with self.subTest(action=action):
                BotState.objects.all().delete()  # each press is its own update
                self.press(action)
                self.assertEqual(self.message.status, expected)

    def test_reading_stamps_the_time_and_going_back_to_new_clears_it(self):
        self.press("read")
        self.assertIsNotNone(self.message.read_at)
        BotState.objects.all().delete()
        self.press("unread")
        self.assertIsNone(self.message.read_at)

    def test_the_notice_is_repainted_with_the_new_state(self):
        self.press("archive")
        edited = self.bale.of("editMessageText")
        self.assertEqual(len(edited), 1)
        self.assertIn("بایگانی", edited[0]["text"])

    def test_only_editing_the_buttons_is_enough_when_the_text_cannot_be_edited(self):
        def refuse_text(method, payload=None, timeout=None):
            if method == "editMessageText":
                raise messenger.BotError("not supported")
            return self.bale(method, payload, timeout)

        with patch.object(messenger, "call", refuse_text):
            self.press("archive")
        self.assertEqual(self.message.status, Message.Status.ARCHIVED)
        self.assertEqual(len(self.bale.of("editMessageReplyMarkup")), 1)

    def test_a_press_from_another_chat_changes_nothing(self):
        self.press("archive", chat_id="999")
        self.assertEqual(self.message.status, Message.Status.NEW)
        self.assertEqual(self.bale.of("editMessageText"), [])

    def test_the_same_update_delivered_twice_is_acted_on_once(self):
        self.press("archive", update_id=42)
        self.press("unarchive", update_id=42)  # a webhook retry of the first
        self.assertEqual(self.message.status, Message.Status.ARCHIVED)

    def test_a_press_on_a_deleted_request_says_so_instead_of_failing(self):
        pk = self.message.pk
        self.message.delete()
        bot.handle_update(callback(f"req:archive:{pk}"))
        self.assertEqual(self.bale.of("answerCallbackQuery")[0]["text"], "این درخواست دیگر وجود ندارد.")


# ── notes ──────────────────────────────────────────────────────────────────
@override_settings(**BOT)
class NoteTests(TestCase):
    def setUp(self):
        self.bale = FakeBale()
        patcher = patch.object(messenger, "call", self.bale)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.message = Message.objects.create(
            name="سارا", email="sara@example.com", body="یک پروژه دارم.", bot_message_id="101", bot_chat_id="555"
        )

    def test_pressing_the_note_button_then_writing_files_the_note(self):
        bot.handle_update(callback(f"req:note:{self.message.pk}", update_id=1))
        bot.handle_update(written("زنگ زدم، فردا جواب می‌دهد.", update_id=2))

        self.message.refresh_from_db()
        self.assertIn("زنگ زدم، فردا جواب می‌دهد.", self.message.notes)
        self.assertIsNone(BotState.load().awaiting_note_for)

    def test_a_note_carries_its_date(self):
        self.message.add_note("پیگیری شد")
        self.assertRegex(self.message.notes, r"^1[34]\d\d/\d\d/\d\d \d\d:\d\d — پیگیری شد$")

    def test_notes_stack_rather_than_replace(self):
        self.message.add_note("اول")
        self.message.add_note("دوم")
        self.assertEqual(len(self.message.notes.strip().splitlines()), 2)

    def test_a_hash_prefix_files_a_note_on_any_request(self):
        other = Message.objects.create(name="علی", email="a@b.co", body="سلام")
        bot.handle_update(written(f"#{other.pk} بعداً تماس بگیر"))
        other.refresh_from_db()
        self.assertIn("بعداً تماس بگیر", other.notes)

    def test_replying_to_a_notice_files_the_note_on_that_request(self):
        bot.handle_update(
            written("قرارداد فرستاده شد", reply_to=f"📩 درخواست تازه #{self.message.pk} — montazeri.ir")
        )
        self.message.refresh_from_db()
        self.assertIn("قرارداد فرستاده شد", self.message.notes)

    def test_the_note_appears_in_the_repainted_notice(self):
        bot.handle_update(callback(f"req:note:{self.message.pk}", update_id=1))
        bot.handle_update(written("پیگیری شد", update_id=2))
        self.assertIn("پیگیری شد", self.bale.of("editMessageText")[0]["text"])

    def test_a_note_for_a_request_that_is_gone_is_not_filed_on_another_one(self):
        bot.handle_update(callback(f"req:note:{self.message.pk}", update_id=1))
        bot.handle_update(written("#9999 یادداشت", update_id=2))
        self.message.refresh_from_db()
        self.assertEqual(self.message.notes, "")
        self.assertIn("#9999", self.bale.texts[-1])

    def test_writing_with_nothing_pending_explains_how_instead_of_guessing(self):
        bot.handle_update(written("یک چیزی"))
        self.message.refresh_from_db()
        self.assertEqual(self.message.notes, "")
        self.assertIn("#12", self.bale.texts[-1])

    def test_a_pending_note_expires_rather_than_landing_on_the_wrong_request(self):
        bot.handle_update(callback(f"req:note:{self.message.pk}", update_id=1))
        BotState.objects.update(awaiting_since="2020-01-01T00:00:00Z")
        bot.handle_update(written("خیلی دیر", update_id=2))
        self.message.refresh_from_db()
        self.assertEqual(self.message.notes, "")

    def test_a_stranger_writing_to_the_bot_is_ignored(self):
        bot.handle_update(written("یادداشت", chat_id="999"))
        self.message.refresh_from_db()
        self.assertEqual(self.message.notes, "")


# ── commands and the webhook ───────────────────────────────────────────────
@override_settings(**BOT)
class BotEndpointTests(TestCase):
    def setUp(self):
        self.bale = FakeBale()
        patcher = patch.object(messenger, "call", self.bale)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_id_answers_anyone_because_that_is_how_the_chat_id_is_found(self):
        bot.handle_update(written("/id", chat_id="999"))
        self.assertIn("999", self.bale.of("sendMessage")[0]["text"])

    def test_id_still_answers_before_the_chat_id_has_been_configured(self):
        # The setup order is: token, then ask the bot who you are, then fill
        # DJANGO_BOT_CHAT_ID in. The middle step must work with it empty.
        with override_settings(BOT_CHAT_ID=""):
            bot.handle_update(written("/id", chat_id="999"))
        self.assertIn("999", self.bale.of("sendMessage")[0]["text"])

    def test_new_lists_the_requests_still_unread(self):
        Message.objects.create(name="سارا", email="s@b.co", body="متن")
        Message.objects.create(name="علی", email="a@b.co", body="متن", status=Message.Status.ARCHIVED)
        bot.handle_update(written("/new"))
        self.assertEqual(len(self.bale.of("sendMessage")), 1)
        self.assertIn("سارا", self.bale.of("sendMessage")[0]["text"])

    def test_an_unknown_command_answers_with_the_help(self):
        bot.handle_update(written("/wat"))
        self.assertIn("/help", self.bale.of("sendMessage")[0]["text"])

    def test_the_webhook_accepts_an_update_on_the_secret_path(self):
        message = Message.objects.create(name="سارا", email="s@b.co", body="متن")
        response = self.client.post(
            "/bot/s3cret/",
            data=callback(f"req:archive:{message.pk}"),
            content_type="application/json",
        )
        message.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(message.status, Message.Status.ARCHIVED)

    def test_a_wrong_secret_is_not_a_page(self):
        self.assertEqual(self.client.post("/bot/nope/", data="{}", content_type="application/json").status_code, 404)

    def test_the_endpoint_does_not_exist_without_a_configured_secret(self):
        with override_settings(BOT_WEBHOOK_SECRET=""):
            response = self.client.post("/bot/s3cret/", data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 404)

    def test_a_broken_body_is_accepted_and_dropped_rather_than_redelivered(self):
        response = self.client.post("/bot/s3cret/", data="not json", content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_the_webhook_is_kept_out_of_robots(self):
        self.assertContains(self.client.get("/robots.txt"), "Disallow: /bot/")


# ── the inbox ──────────────────────────────────────────────────────────────
@override_settings(**BOT)
class InboxTests(TestCase):
    """The admin is the other half of the same triage, so it moves a request
    the same way and repaints the same notice."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import User

        User.objects.create_superuser("mahdi", "m@example.com", "pw-for-tests-only")

    def setUp(self):
        self.bale = FakeBale()
        patcher = patch.object(messenger, "call", self.bale)
        patcher.start()
        self.addCleanup(patcher.stop)
        inline = patch.object(bot, "in_background", bot.guarded)
        inline.start()
        self.addCleanup(inline.stop)

        self.client.login(username="mahdi", password="pw-for-tests-only")
        self.message = Message.objects.create(
            name="سارا", email="sara@example.com", phone="09123456789", body="متن",
            bot_message_id="101", bot_chat_id="555",
        )

    def test_the_list_renders(self):
        self.assertEqual(self.client.get("/admin/content/message/").status_code, 200)

    def test_opening_a_request_reads_it_and_repaints_the_notice(self):
        response = self.client.get(f"/admin/content/message/{self.message.pk}/change/")
        self.message.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.message.status, Message.Status.READ)
        self.assertIn("خوانده‌شده", self.bale.of("editMessageText")[0]["text"])

    def test_a_status_set_here_reaches_the_phone(self):
        self.client.post(
            f"/admin/content/message/{self.message.pk}/change/",
            {"status": Message.Status.ARCHIVED, "notes": "بعداً"},
        )
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, Message.Status.ARCHIVED)
        self.assertIn("بایگانی", self.bale.of("editMessageText")[-1]["text"])

    def test_a_request_cannot_be_invented_here(self):
        self.assertEqual(self.client.get("/admin/content/message/add/").status_code, 403)
