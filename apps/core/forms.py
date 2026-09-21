from __future__ import annotations

import re

from django import forms

from apps.content.models import Message, normalise_tracking_code

from .i18n import t

# Persian and Arabic-Indic digits, in order, so a number typed on a Persian
# keyboard is stored as one a phone can actually dial.
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_PHONE_SHAPE = re.compile(r"^\+?[0-9][0-9 ()-]{6,}$")


class ContactForm(forms.ModelForm):
    """The contact form, plus a honeypot.

    No captcha: a hidden field a human never sees and a bot fills in stops the
    volume a personal site attracts, and costs the reader nothing.
    """

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Message
        # The phone number is optional on purpose: most Iranian clients expect
        # to be called back, and requiring it would cost the replies of the
        # ones who do not want to be.
        fields = ("name", "company", "email", "phone", "kind", "timeline", "subject", "body")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 120}),
            "company": forms.TextInput(attrs={"autocomplete": "organization", "maxlength": 120}),
            "kind": forms.RadioSelect,
            "timeline": forms.RadioSelect,
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "maxlength": 32}),
            "subject": forms.TextInput(attrs={"maxlength": 160}),
            "body": forms.Textarea(attrs={"rows": 6, "maxlength": 4000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Type and timeline help the owner sort, but a visitor who skips them
        # still gets heard: nothing picked is the model's default, not an error.
        for name in ("kind", "timeline"):
            self.fields[name].required = False
            self.fields[name].choices = [c for c in self.fields[name].choices if c[0]]

    def clean_phone(self) -> str:
        phone = (self.cleaned_data.get("phone") or "").strip().translate(_DIGITS)
        if phone and not _PHONE_SHAPE.match(phone):
            raise forms.ValidationError(t("contact.phone_bad"), code="invalid")
        return phone

    def is_spam(self) -> bool:
        return bool(self.data.get("website"))


class ReplyForm(forms.Form):
    """The visitor writing back under their own request. Same honeypot as the
    contact form — the tracking page is public, and so is this box."""

    body = forms.CharField(max_length=4000, widget=forms.Textarea(attrs={"rows": 4, "maxlength": 4000}))
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_body(self) -> str:
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError(t("track.reply_empty"), code="required")
        return body

    def is_spam(self) -> bool:
        return bool(self.data.get("website"))


class TrackForm(forms.Form):
    """A tracking code, however it was typed: lower case, without the dash,
    with Persian digits from a Persian keyboard."""

    code = forms.CharField(max_length=32)

    def clean_code(self) -> str:
        code = normalise_tracking_code(self.cleaned_data["code"].translate(_DIGITS))
        if not code:
            raise forms.ValidationError(t("track.bad_code"), code="invalid")
        return code
