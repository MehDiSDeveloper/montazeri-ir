"""
UI strings, in the three languages, as one Python dict.

Why not Django's gettext catalogues: those need .po files compiled by the
`msgfmt` binary, which turns "add a word to a button" into a build step that
has to run on Windows, in CI and inside the image. This site's UI vocabulary is
about a hundred short strings that only ever change when a feature changes, so
a dict costs one import and no toolchain, and an agent can add a language by
adding a column here.

Everything a *visitor* reads that is not chrome — a project title, a post, a
bio — lives in the database instead (see apps/content/models.py). This file is
only the furniture: buttons, labels, section headings.

Read it from a template with {% t "nav.projects" %}.
"""

from __future__ import annotations

from django.conf import settings
from django.utils.translation import get_language

DEFAULT_LANG = settings.LANGUAGE_CODE

STRINGS: dict[str, dict[str, str]] = {
    # ── chrome ────────────────────────────────────────────────────────────
    "nav.home": {"fa": "خانه", "en": "Home", "de": "Start"},
    "nav.projects": {"fa": "پروژه‌ها", "en": "Work", "de": "Projekte"},
    "nav.writing": {"fa": "نوشته‌ها", "en": "Writing", "de": "Blog"},
    "nav.about": {"fa": "درباره", "en": "About", "de": "Über mich"},
    "nav.contact": {"fa": "تماس", "en": "Contact", "de": "Kontakt"},
    "nav.resume": {"fa": "رزومه", "en": "Resume", "de": "Lebenslauf"},
    "nav.card": {"fa": "کارت", "en": "Card", "de": "Karte"},
    "nav.menu": {"fa": "منو", "en": "Menu", "de": "Menü"},
    "nav.close": {"fa": "بستن", "en": "Close", "de": "Schließen"},
    "nav.skip": {"fa": "پرش به محتوا", "en": "Skip to content", "de": "Zum Inhalt springen"},
    "nav.language": {"fa": "زبان", "en": "Language", "de": "Sprache"},
    "nav.theme": {"fa": "تم", "en": "Theme", "de": "Design"},
    "theme.system": {"fa": "سیستم", "en": "System", "de": "System"},
    "theme.light": {"fa": "روشن", "en": "Light", "de": "Hell"},
    "theme.dark": {"fa": "تاریک", "en": "Dark", "de": "Dunkel"},

    # ── home ──────────────────────────────────────────────────────────────
    "home.available": {"fa": "آمادهٔ همکاری", "en": "Open to work", "de": "Offen für Projekte"},
    "home.view_work": {"fa": "دیدن پروژه‌ها", "en": "See my work", "de": "Projekte ansehen"},
    "home.contact_me": {"fa": "تماس با من", "en": "Get in touch", "de": "Kontakt aufnehmen"},
    "home.download_resume": {"fa": "دانلود رزومه", "en": "Download résumé", "de": "Lebenslauf laden"},
    "home.now": {"fa": "این روزها", "en": "Right now", "de": "Gerade jetzt"},
    "home.selected_work": {"fa": "کارهای منتخب", "en": "Selected work", "de": "Ausgewählte Projekte"},
    "home.all_projects": {"fa": "همهٔ پروژه‌ها", "en": "All projects", "de": "Alle Projekte"},
    "home.skills": {"fa": "چیزهایی که با آن‌ها کار می‌کنم", "en": "What I work with", "de": "Womit ich arbeite"},
    "home.experience": {"fa": "مسیر کاری", "en": "Career", "de": "Werdegang"},
    "home.full_resume": {"fa": "رزومهٔ کامل", "en": "Full résumé", "de": "Ganzer Lebenslauf"},
    "home.writing": {"fa": "نوشته‌ها", "en": "Writing", "de": "Aus dem Blog"},
    "home.all_writing": {"fa": "همهٔ نوشته‌ها", "en": "All posts", "de": "Alle Beiträge"},
    "home.cta_title": {"fa": "پروژه‌ای در ذهن دارید؟", "en": "Have something in mind?", "de": "Sie haben eine Idee?"},
    "home.cta_body": {
        "fa": "برای سپردن یک پروژه از صفر تا صد، همکاری حضوری یا هیبریدی، یا فقط یک گفت‌وگوی فنی، پیام بدهید. معمولاً همان روز جواب می‌دهم.",
        "en": "For a project taken end to end, an on-site or hybrid role, or just a technical conversation. I usually reply the same day.",
        "de": "Für ein Projekt von A bis Z, eine Rolle vor Ort oder hybrid oder einfach ein Fachgespräch. Ich antworte meist am selben Tag.",
    },

    # ── services ──────────────────────────────────────────────────────────
    "nav.services": {"fa": "خدمات", "en": "Services", "de": "Leistungen"},
    "services.start": {"fa": "ثبت درخواست پروژه", "en": "Start a project", "de": "Projekt anfragen"},
    "services.more": {"fa": "جزئیات همکاری", "en": "How it works", "de": "So läuft es ab"},
    "services.subject": {"fa": "درخواست انجام پروژه", "en": "Project enquiry", "de": "Projektanfrage"},
    "services.cta_title": {"fa": "پروژه‌تان را شروع کنیم؟", "en": "Shall we start your project?", "de": "Starten wir Ihr Projekt?"},
    "services.cta_body": {
        "fa": "چند خط درباره‌ی نیاز و زمان‌بندی‌تان بنویسید. معمولاً همان روز جواب می‌دهم.",
        "en": "Write a few lines about what you need and by when. I usually reply the same day.",
        "de": "Schreiben Sie ein paar Zeilen zu Vorhaben und Zeitrahmen. Ich antworte meist am selben Tag.",
    },

    # ── projects ──────────────────────────────────────────────────────────
    "projects.title": {"fa": "پروژه‌ها", "en": "Work", "de": "Projekte"},
    "projects.lede": {
        "fa": "چیزهایی که ساخته‌ام، با تصمیم‌های فنی‌ای که پشتشان بوده.",
        "en": "Things I have built, and the decisions behind them.",
        "de": "Was ich gebaut habe — und die Entscheidungen dahinter.",
    },
    "projects.filter_all": {"fa": "همه", "en": "All", "de": "Alle"},
    "projects.empty": {"fa": "چیزی با این فیلتر پیدا نشد.", "en": "Nothing matches this filter.", "de": "Nichts gefunden."},
    "projects.role": {"fa": "نقش", "en": "Role", "de": "Rolle"},
    "projects.year": {"fa": "سال", "en": "Year", "de": "Jahr"},
    "projects.stack": {"fa": "استک", "en": "Stack", "de": "Stack"},
    "projects.problem": {"fa": "مسئله", "en": "The problem", "de": "Das Problem"},
    "projects.outcome": {"fa": "نتیجه", "en": "Outcome", "de": "Ergebnis"},
    "projects.repo": {"fa": "مخزن کد", "en": "Source", "de": "Quellcode"},
    "projects.demo": {"fa": "نسخهٔ زنده", "en": "Live demo", "de": "Live-Demo"},
    "projects.next": {"fa": "پروژهٔ بعدی", "en": "Next project", "de": "Nächstes Projekt"},
    "projects.back": {"fa": "بازگشت به پروژه‌ها", "en": "Back to work", "de": "Zurück zu den Projekten"},

    # ── writing ───────────────────────────────────────────────────────────
    "blog.title": {"fa": "نوشته‌ها", "en": "Writing", "de": "Blog"},
    "blog.lede": {
        "fa": "یادداشت‌هایی دربارهٔ چیزهایی که یاد می‌گیرم، مسائلی که درگیرشان هستم و گاهی فقط یک فکر.",
        "en": "Notes on what I am learning, problems I am chewing on, and the occasional thought.",
        "de": "Notizen über das, was ich lerne, Probleme, an denen ich sitze — und gelegentlich ein Gedanke.",
    },
    "blog.read_time": {"fa": "دقیقه مطالعه", "en": "min read", "de": "Min. Lesezeit"},
    "blog.back": {"fa": "بازگشت به نوشته‌ها", "en": "Back to writing", "de": "Zurück zum Blog"},
    "blog.empty": {"fa": "هنوز چیزی منتشر نشده.", "en": "Nothing published yet.", "de": "Noch nichts veröffentlicht."},
    "blog.share": {"fa": "اشتراک‌گذاری", "en": "Share", "de": "Teilen"},
    "blog.related": {"fa": "نوشته‌های دیگر", "en": "More writing", "de": "Weitere Beiträge"},
    "blog.only_in": {
        "fa": "این نوشته فقط به این زبان منتشر شده:",
        "en": "This post is only available in:",
        "de": "Dieser Beitrag ist nur verfügbar in:",
    },
    "blog.original_on": {"fa": "نسخه‌ی اصلی این نوشته در", "en": "Originally posted on", "de": "Ursprünglich veröffentlicht auf"},
    "blog.original_open": {"fa": "دیدن پست اصلی", "en": "Open the original", "de": "Original öffnen"},
    "platform.linkedin": {"fa": "لینکدین", "en": "LinkedIn", "de": "LinkedIn"},
    "platform.x": {"fa": "ایکس", "en": "X", "de": "X"},
    "platform.github": {"fa": "گیت‌هاب", "en": "GitHub", "de": "GitHub"},
    "platform.telegram": {"fa": "تلگرام", "en": "Telegram", "de": "Telegram"},
    "platform.medium": {"fa": "مدیوم", "en": "Medium", "de": "Medium"},
    "platform.virgool": {"fa": "ویرگول", "en": "Virgool", "de": "Virgool"},
    "platform.devto": {"fa": "DEV", "en": "DEV", "de": "DEV"},
    "platform.web": {"fa": "سایت دیگری", "en": "another site", "de": "einer anderen Website"},

    # ── about ─────────────────────────────────────────────────────────────
    "about.title": {"fa": "درباره من", "en": "About", "de": "Über mich"},
    "about.work": {"fa": "سابقهٔ کاری", "en": "Experience", "de": "Berufserfahrung"},
    "about.education": {"fa": "تحصیلات", "en": "Education", "de": "Ausbildung"},
    "about.present": {"fa": "اکنون", "en": "Present", "de": "Heute"},

    # ── contact ───────────────────────────────────────────────────────────
    "contact.title": {"fa": "تماس", "en": "Contact", "de": "Kontakt"},
    "contact.lede": {
        "fa": "هر کدام از راه‌های زیر جواب می‌دهد. برای پیام بلندتر، فرم پایین سریع‌ترین راه است.",
        "en": "Any of these reaches me. For anything longer, the form below is quickest.",
        "de": "Jeder dieser Wege erreicht mich. Für Längeres ist das Formular am schnellsten.",
    },
    "contact.direct": {"fa": "راه‌های مستقیم", "en": "Direct channels", "de": "Direkte Wege"},
    "contact.form": {"fa": "پیام بفرستید", "en": "Send a message", "de": "Nachricht senden"},
    "contact.name": {"fa": "نام", "en": "Name", "de": "Name"},
    "contact.email": {"fa": "ایمیل", "en": "Email", "de": "E-Mail"},
    "contact.phone": {"fa": "شمارهٔ تماس", "en": "Phone", "de": "Telefon"},
    "contact.optional": {"fa": "اختیاری", "en": "optional", "de": "optional"},
    "contact.phone_hint": {
        "fa": "اگر بگذارید، برای پروژه زنگ می‌زنم — سریع‌تر از ایمیل.",
        "en": "Leave one and I can call about a project — faster than email.",
        "de": "Mit Nummer rufe ich zu einem Projekt an — schneller als E-Mail.",
    },
    "contact.phone_bad": {
        "fa": "شمارهٔ تماس معتبر نیست.",
        "en": "That phone number does not look right.",
        "de": "Diese Telefonnummer sieht nicht richtig aus.",
    },
    "contact.subject": {"fa": "موضوع", "en": "Subject", "de": "Betreff"},
    "contact.message": {"fa": "پیام", "en": "Message", "de": "Nachricht"},
    "contact.send": {"fa": "ارسال پیام", "en": "Send message", "de": "Absenden"},
    "contact.sent": {
        "fa": "پیام شما رسید. به‌زودی جواب می‌دهم.",
        "en": "Your message arrived. I will get back to you shortly.",
        "de": "Ihre Nachricht ist angekommen. Ich melde mich in Kürze.",
    },
    "contact.too_fast": {
        "fa": "یک پیام همین الان فرستادید. کمی صبر کنید.",
        "en": "You just sent one. Give it a minute.",
        "de": "Sie haben gerade eine gesendet. Einen Moment bitte.",
    },
    "contact.copy": {"fa": "کپی", "en": "Copy", "de": "Kopieren"},
    "contact.copied": {"fa": "کپی شد", "en": "Copied", "de": "Kopiert"},
    "contact.company": {"fa": "شرکت یا سازمان", "en": "Company", "de": "Firma"},
    "contact.kind": {"fa": "نوع درخواست", "en": "What is it about?", "de": "Worum geht es?"},
    "contact.timeline": {"fa": "مهلت مدنظر", "en": "When do you need it?", "de": "Bis wann?"},
    "kind.project": {"fa": "پروژه", "en": "A project", "de": "Ein Projekt"},
    "kind.job": {"fa": "پیشنهاد شغلی", "en": "A job offer", "de": "Ein Jobangebot"},
    "kind.consult": {"fa": "مشاوره", "en": "Consulting", "de": "Beratung"},
    "kind.other": {"fa": "سایر", "en": "Something else", "de": "Etwas anderes"},
    "timeline.week": {"fa": "تا یک هفته", "en": "Within a week", "de": "In einer Woche"},
    "timeline.month": {"fa": "تا یک ماه", "en": "Within a month", "de": "In einem Monat"},
    "timeline.quarter": {"fa": "تا سه ماه", "en": "Within 3 months", "de": "In 3 Monaten"},
    "timeline.flexible": {"fa": "انعطاف‌پذیر", "en": "Flexible", "de": "Flexibel"},
    "contact.code_is": {"fa": "کد پیگیری شما", "en": "Your tracking code", "de": "Ihr Vorgangscode"},
    "contact.code_keep": {
        "fa": "این کد را نگه دارید. پاسخ من در صفحهٔ پیگیری می‌آید و همان‌جا می‌توانید جواب بدهید.",
        "en": "Keep this code. My answer appears on the tracking page, and you can write back there.",
        "de": "Bewahren Sie den Code auf. Meine Antwort erscheint auf der Vorgangsseite, dort können Sie auch antworten.",
    },
    "contact.have_code": {
        "fa": "قبلاً پیام داده‌اید؟ درخواستتان را پیگیری کنید",
        "en": "Already wrote? Follow your request",
        "de": "Schon geschrieben? Anfrage verfolgen",
    },

    # ── following a request ───────────────────────────────────────────────
    "track.title": {"fa": "پیگیری درخواست", "en": "Follow your request", "de": "Anfrage verfolgen"},
    "track.lede": {
        "fa": "کد پیگیری‌ای را که بعد از ارسال پیام گرفتید وارد کنید تا وضعیت و پاسخ‌ها را ببینید.",
        "en": "Enter the tracking code you got after sending your message to see where it stands and read the replies.",
        "de": "Geben Sie den Code ein, den Sie nach dem Absenden erhalten haben, um Stand und Antworten zu sehen.",
    },
    "track.code": {"fa": "کد پیگیری", "en": "Tracking code", "de": "Vorgangscode"},
    "track.open": {"fa": "نمایش درخواست", "en": "Show my request", "de": "Anfrage anzeigen"},
    "track.bad_code": {
        "fa": "کد پیگیری هشت حرف و رقم است، مثل 7KQ4-M2XD.",
        "en": "A tracking code is eight letters and digits, like 7KQ4-M2XD.",
        "de": "Ein Vorgangscode hat acht Zeichen, etwa 7KQ4-M2XD.",
    },
    "track.not_found": {
        "fa": "درخواستی با این کد پیدا نشد. کد را دوباره بررسی کنید.",
        "en": "No request has that code. Please check it and try again.",
        "de": "Kein Vorgang mit diesem Code. Bitte prüfen Sie ihn.",
    },
    "track.locked": {
        "fa": "چند بار کد نادرست وارد شد. لطفاً ربع ساعت دیگر دوباره امتحان کنید.",
        "en": "Too many wrong codes. Please try again in fifteen minutes.",
        "de": "Zu viele falsche Codes. Bitte in fünfzehn Minuten erneut versuchen.",
    },
    "track.no_code": {
        "fa": "کد را گم کرده‌اید؟ از صفحهٔ تماس دوباره پیام بدهید.",
        "en": "Lost the code? Just write again from the contact page.",
        "de": "Code verloren? Schreiben Sie einfach erneut über die Kontaktseite.",
    },
    "track.request": {"fa": "درخواست", "en": "Request", "de": "Anfrage"},
    "track.status": {"fa": "وضعیت", "en": "Status", "de": "Status"},
    "track.sent_on": {"fa": "ارسال", "en": "Sent", "de": "Gesendet"},
    "track.bookmark": {
        "fa": "این صفحه را نشانک کنید؛ نشانی‌اش همان کد پیگیری است.",
        "en": "Bookmark this page — its address is your tracking code.",
        "de": "Setzen Sie ein Lesezeichen — die Adresse ist Ihr Vorgangscode.",
    },
    "track.you": {"fa": "شما", "en": "You", "de": "Sie"},
    "track.conversation": {"fa": "گفت‌وگو", "en": "Conversation", "de": "Verlauf"},
    "track.waiting": {
        "fa": "هنوز پاسخی ثبت نشده. به‌محض پاسخ، همین‌جا نمایش داده می‌شود.",
        "en": "No reply yet. When there is one, it appears right here.",
        "de": "Noch keine Antwort. Sobald es eine gibt, erscheint sie hier.",
    },
    "track.reply": {"fa": "پاسخ شما", "en": "Your reply", "de": "Ihre Antwort"},
    "track.reply_hint": {
        "fa": "جواب، توضیح بیشتر یا هر تغییری در درخواست را همین‌جا بنویسید.",
        "en": "An answer, more detail or a change to your request — write it here.",
        "de": "Antwort, Ergänzung oder Änderung Ihrer Anfrage — schreiben Sie sie hier.",
    },
    "track.reply_send": {"fa": "ارسال پاسخ", "en": "Send reply", "de": "Antwort senden"},
    "track.reply_sent": {
        "fa": "پاسخ شما ثبت شد و به من اطلاع داده شد.",
        "en": "Your reply is in, and I have been notified.",
        "de": "Ihre Antwort ist angekommen, ich wurde benachrichtigt.",
    },
    "track.reply_empty": {
        "fa": "متن پاسخ خالی است.",
        "en": "The reply is empty.",
        "de": "Die Antwort ist leer.",
    },
    # ── the request in the visitor's own Bale ─────────────────────────────
    "bale.title": {"fa": "پاسخ‌ها در بله", "en": "Replies in Bale", "de": "Antworten in Bale"},
    "bale.connect": {"fa": "دریافت پاسخ‌ها در بله", "en": "Get replies in Bale", "de": "Antworten in Bale erhalten"},
    "bale.connect_hint": {
        "fa": "ربات بله شمارهٔ شما را می‌پرسد تا مطمئن شود خودتان هستید؛ باید همان شماره‌ای باشد که در فرم نوشتید. بعد از آن پاسخ‌ها و تغییر وضعیت همین‌جا و در بله می‌رسد و از همان‌جا هم می‌توانید جواب بدهید.",
        "en": "The Bale bot asks for your phone number to make sure it is you — it has to be the number you gave in the form. After that, replies and status changes reach you in Bale too, and you can answer from there.",
        "de": "Der Bale-Bot fragt nach Ihrer Telefonnummer, um sicherzugehen, dass Sie es sind – es muss die Nummer aus dem Formular sein. Danach erreichen Sie Antworten und Statusänderungen auch in Bale, und Sie können dort antworten.",
    },
    "bale.no_phone": {
        "fa": "برای دریافت پاسخ‌ها در بله، درخواست باید شمارهٔ تماس داشته باشد و این یکی ندارد.",
        "en": "Replies in Bale need a phone number on the request, and this one has none.",
        "de": "Für Antworten in Bale braucht die Anfrage eine Telefonnummer, und diese hat keine.",
    },
    "bale.connected": {
        "fa": "این درخواست به بلهٔ شما وصل است؛ پاسخ‌ها و تغییر وضعیت آنجا هم می‌رسد.",
        "en": "This request is connected to your Bale: replies and status changes arrive there too.",
        "de": "Diese Anfrage ist mit Ihrem Bale verbunden: Antworten und Statusänderungen kommen auch dort an.",
    },
    "bale.disconnect": {"fa": "قطع اتصال از بله", "en": "Disconnect Bale", "de": "Bale trennen"},
    "bale.disconnected": {
        "fa": "اتصال بله قطع شد. پاسخ‌ها فقط در همین صفحه دیده می‌شوند.",
        "en": "Bale is disconnected. Replies now appear on this page only.",
        "de": "Bale ist getrennt. Antworten erscheinen jetzt nur noch auf dieser Seite.",
    },
    # What the bot says. «{code}» is the tracking code.
    "bale.ask_contact": {
        "fa": "برای وصل کردن درخواست {code}، با دکمهٔ زیر شمارهٔ خودتان را بفرستید. باید همان شماره‌ای باشد که در فرم نوشتید.",
        "en": "To connect request {code}, share your number with the button below. It has to be the number you gave in the form.",
        "de": "Um Anfrage {code} zu verbinden, teilen Sie Ihre Nummer über die Schaltfläche unten. Es muss die Nummer aus dem Formular sein.",
    },
    "bale.share_phone": {"fa": "📱 ارسال شمارهٔ من", "en": "📱 Share my number", "de": "📱 Meine Nummer teilen"},
    "bale.bad_link": {
        "fa": "این لینک منقضی شده یا قبلاً استفاده شده. صفحهٔ پیگیری را باز کنید و دوباره «دریافت پاسخ‌ها در بله» را بزنید.",
        "en": "This link has expired or was already used. Open your tracking page and press «Get replies in Bale» again.",
        "de": "Dieser Link ist abgelaufen oder wurde schon benutzt. Öffnen Sie Ihre Seite zur Anfrage und tippen Sie erneut auf «Antworten in Bale erhalten».",
    },
    "bale.own_contact": {
        "fa": "لطفاً شمارهٔ خودتان را با همان دکمهٔ زیر بفرستید، نه مخاطب دیگری را.",
        "en": "Please share your own number with the button below, not another contact.",
        "de": "Bitte teilen Sie Ihre eigene Nummer über die Schaltfläche unten, keinen anderen Kontakt.",
    },
    "bale.mismatch": {
        "fa": "این شماره با شمارهٔ ثبت‌شده در درخواست یکی نیست، پس اتصال انجام نشد. اگر شماره را اشتباه نوشته بودید، در صفحهٔ پیگیری پیام بگذارید.",
        "en": "This number is not the one on the request, so nothing was connected. If the number in the form was wrong, say so on your tracking page.",
        "de": "Diese Nummer ist nicht die der Anfrage, daher wurde nichts verbunden. Falls die Nummer im Formular falsch war, schreiben Sie es auf Ihrer Anfrageseite.",
    },
    "bale.linked": {
        "fa": "✅ وصل شد. از این به بعد پاسخ‌ها و تغییر وضعیت درخواست {code} همین‌جا می‌رسد.",
        "en": "✅ Connected. Replies and status changes for request {code} will arrive here.",
        "de": "✅ Verbunden. Antworten und Statusänderungen zu Anfrage {code} kommen ab jetzt hier an.",
    },
    "bale.update": {"fa": "خبر تازه از درخواست", "en": "News on your request", "de": "Neues zu Ihrer Anfrage"},
    "bale.open": {"fa": "🔗 صفحهٔ درخواست", "en": "🔗 Open the request", "de": "🔗 Anfrage öffnen"},
    "bale.reply": {"fa": "💬 پاسخ", "en": "💬 Reply", "de": "💬 Antworten"},
    "bale.cancel": {"fa": "✖️ لغو درخواست", "en": "✖️ Cancel request", "de": "✖️ Anfrage zurückziehen"},
    "bale.reply_prompt": {
        "fa": "متن پاسخ به درخواست {code} را بنویسید و بفرستید.",
        "en": "Write your reply to request {code} and send it.",
        "de": "Schreiben Sie Ihre Antwort zu Anfrage {code} und senden Sie sie ab.",
    },
    "bale.reply_saved": {
        "fa": "✅ پاسخ شما ثبت شد و به دستم رسید.",
        "en": "✅ Your reply is saved and on its way to me.",
        "de": "✅ Ihre Antwort ist gespeichert und bei mir angekommen.",
    },
    "bale.reply_hint": {
        "fa": "برای پاسخ، اول دکمهٔ «پاسخ» را زیر یکی از پیام‌های درخواست بزنید و بعد متن را بفرستید.",
        "en": "To reply, first press «Reply» under one of the request's messages, then send your text.",
        "de": "Tippen Sie zum Antworten zuerst auf «Antworten» unter einer Nachricht zur Anfrage und senden Sie dann Ihren Text.",
    },
    "bale.cancel_confirm": {
        "fa": "درخواست {code} لغو شود؟ درخواست بسته می‌شود؛ اگر بعداً دوباره بنویسید، باز می‌شود.",
        "en": "Cancel request {code}? It will be closed; writing again later reopens it.",
        "de": "Anfrage {code} zurückziehen? Sie wird geschlossen; eine neue Nachricht öffnet sie wieder.",
    },
    "bale.cancel_yes": {"fa": "بله، لغو شود", "en": "Yes, cancel it", "de": "Ja, zurückziehen"},
    "bale.cancel_no": {"fa": "نه، بماند", "en": "No, keep it", "de": "Nein, behalten"},
    "bale.cancelled": {
        "fa": "درخواست {code} لغو شد. اگر دوباره نوشتید، باز می‌شود.",
        "en": "Request {code} is cancelled. Writing again reopens it.",
        "de": "Anfrage {code} ist zurückgezogen. Eine neue Nachricht öffnet sie wieder.",
    },
    "bale.kept": {"fa": "باشد، درخواست سر جایش ماند.", "en": "OK, the request stays open.", "de": "Gut, die Anfrage bleibt offen."},
    "bale.closed": {
        "fa": "این درخواست دیگر باز نیست.",
        "en": "This request is no longer open.",
        "de": "Diese Anfrage ist nicht mehr offen.",
    },
    "bale.too_fast": {
        "fa": "کمی صبر کنید؛ هر دقیقه یک پیام.",
        "en": "Please wait a moment — one message a minute.",
        "de": "Bitte warten Sie kurz – eine Nachricht pro Minute.",
    },
    "bale.not_yours": {
        "fa": "این درخواست به این گفت‌وگو وصل نیست.",
        "en": "This request is not connected to this chat.",
        "de": "Diese Anfrage ist nicht mit diesem Chat verbunden.",
    },
    "track.cancelled_event": {
        "fa": "درخواست را لغو کردید.",
        "en": "You cancelled the request.",
        "de": "Sie haben die Anfrage zurückgezogen.",
    },
    "bale.stopped": {
        "fa": "اتصال قطع شد؛ دیگر پیامی دربارهٔ {codes} اینجا نمی‌آید.",
        "en": "Disconnected: nothing more about {codes} will be sent here.",
        "de": "Getrennt: Zu {codes} kommt hier nichts mehr an.",
    },
    "bale.welcome": {
        "fa": "سلام! برای دریافت پاسخ یک درخواست در بله، صفحهٔ پیگیری آن را در سایت باز کنید و «دریافت پاسخ‌ها در بله» را بزنید.",
        "en": "Hello! To get replies to a request here, open its tracking page on the site and press «Get replies in Bale».",
        "de": "Hallo! Um Antworten zu einer Anfrage hier zu erhalten, öffnen Sie ihre Seite auf der Website und tippen Sie auf «Antworten in Bale erhalten».",
    },
    "status.new": {"fa": "دریافت شد", "en": "Received", "de": "Eingegangen"},
    "status.read": {"fa": "در حال بررسی", "en": "In review", "de": "In Prüfung"},
    "status.answered": {"fa": "پاسخ داده شد", "en": "Answered", "de": "Beantwortet"},
    "status.rejected": {"fa": "پذیرفته نشد", "en": "Declined", "de": "Abgelehnt"},
    "status.archived": {"fa": "بسته شد", "en": "Closed", "de": "Abgeschlossen"},

    # ── card ──────────────────────────────────────────────────────────────
    "card.title": {"fa": "کارت ویزیت", "en": "Business card", "de": "Visitenkarte"},
    "card.add_contact": {"fa": "افزودن به مخاطبین", "en": "Add to contacts", "de": "Zu Kontakten"},
    "card.scan": {"fa": "این کد را اسکن کنید", "en": "Scan this code", "de": "Diesen Code scannen"},
    "card.share": {"fa": "اشتراک‌گذاری لینک", "en": "Share link", "de": "Link teilen"},
    "card.open_site": {"fa": "دیدن سایت کامل", "en": "Open full site", "de": "Ganze Website"},

    # ── resume ────────────────────────────────────────────────────────────
    "resume.title": {"fa": "رزومه", "en": "Resume", "de": "Lebenslauf"},
    "resume.print": {"fa": "چاپ / PDF", "en": "Print / PDF", "de": "Drucken / PDF"},
    "resume.languages": {"fa": "زبان‌ها", "en": "Languages", "de": "Sprachen"},

    # ── errors and footer ─────────────────────────────────────────────────
    "err.404_title": {"fa": "این صفحه پیدا نشد", "en": "Page not found", "de": "Seite nicht gefunden"},
    "err.404_body": {
        "fa": "شاید نشانی عوض شده باشد. از خانه دوباره شروع کنید.",
        "en": "The address may have changed. Start again from the home page.",
        "de": "Die Adresse hat sich vielleicht geändert. Beginnen Sie auf der Startseite.",
    },
    "err.500_title": {"fa": "چیزی از سمت ما خراب شد", "en": "Something broke on our side", "de": "Auf unserer Seite ging etwas schief"},
    "err.500_body": {
        "fa": "خطا ثبت شد. کمی بعد دوباره تلاش کنید.",
        "en": "The error was logged. Please try again shortly.",
        "de": "Der Fehler wurde protokolliert. Bitte später erneut versuchen.",
    },
    "err.home": {"fa": "بازگشت به خانه", "en": "Back home", "de": "Zur Startseite"},
    "footer.rights": {"fa": "همهٔ حقوق محفوظ است.", "en": "All rights reserved.", "de": "Alle Rechte vorbehalten."},
    "footer.built": {"fa": "ساخته‌شده با جنگو", "en": "Built with Django", "de": "Gebaut mit Django"},

    # ── command palette ───────────────────────────────────────────────────
    "cmd.open": {"fa": "جست‌وجو", "en": "Search", "de": "Suche"},
    "cmd.placeholder": {"fa": "صفحه یا پروژه…", "en": "Page or project…", "de": "Seite oder Projekt…"},
    "cmd.empty": {"fa": "نتیجه‌ای نبود", "en": "No results", "de": "Keine Treffer"},
    "cmd.pages": {"fa": "صفحه‌ها", "en": "Pages", "de": "Seiten"},
    "cmd.actions": {"fa": "میان‌برها", "en": "Shortcuts", "de": "Aktionen"},
    "cmd.move": {"fa": "جابه‌جایی", "en": "move", "de": "wählen"},
    "cmd.go": {"fa": "باز کردن", "en": "open", "de": "öffnen"},

    # ── furniture added with the 2026 redesign ────────────────────────────
    # Labels and tooltips only. Nothing here says anything about Mahdi; every
    # value these labels sit next to still comes from the database.
    "nav.breadcrumb": {"fa": "مسیر صفحه", "en": "Breadcrumb", "de": "Brotkrümelpfad"},
    "tip.open": {"fa": "باز کردن", "en": "Open", "de": "Öffnen"},
    "tip.new_tab": {"fa": "در زبانهٔ جدید باز می‌شود", "en": "Opens in a new tab", "de": "Öffnet in neuem Tab"},
    "tip.filter": {"fa": "پروژه‌های همین برچسب", "en": "Projects with this tag", "de": "Projekte mit diesem Tag"},
    "home.at_a_glance": {"fa": "در یک نگاه", "en": "At a glance", "de": "Auf einen Blick"},
    "facts.location": {"fa": "موقعیت", "en": "Location", "de": "Standort"},
    "facts.availability": {"fa": "وضعیت همکاری", "en": "Availability", "de": "Verfügbarkeit"},
    "facts.latest_role": {"fa": "آخرین نقش", "en": "Latest role", "de": "Letzte Position"},
    "facts.core_stack": {"fa": "استک اصلی", "en": "Core stack", "de": "Kern-Stack"},
    "skills.primary": {"fa": "مهارت اصلی", "en": "Core skill", "de": "Kernkompetenz"},
    "projects.read_case": {"fa": "جزئیات پروژه", "en": "Read the case study", "de": "Zur Fallstudie"},
    "exp.duration": {"fa": "مدت", "en": "Duration", "de": "Dauer"},
    "dur.year": {"fa": "سال", "en": "yr", "de": "J."},
    "dur.years": {"fa": "سال", "en": "yrs", "de": "J."},
    "dur.month": {"fa": "ماه", "en": "mo", "de": "Mon."},
    "dur.months": {"fa": "ماه", "en": "mos", "de": "Mon."},
    "dur.and": {"fa": " و ", "en": " ", "de": " "},
    "resume.profile": {"fa": "خلاصه", "en": "Profile", "de": "Profil"},
    "resume.skills": {"fa": "مهارت‌ها", "en": "Skills", "de": "Kenntnisse"},
    "channel.email": {"fa": "ایمیل", "en": "Email", "de": "E-Mail"},
    "channel.telegram": {"fa": "تلگرام", "en": "Telegram", "de": "Telegram"},
    "channel.github": {"fa": "گیت‌هاب", "en": "GitHub", "de": "GitHub"},
    "channel.linkedin": {"fa": "لینکدین", "en": "LinkedIn", "de": "LinkedIn"},
    "channel.phone": {"fa": "تلفن", "en": "Phone", "de": "Telefon"},
    "card.vcf": {"fa": "فایل vCard", "en": "vCard file", "de": "vCard-Datei"},
    "footer.explore": {"fa": "گشت‌وگذار", "en": "Explore", "de": "Entdecken"},
    "footer.career": {"fa": "کارنامه", "en": "Career", "de": "Karriere"},
    "footer.connect": {"fa": "ارتباط", "en": "Connect", "de": "Vernetzen"},
    "footer.sitemap": {"fa": "نقشهٔ سایت", "en": "Sitemap", "de": "Sitemap"},
    "footer.top": {"fa": "بازگشت به بالا", "en": "Back to top", "de": "Nach oben"},
}


def t(key: str, lang: str | None = None) -> str:
    """Look one string up. An unknown key returns the key, loudly and visibly."""
    code = (lang or get_language() or DEFAULT_LANG).split("-")[0]
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(code) or entry.get(DEFAULT_LANG) or key
