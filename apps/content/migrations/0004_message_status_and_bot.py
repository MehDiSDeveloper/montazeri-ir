"""A message stops being a flag and becomes a request with a life cycle.

`is_handled` is carried over first: a handled message was one that had been
dealt with, which is «خوانده‌شده» and not «جدید». The column is only dropped
after that, so the data survives the rename in either direction.
"""

import django.db.models.deletion
from django.db import migrations, models


def handled_becomes_read(apps, schema_editor):
    Message = apps.get_model("content", "Message")
    Message.objects.filter(is_handled=True).update(status="read")


def read_becomes_handled(apps, schema_editor):
    Message = apps.get_model("content", "Message")
    Message.objects.exclude(status="new").update(is_handled=True)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_services_seo_post_images'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_update_id', models.BigIntegerField(default=0)),
                ('awaiting_since', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'bot state',
            },
        ),
        migrations.AddField(
            model_name='message',
            name='bot_chat_id',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='message',
            name='bot_message_id',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='message',
            name='notes',
            field=models.TextField(blank=True, help_text="Private. Written here or from the bot's «یادداشت» button; never shown on the site."),
        ),
        migrations.AddField(
            model_name='message',
            name='notified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='phone',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='message',
            name='read_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='status',
            field=models.CharField(choices=[('new', 'جدید — new'), ('read', 'خوانده‌شده — read'), ('rejected', 'رد شده — rejected'), ('archived', 'بایگانی — archived')], default='new', max_length=16),
        ),
        migrations.RunPython(handled_becomes_read, read_becomes_handled),
        migrations.RemoveField(
            model_name='message',
            name='is_handled',
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['status', '-created_at'], name='content_mes_status_b962a2_idx'),
        ),
        migrations.AddField(
            model_name='botstate',
            name='awaiting_note_for',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='content.message'),
        ),
    ]
