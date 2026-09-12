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
    "nav.resume": {"fa": "رزومه", "en": "Résumé", "de": "Lebenslauf"},
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
        "fa": "برای همکاری، مشاوره یا فقط یک گفت‌وگوی فنی، پیام بدهید. معمولاً همان روز جواب می‌دهم.",
        "en": "For work, advice, or just a technical conversation. I usually reply the same day.",
        "de": "Für Projekte, Beratung oder einfach ein Fachgespräch. Ich antworte meist am selben Tag.",
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

    # ── card ──────────────────────────────────────────────────────────────
    "card.title": {"fa": "کارت ویزیت", "en": "Business card", "de": "Visitenkarte"},
    "card.add_contact": {"fa": "افزودن به مخاطبین", "en": "Add to contacts", "de": "Zu Kontakten"},
    "card.scan": {"fa": "این کد را اسکن کنید", "en": "Scan this code", "de": "Diesen Code scannen"},
    "card.share": {"fa": "اشتراک‌گذاری لینک", "en": "Share link", "de": "Link teilen"},
    "card.open_site": {"fa": "دیدن سایت کامل", "en": "Open full site", "de": "Ganze Website"},

    # ── resume ────────────────────────────────────────────────────────────
    "resume.title": {"fa": "رزومه", "en": "Résumé", "de": "Lebenslauf"},
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
}


def t(key: str, lang: str | None = None) -> str:
    """Look one string up. An unknown key returns the key, loudly and visibly."""
    code = (lang or get_language() or DEFAULT_LANG).split("-")[0]
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(code) or entry.get(DEFAULT_LANG) or key
