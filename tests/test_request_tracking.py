"""A request as a conversation: the tracking code, the visitor's page, replies
from both sides and the status each one leaves behind — and the admin inbox
that finds a request by who sent it, what it is, and how soon it is due.

Like test_contact_requests.py, nothing here reaches the network: the bot is
the same FakeBale in place of `messenger.call`.
"""

from __future__ import annotations

import time
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.content.models import BotState, Message, normalise_tracking_code
from apps.core import bot, messenger

from .test_contact_requests import BOT, FORM, FakeBale, callback, written


def _request(**fields) -> Message:
    return Message.objects.create(**{"name": "سارا", "email": "sara@example.com", "body": "یک پروژه دارم.", **fields})


def _let_the_minute_pass(client) -> None:
    session = client.session
    session["contact_last_sent"] = time.time() - 120
    session.save()


# ── the form, and the code it hands back ───────────────────────────────────
@override_settings(GEO_LANGUAGE_ENABLED=False)
class NewFieldsTests(TestCase):
    def test_company_type_and_timeline_are_saved(self):
        self.client.post("/contact/", {**FORM, "company": "شرکت نمونه", "kind": "consult", "timeline": "week"})
        message = Message.objects.get()
        self.assertEqual(message.company, "شرکت نمونه")
        self.assertEqual(message.kind, Message.Kind.CONSULT)
        self.assertEqual(message.timeline, Message.Timeline.WEEK)

    def test_the_deadline_counts_from_the_day_it_was_asked(self):
        self.client.post("/contact/", {**FORM, "timeline": "month"})
        message = Message.objects.get()
        self.assertEqual(round((message.due_at - message.created_at).total_seconds() / 86400), 30)
        self.assertEqual(message.days_left(), 30)

    def test_skipping_type_and_timeline_is_not_an_error(self):
        response = self.client.post("/contact/", FORM)
        self.assertRedirects(response, "/contact/?sent=1")
        message = Message.objects.get()
        self.assertEqual((message.kind, message.timeline), (Message.Kind.OTHER, Message.Timeline.FLEXIBLE))
        self.assertIsNone(message.due_at)

    def test_start_a_project_picks_the_type_as_well_as_the_subject(self):
        response = self.client.get("/contact/?topic=project")
        self.assertContains(response, 'value="project" checked')

    def test_the_thank_you_shows_the_code_and_the_way_to_use_it(self):
        response = self.client.post("/contact/", FORM, follow=True)
        code = Message.objects.get().tracking_code
        self.assertContains(response, code)
        self.assertContains(response, f"/contact/track/{code}/")

    def test_the_thank_you_address_itself_carries_no_code(self):
        response = self.client.post("/contact/", FORM)
        self.assertNotIn(Message.objects.get().tracking_code, response["Location"])

    def test_every_request_gets_its_own_code(self):
        codes = {_request().tracking_code for _ in range(20)}
        self.assertEqual(len(codes), 20)

    def test_a_code_is_read_however_it_was_typed(self):
        self.assertEqual(normalise_tracking_code("7kq4 m2xd"), "7KQ4-M2XD")
        self.assertEqual(normalise_tracking_code("7KQ4--M2XD"), "7KQ4-M2XD")
        self.assertEqual(normalise_tracking_code("7KQ4"), "")


# ── looking a request up ───────────────────────────────────────────────────
@override_settings(GEO_LANGUAGE_ENABLED=False)
class LookupTests(TestCase):
    def setUp(self):
        cache.clear()
        self.message = _request()

    def test_the_lookup_page_answers_in_every_language_and_is_not_indexed(self):
        for prefix in ("/", "/en/", "/de/"):
            with self.subTest(prefix=prefix):
                response = self.client.get(f"{prefix}contact/track/")
                self.assertContains(response, 'name="code"')
                self.assertContains(response, "noindex")

    def test_a_right_code_opens_the_request(self):
        typed = self.message.tracking_code.lower().replace("-", "")
        response = self.client.post("/contact/track/", {"code": typed})
        self.assertRedirects(response, f"/contact/track/{self.message.tracking_code}/")

    def test_a_wrong_code_says_so(self):
        response = self.client.post("/contact/track/", {"code": "2222-2222"})
        self.assertContains(response, "درخواستی با این کد پیدا نشد")

    @override_settings(TRACK_LOOKUP_LIMIT=3)
    def test_guessing_is_refused_after_a_few_wrong_codes(self):
        for _ in range(3):
            self.client.post("/contact/track/", {"code": "2222-2222"})
        response = self.client.post("/contact/track/", {"code": self.message.tracking_code})
        self.assertEqual(response.status_code, 429)

    def test_an_unknown_code_in_the_address_is_a_404(self):
        self.assertEqual(self.client.get("/contact/track/2222-2222/").status_code, 404)

    def test_a_lower_case_address_goes_to_the_real_one(self):
        response = self.client.get(f"/contact/track/{self.message.tracking_code.lower()}/")
        self.assertRedirects(response, f"/contact/track/{self.message.tracking_code}/")

    def test_the_request_page_is_never_indexed_and_robots_says_so_too(self):
        response = self.client.get(f"/contact/track/{self.message.tracking_code}/")
        self.assertContains(response, "noindex, nofollow")
        self.assertIn("Disallow: /contact/track/", self.client.get("/robots.txt").content.decode())

    def test_private_notes_never_reach_the_visitor(self):
        self.message.add_note("مشتری سخت‌گیر")
        response = self.client.get(f"/contact/track/{self.message.tracking_code}/")
        self.assertContains(response, "یک پروژه دارم.")
        self.assertNotContains(response, "مشتری سخت‌گیر")


# ── the conversation ───────────────────────────────────────────────────────
@override_settings(**BOT)
class ConversationTests(TestCase):
    def setUp(self):
        self.bale = FakeBale()
        patcher = patch.object(messenger, "call", self.bale)
        patcher.start()
        self.addCleanup(patcher.stop)
        inline = patch.object(bot, "in_background", bot.guarded)
        inline.start()
        self.addCleanup(inline.stop)
        self.message = _request(bot_message_id="101", bot_chat_id="555")
        self.url = f"/contact/track/{self.message.tracking_code}/"

    def _reply(self, body="ممنون، یک سؤال دیگر هم دارم.", **extra):
        _let_the_minute_pass(self.client)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(self.url, {"body": body, **extra})

    def test_the_owner_answering_makes_it_answered_and_the_visitor_sees_it(self):
        self.message.add_reply("سلام، فردا تماس می‌گیرم.", from_owner=True)
        self.assertEqual(self.message.status, Message.Status.ANSWERED)
        response = self.client.get(self.url)
        self.assertContains(response, "سلام، فردا تماس می‌گیرم.")
        self.assertContains(response, "پاسخ داده شد")

    def test_the_visitor_writing_back_puts_it_back_to_new(self):
        self.message.add_reply("سلام", from_owner=True)
        response = self._reply()
        self.assertRedirects(response, f"{self.url}?sent=1#thread-end", fetch_redirect_response=False)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, Message.Status.NEW)
        self.assertIsNone(self.message.read_at)
        self.assertTrue(self.message.is_active)

    def test_writing_back_reopens_even_a_rejected_or_archived_request(self):
        for status in (Message.Status.REJECTED, Message.Status.ARCHIVED):
            with self.subTest(status=status):
                self.message.set_status(status)
                self._reply()
                self.message.refresh_from_db()
                self.assertEqual(self.message.status, Message.Status.NEW)

    def test_as_many_turns_as_it_takes_in_order(self):
        for n in range(3):
            self.message.add_reply(f"پاسخ {n}", from_owner=True)
            self._reply(f"جواب {n}")
        bodies = [r.body for r in self.message.replies.all()]
        self.assertEqual(bodies, ["پاسخ 0", "جواب 0", "پاسخ 1", "جواب 1", "پاسخ 2", "جواب 2"])

    def test_a_reply_from_the_visitor_rings_the_phone_with_a_fresh_notice(self):
        self._reply("یک سؤال دیگر")
        text = self.bale.of("sendMessage")[-1]["text"]
        self.assertIn("پاسخ تازه", text)
        self.assertIn("یک سؤال دیگر", text)
        self.message.refresh_from_db()
        self.assertEqual(self.message.bot_message_id, str(self.bale.next_message_id))

    def test_the_reply_box_has_the_same_honeypot_and_throttle(self):
        self._reply(website="http://spam.example")
        self.assertEqual(self.message.replies.count(), 0)

        self._reply("اول")
        self.client.post(self.url, {"body": "دوم، بلافاصله"})
        self.assertEqual(self.message.replies.count(), 1)

    def test_an_empty_reply_is_refused(self):
        response = self._reply("   ")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.message.replies.count(), 0)

    def test_the_notice_carries_the_new_fields_and_the_code(self):
        message = _request(company="شرکت نمونه", kind="project", timeline="week")
        text = bot.notice_text(message)
        self.assertIn("شرکت نمونه", text)
        self.assertIn("نوع: پروژه", text)
        self.assertIn("7 روز مانده", text)
        self.assertIn(message.tracking_code, text)


# ── answering from the phone ───────────────────────────────────────────────
@override_settings(**BOT)
class BotReplyTests(TestCase):
    def setUp(self):
        self.bale = FakeBale()
        patcher = patch.object(messenger, "call", self.bale)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.message = _request(bot_message_id="101", bot_chat_id="555")

    def test_reply_then_text_is_an_answer_the_visitor_sees(self):
        bot.handle_update(callback(f"req:reply:{self.message.pk}", update_id=1))
        bot.handle_update(written("سلام، قیمت را فردا می‌فرستم.", update_id=2))

        self.message.refresh_from_db()
        reply = self.message.replies.get()
        self.assertTrue(reply.from_owner)
        self.assertEqual(self.message.status, Message.Status.ANSWERED)
        self.assertEqual(self.message.notes, "")
        self.assertFalse(BotState.load().awaiting_reply)

    def test_note_still_means_a_private_note(self):
        bot.handle_update(callback(f"req:note:{self.message.pk}", update_id=1))
        bot.handle_update(written("فقط برای خودم", update_id=2))
        self.message.refresh_from_db()
        self.assertIn("فقط برای خودم", self.message.notes)
        self.assertEqual(self.message.replies.count(), 0)

    def test_a_named_request_is_always_a_note_never_an_answer(self):
        bot.handle_update(callback(f"req:reply:{self.message.pk}", update_id=1))
        bot.handle_update(written(f"#{self.message.pk} یادداشت", update_id=2))
        self.assertEqual(self.message.replies.count(), 0)


# ── the inbox ──────────────────────────────────────────────────────────────
@override_settings(**BOT)
class InboxSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser("mahdi", "m@example.com", "pw-for-tests-only")
        now = timezone.now()
        cls.new = _request(name="علی", company="آلفا", kind="project")
        cls.read = _request(name="مریم", kind="consult", status="read")
        cls.answered = _request(name="رضا", status="answered")
        cls.rejected = _request(name="نگار", status="rejected")
        cls.archived = _request(name="کاوه", status="archived")
        cls.overdue = _request(name="دیرکرد", due_at=now - timedelta(days=2))
        cls.soon = _request(name="نزدیک", due_at=now + timedelta(days=2))
        cls.later = _request(name="دور", due_at=now + timedelta(days=20))

    def setUp(self):
        patcher = patch.object(messenger, "call", FakeBale())
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client.login(username="mahdi", password="pw-for-tests-only")

    def listed(self, query: str = "") -> set[str]:
        response = self.client.get(f"/admin/content/message/{query}")
        self.assertEqual(response.status_code, 200)
        return {m.name for m in response.context["cl"].result_list}

    def test_the_inbox_opens_on_active_requests(self):
        names = self.listed()
        self.assertIn("علی", names)
        self.assertIn("مریم", names)
        self.assertFalse({"رضا", "نگار", "کاوه"} & names)

    def test_all_is_every_status(self):
        self.assertTrue({"رضا", "نگار", "کاوه", "علی"} <= self.listed("?status=all"))

    def test_several_statuses_at_once(self):
        self.assertEqual(self.listed("?status=answered,archived"), {"رضا", "کاوه"})

    def test_a_status_link_toggles_one_status_in_or_out(self):
        response = self.client.get("/admin/content/message/")
        links = {c["display"].split(" (")[0]: c["query_string"]
                 for spec in response.context["cl"].filter_specs if getattr(spec, "parameter_name", "") == "status"
                 for c in spec.choices(response.context["cl"])}
        self.assertEqual(links["☐ پاسخ داده شده"], "?status=new%2Cread%2Canswered")
        self.assertEqual(links["☑ جدید"], "?status=read")

    def test_search_by_person_or_company(self):
        self.assertEqual(self.listed("?q=علی"), {"علی"})
        self.assertEqual(self.listed("?q=آلفا"), {"علی"})

    def test_search_by_request_type_by_name(self):
        self.assertEqual(self.listed("?q=مشاوره"), {"مریم"})
        self.assertEqual(self.listed("?q=project"), {"علی"})

    def test_search_by_tracking_code_however_typed(self):
        typed = self.new.tracking_code.lower().replace("-", "")
        self.assertEqual(self.listed(f"?q={typed}"), {"علی"})

    def test_search_looks_only_in_the_chosen_statuses(self):
        self.assertEqual(self.listed("?q=رضا"), set())
        self.assertEqual(self.listed("?q=رضا&status=all"), {"رضا"})

    def test_search_reaches_the_conversation(self):
        self.new.replies.create(body="بودجه‌ی تقریبی")
        self.assertEqual(self.listed("?q=بودجه‌ی"), {"علی"})

    def test_the_deadline_filter_and_its_closest_first_order(self):
        self.assertEqual(self.listed("?due=overdue"), {"دیرکرد"})
        self.assertEqual(self.listed("?due=3"), {"نزدیک"})
        response = self.client.get("/admin/content/message/?due=30")
        self.assertEqual([m.name for m in response.context["cl"].result_list], ["نزدیک", "دور"])

    def test_answering_from_the_admin_reaches_the_visitor(self):
        self.client.post(
            f"/admin/content/message/{self.read.pk}/change/",
            {"status": "read", "notes": "", "reply": "هفتهٔ بعد شروع می‌کنیم."},
        )
        self.read.refresh_from_db()
        self.assertEqual(self.read.status, Message.Status.ANSWERED)
        page = self.client.get(f"/contact/track/{self.read.tracking_code}/")
        self.assertContains(page, "هفتهٔ بعد شروع می‌کنیم.")

    def test_the_change_page_shows_the_conversation_and_the_visitors_link(self):
        self.new.add_reply("سلام", from_owner=True)
        response = self.client.get(f"/admin/content/message/{self.new.pk}/change/")
        self.assertContains(response, "سلام")
        self.assertContains(response, f"/contact/track/{self.new.tracking_code}/")
