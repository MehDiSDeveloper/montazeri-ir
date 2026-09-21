from __future__ import annotations

import re

from django import forms

from apps.content.models import Message

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
        fields = ("name", "email", "phone", "subject", "body")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 120}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "maxlength": 32}),
            "subject": forms.TextInput(attrs={"maxlength": 160}),
            "body": forms.Textarea(attrs={"rows": 6, "maxlength": 4000}),
        }

    def clean_phone(self) -> str:
        phone = (self.cleaned_data.get("phone") or "").strip().translate(_DIGITS)
        if phone and not _PHONE_SHAPE.match(phone):
            raise forms.ValidationError(t("contact.phone_bad"), code="invalid")
        return phone

    def is_spam(self) -> bool:
        return bool(self.data.get("website"))

