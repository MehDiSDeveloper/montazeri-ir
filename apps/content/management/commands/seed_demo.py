"""
Seed the site with placeholder content in all three languages.

Idempotent: it upserts by slug, so running it twice changes nothing. It exists
so a fresh clone renders a complete site instead of an empty shell — every
string it writes is a placeholder Mahdi replaces in the admin.

    python manage.py seed_demo
    python manage.py seed_demo --wipe   # start over
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.content.models import (
    Experience,
    Post,
    Profile,
    Project,
    Skill,
    SkillGroup,
    Tag,
)


class Command(BaseCommand):
    help = "Fill the database with three-language placeholder content."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true", help="Delete existing content first.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["wipe"]:
            for model in (Project, Post, Experience, Skill, SkillGroup, Tag):
                model.objects.all().delete()
            self.stdout.write(self.style.WARNING("wiped existing content"))

        self._profile()
        tags = self._tags()
        self._skills()
        self._projects(tags)
        self._experience()
        self._posts(tags)
        self.stdout.write(self.style.SUCCESS("seeded — every string here is a placeholder"))

    # ── profile ───────────────────────────────────────────────────────────
    def _profile(self):
        p = Profile.load()
        p.full_name_fa = "مهدی منتظری"
        p.full_name_en = "Mahdi Montazeri"
        p.full_name_de = "Mahdi Montazeri"

        p.headline_fa = "مهندس نرم‌افزار — پایتون، جنگو، زیرساخت"
        p.headline_en = "Software engineer — Python, Django, infrastructure"
        p.headline_de = "Softwareentwickler — Python, Django, Infrastruktur"

        p.intro_fa = (
            "سامانه‌های وب می‌سازم که زیر بار واقعی سرپا بمانند — از مدل داده و "
            "قواعد دسترسی تا استقرار داکری و چیزی که کاربر روی گوشی‌اش می‌بیند."
        )
        p.intro_en = (
            "I build web systems that hold up under real load — from the data model "
            "and access rules to the Docker deploy and what the user finally sees on a phone."
        )
        p.intro_de = (
            "Ich baue Websysteme, die unter echter Last bestehen — vom Datenmodell "
            "über die Zugriffsregeln bis zum Docker-Deployment und dem, was am Ende auf dem Handy erscheint."
        )

        p.bio_fa = (
            "### چطور کار می‌کنم\n\n"
            "با یک مسئلهٔ مشخص شروع می‌کنم، نه با یک فریم‌ورک. اول می‌فهمم داده چه شکلی است و "
            "چه کسی اجازهٔ دیدن چه چیزی را دارد؛ بقیهٔ سیستم از همان‌جا بیرون می‌آید.\n\n"
            "بیشترِ کارم سمت سرور است — پایتون، جنگو، فست‌ای‌پی‌آی، پایگاه داده، داکر — "
            "ولی تا وقتی چیزی روی گوشی درست دیده نشود، آن را تمام‌شده حساب نمی‌کنم.\n\n"
            "*این متن نمونه است و باید با روایت خودتان جایگزین شود.*"
        )
        p.bio_en = (
            "### How I work\n\n"
            "I start from a concrete problem, not from a framework. First I work out the shape of "
            "the data and who is allowed to see what; the rest of the system falls out of that.\n\n"
            "Most of my work is server-side — Python, Django, FastAPI, databases, Docker — but I do "
            "not call anything finished until it reads correctly on a phone.\n\n"
            "*Placeholder text — replace with your own.*"
        )
        p.bio_de = (
            "### Wie ich arbeite\n\n"
            "Ich beginne bei einem konkreten Problem, nicht bei einem Framework. Zuerst kläre ich, "
            "welche Form die Daten haben und wer was sehen darf; alles Weitere ergibt sich daraus.\n\n"
            "*Platzhaltertext — bitte ersetzen.*"
        )

        p.location_fa, p.location_en, p.location_de = "تهران، ایران", "Tehran, Iran", "Teheran, Iran"
        p.now_fa = "روی یک اپلیکیشن چالش و عادت کار می‌کنم و دربارهٔ طراحی مجوزها می‌نویسم."
        p.now_en = "Building a habit-and-challenge app, and writing about permission design."
        p.now_de = "Ich baue eine Habit-App und schreibe über Berechtigungsdesign."
        p.availability_fa, p.availability_en, p.availability_de = "آمادهٔ همکاری", "Open to work", "Offen für Projekte"

        p.email = "hello@montazeri.ir"
        p.github = "mahdimontazeri"
        p.linkedin = "mahdimontazeri"
        p.telegram = "mahdimontazeri"
        p.is_available = True
        p.save()

    # ── tags ──────────────────────────────────────────────────────────────
    def _tags(self) -> dict[str, Tag]:
        rows = [
            ("backend", "بک‌اند", "Backend", "Backend"),
            ("web", "وب", "Web", "Web"),
            ("mobile", "موبایل", "Mobile", "Mobile"),
            ("infra", "زیرساخت", "Infrastructure", "Infrastruktur"),
            ("notes", "یادداشت", "Notes", "Notizen"),
            ("design", "طراحی", "Design", "Design"),
        ]
        out = {}
        for slug, fa, en, de in rows:
            tag, _ = Tag.objects.update_or_create(
                slug=slug, defaults={"name_fa": fa, "name_en": en, "name_de": de}
            )
            out[slug] = tag
        return out

    # ── skills ────────────────────────────────────────────────────────────
    def _skills(self):
        groups = [
            (("زبان‌ها و فریم‌ورک‌ها", "Languages & frameworks", "Sprachen & Frameworks"), 0,
             [("Python", True), ("Django", True), ("FastAPI", True), ("JavaScript", False),
              ("HTML/CSS", False), ("SQL", True)]),
            (("داده و زیرساخت", "Data & infrastructure", "Daten & Infrastruktur"), 1,
             [("PostgreSQL", True), ("SQLite", False), ("Redis", False), ("Docker", True),
              ("Linux", False), ("CI/CD", False)]),
            (("ابزارها", "Tools & practice", "Werkzeuge"), 2,
             [("Git", False), ("Nginx", False), ("Alembic", False), ("pytest", False),
              ("REST", False), ("Figma", False)]),
        ]
        for (fa, en, de), order, skills in groups:
            group, _ = SkillGroup.objects.update_or_create(
                name_fa=fa, defaults={"name_en": en, "name_de": de, "order": order}
            )
            group.skills.all().delete()
            for i, (name, primary) in enumerate(skills):
                Skill.objects.create(group=group, name=name, order=i, is_primary=primary)

    # ── projects ──────────────────────────────────────────────────────────
    def _projects(self, tags):
        rows = [
            {
                "slug": "challenge-app",
                "year": 2026,
                "stack": "FastAPI, SQLite, Capacitor, Docker",
                "featured": True,
                "tags": ["backend", "mobile"],
                "fa": {
                    "title": "سامانهٔ چالش",
                    "summary": "اپلیکیشن چالش و عادت با موتور رخداد شمسی، اعلان وب‌پوش و پوستهٔ اندروید.",
                    "role": "طراحی، توسعهٔ کامل، استقرار",
                    "outcome": "یک سامانهٔ زنده با گروه‌ها، مسیرهای یادگیری و کارت امتیاز",
                    "problem": (
                        "ثبت عادت روزانه ساده به نظر می‌رسد تا وقتی بفهمی «امروز» برای دو نفر در دو "
                        "منطقهٔ زمانی یک چیز نیست، و «این ماه» در تقویم شمسی با تقویم میلادی یکی نمی‌شود."
                    ),
                    "body": (
                        "موتور رخداد، هستهٔ سیستم است: از یک الگوی تکرار و منطقهٔ زمانی هر عضو، "
                        "کلید یکتای هر نوبت را می‌سازد. همین کلید یکتا، ثبت تکراری را بی‌خطر می‌کند.\n\n"
                        "### چند تصمیم که ماند\n\n"
                        "- **دسترسی یک شرط SQL است، نه یک `if` بعد از خواندن.** چهار فیلتر مرکزی دارد و هر دو "
                        "لایهٔ API و صفحه‌ها همان‌ها را می‌خوانند.\n"
                        "- **زنجیره‌ها دوباره محاسبه می‌شوند، هرگز جمع نمی‌شوند.** هیچ `+= 1` در سیستم نیست.\n"
                        "- **ماه، ماه شمسی است.** یک ماه میلادی وسط شهریور سهمیهٔ کاربر را دو تکه می‌کرد.\n\n"
                        "*این متن نمونه است.*"
                    ),
                },
                "en": {
                    "title": "Challenge",
                    "summary": "A habit and challenge app with a Jalali occurrence engine, web push and an Android shell.",
                    "role": "Design, full build, deployment",
                    "outcome": "A live system with groups, learning paths and a leaderboard",
                    "problem": (
                        "Logging a daily habit looks simple until you notice that \"today\" is not the same "
                        "thing for two people in two timezones, and that \"this month\" in the Persian "
                        "calendar is not the Gregorian one."
                    ),
                    "body": (
                        "The occurrence engine is the core: from a recurrence pattern and each member's own "
                        "timezone it derives a unique key per due occurrence. That key is what makes a "
                        "duplicate submission harmless.\n\n"
                        "### Decisions that held\n\n"
                        "- **Access is a SQL predicate, not an `if` after loading.** Four central filters, "
                        "shared by the JSON API and the server-rendered pages.\n"
                        "- **Streaks are recomputed, never incremented.** There is no `+= 1` anywhere.\n"
                        "- **A month is a Jalali month.** A Gregorian one split a user's quota mid-Shahrivar.\n\n"
                        "*Placeholder text.*"
                    ),
                },
                "de": {
                    "title": "Challenge",
                    "summary": "Eine Habit-App mit Jalali-Kalenderlogik, Web-Push und Android-Hülle.",
                    "role": "Konzept, Umsetzung, Betrieb",
                    "outcome": "Ein laufendes System mit Gruppen, Lernpfaden und Rangliste",
                    "problem": "",
                    "body": "*Platzhaltertext.*",
                },
            },
            {
                "slug": "rechnungskit",
                "year": 2025,
                "stack": "Django, PostgreSQL, Docker",
                "featured": True,
                "tags": ["backend", "web"],
                "fa": {
                    "title": "Rechnungskit",
                    "summary": "صدور و پیگیری فاکتور برای کسب‌وکار کوچک، با خروجی استاندارد و بایگانی.",
                    "role": "توسعهٔ بک‌اند",
                    "outcome": "چرخهٔ صدور تا وصول در یک ابزار",
                    "problem": "",
                    "body": "شرح این پروژه را در پنل مدیریت بنویسید.\n\n*این متن نمونه است.*",
                },
                "en": {
                    "title": "Rechnungskit",
                    "summary": "Invoicing and receivables for small businesses, with a standards-compliant export.",
                    "role": "Backend development",
                    "outcome": "Issue-to-paid in one tool",
                    "problem": "",
                    "body": "Write this case study in the admin.\n\n*Placeholder text.*",
                },
                "de": {
                    "title": "Rechnungskit",
                    "summary": "Rechnungsstellung und Zahlungsverfolgung für kleine Unternehmen.",
                    "role": "Backend-Entwicklung",
                    "outcome": "Von der Rechnung bis zur Zahlung in einem Werkzeug",
                    "problem": "",
                    "body": "*Platzhaltertext.*",
                },
            },
            {
                "slug": "tenantforge",
                "year": 2025,
                "stack": "Python, PostgreSQL, CI/CD",
                "featured": True,
                "tags": ["infra", "backend"],
                "fa": {
                    "title": "TenantForge",
                    "summary": "زیرساخت چنداجاره‌ای با جداسازی داده در سطح پایگاه‌داده و استقرار خودکار.",
                    "role": "معماری و پیاده‌سازی",
                    "outcome": "افزودن یک مشتری جدید از چند روز به چند دقیقه رسید",
                    "problem": "",
                    "body": "شرح این پروژه را در پنل مدیریت بنویسید.\n\n*این متن نمونه است.*",
                },
                "en": {
                    "title": "TenantForge",
                    "summary": "Multi-tenant infrastructure with database-level isolation and automated provisioning.",
                    "role": "Architecture and implementation",
                    "outcome": "Onboarding a new tenant went from days to minutes",
                    "problem": "",
                    "body": "Write this case study in the admin.\n\n*Placeholder text.*",
                },
                "de": {
                    "title": "TenantForge",
                    "summary": "Mandantenfähige Infrastruktur mit Isolation auf Datenbankebene.",
                    "role": "Architektur und Umsetzung",
                    "outcome": "Neue Mandanten in Minuten statt Tagen",
                    "problem": "",
                    "body": "*Platzhaltertext.*",
                },
            },
        ]

        for order, row in enumerate(rows):
            defaults = {
                "year": row["year"],
                "stack": row["stack"],
                "is_featured": row["featured"],
                "is_published": True,
                "order": order,
            }
            for code in ("fa", "en", "de"):
                for field, value in row[code].items():
                    defaults[f"{field}_{code}"] = value
            project, _ = Project.objects.update_or_create(slug=row["slug"], defaults=defaults)
            project.tags.set([tags[s] for s in row["tags"]])

    # ── experience ────────────────────────────────────────────────────────
    def _experience(self):
        rows = [
            {
                "kind": Experience.Kind.WORK,
                "start": date(2023, 4, 1),
                "end": None,
                "fa": ("مستقل / فریلنس", "مهندس نرم‌افزار", "تهران",
                       "طراحی و ساخت سامانه‌های وب برای کسب‌وکارهای کوچک: از مدل داده تا استقرار.\n\n*نمونه.*"),
                "en": ("Independent", "Software engineer", "Tehran",
                       "Designing and building web systems for small businesses, from the data model to the deploy.\n\n*Placeholder.*"),
                "de": ("Selbstständig", "Softwareentwickler", "Teheran", "*Platzhalter.*"),
            },
            {
                "kind": Experience.Kind.WORK,
                "start": date(2021, 1, 1),
                "end": date(2023, 3, 1),
                "fa": ("نام شرکت", "توسعه‌دهندهٔ بک‌اند", "تهران", "شرح این نقش را در پنل مدیریت بنویسید."),
                "en": ("Company name", "Backend developer", "Tehran", "Write this role in the admin."),
                "de": ("Firmenname", "Backend-Entwickler", "Teheran", ""),
            },
            {
                "kind": Experience.Kind.EDUCATION,
                "start": date(2016, 9, 1),
                "end": date(2020, 7, 1),
                "fa": ("نام دانشگاه", "کارشناسی مهندسی کامپیوتر", "", ""),
                "en": ("University name", "BSc, Computer Engineering", "", ""),
                "de": ("Universität", "B.Sc. Technische Informatik", "", ""),
            },
        ]
        for order, row in enumerate(rows):
            defaults = {"kind": row["kind"], "start": row["start"], "end": row["end"], "order": order}
            for code in ("fa", "en", "de"):
                org, role, loc, desc = row[code]
                defaults[f"org_{code}"] = org
                defaults[f"role_{code}"] = role
                defaults[f"location_{code}"] = loc
                defaults[f"description_{code}"] = desc
            Experience.objects.update_or_create(
                org_fa=row["fa"][0], start=row["start"], defaults=defaults
            )

    # ── posts ─────────────────────────────────────────────────────────────
    def _posts(self, tags):
        rows = [
            {
                "slug": "permissions-are-a-query",
                "tags": ["backend", "notes"],
                "days": 6,
                "fa": (
                    "دسترسی، یک کوئری است — نه یک if",
                    "وقتی قاعدهٔ دسترسی بعد از خواندن ردیف اجرا شود، هر صفحهٔ جدید یک فرصت تازه برای فراموش‌کردنش است.",
                    "معمول‌ترین اشتباه در سیستم‌های چنداستفاده‌کننده این است که ردیف را می‌خوانیم و بعد "
                    "می‌پرسیم «این کاربر اجازه دارد؟».\n\n"
                    "مشکل این نیست که کار نمی‌کند؛ مشکل این است که این پرسش را باید در هر مسیر تازه دوباره "
                    "بپرسی، و مسیری که یادت برود یک نشتی خاموش است.\n\n"
                    "راه بهتر این است که قاعده را به خود کوئری بدهی. آن‌وقت نبودن اجازه به شکل «چنین ردیفی "
                    "وجود ندارد» بیرون می‌آید و ۴۰۴ می‌گیری — که اتفاقاً همان جوابی است که یک شمارندهٔ شناسه "
                    "نباید بیشتر از آن بفهمد.\n\n"
                    "*این نوشتهٔ نمونه است.*"
                ),
                "en": (
                    "Permissions are a query, not an if",
                    "When the rule runs after the row is loaded, every new page is a fresh chance to forget it.",
                    "The common shape in multi-user systems is: load the row, then ask whether this user is "
                    "allowed to see it.\n\n"
                    "The problem is not that it fails. The problem is that the question has to be asked again "
                    "on every new path, and the path that forgets is a silent leak.\n\n"
                    "The better shape is to hand the rule to the query itself. A miss then falls out as \"no "
                    "such row\" and you answer 404 — which happens to be exactly what somebody walking "
                    "sequential ids should be told.\n\n"
                    "*Placeholder post.*"
                ),
                "de": (
                    "Berechtigungen sind eine Abfrage, kein if",
                    "Wenn die Regel erst nach dem Laden greift, ist jede neue Seite eine neue Gelegenheit, sie zu vergessen.",
                    "*Platzhalterbeitrag.*"
                ),
            },
            {
                "slug": "sqlite-in-production",
                "tags": ["infra", "notes"],
                "days": 21,
                "fa": (
                    "SQLite در تولید، و کِی دیگر کافی نیست",
                    "برای یک سایت شخصی و خیلی بیشتر از آن، یک فایل روی دیسک جواب می‌دهد — به شرط چند تنظیم.",
                    "SQLite را «پایگاه دادهٔ اسباب‌بازی» صدا می‌زنند و بعد کشف می‌کنند که چند صد هزار "
                    "بازدید ماهانه را بی‌صدا تحمل کرده است.\n\n"
                    "سه تنظیم است که فرق می‌گذارد: `journal_mode=WAL` تا خواندن و نوشتن هم‌زمان ممکن شود، "
                    "یک `timeout` معقول، و اینکه فایل روی یک دیسک واقعی باشد نه روی یک اشتراک شبکه.\n\n"
                    "کجا دیگر کافی نیست؟ وقتی نوشتن‌های هم‌زمان زیاد شود، یا وقتی بخواهی بیش از یک ماشین "
                    "به یک داده وصل شود.\n\n"
                    "*این نوشتهٔ نمونه است.*"
                ),
                "en": (
                    "SQLite in production, and when it stops being enough",
                    "For a personal site and a good deal more, one file on disk is the right answer — given a few settings.",
                    "People call SQLite a toy database and then discover it quietly carried a few hundred "
                    "thousand visits a month.\n\n"
                    "Three settings make the difference: `journal_mode=WAL` so a reader and a writer can "
                    "coexist, a sane `timeout`, and the file sitting on a real disk rather than a network share.\n\n"
                    "Where does it stop? When concurrent writes get heavy, or when more than one machine "
                    "needs the same data.\n\n"
                    "*Placeholder post.*"
                ),
                "de": (
                    "SQLite im Produktivbetrieb",
                    "Für eine persönliche Website und einiges mehr reicht eine Datei auf der Festplatte.",
                    "*Platzhalterbeitrag.*"
                ),
            },
        ]

        for row in rows:
            defaults = {
                "published_at": timezone.now() - timezone.timedelta(days=row["days"]),
                "is_published": True,
            }
            for code in ("fa", "en", "de"):
                title, excerpt, body = row[code]
                defaults[f"title_{code}"] = title
                defaults[f"excerpt_{code}"] = excerpt
                defaults[f"body_{code}"] = body
            post, _ = Post.objects.update_or_create(slug=row["slug"], defaults=defaults)
            post.tags.set([tags[s] for s in row["tags"]])
