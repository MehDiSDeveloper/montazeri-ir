from __future__ import annotations

from django import forms

from apps.content.models import Message


class ContactForm(forms.ModelForm):
    """The contact form, plus a honeypot.

    No captcha: a hidden field a human never sees and a bot fills in stops the
    volume a personal site attracts, and costs the reader nothing.
    """

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Message
        fields = ("name", "email", "subject", "body")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 120}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "subject": forms.TextInput(attrs={"maxlength": 160}),
            "body": forms.Textarea(attrs={"rows": 6, "maxlength": 4000}),
        }

    def is_spam(self) -> bool:
        return bool(self.data.get("website"))
