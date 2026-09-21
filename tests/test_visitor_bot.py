"""The request bot from the visitor's side: linking a chat to a request, the
updates it then receives, and the reply and cancellation it can send back.

The same FakeBale as test_contact_requests.py stands in for the API, so none
of it touches the network. The owner is chat 555; the visitor is chat 777;
chat 888 is somebody else.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.content.models import ChatLink, ChatLinkToken, Message, normalise_phone
from apps.core import bot, messenger

from .test_contact_requests import BOT, FakeBale, callback, written

VISITOR = {**BOT, "BOT_USERNAME": "montazeri_bot"}
VISITOR_CHAT = 777
STRANGER_CHAT = 888


def _request(**fields) -> Message:
    return Message.objects.create(
        **{
            "name": "سارا",
            "email": "sara@example.com",
            "phone": "0912 345 6789",
            "body": "یک پروژه دارم.",
            "language": "fa",
            **fields,
        }
    )


def shared(phone: str, chat_id=VISITOR_CHAT, user_id=None, update_id: int = 50) -> dict:
    """The update a request_contact button sends: the sender's own card."""
    return {
        "update_id": update_id,
        "message": {
            "message_id": 9,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": chat_id},
            "contact": {
                "phone_number": phone,
                "first_name": "Sara",
                "user_id": chat_id if user_id is None else user_id,
            },
        },
    }


class VisitorBotCase(TestCase):
    """The fake API, with background work run inline through the real guard."""

    def setUp(self):
        self.bale = FakeBale()
        for target, name, value in (
            (messenger, "call", self.bale),
            (bot, "in_background", bot.guarded),
        ):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.update_id = 100

    def send(self, update: dict) -> None:
        self.update_id += 1
        update["update_id"] = self.update_id
        with self.captureOnCommitCallbacks(execute=True):
            bot.handle_update(update)

    def to(self, chat_id) -> list[dict]:
        return [p for p in self.bale.of("sendMessage") if str(p.get("chat_id")) == str(chat_id)]

    def last_to(self, chat_id) -> dict:
        sent = self.to(chat_id)
        self.assertTrue(sent, f"nothing was sent to {chat_id}")
        return sent[-1]

    def link(self, message: Message, chat_id=VISITOR_CHAT) -> ChatLink:
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=chat_id))
        self.send(shared("+989123456789", chat_id=chat_id))
        return ChatLink.objects.get(message=message)


# ── the phone number ───────────────────────────────────────────────────────
class PhoneTests(TestCase):
    def test_every_way_of_writing_an_iranian_mobile_is_the_same_number(self):
        for written_as in ("09123456789", "۰۹۱۲۳۴۵۶۷۸۹", "+98 912 345 6789", "00989123456789", "989123456789", "9123456789"):
            with self.subTest(written_as=written_as):
                self.assertEqual(normalise_phone(written_as), "09123456789")

    def test_a_foreign_number_keeps_its_country_code(self):
        self.assertEqual(normalise_phone("+49 151 2345 6789"), "4915123456789")

    def test_too_few_digits_is_no_number(self):
        self.assertEqual(normalise_phone("12"), "")


# ── the tracking page ──────────────────────────────────────────────────────
@override_settings(**VISITOR)
class TrackingPageTests(VisitorBotCase):
    def test_the_page_offers_bale_when_the_request_has_a_phone(self):
        message = _request()
        response = self.client.get(message.get_absolute_url())
        self.assertContains(response, f"/contact/track/{message.tracking_code}/bale/")

    def test_without_a_phone_the_page_says_why_instead_of_offering_a_button(self):
        message = _request(phone="")
        response = self.client.get(message.get_absolute_url())
        self.assertNotContains(response, "/bale/")
        self.assertContains(response, "شمارهٔ تماس داشته باشد")

    def test_the_button_leads_to_the_bot_with_a_token_and_not_the_code(self):
        message = _request()
        response = self.client.post(f"/contact/track/{message.tracking_code}/bale/")
        token = ChatLinkToken.objects.get(message=message)
        self.assertEqual(response["Location"], f"https://ble.ir/montazeri_bot?start={token.token}")
        self.assertNotIn(message.tracking_code.replace("-", ""), response["Location"].replace("-", ""))

    def test_pressing_again_reuses_the_waiting_token(self):
        message = _request()
        self.client.post(f"/contact/track/{message.tracking_code}/bale/")
        self.client.post(f"/contact/track/{message.tracking_code}/bale/")
        self.assertEqual(ChatLinkToken.objects.count(), 1)

    def test_a_get_never_mints_a_token(self):
        message = _request()
        response = self.client.get(f"/contact/track/{message.tracking_code}/bale/")
        self.assertEqual(response.status_code, 405)
        self.assertFalse(ChatLinkToken.objects.exists())

    def test_the_page_can_disconnect_and_the_chat_is_told(self):
        message = _request()
        self.link(message)
        self.assertContains(self.client.get(message.get_absolute_url()), "/bale/stop/")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(f"/contact/track/{message.tracking_code}/bale/stop/")
        self.assertRedirects(response, f"{message.get_absolute_url()}?bale=off#bale", fetch_redirect_response=False)
        self.assertFalse(ChatLink.objects.exists())
        self.assertIn(message.tracking_code, self.last_to(VISITOR_CHAT)["text"])


@override_settings(**BOT)
class SwitchedOffTests(VisitorBotCase):
    """No BOT_USERNAME: the visitor half does not exist."""

    def test_the_page_offers_nothing(self):
        message = _request()
        self.assertNotContains(self.client.get(message.get_absolute_url()), "/bale/")

    def test_the_button_mints_nothing(self):
        message = _request()
        self.client.post(f"/contact/track/{message.tracking_code}/bale/")
        self.assertFalse(ChatLinkToken.objects.exists())

    def test_start_still_answers_with_the_chat_id(self):
        self.send(written("/start whatever", chat_id=STRANGER_CHAT))
        self.assertIn(str(STRANGER_CHAT), self.last_to(STRANGER_CHAT)["text"])

    def test_a_shared_contact_is_ignored(self):
        _request()
        self.send(shared("+989123456789"))
        self.assertFalse(ChatLink.objects.exists())
        self.assertFalse(self.bale.calls)


# ── linking ────────────────────────────────────────────────────────────────
@override_settings(**VISITOR)
class LinkingTests(VisitorBotCase):
    def test_start_asks_for_the_phone_with_a_contact_button(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        asked = self.last_to(VISITOR_CHAT)
        self.assertIn(message.tracking_code, asked["text"])
        self.assertTrue(asked["reply_markup"]["keyboard"][0][0]["request_contact"])
        self.assertFalse(ChatLink.objects.exists())

    def test_the_matching_number_links_the_chat(self):
        message = _request()
        link = self.link(message)
        self.assertEqual((link.chat_id, link.phone), (str(VISITOR_CHAT), "09123456789"))
        confirmed = self.last_to(VISITOR_CHAT)
        self.assertIn("وصل شد", confirmed["text"])
        self.assertTrue(confirmed["reply_markup"]["remove_keyboard"])

    def test_the_bot_speaks_the_language_the_request_was_written_in(self):
        message = _request(language="de")
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        self.assertIn("Nummer", self.last_to(VISITOR_CHAT)["text"])

    def test_a_different_number_is_refused_and_the_link_is_spent(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        self.send(shared("+989350000000"))
        self.assertFalse(ChatLink.objects.exists())
        self.assertIn("یکی نیست", self.last_to(VISITOR_CHAT)["text"])
        # The right number afterwards does not rescue a spent link.
        self.send(shared("+989123456789"))
        self.assertFalse(ChatLink.objects.exists())

    def test_somebody_elses_contact_card_is_refused(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        # A card carrying the right number, but for a different Bale user.
        self.send(shared("+989123456789", user_id=12345))
        self.assertFalse(ChatLink.objects.exists())
        self.assertIn("شمارهٔ خودتان", self.last_to(VISITOR_CHAT)["text"])
        # Not spent: the button itself still works.
        self.send(shared("+989123456789"))
        self.assertTrue(ChatLink.objects.exists())

    def test_a_card_without_a_user_id_proves_nothing(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        update = shared("+989123456789")
        del update["message"]["contact"]["user_id"]
        self.send(update)
        self.assertFalse(ChatLink.objects.exists())

    def test_an_expired_link_is_refused(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        ChatLinkToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        self.assertIn("منقضی", self.last_to(VISITOR_CHAT)["text"])
        self.send(shared("+989123456789"))
        self.assertFalse(ChatLink.objects.exists())

    def test_a_used_link_is_refused(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        self.link(message)
        self.send(written(f"/start {token.token}", chat_id=STRANGER_CHAT))
        self.assertIn("منقضی", self.last_to(STRANGER_CHAT)["text"])
        self.assertEqual(ChatLink.objects.get().chat_id, str(VISITOR_CHAT))

    def test_a_link_opened_in_one_chat_cannot_be_finished_in_another(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        self.send(written(f"/start {token.token}", chat_id=STRANGER_CHAT))
        self.assertIn("منقضی", self.last_to(STRANGER_CHAT)["text"])
        self.send(shared("+989123456789", chat_id=STRANGER_CHAT))
        self.assertFalse(ChatLink.objects.exists())

    def test_a_made_up_token_is_refused(self):
        _request()
        self.send(written("/start not-a-real-token", chat_id=VISITOR_CHAT))
        self.assertIn("منقضی", self.last_to(VISITOR_CHAT)["text"])

    def test_a_request_without_a_phone_cannot_be_linked(self):
        message = _request(phone="")
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id=VISITOR_CHAT))
        self.send(shared("+989123456789"))
        self.assertFalse(ChatLink.objects.exists())
        self.assertIn("شمارهٔ تماس", self.last_to(VISITOR_CHAT)["text"])

    def test_the_owner_never_becomes_a_visitor(self):
        message = _request()
        token = ChatLinkToken.issue(message)
        self.send(written(f"/start {token.token}", chat_id="555"))
        self.send(shared("+989123456789", chat_id=555))
        self.assertFalse(ChatLink.objects.exists())

    def test_plain_start_explains_how_to_connect(self):
        self.send(written("/start", chat_id=STRANGER_CHAT))
        self.assertIn("دریافت پاسخ‌ها در بله", self.last_to(STRANGER_CHAT)["text"])

    def test_stop_disconnects_every_request_of_the_chat(self):
        first, second = _request(), _request()
        self.link(first)
        self.link(second)
        self.send(written("/stop", chat_id=VISITOR_CHAT))
        self.assertFalse(ChatLink.objects.exists())
        self.assertIn(first.tracking_code, self.last_to(VISITOR_CHAT)["text"])
