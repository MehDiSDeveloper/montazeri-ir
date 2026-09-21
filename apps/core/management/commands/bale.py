"""
`manage.py bale <action>` — set the bot up, and check on it.

One command rather than five, because these are five things done once each,
in the same ten minutes, and a single `--help` that lists them is the whole
documentation of the feature:

    manage.py bale status          # is the token right, where do updates go
    manage.py bale set-webhook     # point Bale at DJANGO_SITE_URL/bot/<secret>/
    manage.py bale delete-webhook  # stop it (required before `poll`)
    manage.py bale poll            # receive updates without a public address
    manage.py bale test            # send yourself a message, prove the chat id

`poll` exists for local work and for a host with no public HTTPS. In
production the webhook is the right transport: this site is one container with
one process, and long-polling would need a second one.
"""

from __future__ import annotations

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.content.models import BotState
from apps.core import bot, messenger

POLL_SECONDS = 30
RETRY_SECONDS = 15


class Command(BaseCommand):
    help = "Set up and run the Bale/Telegram request bot."

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["status", "set-webhook", "delete-webhook", "poll", "test"],
            help="What to do. See the module docstring.",
        )

    def handle(self, *args, **options):
        if not settings.BOT_TOKEN:
            raise CommandError("DJANGO_BOT_TOKEN is empty - there is no bot to talk to.")

        try:
            getattr(self, options["action"].replace("-", "_"))()
        except messenger.BotError as error:
            raise CommandError(str(error)) from None

    # ── actions ────────────────────────────────────────────────────────────
    def status(self):
        me = messenger.get_me()
        self.stdout.write(self.style.SUCCESS(f"bot @{me.get('username', '?')} at {settings.BOT_API}"))
        self.stdout.write(f"chat id: {settings.BOT_CHAT_ID or '(empty - send /id to the bot to find it)'}")
        self.stdout.write(f"webhook secret: {'set' if settings.BOT_WEBHOOK_SECRET else '(empty - webhook disabled)'}")

        try:
            info = messenger.webhook_info()
            self.stdout.write(f"webhook now: {info.get('url') or '(none - updates must be polled)'}")
        except messenger.BotError as error:
            self.stdout.write(f"webhook now: unknown ({error})")

        state = BotState.load()
        self.stdout.write(f"last update handled: {state.last_update_id}")

    def set_webhook(self):
        if not settings.BOT_WEBHOOK_SECRET:
            raise CommandError("DJANGO_BOT_WEBHOOK_SECRET is empty - the endpoint does not exist without it.")
        url = self._webhook_url()
        messenger.set_webhook(url)
        self.stdout.write(self.style.SUCCESS(f"updates will be posted to {self._masked(url)}"))

    def delete_webhook(self):
        messenger.delete_webhook()
        self.stdout.write(self.style.SUCCESS("webhook removed - updates can be polled now."))

    def test(self):
        if not settings.BOT_CHAT_ID:
            raise CommandError("DJANGO_BOT_CHAT_ID is empty - send /id to the bot and put the answer there.")
        messenger.send(f"✅ ربات {self._site()} وصل است.\n\n/help برای راهنما")
        self.stdout.write(self.style.SUCCESS("sent."))

    def poll(self):
        """Long-poll getUpdates until interrupted. One process only: two would
        each handle half the presses."""
        self.stdout.write(f"polling {settings.BOT_API} - ctrl-c to stop")
        # Not deleted here: the webhook may be a live deployment on the same
        # token, and silently cutting it off is worse than saying so.
        try:
            hooked = messenger.webhook_info().get("url")
        except messenger.BotError:
            hooked = ""
        if hooked:
            self.stderr.write(
                "a webhook is registered, so getUpdates will be refused until "
                "`manage.py bale delete-webhook` is run."
            )
        while True:
            state = BotState.load()
            try:
                updates = messenger.get_updates(state.last_update_id + 1, POLL_SECONDS)
            except messenger.BotError as error:
                self.stderr.write(f"getUpdates failed, retrying: {error}")
                time.sleep(RETRY_SECONDS)
                continue

            for update in updates:
                try:
                    bot.handle_update(update)
                except Exception as error:  # noqa: BLE001 — one bad update stops nothing
                    self.stderr.write(f"update {update.get('update_id')} failed: {error}")

    # ── helpers ────────────────────────────────────────────────────────────
    def _webhook_url(self) -> str:
        return f"{settings.SITE_URL}/bot/{settings.BOT_WEBHOOK_SECRET}/"

    def _masked(self, url: str) -> str:
        """The secret is a secret; a terminal is a place secrets get pasted."""
        return url.replace(settings.BOT_WEBHOOK_SECRET, "***")

    def _site(self) -> str:
        return settings.SITE_URL.split("://")[-1].rstrip("/")
