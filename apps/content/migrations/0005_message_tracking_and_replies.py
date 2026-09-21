"""A request becomes a conversation the visitor can follow.

The tracking code is unique, so it cannot arrive as a column with a default:
every existing row would get the same one. It is added empty, each row is
given its own code, and only then is it made unique.
"""

import secrets

import django.db.models.deletion
from django.db import migrations, models

import apps.content.models

ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def give_every_request_a_code(apps, schema_editor):
    Message = apps.get_model("content", "Message")
    used = set()
    for message in Message.objects.all().only("pk"):
        code = ""
        while not code or code in used:
            raw = "".join(secrets.choice(ALPHABET) for _ in range(8))
            code = f"{raw[:4]}-{raw[4:]}"
        used.add(code)
        Message.objects.filter(pk=message.pk).update(tracking_code=code)


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0004_message_status_and_bot"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="company",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="message",
            name="kind",
            field=models.CharField(
                choices=[
                    ("project", "پروژه — project"),
                    ("job", "پیشنهاد شغلی — job offer"),
                    ("consult", "مشاوره — consulting"),
                    ("other", "سایر — other"),
                ],
                default="other",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="timeline",
            field=models.CharField(
                choices=[
                    ("week", "تا یک هفته — within a week"),
                    ("month", "تا یک ماه — within a month"),
                    ("quarter", "تا سه ماه — within three months"),
                    ("flexible", "انعطاف‌پذیر — flexible"),
                ],
                default="flexible",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="due_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="message",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "جدید — new"),
                    ("read", "خوانده‌شده — read"),
                    ("answered", "پاسخ داده شده — answered"),
                    ("rejected", "رد شده — rejected"),
                    ("archived", "بایگانی — archived"),
                ],
                default="new",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="tracking_code",
            field=models.CharField(editable=False, max_length=9, null=True),
        ),
        migrations.RunPython(give_every_request_a_code, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="message",
            name="tracking_code",
            field=models.CharField(
                default=apps.content.models.new_tracking_code, editable=False, max_length=9, unique=True
            ),
        ),
        migrations.AddField(
            model_name="botstate",
            name="awaiting_reply",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="Reply",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_owner", models.BooleanField(default=False)),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="replies", to="content.message"
                    ),
                ),
            ],
            options={"ordering": ("created_at", "pk"), "verbose_name_plural": "replies"},
        ),
    ]
