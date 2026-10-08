"""
Seed the site with Mahdi's real content in all three languages.

This is the counterpart to `seed_demo`: same shape, but every string here is
true and traceable to `master-profile.md`. It is the reproducible record of
what the live site says, so a claim can be changed in one reviewed place
rather than in an admin form nobody can diff.

    python manage.py seed_profile           # upsert, keeps the database
    python manage.py seed_profile --wipe    # replace projects/skills/roles

── Rules this file follows ────────────────────────────────────────────────
Three claims from the old CV are retired and must never come back: "6 years",
"25+ microservices", "90%+ test coverage", "60M+ customers". The numbers here
are the defensible ones — 25M unique customers, 800M invoice records, up to
30x on page data loads, ~70% of the architecture migration done.

The site itself is no longer listed as a project — see `_retire_projects`.
The personal projects here (actpact, rechnungskit, webhook-gateway,
TenantForge) are described from their own READMEs; actpact's repository is
private on purpose, the three libraries link to their public ones.

Smart Studio, Salonyar, GeekWare and Podcast Workspace come from
`portfolio-new-projects.md` (2026-10-08), itself drawn from each project's
code. Their repositories are private, except Podcast Workspace's. Salonyar is
pilot-ready but not live, so it has no link and claims no salon uses it;
Smart Studio needs a login, so it has no demo link either.

Education is deliberately absent. There is no completed degree, and an empty
section renders nothing at all, which reads better than an unfinished entry.

Nothing private is here: no age, no marital status, no military status, no
visa arithmetic. Relocation is retired too — no "moving to Germany", no
§19c(2) residence route, no "open to roles in Germany". The site is read by
recruiters in Iran as well, and a stated move abroad reads to them as a hire
who is about to leave. Location is Tehran.

Remote is retired as well: Mahdi works on-site, hybrid, or by the project —
never fully remote. The copy says what he does rather than what he does not,
so "remote" simply no longer appears anywhere a visitor reads.

Project work is a line of income, so it has its own offer (`offer_*` on the
profile, the `Service` cards, /services/): end to end, a quick start with fast
delivery, and a price agreed per project.
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.models import (
    Experience,
    Post,
    Profile,
    Project,
    Service,
    Skill,
    SkillGroup,
    Tag,
)


class Command(BaseCommand):
    help = "Fill the database with Mahdi's real content, in fa/en/de."

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete projects, skills, tags and roles first. Posts are only unpublished.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["wipe"]:
            for model in (Project, Experience, Skill, SkillGroup, Tag):
                model.objects.all().delete()
            self.stdout.write(self.style.WARNING("wiped projects, skills, tags and roles"))

        self._profile()
        self._services()
        tags = self._tags()
        self._skills()
        self._projects(tags)
        self._experience()
        self._retire_demo_posts()
        self._retire_projects()
        self.stdout.write(self.style.SUCCESS("seeded — real content, fa/en/de"))

    # ── profile ───────────────────────────────────────────────────────────
    def _profile(self):
        p = Profile.load()

        p.full_name_fa = "مهدی منتظری"
        p.full_name_en = "Mahdi Montazeri"
        p.full_name_de = "Mahdi Montazeri"

        p.headline_fa = "مهندس بک‌اند — دات‌نت و پایتون. سیستم‌های رویدادمحور، داده‌ی حجیم."
        p.headline_en = "Backend engineer — .NET and Python. Event-driven systems, high-volume data."
        p.headline_de = (
            "Backend-Entwickler — .NET und Python. Ereignisgesteuerte Systeme, große Datenmengen."
        )

        p.intro_fa = (
            "سیستم‌های بک‌اندی می‌سازم که وقتی داده بزرگ می‌شود، درست باقی می‌مانند. "
            "دو سال و نیم گذشته را روی یک پلتفرم باشگاه مشتریان و CRM کار کرده‌ام با حدود "
            "۲۵ میلیون مشتری یکتا و ۸۰۰ میلیون رکورد فاکتور: بازنویسی از "
            ".NET Framework تا .NET 9، بازطراحی اسکیمای SQL Server زیر آن، و تفکیک "
            "سیستم به سرویس‌های دامنه‌محور روی RabbitMQ و gRPC. "
            "استک دوم من پایتون و FastAPI است."
        )
        p.intro_en = (
            "I build backend systems that stay correct when the data gets large. "
            "For the last two and a half years that has meant a customer loyalty and "
            "CRM platform holding around 25 million unique customers and 800 million "
            "invoice records — modernising it from .NET Framework to .NET 9, rebuilding "
            "the SQL Server schema underneath it, and splitting it into domain services "
            "over RabbitMQ and gRPC. My second stack is Python and FastAPI."
        )
        p.intro_de = (
            "Ich baue Backend-Systeme, die auch bei großen Datenmengen korrekt bleiben. "
            "In den letzten zweieinhalb Jahren war das eine Kundenbindungs- und "
            "CRM-Plattform mit rund 25 Millionen eindeutigen Kunden und 800 Millionen "
            "Rechnungsdatensätzen: Modernisierung von .NET Framework auf .NET 9, "
            "Umbau des darunterliegenden SQL-Server-Schemas und Aufteilung in "
            "Domain-Services über RabbitMQ und gRPC. Mein zweiter Stack ist Python "
            "mit FastAPI."
        )

        p.bio_fa = _BIO_FA
        p.bio_en = _BIO_EN
        p.bio_de = _BIO_DE

        p.location_fa = "تهران، ایران"
        p.location_en = "Tehran, Iran"
        p.location_de = "Teheran, Iran"

        p.now_fa = "عمیق‌تر کردن کار با پایتون و FastAPI، و ساختن ابزارهای کوچک و قابل‌اتکا با آن."
        p.now_en = "Deepening the Python and FastAPI side of my work, and shipping small, dependable tools with it."
        p.now_de = (
            "Ich vertiefe meine Arbeit mit Python und FastAPI und baue damit kleine, "
            "verlässliche Werkzeuge."
        )

        # Stated plainly, including the A1. A German recruiter finds out in the
        # first call either way; finding out from the site costs nothing, and
        # finding out after fluent German copy costs credibility.
        p.languages_fa = "فارسی زبان مادری · انگلیسی C1 · آلمانی A1 (در حال یادگیری)"
        p.languages_en = "Persian native · English C1 · German A1 (learning)"
        p.languages_de = "Persisch Muttersprache · Englisch C1 · Deutsch A1 (im Aufbau)"

        p.availability_fa = "آماده‌ی همکاری — حضوری، هیبریدی یا پروژه‌ای"
        p.availability_en = "Open to work — on-site, hybrid or project-based"
        p.availability_de = "Offen für Zusammenarbeit — vor Ort, hybrid oder projektbasiert"

        # ── search results: the home page title and the two lines under it ──
        p.seo_title_fa = "مهدی منتظری | برنامه‌نویس بک‌اند دات‌نت و پایتون"
        p.seo_title_en = "Mahdi Montazeri — Backend Engineer, .NET & Python"
        p.seo_title_de = "Mahdi Montazeri — Backend-Entwickler, .NET & Python"
        p.seo_description_fa = (
            "مهدی منتظری، مهندس بک‌اند در تهران — دات‌نت، پایتون و SQL Server در مقیاس ۲۵ میلیون "
            "کاربر. انجام پروژه‌ی نرم‌افزاری از صفر تا صد؛ حضوری، هیبریدی یا پروژه‌ای."
        )
        p.seo_description_en = (
            "Mahdi Montazeri, backend engineer in Tehran — .NET, Python and SQL Server at "
            "25M-customer scale. Software projects end to end: on-site, hybrid or by contract."
        )
        p.seo_description_de = (
            "Mahdi Montazeri, Backend-Entwickler in Teheran: .NET, Python, SQL Server bei 25 Mio. "
            "Kunden. Softwareprojekte von A bis Z — vor Ort, hybrid oder projektbasiert."
        )

        # ── project work ──
        p.offer_title_fa = "پروژه‌ی نرم‌افزاری شما، از صفر تا صد"
        p.offer_title_en = "Your software project, from first idea to launch"
        p.offer_title_de = "Ihr Softwareprojekt — von der Idee bis zum Livegang"
        p.offer_lede_fa = (
            "از گفت‌وگوی اول و تحلیل نیاز تا طراحی، توسعه، استقرار و تحویل — با یک مسئولِ "
            "پاسخ‌گو، شروع بی‌معطلی، تحویل سریع و هزینه‌ای که متناسب با پروژه‌ی شما توافق می‌شود."
        )
        p.offer_lede_en = (
            "From the first conversation and the requirements through design, build, deployment "
            "and hand-over — one accountable engineer, a quick start, fast delivery, and a price "
            "agreed around your project."
        )
        p.offer_lede_de = (
            "Vom ersten Gespräch über Anforderungen, Entwurf, Umsetzung und Deployment bis zur "
            "Übergabe — ein verantwortlicher Entwickler, kurzfristiger Start, zügige Lieferung und "
            "ein Preis, der zu Ihrem Projekt passt."
        )
        p.offer_body_fa = _OFFER_FA
        p.offer_body_en = _OFFER_EN
        p.offer_body_de = _OFFER_DE

        p.email = "mahdii.montazeri@gmail.com"
        p.github = "MehDiSDeveloper"
        p.linkedin = "mahdi-montazeri-tehran"
        p.website = "https://montazeri.ir"
        p.is_available = True

        p.save()

    # ── services: the four promises on /services/ ──────────────────────────
    def _services(self):
        rows = [
            (
                "layers",
                ("از صفر تا صد", "تحلیل نیاز، طراحی معماری و پایگاه داده، توسعه‌ی بک‌اند و API، تست و استقرار — یک نفر مسئول کل مسیر است، نه زنجیره‌ای از پیمانکارها."),
                ("End to end", "Requirements, architecture and database design, backend and API, testing and deployment — one person accountable for the whole path, not a chain of contractors."),
                ("Von A bis Z", "Anforderungen, Architektur und Datenbankdesign, Backend und API, Tests und Deployment — eine verantwortliche Person statt einer Kette von Dienstleistern."),
            ),
            (
                "clock",
                ("شروع فوری، تحویل سریع", "بدون دوره‌ی انتظار شروع می‌کنم و کار را در گام‌های کوتاه تحویل می‌دهم؛ نسخه‌ی قابل‌استفاده زود به دستتان می‌رسد، نه بعد از ماه‌ها."),
                ("Quick start, fast delivery", "I start without a waiting period and deliver in short steps, so you have something usable early rather than after months."),
                ("Schneller Start, zügige Lieferung", "Start ohne Wartezeit, Lieferung in kurzen Schritten — Sie haben früh etwas Nutzbares in der Hand, nicht erst nach Monaten."),
            ),
            (
                "target",
                ("هزینه‌ی توافقی", "قیمت بر اساس دامنه و زمان‌بندی پروژه تعیین می‌شود و پیش از شروع، شفاف توافق می‌کنیم — بدون هزینه‌ی پنهان."),
                ("Price by agreement", "The price follows the scope and the timeline, and we agree it clearly before work starts — no hidden costs."),
                ("Preis nach Vereinbarung", "Der Preis richtet sich nach Umfang und Zeitplan und wird vor Beginn transparent vereinbart — ohne versteckte Kosten."),
            ),
            (
                "briefcase",
                ("حضوری، هیبریدی یا پروژه‌ای", "در تهران به‌صورت حضوری یا هیبریدی کنار تیم شما هستم، یا پروژه را به‌صورت قراردادی و با تحویل مشخص انجام می‌دهم."),
                ("On-site, hybrid or by project", "In Tehran I work on-site or hybrid alongside your team, or take the work as a contract with a defined delivery."),
                ("Vor Ort, hybrid oder projektbasiert", "In Teheran vor Ort oder hybrid mit Ihrem Team — oder als Auftrag mit klar definierter Lieferung."),
            ),
        ]
        Service.objects.all().delete()
        for order, (icon, fa, en, de) in enumerate(rows):
            Service.objects.create(
                icon=icon,
                order=order,
                title_fa=fa[0], body_fa=fa[1],
                title_en=en[0], body_en=en[1],
                title_de=de[0], body_de=de[1],
            )

    # ── tags ──────────────────────────────────────────────────────────────
    def _tags(self) -> dict[str, Tag]:
        rows = [
            ("dotnet", "دات‌نت", ".NET", ".NET"),
            ("python", "پایتون", "Python", "Python"),
            ("architecture", "معماری", "Architecture", "Architektur"),
            ("performance", "کارایی", "Performance", "Performance"),
            ("databases", "پایگاه داده", "Databases", "Datenbanken"),
            ("fastapi", "فست‌ای‌پی‌آی", "FastAPI", "FastAPI"),
            ("security", "امنیت", "Security", "Sicherheit"),
            ("typescript", "تایپ‌اسکریپت", "TypeScript", "TypeScript"),
            ("react", "ری‌اکت", "React", "React"),
            ("nodejs", "نود جی‌اس", "Node.js", "Node.js"),
            ("android", "اندروید", "Android", "Android"),
            ("bale", "بله", "Bale", "Bale"),
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
        # Tier 1 and the defensible half of Tier 2 only. Anything that reads as
        # filler on a backend CV — markup, jQuery, Bootstrap, a UI framework
        # touched once — is left out on purpose: it lowers the perceived level
        # rather than widening the match.
        groups = [
            (
                ("بک‌اند و دات‌نت", "Backend & .NET", "Backend & .NET"),
                [
                    ("C#", True),
                    ("ASP.NET Core", True),
                    (".NET 8 / 9", True),
                    ("EF Core", False),
                    ("REST API design", False),
                    ("SignalR", False),
                    ("Hangfire", False),
                    ("Serilog", False),
                ],
            ),
            (
                ("پایتون", "Python", "Python"),
                [
                    ("Python", True),
                    ("FastAPI", True),
                    ("Pydantic", False),
                    ("SQLAlchemy", False),
                    ("Alembic", False),
                    ("pytest", False),
                    ("asyncio", False),
                    ("LLM API integration", False),
                ],
            ),
            (
                ("داده و کارایی", "Data & performance", "Daten & Performance"),
                [
                    ("SQL Server", True),
                    ("PostgreSQL", True),
                    ("T-SQL", False),
                    ("Stored procedures", False),
                    ("Query tuning", False),
                    ("Schema migration at scale", False),
                    ("Multi-tenancy", False),
                ],
            ),
            (
                ("معماری و تحویل", "Architecture & delivery", "Architektur & Delivery"),
                [
                    ("Clean Architecture", True),
                    ("CQRS", True),
                    ("Vertical slice", False),
                    ("Event-driven design", False),
                    ("DDD", False),
                    ("RabbitMQ", True),
                    ("gRPC", True),
                    ("Docker", True),
                    ("CI/CD", False),
                    ("Scrum", False),
                ],
            ),
        ]

        for gi, ((fa, en, de), skills) in enumerate(groups):
            group, _ = SkillGroup.objects.update_or_create(
                name_en=en, defaults={"name_fa": fa, "name_de": de, "order": gi}
            )
            group.skills.all().delete()
            for si, (name, primary) in enumerate(skills):
                Skill.objects.create(group=group, name=name, order=si, is_primary=primary)

    # ── projects ──────────────────────────────────────────────────────────
    def _projects(self, tags):
        self._upsert_project(
            slug="customer-club-platform",
            year=2026,
            order=0,
            stack="C#, .NET 9, ASP.NET Core, EF Core, SQL Server, RabbitMQ, gRPC, Docker",
            tag_slugs=("dotnet", "architecture", "performance"),
            tags=tags,
            fa=dict(
                title="پلتفرم باشگاه مشتریان در مقیاس ۲۵ میلیون کاربر",
                summary=(
                    "یک پلتفرم وفاداری و CRM از نوع B2B2C با ۲۵ میلیون مشتری یکتا و ۸۰۰ میلیون "
                    "رکورد فاکتور — از .NET Framework تا .NET 9 و سپس تفکیک به سرویس‌های دامنه‌محور."
                ),
                role="توسعه‌دهنده‌ی اصلی محصول — معماری و پیاده‌سازی",
                problem=_P1_PROBLEM_FA,
                body=_P1_BODY_FA,
                outcome=(
                    "زمان بارگذاری داده‌ی صفحات تا ۳۰ برابر سریع‌تر؛ محصول روی .NET 9 و حدود "
                    "۷۰٪ از مسیر مهاجرت معماری طی‌شده."
                ),
            ),
            en=dict(
                title="A customer loyalty platform at 25M-customer scale",
                summary=(
                    "A B2B2C loyalty and CRM platform holding 25 million unique customers and "
                    "800 million invoice records, modernised from .NET Framework to .NET 9 and "
                    "split into domain services."
                ),
                role="Primary developer on the product — architecture and implementation",
                problem=_P1_PROBLEM_EN,
                body=_P1_BODY_EN,
                outcome=(
                    "Page data loads up to 30x faster, the product running on .NET 9, and about "
                    "70% of the architecture migration complete."
                ),
            ),
            de=dict(
                title="Kundenbindungsplattform für 25 Millionen Kunden",
                summary=(
                    "Eine B2B2C-Loyalty- und CRM-Plattform mit 25 Millionen eindeutigen Kunden "
                    "und 800 Millionen Rechnungsdatensätzen — modernisiert von .NET Framework "
                    "auf .NET 9 und in Domain-Services aufgeteilt."
                ),
                role="Hauptentwickler des Produkts — Architektur und Umsetzung",
                problem=_P1_PROBLEM_DE,
                body=_P1_BODY_DE,
                outcome=(
                    "Datenladezeiten der Seiten bis zu 30-mal schneller, das Produkt auf .NET 9, "
                    "die Architekturmigration zu rund 70 % abgeschlossen."
                ),
            ),
        )

        self._upsert_project(
            slug="sql-server-at-scale",
            year=2025,
            order=5,
            stack="SQL Server, T-SQL, EF Core, C#",
            tag_slugs=("databases", "performance", "dotnet"),
            tags=tags,
            fa=dict(
                title="بازطراحی اسکیمای SQL Server روی پایگاه داده‌ی زنده",
                summary=(
                    "بازطراحی‌های سنگین اسکیما روی پایگاه داده‌ای با ۸۰۰ میلیون رکورد فاکتور — "
                    "جایی که بخش سخت ماجرا اسکیما نبود، قفل‌ها بودند."
                ),
                role="مهندس پایگاه داده و بک‌اند",
                problem=_P2_PROBLEM_FA,
                body=_P2_BODY_FA,
                outcome=(
                    "یک راهبرد مهاجرت که از پس این حجم داده برآمد — بعد از آزمودن و کنار گذاشتن "
                    "چند راهبرد دیگر."
                ),
            ),
            en=dict(
                title="Refactoring a SQL Server schema under load",
                summary=(
                    "Heavy schema refactors on a live database of 800 million invoice records — "
                    "where the hard part was never the schema, it was the locking."
                ),
                role="Database and backend engineer",
                problem=_P2_PROBLEM_EN,
                body=_P2_BODY_EN,
                outcome=(
                    "A migration strategy that held at this data volume, arrived at by testing "
                    "and rejecting several others first."
                ),
            ),
            de=dict(
                title="Schema-Refactoring in SQL Server unter Last",
                summary=(
                    "Umfangreiche Schema-Refactorings an einer produktiven Datenbank mit 800 "
                    "Millionen Rechnungsdatensätzen — schwierig war nie das Schema, sondern das "
                    "Sperrverhalten."
                ),
                role="Datenbank- und Backend-Entwickler",
                problem=_P2_PROBLEM_DE,
                body=_P2_BODY_DE,
                outcome=(
                    "Eine Migrationsstrategie, die diesem Datenvolumen standhielt — gefunden, "
                    "indem mehrere andere getestet und verworfen wurden."
                ),
            ),
        )

        self._upsert_project(
            slug="actpact",
            year=2026,
            order=4,
            stack="FastAPI, SQLAlchemy 2, SQLite, Jinja2, PWA, Capacitor, Docker",
            tag_slugs=("python", "fastapi", "architecture"),
            tags=tags,
            demo_url="https://actpact.ir",
            fa=dict(
                title="اکت‌پکت — ردیاب عادت و چالش، برای کاربر ایرانی",
                summary=(
                    "یک اپلیکیشن عادت و چالش که تقویم جلالی در عمق آن است، نه رویش: رابط فارسی، "
                    "راست‌به‌چپ از سر تا ته، و ورود با پیامک بدون نیاز به ایمیل."
                ),
                role="پروژه‌ی تک‌نفره — طراحی، بک‌اند، فرانت‌اند و پوسته‌ی اندروید",
                problem=_P3_PROBLEM_FA,
                body=_P3_BODY_FA,
                outcome=(
                    "روی actpact.ir بالاست: حدود ۱۶ هزار خط پایتون، ۱۹ جدول و ۸۰۶ تست — "
                    "نصب‌شدنی به‌عنوان PWA و منتشرشده به‌عنوان اپ اندروید."
                ),
            ),
            en=dict(
                title="actpact — a habit and challenge tracker for Iranian users",
                summary=(
                    "A habit and challenge app with the Jalali calendar underneath it rather "
                    "than on top of it: Farsi UI, right-to-left throughout, and an SMS login "
                    "that needs no email address."
                ),
                role="Solo project — design, backend, frontend and the Android shell",
                problem=_P3_PROBLEM_EN,
                body=_P3_BODY_EN,
                outcome=(
                    "Live at actpact.ir: about 16k lines of Python, 19 tables and 806 tests, "
                    "installable as a PWA and shipped as an Android app."
                ),
            ),
            de=dict(
                title="actpact — ein Gewohnheits- und Challenge-Tracker für iranische Nutzer",
                summary=(
                    "Eine Gewohnheits- und Challenge-App, in der der Jalali-Kalender nicht "
                    "obenauf liegt, sondern ganz unten: persische Oberfläche, durchgehend "
                    "rechts-nach-links, Anmeldung per SMS ohne E-Mail-Adresse."
                ),
                role="Einzelprojekt — Design, Backend, Frontend und die Android-Hülle",
                problem=_P3_PROBLEM_DE,
                body=_P3_BODY_DE,
                outcome=(
                    "Live unter actpact.ir: rund 16.000 Zeilen Python, 19 Tabellen und 806 "
                    "Tests — als PWA installierbar und als Android-App ausgeliefert."
                ),
            ),
        )

        self._upsert_project(
            slug="rechnungskit",
            year=2026,
            order=6,
            stack="Python, FastAPI, Pydantic, lxml, EN 16931, XRechnung, Factur-X",
            tag_slugs=("python", "fastapi", "architecture"),
            tags=tags,
            featured=False,
            repo_url="https://github.com/MehDiSDeveloper/rechnungskit",
            fa=dict(
                title="rechnungskit — فاکتور الکترونیکی آلمان در پایتون",
                summary=(
                    "کتابخانه‌ای تایپ‌شده برای ساخت، سریال‌سازی، جاسازی و اعتبارسنجی XRechnung و "
                    "ZUGFeRD روی مدل معنایی EN 16931، با گزارش خطای ماشین‌خوان."
                ),
                role="پروژه‌ی شخصی — طراحی و پیاده‌سازی",
                problem=_P4_PROBLEM_FA,
                body=_P4_BODY_FA,
                outcome=(
                    "۲۱۷ قاعده پیاده‌سازی‌شده — ۱۸۵ تای EN 16931 و ۳۲ تای BR-DE — با ۲۱۴ تست و "
                    "mypy strict؛ و فهرستی صریح از آنچه پوشش داده نشده، به‌جای قبولِ خاموش."
                ),
            ),
            en=dict(
                title="rechnungskit — German electronic invoicing in Python",
                summary=(
                    "A typed library to build, serialise, embed and validate XRechnung and "
                    "ZUGFeRD / Factur-X on the EN 16931 semantic model, with machine-readable "
                    "validation reports."
                ),
                role="Personal project — design and implementation",
                problem=_P4_PROBLEM_EN,
                body=_P4_BODY_EN,
                outcome=(
                    "217 rules implemented — 185 from EN 16931 and 32 BR-DE — with 214 tests "
                    "and mypy strict, and a named list of what is not covered instead of a "
                    "silent pass."
                ),
            ),
            de=dict(
                title="rechnungskit — deutsche E-Rechnung in Python",
                summary=(
                    "Eine typisierte Bibliothek zum Erzeugen, Serialisieren, Einbetten und "
                    "Prüfen von XRechnung und ZUGFeRD / Factur-X auf dem semantischen Modell "
                    "EN 16931 — mit maschinenlesbaren Prüfberichten."
                ),
                role="Eigenprojekt — Entwurf und Umsetzung",
                problem=_P4_PROBLEM_DE,
                body=_P4_BODY_DE,
                outcome=(
                    "217 Regeln umgesetzt — 185 aus EN 16931, 32 BR-DE — mit 214 Tests und "
                    "mypy strict, und einer benannten Liste dessen, was nicht abgedeckt ist, "
                    "statt eines stillen Durchwinkens."
                ),
            ),
        )

        self._upsert_project(
            slug="webhook-gateway",
            year=2026,
            order=7,
            stack="FastAPI, PostgreSQL, Redis, SQLAlchemy 2, Alembic, Prometheus",
            tag_slugs=("python", "fastapi", "databases", "security"),
            tags=tags,
            featured=False,
            repo_url="https://github.com/MehDiSDeveloper/webhook-gateway",
            fa=dict(
                title="webhook-gateway — دریافت و تحویل بادوامِ وبهوک",
                summary=(
                    "دروازه‌ای که وبهوک‌های ورودی را امضاسنجی، حذف‌تکراری و ذخیره می‌کند و با "
                    "تلاش مجدد، مدارشکن و صف مرده تحویلشان می‌دهد — با پستگرس به‌عنوان صف."
                ),
                role="پروژه‌ی شخصی — طراحی و پیاده‌سازی",
                problem=_P5_PROBLEM_FA,
                body=_P5_BODY_FA,
                outcome=(
                    "۱۵۴ تست، همه روی یک پستگرس واقعی — و یک بنچمارک که نامطلوب‌ترین سطرش همان "
                    "سطری است که توضیح داده شده."
                ),
            ),
            en=dict(
                title="webhook-gateway — durable webhook ingestion and delivery",
                summary=(
                    "A gateway that verifies, deduplicates and stores inbound webhooks, then "
                    "delivers them with retries, circuit breaking and a dead-letter queue — "
                    "with PostgreSQL as the queue."
                ),
                role="Personal project — design and implementation",
                problem=_P5_PROBLEM_EN,
                body=_P5_BODY_EN,
                outcome=(
                    "154 tests, every one against a real PostgreSQL — and a benchmark whose "
                    "least flattering row is the one that gets explained."
                ),
            ),
            de=dict(
                title="webhook-gateway — belastbare Webhook-Annahme und -Zustellung",
                summary=(
                    "Ein Gateway, das eingehende Webhooks signaturprüft, dedupliziert und "
                    "speichert und sie mit Retries, Circuit Breaking und Dead-Letter-Queue "
                    "zustellt — mit PostgreSQL als Warteschlange."
                ),
                role="Eigenprojekt — Entwurf und Umsetzung",
                problem=_P5_PROBLEM_DE,
                body=_P5_BODY_DE,
                outcome=(
                    "154 Tests, alle gegen ein echtes PostgreSQL — und ein Benchmark, dessen "
                    "unvorteilhafteste Zeile genau die ist, die erklärt wird."
                ),
            ),
        )

        self._upsert_project(
            slug="tenantforge",
            year=2026,
            order=8,
            stack="FastAPI, PostgreSQL, SQLAlchemy 2, Row-Level Security, JWT, Argon2",
            tag_slugs=("python", "fastapi", "databases", "security"),
            tags=tags,
            featured=False,
            repo_url="https://github.com/MehDiSDeveloper/tenantforge",
            fa=dict(
                title="TenantForge — اسکلت یک بک‌اند SaaS چندمستأجری",
                summary=(
                    "جداسازی مستأجرها را به‌جای «یادت باشد WHERE بگذاری» به Row-Level Security "
                    "خودِ پستگرس می‌سپارد — به‌علاوه‌ی توکن‌های چرخشی، RBAC و ردِ ممیزی."
                ),
                role="پروژه‌ی شخصی — طراحی و پیاده‌سازی",
                problem=_P6_PROBLEM_FA,
                body=_P6_BODY_FA,
                outcome=(
                    "یک ادعا، و یک مجموعه تست که کارش شکستن همان ادعاست: هر درخواست فقط همان "
                    "کارگاهی را می‌بیند که توکنش نام برده — و این را پستگرس تضمین می‌کند، نه کد."
                ),
            ),
            en=dict(
                title="TenantForge — a multi-tenant SaaS backend starter",
                summary=(
                    "Tenant isolation enforced by PostgreSQL Row-Level Security rather than by "
                    "application code remembering to filter — with rotating refresh tokens, "
                    "per-tenant RBAC and an audit trail."
                ),
                role="Personal project — design and implementation",
                problem=_P6_PROBLEM_EN,
                body=_P6_BODY_EN,
                outcome=(
                    "One claim, and a suite whose job is to break it: a request can only ever "
                    "see the workspace its token names, and PostgreSQL is what guarantees it."
                ),
            ),
            de=dict(
                title="TenantForge — ein Starter für mandantenfähige SaaS-Backends",
                summary=(
                    "Mandantentrennung, die PostgreSQL per Row-Level Security durchsetzt — "
                    "statt Anwendungscode, der ans Filtern denken muss. Dazu rotierende "
                    "Refresh-Tokens, RBAC je Mandant und ein Audit-Log."
                ),
                role="Eigenprojekt — Entwurf und Umsetzung",
                problem=_P6_PROBLEM_DE,
                body=_P6_BODY_DE,
                outcome=(
                    "Eine Behauptung und eine Testsuite, die sie zu widerlegen versucht: Eine "
                    "Anfrage sieht nur den Workspace, den ihr Token nennt — garantiert von "
                    "PostgreSQL, nicht vom Code."
                ),
            ),
        )

        self._upsert_project(
            slug="content-studio",
            year=2026,
            order=1,
            stack=(
                "Python, FastAPI, PostgreSQL 16, SQLAlchemy, Alembic, React 19, TypeScript, Vite, "
                "Kotlin, Jetpack Compose, Room, Docker"
            ),
            tag_slugs=("python", "fastapi", "architecture", "databases", "react", "android"),
            tags=tags,
            fa=dict(
                title="استودیو هوشمند — برنامه‌ریزی و تولید محتوای اینستاگرام",
                summary=(
                    "ابزار برنامه‌ریزی و تولید محتوای اینستاگرام برای یک استراتژیست محتوا و "
                    "تیمش، با اپ اندروید آفلاین‌محور، پنل وب و تقویم جلالی که مناسبت‌های ایرانی "
                    "را می‌شناسد."
                ),
                role="پروژه‌ی تک‌نفره — بک‌اند، پنل وب، اپ اندروید، سیستم طراحی و استقرار",
                problem=_P7_PROBLEM_FA,
                body=_P7_BODY_FA,
                outcome=(
                    "روی localand.ir زنده است: ۱۹۰ تست بک‌اند، ۲۱ تست Playwright برای پنل وب، "
                    "۹۵ عملیات API و اپ اندرویدی که خودش را به‌روز می‌کند."
                ),
            ),
            en=dict(
                title="Smart Studio — planning and producing Instagram content",
                summary=(
                    "A planning and production tool for an Instagram content strategist and "
                    "their team: an offline-first Android app, a web panel, and a Jalali "
                    "calendar that knows Iranian occasions."
                ),
                role="Solo project — backend, web panel, Android app, design system and deployment",
                problem=_P7_PROBLEM_EN,
                body=_P7_BODY_EN,
                outcome=(
                    "Live at localand.ir: 190 backend tests, 21 Playwright tests for the web "
                    "panel, 95 API operations, and an Android app that updates itself."
                ),
            ),
            de=dict(
                title="Smart Studio — Instagram-Inhalte planen und produzieren",
                summary=(
                    "Ein Planungs- und Produktionswerkzeug für Instagram-Content-Strategie und "
                    "das Team dahinter: Offline-first-Android-App, Web-Panel und ein "
                    "Jalali-Kalender, der iranische Anlässe kennt."
                ),
                role="Einzelprojekt — Backend, Web-Panel, Android-App, Designsystem und Deployment",
                problem=_P7_PROBLEM_DE,
                body=_P7_BODY_DE,
                outcome=(
                    "Live unter localand.ir: 190 Backend-Tests, 21 Playwright-Tests für das "
                    "Web-Panel, 95 API-Operationen und eine Android-App, die sich selbst "
                    "aktualisiert."
                ),
            ),
        )

        self._upsert_project(
            slug="salonyar",
            year=2026,
            order=2,
            stack=(
                "TypeScript, NestJS, Prisma, PostgreSQL, Redis, BullMQ, React, Vite, Tailwind, "
                "Bale Mini App, Docker, nginx"
            ),
            tag_slugs=("typescript", "react", "architecture", "databases", "performance", "bale"),
            tags=tags,
            fa=dict(
                title="سالن‌یار — نوبت‌دهی آرایشگاه، بدون نصب اپ",
                summary=(
                    "سامانه‌ی نوبت‌دهی چندمستأجری برای آرایشگاه‌ها: هر سالن یک لینک رزرو می‌گیرد "
                    "که در هر مرورگری باز می‌شود، به‌علاوه‌ی مینی‌اپ بله، پنل سالن و آرایشگر و "
                    "کنسول مدیر پلتفرم."
                ),
                role="پروژه‌ی تک‌نفره — طراحی محصول، بک‌اند، فرانت‌اند و استقرار",
                problem=_P8_PROBLEM_FA,
                body=_P8_BODY_FA,
                outcome=(
                    "آماده‌ی پایلوت پس از ۱۲ فاز: تست واحد و e2e، بودجه‌ی کارایی اجباری در build "
                    "(حدود ۸۸ کیلوبایت جاوااسکریپت gzip در صفحه‌ی اول) و کوئری‌های اصلی "
                    "اندازه‌گیری‌شده روی حدود ۴٫۴ میلیون نوبت."
                ),
            ),
            en=dict(
                title="Salonyar — salon booking with no app to install",
                summary=(
                    "A multi-tenant booking system for hair salons: each salon gets a public "
                    "booking link that opens in any browser, plus a Bale mini app, a salon and "
                    "stylist panel, and a platform console."
                ),
                role="Solo project — product design, backend, frontend and deployment",
                problem=_P8_PROBLEM_EN,
                body=_P8_BODY_EN,
                outcome=(
                    "Pilot-ready after 12 phases: unit and e2e tests, a performance budget the "
                    "build enforces (about 88 KB of gzipped JavaScript on first load), and the "
                    "main queries measured on about 4.4M bookings."
                ),
            ),
            de=dict(
                title="Salonyar — Terminbuchung für Friseursalons, ohne App",
                summary=(
                    "Ein mandantenfähiges Buchungssystem für Friseursalons: Jeder Salon bekommt "
                    "einen Buchungslink, der in jedem Browser öffnet, dazu eine Bale-Mini-App, "
                    "ein Salon-Panel und eine Plattform-Konsole."
                ),
                role="Einzelprojekt — Produktdesign, Backend, Frontend und Deployment",
                problem=_P8_PROBLEM_DE,
                body=_P8_BODY_DE,
                outcome=(
                    "Pilotreif nach 12 Phasen: Unit- und E2E-Tests, ein im Build erzwungenes "
                    "Performance-Budget (rund 88 KB JavaScript gzip beim ersten Laden) und die "
                    "Hauptabfragen an rund 4,4 Mio. Terminen gemessen."
                ),
            ),
        )

        self._upsert_project(
            slug="geekware",
            year=2026,
            order=3,
            stack=(
                "Node.js, Express 5, Server-side rendering, JSON file storage, Bale Bot API, PWA, "
                "Docker, Caddy"
            ),
            tag_slugs=("nodejs", "architecture", "bale"),
            tags=tags,
            demo_url="https://geekware.ir",
            fa=dict(
                title="گیک‌ویر — ثبت سفارش نرم‌افزار با متن یا ویس",
                summary=(
                    "سایت موبایل‌محور برای ثبت سفارش نرم‌افزار با متن یا پیام صوتی، که هر سفارش "
                    "را با دکمه‌های وضعیت به ربات بله می‌فرستد و با پنل ادمین همگام می‌ماند."
                ),
                role="طراحی، توسعه و راه‌اندازی کامل",
                problem=_P9_PROBLEM_FA,
                body=_P9_BODY_FA,
                outcome=(
                    "روی geekware.ir زنده است: حدود ۷ هزار خط جاوااسکریپت بدون فریم‌ورک فرانت، "
                    "که سفارش را از ثبت تا پرداخت و تحویل در یک مسیر بین سایت، دو ربات بله و پنل "
                    "نگه می‌دارد."
                ),
            ),
            en=dict(
                title="GeekWare — ordering software by text or voice",
                summary=(
                    "A mobile-first site for ordering software by text or voice message; each "
                    "order reaches a Bale bot with status buttons and stays in step with the "
                    "admin panel."
                ),
                role="Design, development and launch, end to end",
                problem=_P9_PROBLEM_EN,
                body=_P9_BODY_EN,
                outcome=(
                    "Live at geekware.ir: about 7k lines of JavaScript with no front-end "
                    "framework, keeping an order on one path from request to payment and "
                    "delivery across the site, two Bale bots and the panel."
                ),
            ),
            de=dict(
                title="GeekWare — Software bestellen per Text oder Sprachnachricht",
                summary=(
                    "Eine Mobile-first-Website, über die man Software per Text oder "
                    "Sprachnachricht bestellt; jede Bestellung landet mit Status-Buttons in "
                    "einem Bale-Bot und bleibt mit dem Admin-Panel synchron."
                ),
                role="Entwurf, Entwicklung und Launch, durchgehend",
                problem=_P9_PROBLEM_DE,
                body=_P9_BODY_DE,
                outcome=(
                    "Live unter geekware.ir: rund 7.000 Zeilen JavaScript ohne Frontend-"
                    "Framework, die eine Bestellung von der Anfrage bis zu Zahlung und Lieferung "
                    "auf einem Weg halten."
                ),
            ),
        )

        self._upsert_project(
            slug="podcast-workspace",
            year=2026,
            order=9,
            stack="Python 3.12, PySide6, SQLAlchemy, Alembic, SQLite FTS5, faster-whisper, ffmpeg",
            tag_slugs=("python", "architecture"),
            tags=tags,
            featured=False,
            repo_url="https://github.com/MehDiSDeveloper/content-manager",
            fa=dict(
                title="Podcast Workspace — میز کار آفلاین برای پادکستر",
                summary=(
                    "فضای کاری دسکتاپ و آفلاین برای یک پادکستر فارسی‌زبان: اپیزودها، فصل‌ها، "
                    "ویس‌ها، ایده‌ها، تگ‌ها، یادداشت‌های زمان‌دار و متن پیاده‌شده‌ی صدا، در یک جا."
                ),
                role="طراحی و پیاده‌سازی",
                problem=_P10_PROBLEM_FA,
                body=_P10_BODY_FA,
                outcome=(
                    "یک اپ ویندوز در نسخه‌ی 1.22 با کد باز روی GitHub — پیاده‌سازی متن و جستجوی "
                    "تمام‌متن، هر دو کاملاً روی خود دستگاه."
                ),
            ),
            en=dict(
                title="Podcast Workspace — an offline desk for a podcaster",
                summary=(
                    "An offline desktop workspace for a Persian-language podcaster: episodes, "
                    "seasons, voice notes, ideas, tags, timestamped notes and transcripts, in "
                    "one place."
                ),
                role="Design and implementation",
                problem=_P10_PROBLEM_EN,
                body=_P10_BODY_EN,
                outcome=(
                    "A Windows app at version 1.22, open source on GitHub — transcription and "
                    "full-text search both running entirely on the machine."
                ),
            ),
            de=dict(
                title="Podcast Workspace — ein Offline-Arbeitsplatz für Podcaster",
                summary=(
                    "Ein Offline-Desktop-Arbeitsplatz für einen persischsprachigen Podcaster: "
                    "Episoden, Staffeln, Sprachnotizen, Ideen, Tags, Notizen mit Zeitstempel "
                    "und Transkripte an einem Ort."
                ),
                role="Entwurf und Umsetzung",
                problem=_P10_PROBLEM_DE,
                body=_P10_BODY_DE,
                outcome=(
                    "Eine Windows-App in Version 1.22, quelloffen auf GitHub — Transkription "
                    "und Volltextsuche laufen vollständig auf dem Rechner."
                ),
            ),
        )

    def _upsert_project(
        self, *, slug, year, order, stack, tag_slugs, tags, fa, en, de,
        demo_url="", repo_url="", featured=True,
    ):
        # `featured` is what the home page shows, and it shows the first three
        # by `order`: the paid role and the two newest products. The libraries
        # live on /projects, which is where someone who wants to read code goes
        # looking for them.
        defaults = {
            "year": year,
            "order": order,
            "stack": stack,
            "demo_url": demo_url,
            "repo_url": repo_url,
            "is_featured": featured,
            "is_published": True,
        }
        for code, values in (("fa", fa), ("en", en), ("de", de)):
            for field, value in values.items():
                defaults[f"{field}_{code}"] = value
        project, _ = Project.objects.update_or_create(slug=slug, defaults=defaults)
        project.tags.set([tags[s] for s in tag_slugs])

    # ── experience ────────────────────────────────────────────────────────
    def _experience(self):
        # Work only. Delta Real Estate (2019) is left off: it is the weakest
        # entry, it is unevidenced, and a junior title from seven years ago
        # pulls the whole timeline down rather than lengthening it.
        rows = [
            dict(
                order=0,
                start=date(2023, 11, 1),
                end=date(2026, 3, 20),
                org_fa="اسمارت ایکس",
                org_en="Smart X",
                org_de="Smart X",
                role_fa="توسعه‌دهنده‌ی دات‌نت",
                role_en=".NET Developer",
                role_de=".NET-Entwickler",
                location_fa="تهران",
                location_en="Tehran",
                location_de="Teheran",
                description_fa=_E_SMARTX_FA,
                description_en=_E_SMARTX_EN,
                description_de=_E_SMARTX_DE,
            ),
            dict(
                order=1,
                start=date(2023, 1, 1),
                end=date(2026, 3, 1),
                org_fa="مستقل",
                org_en="Independent",
                org_de="Freiberuflich",
                role_fa="توسعه‌دهنده‌ی بک‌اند (فریلنس)",
                role_en="Backend Developer (freelance)",
                role_de="Backend-Entwickler (freiberuflich)",
                location_fa="پروژه‌ای",
                location_en="Project-based",
                location_de="Projektbasiert",
                description_fa=_E_FREELANCE_FA,
                description_en=_E_FREELANCE_EN,
                description_de=_E_FREELANCE_DE,
            ),
            dict(
                order=2,
                start=date(2021, 2, 1),
                end=date(2023, 3, 1),
                org_fa="بالا۲۴",
                org_en="bala24",
                org_de="bala24",
                role_fa="توسعه‌دهنده‌ی ارشد نرم‌افزار، فول‌استک (پاره‌وقت)",
                role_en="Senior Software Developer, full-stack (part-time)",
                role_de="Senior Software Developer, Full-Stack (Teilzeit)",
                location_fa="تهران",
                location_en="Tehran",
                location_de="Teheran",
                description_fa=_E_BALA_FA,
                description_en=_E_BALA_EN,
                description_de=_E_BALA_DE,
            ),
        ]
        for row in rows:
            Experience.objects.update_or_create(
                org_en=row["org_en"],
                role_en=row["role_en"],
                defaults={"kind": Experience.Kind.WORK, **row},
            )

    # ── posts ─────────────────────────────────────────────────────────────
    def _retire_projects(self):
        """Delete projects that used to be here and are not coming back.

        This site itself was one of them. A personal site listing itself as a
        portfolio piece says nothing a reader cannot already see — they are
        looking at it — and it pads a list that should only hold work worth
        reading about. Unlike a post, there is no slug worth preserving, so
        this deletes rather than unpublishes.
        """
        gone, _ = Project.objects.filter(slug__in=("montazeri-ir",)).delete()
        if gone:
            self.stdout.write(self.style.WARNING("removed retired project(s)"))

    def _retire_demo_posts(self):
        """Unpublish the placeholder posts rather than delete them.

        They are hidden because Mahdi did not write them. Deleting would lose
        the two slugs, which are worth keeping if he decides to write the real
        versions under the same URLs.
        """
        hidden = Post.objects.filter(
            slug__in=("permissions-are-a-query", "sqlite-in-production")
        ).update(is_published=False)
        if hidden:
            self.stdout.write(self.style.WARNING(f"unpublished {hidden} placeholder post(s)"))


# ── long copy ──────────────────────────────────────────────────────────────
# Kept at the bottom so the command reads as structure, not as prose.

# ── the services page ──────────────────────────────────────────────────────
_OFFER_EN = """\
### What I build

- **Web systems and admin panels** — from internal tools and CRMs to customer
  loyalty platforms.
- **Backends and APIs** for websites and mobile apps, in .NET or Python (FastAPI).
- **Performance and database work** — slow queries, ageing schemas, SQL Server
  and PostgreSQL at volume.
- **Migration and modernisation** from .NET Framework to modern .NET, without
  stopping the product.
- **Integrations** with outside services, webhooks, and AI through LLM APIs.

### How a project runs

1. **A first conversation** — what you need, the constraints and the timeline.
2. **A proposal and an agreement** — scope, delivery steps and price, settled
   before work starts.
3. **Built in short steps** — each one delivered where you can see and test it.
4. **Deployment and hand-over** — running on your server, with the source code
   and documentation.
"""

_OFFER_DE = """\
### Was ich baue

- **Websysteme und Admin-Oberflächen** — von internen Werkzeugen und CRMs bis zu
  Kundenbindungsplattformen.
- **Backends und APIs** für Websites und mobile Apps, mit .NET oder Python (FastAPI).
- **Performance- und Datenbankarbeit** — langsame Abfragen, gewachsene Schemata,
  SQL Server und PostgreSQL bei großen Datenmengen.
- **Migration und Modernisierung** von .NET Framework auf aktuelles .NET, ohne
  das Produkt anzuhalten.
- **Integrationen** mit externen Diensten, Webhooks und KI über LLM-APIs.

### So läuft ein Projekt ab

1. **Ein erstes Gespräch** — Bedarf, Rahmenbedingungen und Zeitplan.
2. **Angebot und Vereinbarung** — Umfang, Lieferschritte und Preis stehen vor
   Beginn fest.
3. **Umsetzung in kurzen Schritten** — jeder Schritt dort geliefert, wo Sie ihn
   sehen und testen können.
4. **Deployment und Übergabe** — lauffähig auf Ihrem Server, mit Quellcode und
   Dokumentation.
"""

_OFFER_FA = """\
### چه چیزهایی می‌سازم

- **سامانه‌ها و پنل‌های تحت وب** — از ابزارهای داخلی و CRM تا پلتفرم باشگاه
  مشتریان.
- **بک‌اند و API** برای وب‌سایت و اپلیکیشن موبایل، با دات‌نت یا پایتون (FastAPI).
- **بهینه‌سازی کارایی و پایگاه داده** — کوئری‌های کند، اسکیمای فرسوده، SQL Server
  و PostgreSQL در حجم بالا.
- **مهاجرت و نوسازی** از .NET Framework به نسخه‌های جدید دات‌نت، بدون متوقف‌کردن
  محصول.
- **یکپارچه‌سازی** با سرویس‌های بیرونی، وبهوک‌ها و هوش مصنوعی از طریق LLM API.

### یک پروژه چطور پیش می‌رود

1. **گفت‌وگوی اول** — نیاز، محدودیت‌ها و زمان‌بندی را روشن می‌کنیم.
2. **پیشنهاد و توافق** — دامنه‌ی کار، مراحل تحویل و هزینه پیش از شروع مشخص می‌شود.
3. **ساخت در گام‌های کوتاه** — هر مرحله جایی تحویل می‌شود که بتوانید ببینید و
   امتحانش کنید.
4. **استقرار و تحویل** — راه‌اندازی روی سرور شما، همراه با سورس‌کد و مستندات.
"""

_BIO_EN = """\
I am a backend engineer. For the last two and a half years I have worked on a
customer loyalty and CRM platform in Tehran holding roughly 25 million unique
customers, 800 million invoice records and over a billion SMS records — the
kind of system where a query plan nobody thought about becomes an incident.

### What that work actually was

- Modernised the product from .NET Framework 4.7 to .NET 8 and then .NET 9 — a
  real refactor rather than a lift-and-shift.
- Rebuilt large parts of the SQL Server schema on a live database of that size,
  which meant working through repeated locking and blocking problems and
  testing several migration strategies before committing to one.
- Systematic performance work across the application: page data loads improved
  by up to 30x in the worst cases.
- Led the move onto a consolidated architecture — vertical slice over Clean
  Architecture, split by domain, with RabbitMQ and gRPC between services. It
  was about 70% migrated when I left.
- Built customer segmentation (RFM among other methods), multi-tenancy, and the
  event-driven flows around them.
- Onboarded and mentored the two engineers who later joined the product.

### The second stack

Python is where my own time has gone for about two years: FastAPI, Pydantic,
SQLAlchemy, pytest, asyncio, and a good deal of LLM API integration for
freelance clients. It is a working second stack rather than an enterprise-scale
one, and I would rather say that plainly than be found out in a take-home. This
site is one of the results.

### Before software

I managed a real-estate agency, ran two startups that did not survive and a
computer-services business, and taught English. That is where the client
handling and the habit of owning a problem end to end come from.

### Practicalities

I am based in Tehran and work on-site, hybrid or by the project — and a project
I take on, I take from the first requirement to delivery. English is C1, and I
work comfortably in English-speaking teams. I have no notice period.
"""

_BIO_DE = """\
Ich bin Backend-Entwickler. In den letzten zweieinhalb Jahren habe ich in
Teheran an einer Kundenbindungs- und CRM-Plattform gearbeitet: rund 25
Millionen eindeutige Kunden, 800 Millionen Rechnungsdatensätze und über eine
Milliarde SMS-Datensätze — ein System, in dem ein übersehener Ausführungsplan
zur Störung wird.

### Woraus diese Arbeit bestand

- Modernisierung des Produkts von .NET Framework 4.7 auf .NET 8 und
  anschließend .NET 9 — ein echtes Refactoring, keine reine Portierung.
- Umbau großer Teile des SQL-Server-Schemas im laufenden Betrieb. Dabei traten
  wiederholt Sperr- und Blockierungsprobleme auf; mehrere Migrationsstrategien
  wurden getestet, bevor eine ausgewählt wurde.
- Systematische Performance-Arbeit an der gesamten Anwendung: Datenladezeiten
  der Seiten wurden in den schlechtesten Fällen bis zu 30-mal schneller.
- Federführung beim Umstieg auf eine konsolidierte Architektur — Vertical Slice
  auf Basis von Clean Architecture, nach Domänen geschnitten, mit RabbitMQ und
  gRPC zwischen den Services. Bei meinem Weggang war sie zu rund 70 % migriert.
- Kundensegmentierung (unter anderem RFM), Mandantenfähigkeit und die
  zugehörigen ereignisgesteuerten Abläufe.
- Einarbeitung und Mentoring der zwei Entwickler, die später zum Produkt kamen.

### Der zweite Stack

In Python steckt seit etwa zwei Jahren meine eigene Zeit: FastAPI, Pydantic,
SQLAlchemy, pytest, asyncio und einiges an LLM-API-Integration für
Freelance-Kunden. Das ist ein funktionierender zweiter Stack, aber kein
Enterprise-Maßstab — das sage ich lieber offen, als es in einer Take-Home-
Aufgabe sichtbar werden zu lassen. Diese Seite ist eines der Ergebnisse.

### Vor der Softwareentwicklung

Ich habe ein Immobilienbüro geleitet, zwei gescheiterte Startups und einen
IT-Dienstleistungsbetrieb geführt und Englisch unterrichtet. Daher kommen der
Umgang mit Kunden und die Gewohnheit, ein Problem von Anfang bis Ende zu
verantworten.

### Praktisches

Ich lebe in Teheran und arbeite vor Ort, hybrid oder projektbasiert — und ein
Projekt übernehme ich von der ersten Anforderung bis zur Übergabe. Englisch C1;
Deutsch A1 und im Aufbau — Arbeitssprache wäre zunächst Englisch. Ich habe
keine Kündigungsfrist.
"""

_BIO_FA = """\
مهندس بک‌اند هستم. دو سال و نیم گذشته را در تهران روی یک پلتفرم باشگاه مشتریان
و CRM کار کرده‌ام: حدود ۲۵ میلیون مشتری یکتا، ۸۰۰ میلیون رکورد فاکتور و بیش از
یک میلیارد رکورد پیامک — سیستمی که در آن یک execution plan که کسی به آن فکر
نکرده، تبدیل به حادثه می‌شود.

### آن کار دقیقاً چه بود

- مدرن‌سازی محصول از .NET Framework 4.7 به .NET 8 و سپس .NET 9 — یک بازنویسی
  واقعی، نه صرفاً جابه‌جایی.
- بازطراحی بخش‌های بزرگی از اسکیمای SQL Server روی پایگاه داده‌ی زنده‌ای در این
  ابعاد؛ که یعنی عبور از مشکلات پی‌درپی locking و blocking و آزمودن چند راهبرد
  مهاجرت پیش از انتخاب یکی.
- کار سیستماتیک روی کارایی در سراسر برنامه: زمان بارگذاری داده‌ی صفحات در
  بدترین موارد تا ۳۰ برابر بهتر شد.
- هدایت انتقال به معماری یکپارچه‌ی جدید — vertical slice روی Clean Architecture،
  تفکیک‌شده بر اساس دامنه، با RabbitMQ و gRPC میان سرویس‌ها. هنگام خروج من حدود
  ۷۰٪ از این مسیر طی شده بود.
- بخش‌بندی مشتریان (از جمله با روش RFM)، multi-tenancy و جریان‌های رویدادمحور
  پیرامون آن‌ها.
- آنبوردینگ و منتورینگ دو مهندسی که بعدتر به محصول اضافه شدند.

### استک دوم

پایتون جایی است که وقت شخصی‌ام حدود دو سال است آنجا می‌رود: FastAPI، Pydantic،
SQLAlchemy، pytest، asyncio و مقدار قابل توجهی یکپارچه‌سازی با LLM API برای
مشتریان فریلنس. این یک استک دوم کارآمد است، نه در مقیاس enterprise — و ترجیح
می‌دهم همین را صریح بگویم تا در یک تمرین فنی معلوم شود. این سایت یکی از
نتیجه‌های همان مسیر است.

### پیش از نرم‌افزار

یک آژانس املاک را مدیریت کرده‌ام، دو استارتاپ که دوام نیاوردند و یک کسب‌وکار
خدمات کامپیوتری را اداره کرده‌ام و انگلیسی تدریس کرده‌ام. توانایی کار با
مشتری و عادت به مالکیت مسئله از ابتدا تا انتها از همان‌جا می‌آید.

### نکات عملی

ساکن تهرانم و به‌صورت حضوری، هیبریدی یا پروژه‌ای همکاری می‌کنم؛ و پروژه‌ای را
که به عهده می‌گیرم، از تحلیل نیاز تا تحویل پیش می‌برم. انگلیسی‌ام در سطح C1 است
و در تیم‌های انگلیسی‌زبان راحت کار می‌کنم. امکان شروع همکاری بدون دوره‌ی انتظار
را دارم.
"""

# ── project 1: the loyalty platform ────────────────────────────────────────
_P1_PROBLEM_EN = """\
A loyalty and CRM platform that had grown for years on .NET Framework 4.7 and a
SQL Server database it had long outgrown. Roughly 25 million unique customers
(about 60 million non-unique records), 800 million invoice records and more
than a billion SMS records sat behind screens that took long enough to load
that people stopped opening them.

The product could not be paused and rewritten. Whatever changed had to change
underneath a system that was in daily use by businesses and their customers.
"""

_P1_BODY_EN = """\
I was the primary developer on the product and owned most of the architectural
decisions and the approach to implementing them.

**Modernisation.** .NET Framework 4.7 to .NET 8, then to .NET 9. A refactor
rather than a lift-and-shift: the point was to be able to change the thing
afterwards, not only to be on a supported runtime.

**Performance.** Systematic work across the application rather than a hunt for
one hot spot. Page data loads improved by up to 30x in the worst cases — mostly
by fixing what the queries and the schema were asking the database to do, not
by adding caches on top of them.

**Architecture.** In the final phase I moved the company's products, the
loyalty club first, onto a consolidated architecture: vertical slice over Clean
Architecture, split by domain, with RabbitMQ for messaging and gRPC between
services. It is a domain-split modular architecture with messaging rather than
microservices at scale, and about 70% of the migration was done when I left.

**Features.** Customer segmentation using several methods including RFM,
multi-tenancy, and the event-driven flows underneath both. Tests were written
at unit, integration and UI level.

Two other engineers joined the product later; I onboarded and mentored them.
"""

_P1_PROBLEM_DE = """\
Eine Loyalty- und CRM-Plattform, die über Jahre auf .NET Framework 4.7 und
einer SQL-Server-Datenbank gewachsen war, der sie längst entwachsen war. Hinter
den Oberflächen lagen rund 25 Millionen eindeutige Kunden (etwa 60 Millionen
nicht eindeutige Datensätze), 800 Millionen Rechnungsdatensätze und über eine
Milliarde SMS-Datensätze — und die Seiten luden so langsam, dass sie kaum noch
geöffnet wurden.

Das Produkt konnte nicht angehalten und neu geschrieben werden. Jede Änderung
musste unter einem System stattfinden, das täglich von Unternehmen und deren
Kunden genutzt wurde.
"""

_P1_BODY_DE = """\
Ich war Hauptentwickler des Produkts und habe die architektonischen
Entscheidungen sowie die Umsetzung weitgehend verantwortet.

**Modernisierung.** Von .NET Framework 4.7 auf .NET 8, dann auf .NET 9. Ein
Refactoring statt einer reinen Portierung: Ziel war, das System danach ändern
zu können, nicht nur auf einer unterstützten Runtime zu laufen.

**Performance.** Systematische Arbeit an der gesamten Anwendung statt der Suche
nach einem einzelnen Hotspot. Datenladezeiten der Seiten wurden in den
schlechtesten Fällen bis zu 30-mal schneller — vor allem, indem korrigiert
wurde, was Queries und Schema von der Datenbank verlangten, und nicht durch
zusätzliche Caches darüber.

**Architektur.** In der letzten Phase habe ich die Produkte des Unternehmens,
zuerst den Kundenclub, auf eine konsolidierte Architektur umgestellt: Vertical
Slice auf Basis von Clean Architecture, nach Domänen geschnitten, mit RabbitMQ
für Messaging und gRPC zwischen den Services. Es handelt sich um eine modulare,
nach Domänen geschnittene Architektur mit Messaging, nicht um Microservices im
großen Maßstab; bei meinem Weggang waren rund 70 % migriert.

**Fachlichkeit.** Kundensegmentierung mit mehreren Verfahren, unter anderem
RFM, Mandantenfähigkeit und die darunterliegenden ereignisgesteuerten Abläufe.
Tests wurden auf Unit-, Integrations- und UI-Ebene geschrieben.

Zwei weitere Entwickler kamen später zum Produkt; ich habe sie eingearbeitet
und betreut.
"""

_P1_PROBLEM_FA = """\
پلتفرمی برای وفاداری مشتری و CRM که سال‌ها روی .NET Framework 4.7 و پایگاه
داده‌ای در SQL Server رشد کرده بود که مدت‌ها بود از آن بزرگ‌تر شده بود. پشت
صفحه‌ها حدود ۲۵ میلیون مشتری یکتا (نزدیک ۶۰ میلیون رکورد غیریکتا)، ۸۰۰ میلیون
رکورد فاکتور و بیش از یک میلیارد رکورد پیامک قرار داشت — و صفحه‌ها آن‌قدر کند
باز می‌شدند که کاربران دیگر سراغشان نمی‌رفتند.

محصول را نمی‌شد متوقف کرد و از نو نوشت. هر تغییری باید زیر سیستمی اتفاق می‌افتاد
که هر روز توسط کسب‌وکارها و مشتریانشان استفاده می‌شد.
"""

_P1_BODY_FA = """\
توسعه‌دهنده‌ی اصلی محصول بودم و بخش عمده‌ی تصمیم‌های معماری و شیوه‌ی پیاده‌سازی
آن‌ها بر عهده‌ی من بود.

**مدرن‌سازی.** از .NET Framework 4.7 به .NET 8 و سپس .NET 9. یک بازنویسی واقعی،
نه فقط جابه‌جایی: هدف این بود که بعد از آن بشود سیستم را تغییر داد، نه صرفاً
اینکه روی یک runtime پشتیبانی‌شده اجرا شود.

**کارایی.** کار سیستماتیک روی کل برنامه، نه شکار یک نقطه‌ی داغ. زمان بارگذاری
داده‌ی صفحات در بدترین موارد تا ۳۰ برابر بهتر شد — عمدتاً با اصلاح آنچه
کوئری‌ها و اسکیما از پایگاه داده می‌خواستند، نه با افزودن کش روی آن‌ها.

**معماری.** در فاز پایانی، محصولات شرکت و پیش از همه باشگاه مشتریان را به یک
معماری یکپارچه منتقل کردم: vertical slice روی Clean Architecture، تفکیک‌شده بر
اساس دامنه، با RabbitMQ برای پیام‌رسانی و gRPC میان سرویس‌ها. این یک معماری
ماژولار دامنه‌محور با پیام‌رسانی است، نه میکروسرویس در مقیاس بزرگ؛ هنگام خروج
من حدود ۷۰٪ از مهاجرت انجام شده بود.

**قابلیت‌ها.** بخش‌بندی مشتریان با چند روش از جمله RFM، multi-tenancy و
جریان‌های رویدادمحور زیر هر دو. تست‌ها در سطح unit، integration و UI نوشته شدند.

دو مهندس دیگر بعدتر به محصول اضافه شدند؛ آنبوردینگ و منتورینگشان با من بود.
"""

# ── project 2: the database ────────────────────────────────────────────────
_P2_PROBLEM_EN = """\
The schema underneath the loyalty platform had to change: large, structural
refactors, on tables holding 800 million invoice records, in a database that
could not be taken offline for the length of time the obvious approach needed.

On a small database this is an afternoon. At this size, the schema change is
the easy half. The hard half is that every strategy for applying it holds locks
somewhere, and the wrong lock in the wrong place stops the product.
"""

_P2_BODY_EN = """\
The work was mostly not writing DDL. It was finding a way to apply it.

Early attempts ran into repeated locking and blocking — the migration would
start, take a lock that the application also wanted, and the two would wait on
each other while the product degraded. I worked through several migration
strategies, testing each against the real data volume rather than against a
scaled-down copy, since the behaviour that matters here only appears at size.

What that involved:

- Reading what the database was actually doing during a migration, from the
  system tables, rather than guessing from the outside.
- Splitting changes into steps that each hold their locks briefly, instead of
  one statement that holds one lock for a long time.
- Backfilling and switching over separately, so the long-running part of the
  work never sits in the path of a user request.
- Accepting a slower migration in exchange for a shorter blocking window, which
  is the trade nearly every version of this problem comes down to.

This is the piece of work I would most like to be asked about. It is specific,
it went wrong before it went right, and I can walk through why each rejected
strategy was rejected.
"""

_P2_PROBLEM_DE = """\
Das Schema unter der Loyalty-Plattform musste sich ändern: große, strukturelle
Refactorings an Tabellen mit 800 Millionen Rechnungsdatensätzen, in einer
Datenbank, die sich nicht so lange offline nehmen ließ, wie der naheliegende
Weg gebraucht hätte.

Bei einer kleinen Datenbank ist das ein Nachmittag. In dieser Größenordnung ist
die Schemaänderung die leichte Hälfte. Die schwierige ist, dass jede Strategie
irgendwo Sperren hält — und die falsche Sperre an der falschen Stelle legt das
Produkt lahm.
"""

_P2_BODY_DE = """\
Der Aufwand lag kaum im Schreiben des DDL, sondern darin, einen Weg zu finden,
es anzuwenden.

Erste Versuche liefen wiederholt in Sperr- und Blockierungsprobleme: Die
Migration nahm eine Sperre, die die Anwendung ebenfalls brauchte, beide warteten
aufeinander, und das Produkt wurde langsam. Ich habe mehrere
Migrationsstrategien durchgearbeitet und jede gegen das reale Datenvolumen
getestet statt gegen eine verkleinerte Kopie — das relevante Verhalten zeigt
sich erst in dieser Größe.

Konkret hieß das:

- Aus den Systemtabellen lesen, was die Datenbank während einer Migration
  tatsächlich tut, statt es von außen zu vermuten.
- Änderungen in Schritte zerlegen, die ihre Sperren jeweils nur kurz halten,
  statt eines Statements mit einer langen Sperre.
- Backfill und Umschaltung trennen, damit der langlaufende Teil nie im Pfad
  einer Benutzeranfrage liegt.
- Eine langsamere Migration gegen ein kürzeres Blocking-Fenster eintauschen —
  worauf fast jede Variante dieses Problems hinausläuft.

Das ist die Arbeit, zu der ich am liebsten befragt werde. Sie ist konkret, sie
ist erst schiefgegangen und dann gelungen, und ich kann zu jeder verworfenen
Strategie sagen, warum sie verworfen wurde.
"""

_P2_PROBLEM_FA = """\
اسکیمای زیر پلتفرم وفاداری باید تغییر می‌کرد: بازطراحی‌های بزرگ و ساختاری روی
جدول‌هایی با ۸۰۰ میلیون رکورد فاکتور، در پایگاه داده‌ای که نمی‌شد به اندازه‌ی
زمانی که راه‌حل بدیهی لازم داشت آفلاین کرد.

روی یک پایگاه داده‌ی کوچک این کار یک بعدازظهر است. در این ابعاد، تغییر اسکیما
نیمه‌ی آسان ماجراست. نیمه‌ی سخت این است که هر راهبردی برای اعمال آن، جایی قفل
می‌گیرد — و قفل اشتباه در جای اشتباه، محصول را می‌خواباند.

"""

_P2_BODY_FA = """\
بخش عمده‌ی کار نوشتن DDL نبود؛ پیدا کردن راهی برای اعمال کردن آن بود.

تلاش‌های اول پی‌درپی به locking و blocking خوردند: مهاجرت شروع می‌شد، قفلی
می‌گرفت که برنامه هم آن را می‌خواست، و هر دو منتظر هم می‌ماندند در حالی که
محصول کند می‌شد. چند راهبرد مهاجرت را یکی‌یکی آزمودم، هر کدام را روی حجم واقعی
داده و نه یک کپی کوچک‌شده — چون رفتاری که اینجا اهمیت دارد فقط در همین ابعاد
خودش را نشان می‌دهد.

آنچه این کار در عمل شامل شد:

- خواندن اینکه پایگاه داده حین مهاجرت واقعاً چه می‌کند، از دل system tableها،
  نه حدس زدن از بیرون.
- شکستن تغییرات به گام‌هایی که هر کدام قفلشان را کوتاه نگه می‌دارند، به‌جای یک
  دستور که یک قفل را طولانی نگه می‌دارد.
- جدا کردن backfill از switchover، تا بخش طولانی کار هیچ‌وقت سر راه یک درخواست
  کاربر نباشد.
- پذیرفتن مهاجرت کندتر در ازای پنجره‌ی blocking کوتاه‌تر — همان معامله‌ای که
  تقریباً هر نسخه‌ای از این مسئله به آن ختم می‌شود.

این همان کاری است که بیش از همه دوست دارم درباره‌اش پرسیده شوم. مشخص است، اول
شکست خورد و بعد جواب داد، و می‌توانم برای هر راهبرد کنارگذاشته‌شده توضیح بدهم
چرا کنار گذاشته شد.
"""

# ── project 3: this site ───────────────────────────────────────────────────
_P3_PROBLEM_EN = """\
Habit trackers assume a Gregorian month and a Latin, left-to-right interface,
and an Iranian user lives in neither. A monthly quota — "twelve sessions this
month" — has to reset on the first of Farvardin, not the first of March; a
Gregorian month straddles two Jalali ones, so bucketing by the Gregorian month
splits one member's quota across two periods and nobody can tell why their
count halved.
"""

_P3_BODY_EN = """\
A FastAPI application with a server-rendered Jinja2 front end, and a Capacitor
shell around the deployed site for Android.

**The calendar goes all the way down.** Occurrence keys are Jalali, period
boundaries are real Jalali boundaries, and weeks start on Saturday. The
conversion is arithmetic with no dependency, and its test walks all ~44,000 days
from 1300 to 1420 against ICU's Persian calendar — the same authority the
browser formats with, so the server cannot bucket a date into a month the UI
labels differently.

**"Today" is a question about the member, not the server.** Each enrolment
carries its own timezone, so the same UTC instant yields different occurrence
keys for two people in different zones. That is why the occurrence engine is a
pure module with no database and no routes: it can be tested exhaustively, and
it is. Check-ins are idempotent through a unique constraint — on a phone with
poor signal a retry is the normal case, not an error.

**Authorization is a SQL predicate, not an `if`.** Object access is four
composed `WHERE` clauses, so a row the caller may not see never loads at all and
a miss falls out of the query as "no such row" rather than as a decision taken
after the fact. Four role systems — app, challenge, group, course — are
deliberately never merged, and the suite asserts what an operator *cannot* do:
admin grants moderation and deletion and not `CHALLENGE_EDIT`, because changing
what state a challenge is in is moderation and changing what it *says* is
authorship.

**Nothing that can be derived is stored.** Streaks are recomputed by walking the
expected occurrences backwards; there is no `+= 1` anywhere in the codebase.
Leaderboard rank is counted live, because a monotonic counter would rank an
abandoned challenge above a live one.

Web Push is written straight against RFC 8291 over RFC 8188 with an RFC 8292
VAPID assertion — about a hundred lines, one dependency instead of three. The
ordering mattered more than the crypto: a push is dispatched only once the
transaction is known to have ended, because there is no un-sending a
notification that reached a lock screen before its commit.

No bundler, no framework, no `node_modules` in the web app. The service worker
caches static assets and refuses to cache a page of HTML — every screen computes
its rings and counters live, and a cached page is a page of confidently wrong
numbers. The repository is private because this is a product I intend to run;
the architecture is documented and I am happy to walk through any of it.
"""

_P3_PROBLEM_DE = """\
Habit-Tracker setzen einen gregorianischen Monat und eine lateinische Oberfläche
von links nach rechts voraus — iranische Nutzer leben in beidem nicht. Ein
Monatskontingent („zwölf Einheiten diesen Monat") muss am 1. Farvardin
zurückgesetzt werden, nicht am 1. März. Ein gregorianischer Monat überlappt zwei
Jalali-Monate: Wer nach dem gregorianischen Monat gruppiert, zerlegt das
Kontingent eines Mitglieds in zwei Perioden, und niemand versteht, warum sich
der Zähler halbiert hat.
"""

_P3_BODY_DE = """\
Eine FastAPI-Anwendung mit serverseitig gerendertem Jinja2-Frontend und einer
Capacitor-Hülle um die deployte Seite für Android.

**Der Kalender reicht bis ganz nach unten.** Occurrence-Schlüssel sind Jalali,
Periodengrenzen sind echte Jalali-Grenzen, und Wochen beginnen am Samstag. Die
Umrechnung ist reine Arithmetik ohne Abhängigkeit, und ihr Test läuft alle rund
44.000 Tage von 1300 bis 1420 gegen den persischen Kalender von ICU — dieselbe
Instanz, mit der der Browser formatiert. Der Server kann ein Datum also nicht in
einen Monat einsortieren, den die Oberfläche anders beschriftet.

**„Heute" ist eine Frage an das Mitglied, nicht an den Server.** Jede Teilnahme
trägt ihre eigene Zeitzone; derselbe UTC-Zeitpunkt ergibt für zwei Menschen in
verschiedenen Zonen verschiedene Occurrence-Schlüssel. Deshalb ist die
Occurrence-Engine ein reines Modul ohne Datenbank und ohne Routen — so lässt sie
sich erschöpfend testen, und genau das passiert. Check-ins sind über einen
Unique-Constraint idempotent: Auf einem Handy mit schlechtem Empfang ist ein
Retry der Normalfall, kein Fehler.

**Autorisierung ist ein SQL-Prädikat, kein `if`.** Objektzugriff sind vier
zusammengesetzte `WHERE`-Klauseln; eine Zeile, die der Aufrufer nicht sehen
darf, wird gar nicht erst geladen, und ein Treffer fehlt schlicht im
Abfrageergebnis. Vier Rollensysteme — App, Challenge, Gruppe, Kurs — werden
bewusst nie zusammengelegt, und die Tests halten fest, was ein Operator *nicht*
darf: Admin erlaubt Moderation und Löschen, aber nicht `CHALLENGE_EDIT`. Den
Zustand einer Challenge zu ändern ist Moderation; zu ändern, was sie *sagt*, ist
Autorschaft.

**Was sich herleiten lässt, wird nicht gespeichert.** Streaks werden berechnet,
indem die erwarteten Occurrences rückwärts durchlaufen werden; im ganzen Code
steht kein `+= 1`. Der Rang in der Rangliste wird live gezählt, weil ein
monoton steigender Zähler eine aufgegebene Challenge über eine aktive stellen
würde.

Web Push ist direkt gegen RFC 8291 über RFC 8188 mit einer VAPID-Assertion nach
RFC 8292 geschrieben — rund hundert Zeilen, eine Abhängigkeit statt dreier.
Wichtiger als die Kryptografie war die Reihenfolge: Eine Push-Nachricht geht
erst raus, wenn die Transaktion nachweislich beendet ist — eine Benachrichtigung
auf einem Sperrbildschirm lässt sich nicht zurückholen.

Kein Bundler, kein Framework, kein `node_modules` in der Web-App. Der Service
Worker cacht statische Dateien und verweigert das Cachen von HTML-Seiten: Jeder
Screen berechnet seine Ringe und Zähler live, und eine gecachte Seite ist eine
Seite mit selbstbewusst falschen Zahlen. Das Repository ist privat, weil ich das
Produkt betreiben will; die Architektur ist dokumentiert, und ich gehe sie gern
im Detail durch.
"""

_P3_PROBLEM_FA = """\
ردیاب‌های عادت فرض می‌کنند ماه میلادی است و رابط، لاتین و چپ‌به‌راست — و کاربر
ایرانی در هیچ‌کدام زندگی نمی‌کند. سهمیه‌ی ماهانه («این ماه دوازده جلسه») باید
اول فروردین صفر شود، نه اول مارس. یک ماه میلادی روی دو ماه جلالی می‌افتد؛ پس
اگر بر اساس ماه میلادی دسته‌بندی کنی، سهمیه‌ی یک نفر بین دو دوره تکه می‌شود و
هیچ‌کس نمی‌فهمد چرا شمارشش نصف شده است.
"""

_P3_BODY_FA = """\
یک اپلیکیشن FastAPI با فرانت‌اند Jinja2 که سمت سرور رندر می‌شود، و یک پوسته‌ی
Capacitor دور همان سایتِ دیپلوی‌شده برای اندروید.

**تقویم تا ته پایین می‌رود.** کلید هر occurrence جلالی است، مرزهای دوره مرزهای
واقعی جلالی‌اند، و هفته شنبه شروع می‌شود. تبدیل، حساب ساده است و هیچ وابستگی
ندارد؛ تستش تمام ~۴۴٬۰۰۰ روزِ ۱۳۰۰ تا ۱۴۲۰ را با تقویم فارسی ICU مقایسه می‌کند
— همان مرجعی که مرورگر با آن فرمت می‌کند. پس سرور نمی‌تواند تاریخی را در ماهی
بگذارد که رابط کاربری اسم دیگری رویش می‌گذارد.

**«امروز» سؤالی درباره‌ی عضو است، نه درباره‌ی ساعتِ سرور.** هر ثبت‌نام منطقه‌ی
زمانی خودش را دارد؛ یک لحظه‌ی UTC یکسان برای دو نفر در دو منطقه دو کلید متفاوت
می‌دهد. برای همین موتور occurrence یک ماژول خالص است، بدون دیتابیس و بدون
route: می‌شود کامل تستش کرد، و شده. ثبت انجام، با یک unique constraint idempotent
است — روی گوشی با آنتن ضعیف، تلاش دوباره حالت عادی است نه خطا.

**مجوز یک گزاره‌ی SQL است، نه یک `if`.** دسترسی به هر شیء چهار `WHERE` ترکیب‌شده
است؛ ردیفی که کاربر حق دیدنش را ندارد اصلاً بارگذاری نمی‌شود و نبودنش از دل
کوئری درمی‌آید، نه از تصمیمی که بعد از خواندن گرفته شده باشد. چهار نظام نقش —
اپ، چالش، گروه، دوره — عمداً هرگز ادغام نشده‌اند و تست‌ها روی چیزی تأکید می‌کنند
که یک ادمین *نمی‌تواند* انجام دهد: ادمین حق مدیریت و حذف دارد و حق
`CHALLENGE_EDIT` ندارد، چون عوض‌کردن وضعیت یک چالش مدیریت است و عوض‌کردن
*حرفش* تألیف.

**هر چیزی که بشود محاسبه کرد، ذخیره نمی‌شود.** استریک با پیمودن رو به عقبِ
occurrenceهای مورد انتظار دوباره حساب می‌شود؛ در کل کد یک `+= 1` وجود ندارد.
رتبه‌ی جدول هم زنده شمرده می‌شود، چون یک شمارنده‌ی همیشه‌صعودی چالشِ رهاشده را
بالاتر از چالشِ زنده می‌نشاند.

Web Push مستقیم روی RFC 8291 و RFC 8188 با VAPID مطابق RFC 8292 نوشته شده —
حدود صد خط، یک وابستگی به‌جای سه تا. مهم‌تر از رمزنگاری، ترتیب بود: نوتیفیکیشن
فقط وقتی فرستاده می‌شود که تراکنش قطعاً تمام شده باشد، چون نوتیفیکیشنی که روی
صفحه‌قفل نشسته پس گرفته نمی‌شود.

نه باندلر، نه فریم‌ورک، نه `node_modules` در وب‌اپ. سرویس‌ورکر فایل‌های استاتیک
را کش می‌کند و از کش‌کردن صفحه‌ی HTML سر باز می‌زند: هر صفحه حلقه‌ها و
شمارنده‌هایش را زنده حساب می‌کند و یک صفحه‌ی کش‌شده یعنی یک صفحه عددِ غلط
که مطمئن به نظر می‌رسند. مخزن کد خصوصی است، چون این محصولی است که می‌خواهم اجرایش کنم؛
معماری‌اش مستند است و با کمال میل هر بخشش را توضیح می‌دهم.
"""

_P4_PROBLEM_EN = """\
Since January 2025 receiving a structured electronic invoice is mandatory for
German B2B, and issuing one is being phased in. In practice an invoice has to
satisfy three layers at once: the EN 16931 semantic model, a national narrowing
of it (XRechnung 3.0 and its `BR-DE-*` rules), and a syntax — the same model
written as either UBL 2.1 or CII D16B, with different element names for every
field. It can arrive as bare XML or as a hybrid PDF, in whichever syntax the
sender preferred. Getting it wrong is not a soft failure: the invoice is
rejected at the portal by an automated validator quoting a rule identifier like
`BR-CO-13`, and you need to know what that means and where it happened.
"""

_P4_BODY_EN = """\
A layered package whose dependencies point one way only. `domain` reads no file,
opens no socket, parses no XML and looks at no clock; `syntax`, `validation` and
`pdf` sit above it, and the CLI and the HTTP service are thin shells over both.

**Rules run against the model, not against XPath.** Most tooling here wraps the
official Schematron, which is written per syntax — so the same rule exists twice
and an invoice can only be checked after it has been serialised. A rule here is
a small pure function from `Invoice` to the problems it finds. One rule serves
both UBL and CII, an invoice can be validated *before* it exists as a document,
and `GET /v1/rules` is generated from the rules rather than being a second list
to keep in step.

**Mandatory-ness is a property of the standard, not of the type system.**
`Invoice.number` is `str | None` even though `BR-02` requires it: to report
`BR-02` you must first be able to hold a document that has no invoice number. A
model that refused could only raise a parse error, which tells a caller nothing
about which rule broke. The same reasoning keeps codes as plain strings — an
invoice carrying `"XX"` as a VAT category has to survive long enough to be
reported as `BR-CL-18`.

**Money is `Decimal`, and a `float` is refused rather than coerced.** An invoice
one cent out is a rejected invoice. The subtler reason: a `Decimal` remembers
the scale it was written with, which is exactly what the `BR-DEC-*` rules ask
about, so amounts are parsed from the lexical form and never normalised —
normalising would erase the defect those rules exist to find.

**Each syntax is one module holding both directions.** The mapping between a
business term and an element path is one fact; splitting the writer and the
reader across two files is how they come to disagree. The round-trip tests
compare the whole model rather than a handful of fields, and earned their keep
immediately by catching a field the CII writer dropped and another lost on a UBL
credit note.

Every input is treated as hostile: `<!DOCTYPE>` is refused before parsing, no
network and no DTD, byte/depth/element ceilings, and one configured call to
`etree.fromstring` in the whole package. Errors are RFC 9457 problem details,
and the two conventions are deliberate — generation refuses to write a
non-conformant invoice, and validation never refuses: finding fifty errors is a
successful request, so it is `200` with `valid: false`.

The known limitations are named rather than left to be discovered — the rule
families that are not implemented, the absence of XSD validation, no Peppol —
because a validator that quietly passes what it did not check is worse than no
validator.
"""

_P4_PROBLEM_DE = """\
Seit Januar 2025 ist der Empfang strukturierter elektronischer Rechnungen im
deutschen B2B Pflicht, das Ausstellen wird schrittweise verpflichtend. In der
Praxis muss eine Rechnung drei Schichten gleichzeitig erfüllen: das semantische
Modell EN 16931, dessen nationale Einschränkung (XRechnung 3.0 mit den
`BR-DE-*`-Regeln) und eine Syntax — dasselbe Modell, geschrieben entweder als
UBL 2.1 oder als CII D16B, mit anderen Elementnamen für jedes einzelne Feld.
Ankommen kann sie als reines XML oder als hybrides PDF, in der Syntax, die der
Absender gewählt hat. Ein Fehler ist dabei kein weiches Scheitern: Die Rechnung
wird am Portal von einem automatischen Prüfer abgelehnt, der eine Regel-Kennung
wie `BR-CO-13` nennt — und man muss wissen, was das heißt und wo es passiert
ist.
"""

_P4_BODY_DE = """\
Ein geschichtetes Paket, dessen Abhängigkeiten nur in eine Richtung zeigen.
`domain` liest keine Datei, öffnet keinen Socket, parst kein XML und schaut auf
keine Uhr; `syntax`, `validation` und `pdf` liegen darüber, CLI und HTTP-Service
sind dünne Hüllen.

**Regeln laufen gegen das Modell, nicht gegen XPath.** Die meisten Werkzeuge
hier kapseln das offizielle Schematron, das pro Syntax geschrieben ist — dieselbe
Regel existiert also zweimal, und geprüft werden kann erst nach dem
Serialisieren. Hier ist eine Regel eine kleine reine Funktion von `Invoice` auf
die gefundenen Probleme. Eine Regel bedient UBL und CII, eine Rechnung lässt
sich prüfen, *bevor* es das Dokument gibt, und `GET /v1/rules` wird aus den
Regeln erzeugt statt als zweite Liste gepflegt.

**Pflichtfeld zu sein ist eine Eigenschaft der Norm, nicht des Typsystems.**
`Invoice.number` ist `str | None`, obwohl `BR-02` es verlangt: Um `BR-02` melden
zu können, muss man ein Dokument ohne Rechnungsnummer überhaupt halten können.
Ein Modell, das sich weigert, könnte nur einen Parse-Fehler werfen — und der
sagt nichts darüber, welche Regel gebrochen wurde. Aus demselben Grund sind
Codes einfache Strings: Eine Rechnung mit `"XX"` als Steuerkategorie muss lange
genug überleben, um als `BR-CL-18` gemeldet zu werden.

**Beträge sind `Decimal`, ein `float` wird abgelehnt statt umgewandelt.** Eine
Rechnung, die einen Cent danebenliegt, ist eine abgelehnte Rechnung. Der
feinere Grund: Ein `Decimal` merkt sich die Stellenzahl, mit der es geschrieben
wurde — genau das fragen die `BR-DEC-*`-Regeln ab. Beträge werden deshalb aus
der lexikalischen Form gelesen und nie normalisiert; Normalisieren würde den
Defekt löschen, den diese Regeln finden sollen.

**Jede Syntax ist ein Modul mit beiden Richtungen.** Die Zuordnung von
Geschäftsbegriff zu Elementpfad ist *eine* Tatsache; Schreiber und Leser auf
zwei Dateien zu verteilen ist der Weg, auf dem sie auseinanderlaufen. Die
Round-Trip-Tests vergleichen das ganze Modell und haben sich sofort bezahlt
gemacht: Sie fanden ein Feld, das der CII-Writer verlor, und eines, das bei
einer UBL-Gutschrift verschwand.

Jede Eingabe gilt als feindlich: `<!DOCTYPE>` wird vor dem Parsen abgelehnt,
kein Netzwerk, keine DTD, Grenzen für Bytes, Tiefe und Elementzahl, und genau
ein konfigurierter `etree.fromstring`-Aufruf im ganzen Paket. Fehler sind
Problem Details nach RFC 9457, und zwei Konventionen sind bewusst gesetzt: Die
Erzeugung weigert sich, eine nicht konforme Rechnung zu schreiben — die Prüfung
weigert sich nie. Fünfzig gefundene Fehler sind eine erfolgreiche Anfrage, also
`200` mit `valid: false`.

Die bekannten Grenzen sind benannt statt dem Zufall überlassen — die nicht
umgesetzten Regelfamilien, keine XSD-Prüfung, kein Peppol. Ein Prüfer, der still
durchwinkt, was er nie geprüft hat, ist schlimmer als gar keiner.
"""

_P4_PROBLEM_FA = """\
از ژانویه‌ی ۲۰۲۵ دریافت فاکتور الکترونیکی ساختاریافته در B2B آلمان اجباری شده و
صدورش هم مرحله‌به‌مرحله اجباری می‌شود. عملاً هر فاکتور باید هم‌زمان سه لایه را
راضی کند: مدل معنایی EN 16931، تنگ‌ترکردن ملی‌اش (XRechnung 3.0 و قواعد
`BR-DE-*`)، و یک نحو — همان مدل، نوشته‌شده یا به UBL 2.1 یا به CII D16B، با
نام عنصر متفاوت برای تک‌تک فیلدها. فاکتور ممکن است XML خام باشد یا PDF هیبرید،
به هر نحوی که فرستنده پسندیده. اشتباه‌کردن هم شکست نرمی نیست: فاکتور در پورتال
توسط یک اعتبارسنج خودکار رد می‌شود که شناسه‌ی قاعده‌ای مثل `BR-CO-13` را جلوی
تو می‌گذارد، و باید بدانی یعنی چه و کجا اتفاق افتاده.
"""

_P4_BODY_FA = """\
یک پکیج لایه‌لایه که وابستگی‌هایش فقط یک‌طرفه‌اند. `domain` هیچ فایلی نمی‌خواند،
هیچ سوکتی باز نمی‌کند، هیچ XMLای پارس نمی‌کند و به هیچ ساعتی نگاه نمی‌کند؛
`syntax` و `validation` و `pdf` رویش می‌نشینند، و CLI و سرویس HTTP پوسته‌های
نازکی روی هر دو هستند.

**قاعده‌ها روی مدل اجرا می‌شوند، نه روی XPath.** بیشتر ابزارهای این حوزه
Schematron رسمی را می‌پیچند که به‌ازای هر نحو نوشته شده — یعنی هر قاعده دو بار
وجود دارد و فاکتور فقط *بعد* از سریال‌سازی قابل بررسی است. اینجا هر قاعده یک
تابع خالص کوچک است از `Invoice` به مشکلاتی که پیدا می‌کند. یک قاعده هم UBL را
پوشش می‌دهد هم CII، فاکتور را می‌شود *پیش از* آنکه سندی وجود داشته باشد
اعتبارسنجی کرد، و `GET /v1/rules` از خود قاعده‌ها ساخته می‌شود نه از فهرست دومی
که باید هم‌گام نگه داشته شود.

**اجباری‌بودن خاصیتِ استاندارد است، نه خاصیتِ سیستم تایپ.** `Invoice.number`
از نوع `str | None` است، با اینکه `BR-02` وجودش را لازم می‌داند: برای گزارش
`BR-02` اول باید بتوانی سندی را نگه داری که شماره‌ی فاکتور ندارد. مدلی که
قبولش نکند فقط می‌تواند خطای پارس بدهد، و خطای پارس به تماس‌گیرنده نمی‌گوید کدام
قاعده شکسته. به همین دلیل کدها رشته‌ی ساده‌اند — فاکتوری که `"XX"` را به‌عنوان
دسته‌ی مالیاتی آورده باید آن‌قدر زنده بماند که به‌شکل `BR-CL-18` گزارش شود.

**پول `Decimal` است و `float` رد می‌شود، نه تبدیل.** فاکتوری که یک سنت اختلاف
دارد فاکتور ردشده است. دلیل ظریف‌ترش: `Decimal` تعداد رقم اعشاری که با آن
نوشته شده را به یاد می‌آورد، و دقیقاً همین چیزی است که قواعد `BR-DEC-*`
می‌پرسند؛ پس مبلغ‌ها از شکل لفظی خوانده می‌شوند و هرگز نرمال نمی‌شوند —
نرمال‌کردن همان عیبی را پاک می‌کند که این قاعده‌ها برای پیداکردنش هستند.

**هر نحو یک ماژول است که هر دو جهت را با هم نگه می‌دارد.** نگاشت میان یک اصطلاح
کسب‌وکاری و مسیر یک عنصر *یک واقعیت* است؛ تقسیم نویسنده و خواننده بین دو فایل
همان راهی است که این دو از هم می‌افتند. تست‌های رفت‌وبرگشت کل مدل را مقایسه
می‌کنند نه چند فیلد را، و همان اول جواب دادند: فیلدی که نویسنده‌ی CII می‌انداخت
و فیلد دیگری که روی credit note در UBL گم می‌شد.

هر ورودی دشمن فرض می‌شود: `<!DOCTYPE>` پیش از پارس رد می‌شود، بدون شبکه و بدون
DTD، با سقف برای بایت و عمق و تعداد عنصر، و در کل پکیج فقط یک فراخوانی
پیکربندی‌شده‌ی `etree.fromstring` وجود دارد. خطاها RFC 9457 هستند و دو قرارداد
عمدی‌اند: تولید حاضر نیست فاکتور ناسازگار بنویسد، و اعتبارسنجی هرگز امتناع
نمی‌کند — پیداکردن پنجاه خطا یک درخواست *موفق* است، پس `200` با `valid: false`.

محدودیت‌های شناخته‌شده به‌جای اینکه بماند تا کسی کشفشان کند، اسم برده شده‌اند:
خانواده‌های قاعده‌ای که پیاده نشده‌اند، نبودِ اعتبارسنجی XSD، نبودِ Peppol. چون
اعتبارسنجی که آنچه را بررسی نکرده بی‌صدا قبول کند، از نبودِ اعتبارسنج بدتر است.
"""

_P5_PROBLEM_EN = """\
A third-party webhook arrives once. If it is lost between the socket and the
database, nobody can ask Stripe or GitHub to send it again, and the failure is
silent — the producer got its `200`. Meanwhile the subscriber on the other side
is a machine you do not control: it times out, it returns a `500`, it goes down
for an hour, it returns `400` because the contract changed. Each of those needs
a different answer, and "retry everything with exponential backoff" is the wrong
answer to most of them.
"""

_P5_BODY_EN = """\
The guarantee is stated honestly, because the honest version is the useful one:
**exactly once at the persistence boundary, at least once to the subscriber.**
The first half is enforced by a unique constraint and proved by a concurrency
test. The second half cannot be enforced by anybody — the last step is an HTTP
request to someone else's machine, and a worker killed between their `200` and
our commit must retry rather than guess. So every outbound request carries a
stable `Idempotency-Key` and an attempt number, which is exactly what a
subscriber needs to close the gap on their side.

**PostgreSQL is the queue**, so the queue and the data it refers to are in one
transaction. Fan-out cannot commit an event whose work item was lost, a claim
cannot survive a rolled-back attempt, and there is no reconciliation job between
two stores that disagree. A broker would buy cross-language fan-out and cost
exactly the property this service exists to have. `FOR UPDATE SKIP LOCKED` lets
N workers claim disjoint batches with no coordinator, and a lease means a worker
killed mid-flight has its rows swept back rather than stranded.

Every failure mode has a considered answer rather than a generic retry. A
duplicate is `200` with `duplicate: true`, not a `409` that makes the producer
retry harder and page someone. A `400` from a subscriber is dead-lettered
immediately, because eight identical rejections teach nobody anything. A `429`
with `Retry-After` is honoured, because a subscriber saying when to come back
knows better than our curve. Backoff is full jitter rather than "exponential
plus noise", which re-synchronises the whole herd onto one instant and re-kills
the endpoint that just recovered. A circuit opens after N failures and
reschedules **without spending an attempt**, so a 30-second outage does not
exhaust an eight-attempt budget on requests that were never sent — and exactly
one probe is admitted on half-open, or the backlog stampedes the endpoint the
moment it comes back.

Outbound delivery is where a gateway is a confused deputy by construction, so
every resolved address is validated and then the connection is **pinned to the
address that passed**, with `Host` and TLS SNI preserved: validating a DNS
answer and then letting the client resolve again is a TOCTOU window, and
`169.254.169.254` hands out cloud credentials.

The centrepiece test fires 24 genuinely concurrent identical webhooks — separate
sessions, separate connections, separate backends racing on one constraint — and
asserts one event, one winner and one delivery. Every test runs against a real
PostgreSQL, because the guarantees are PostgreSQL's and a suite passing against
SQLite would be testing a fiction. The load harness found two real bugs,
including a fail-open path that was paying a Redis connect timeout on every
request; the benchmark table reports the machine and the unflattering rows
along with the rest.
"""

_P5_PROBLEM_DE = """\
Ein Webhook von einem Drittanbieter kommt genau einmal. Geht er zwischen Socket
und Datenbank verloren, kann niemand Stripe oder GitHub bitten, ihn erneut zu
schicken — und der Fehler ist still, denn der Produzent hat sein `200` bekommen.
Auf der anderen Seite steht ein Subscriber, den man nicht kontrolliert: Er läuft
in einen Timeout, antwortet mit `500`, ist eine Stunde weg, oder antwortet mit
`400`, weil sich der Vertrag geändert hat. Jeder dieser Fälle braucht eine
andere Antwort, und „alles mit exponentiellem Backoff wiederholen" ist für die
meisten davon die falsche.
"""

_P5_BODY_DE = """\
Die Zusage ist ehrlich formuliert, weil nur die ehrliche Version brauchbar ist:
**genau einmal an der Persistenzgrenze, mindestens einmal zum Subscriber.** Die
erste Hälfte erzwingt ein Unique-Constraint, bewiesen von einem Nebenläufigkeitstest.
Die zweite Hälfte kann niemand erzwingen — der letzte Schritt ist ein
HTTP-Request an eine fremde Maschine, und ein Worker, der zwischen deren `200`
und dem eigenen Commit stirbt, muss es erneut versuchen statt zu raten. Jeder
ausgehende Request trägt deshalb einen stabilen `Idempotency-Key` und eine
Versuchsnummer — genau das, was ein Subscriber braucht, um die Lücke auf seiner
Seite zu schließen.

**PostgreSQL ist die Warteschlange**, damit die Warteschlange und die Daten, auf
die sie sich bezieht, in einer Transaktion liegen. Ein Fan-out kann kein
Ereignis committen, dessen Arbeitsauftrag verloren ging, ein Claim überlebt
keinen zurückgerollten Versuch, und es gibt keinen Abgleichjob zwischen zwei
Speichern, die sich widersprechen. Ein Broker brächte sprachübergreifendes
Fan-out und kostete genau die Eigenschaft, für die es diesen Dienst gibt.
`FOR UPDATE SKIP LOCKED` lässt N Worker disjunkte Batches ohne Koordinator
übernehmen, und ein Lease sorgt dafür, dass die Zeilen eines abgestürzten
Workers zurückgeholt statt liegen gelassen werden.

Jeder Fehlerfall hat eine durchdachte Antwort statt eines generischen Retrys.
Ein Duplikat ist `200` mit `duplicate: true` — kein `409`, das den Produzenten
härter wiederholen lässt und jemanden aus dem Bett klingelt. Ein `400` vom
Subscriber landet sofort im Dead Letter, denn acht identische Ablehnungen
bringen niemandem etwas. Ein `429` mit `Retry-After` wird respektiert, denn ein
Subscriber, der sagt, wann er wieder kann, weiß es besser als unsere Kurve.
Backoff ist Full Jitter statt „exponentiell plus Rauschen", das die ganze Herde
auf einen Zeitpunkt synchronisiert und den gerade genesenen Endpunkt erneut
umbringt. Ein Circuit öffnet nach N Fehlern und verschiebt Zustellungen, **ohne
einen Versuch zu verbrauchen** — ein 30-Sekunden-Ausfall soll kein Budget von
acht Versuchen für nie gesendete Requests aufbrauchen. Im Halb-offen-Zustand
wird genau eine Probe zugelassen, sonst stürmt der gesamte Rückstau den
Endpunkt in dem Moment, in dem er zurückkommt.

Beim Ausliefern ist ein Gateway von Natur aus ein Confused Deputy: Jede
aufgelöste Adresse wird geprüft, und die Verbindung wird anschließend **auf die
geprüfte Adresse festgenagelt**, mit erhaltenem `Host` und TLS-SNI. Eine
DNS-Antwort zu prüfen und den Client danach erneut auflösen zu lassen, ist ein
TOCTOU-Fenster — und `169.254.169.254` gibt Cloud-Zugangsdaten heraus.

Der zentrale Test feuert 24 wirklich gleichzeitige, identische Webhooks —
getrennte Sessions, getrennte Verbindungen, getrennte Backends im Wettlauf um
ein Constraint — und prüft: ein Ereignis, ein Gewinner, eine Zustellung. Alle
Tests laufen gegen ein echtes PostgreSQL, denn die Garantien sind die von
PostgreSQL; eine Suite, die gegen SQLite grün wird, prüft eine Fiktion. Das
Lastwerkzeug fand zwei echte Fehler, darunter einen Fail-open-Pfad, der pro
Request ein Redis-Connect-Timeout bezahlte. Die Benchmark-Tabelle nennt die
Maschine und die unvorteilhaften Zeilen mit.
"""

_P5_PROBLEM_FA = """\
وبهوکِ یک سرویس بیرونی فقط یک بار می‌آید. اگر بین سوکت و دیتابیس گم شود، هیچ‌کس
نمی‌تواند از Stripe یا GitHub بخواهد دوباره بفرستدش — و خرابی هم بی‌صداست، چون
فرستنده `200` خودش را گرفته است. آن‌طرف ماجرا هم مشترکی ایستاده که دست تو
نیست: تایم‌اوت می‌دهد، `500` برمی‌گرداند، یک ساعت پایین می‌رود، یا `400` می‌دهد
چون قرارداد عوض شده. هر کدامِ اینها جواب متفاوتی می‌خواهد، و «همه را با backoff
نمایی دوباره بفرست» برای بیشترشان جواب غلطی است.
"""

_P5_BODY_FA = """\
تضمین صادقانه نوشته شده، چون فقط نسخه‌ی صادقانه به درد می‌خورد: **دقیقاً یک بار
روی مرز ماندگاری، دست‌کم یک بار به مشترک.** نیمه‌ی اول را یک unique constraint
تحمیل می‌کند و یک تست هم‌روندی اثباتش می‌کند. نیمه‌ی دوم را هیچ‌کس نمی‌تواند
تضمین کند — آخرین قدم یک درخواست HTTP به ماشین دیگری است، و کارگری که بین
`200` آن‌ها و commit خودمان کشته شود باید دوباره تلاش کند، نه حدس بزند. پس هر
درخواست خروجی یک `Idempotency-Key` پایدار و شماره‌ی تلاش را با خودش می‌برد؛
دقیقاً همان چیزی که مشترک لازم دارد تا شکاف را سمت خودش ببندد.

**پستگرس خودِ صف است**، تا صف و داده‌ای که به آن اشاره می‌کند در یک تراکنش
باشند. فن‌اوت نمی‌تواند رویدادی را commit کند که کارِ مربوط به آن گم شده، یک
claim از تلاشِ rollback‌شده جان به در نمی‌برد، و هیچ job تطبیقی بین دو انبارِ
ناموافق لازم نیست. یک broker فن‌اوت چندزبانه می‌داد و دقیقاً همان خاصیتی را
می‌گرفت که این سرویس برای آن ساخته شده. `FOR UPDATE SKIP LOCKED` اجازه می‌دهد N
کارگر دسته‌های مجزا بردارند بدون هیچ هماهنگ‌کننده‌ای، و lease یعنی سطرهای کارگرِ
مرده برمی‌گردند به‌جای اینکه گیر کنند.

هر حالت خرابی جواب سنجیده‌ی خودش را دارد، نه یک retry عمومی. تکراری یعنی `200`
با `duplicate: true`، نه `409` که فرستنده را وادار به تلاش شدیدتر کند و کسی را
نصف شب بیدار کند. `400` از سمت مشترک بلافاصله dead-letter می‌شود، چون هشت بار
ردِ یکسان به هیچ‌کس چیزی یاد نمی‌دهد. `429` با `Retry-After` رعایت می‌شود، چون
مشترکی که می‌گوید کِی برگرد، بهتر از منحنی ما می‌داند. backoff از نوع full
jitter است نه «نمایی به‌علاوه‌ی نویز» — که کل گله را روی یک لحظه هم‌زمان می‌کند
و همان سروری را که تازه بلند شده دوباره می‌خواباند. مدار بعد از N خطا باز
می‌شود و تحویل‌ها را **بدون خرج‌کردن یک تلاش** جابه‌جا می‌کند، تا یک قطعی
سی‌ثانیه‌ای بودجه‌ی هشت‌تایی را روی درخواست‌هایی که اصلاً فرستاده نشدند تمام
نکند؛ و در حالت نیمه‌باز فقط یک درخواست آزمایشی رد می‌شود، وگرنه کل صفِ عقب‌افتاده
همان لحظه‌ی برگشتن به سرور هجوم می‌برد.

تحویل خروجی جایی است که یک دروازه ذاتاً «معاونِ گیج» است: هر آدرسِ resolve‌شده
بررسی می‌شود و بعد اتصال **به همان آدرسی که قبول شد سنجاق می‌شود**، با حفظ
`Host` و SNI — چون بررسی یک پاسخ DNS و بعد اجازه‌دادن به کلاینت که دوباره
resolve کند یک پنجره‌ی TOCTOU است، و `169.254.169.254` کلید ابر را دستی
تحویل می‌دهد.

تست محوری ۲۴ وبهوکِ واقعاً هم‌زمان و یکسان شلیک می‌کند — نشست جدا، اتصال جدا،
بک‌اند جدا، همه روی یک constraint در مسابقه — و می‌سنجد که یک رویداد، یک برنده
و یک تحویل بماند. همه‌ی تست‌ها روی یک پستگرسِ واقعی اجرا می‌شوند، چون تضمین‌ها
مالِ پستگرس‌اند و سوییتی که روی SQLite سبز شود دارد یک افسانه را تست می‌کند.
ابزار بارگذاری دو باگ واقعی پیدا کرد، یکی‌شان مسیر fail-open که به‌ازای هر
درخواست تایم‌اوتِ اتصال به Redis را می‌پرداخت؛ جدول بنچمارک هم مشخصات ماشین و
سطرهای نامطلوب را کنار بقیه گزارش می‌کند.
"""

_P6_PROBLEM_EN = """\
In a multi-tenant backend the usual answer is "always filter by `tenant_id`",
and it is one forgotten `WHERE` clause away from a breach — in a new endpoint,
in a `JOIN` somebody wrote at speed, in a `COUNT(*)` for a dashboard. It relies
on every developer, forever, and it fails *open*: the symptom of the bug is more
data, not less, so nothing crashes and no test fails unless somebody thought to
write that exact test.
"""

_P6_BODY_EN = """\
One database, one schema, a `tenant_id` column on every tenant-owned table, and
PostgreSQL Row-Level Security enforcing it. The repository's single claim is
that a request can only ever see the workspace its token names, and the suite
exists to try to break it.

Three things make the RLS real rather than decorative. **The application
connects as a role that cannot escape a policy** — the first migration
provisions it `NOSUPERUSER` and `NOBYPASSRLS`, because "we have RLS" is worth
nothing until you can say which role connects. **Every policy is `FORCE`d**,
since without that a table's owner is exempt from its own policies, and the
owner is exactly the role migrations and seeds run as. **The tenant is a
transaction-local setting**, not a query parameter: the request dependency runs
`set_config('app.current_tenant', …, true)`, so the value dies with the
transaction and cannot leak onto the next checkout of a pooled connection.

Each policy has both halves. `USING` is why an id from another workspace
resolves to nothing; `WITH CHECK` is why a service that computed the wrong
`tenant_id` gets its `INSERT` refused instead of silently storing a leaked row.
And it fails closed: with the setting unset the predicate is `NULL`, so an
unbound session reads *zero* rows. The default state of a session that forgot to
identify itself is blindness.

Database-per-tenant and schema-per-tenant were both considered and are both
argued against in the README rather than waved away — N migration runs per
deploy, a partial-failure story, `search_path` as load-bearing global state. The
real cost of the chosen approach is stated too: the policies are invisible in
the Python, so a newcomer reads a repository method with no tenant filter and
has to know the database is adding one. That is why the suite pins the role
attributes, `pg_class` and `pg_policies` directly.

The rest is the ordinary security work done properly. Argon2id at the OWASP
profile with rehash on login. **Refresh tokens are not JWTs** — they are opaque
random strings stored as a keyed HMAC digest, so a leaked table yields no usable
credential, and rotation detects reuse: presenting a consumed token means a copy
escaped, so the whole family is revoked and the legitimate holder notices rather
than quietly sharing a session with a thief. Access tokens stay stateless but
revocable through a `token_version` claim. UUID keys, one login failure message
for every cause with a dummy verification on the unknown-user path, and 404
rather than 403 for another workspace's data — a 403 answers the only question
an enumerator is asking.
"""

_P6_PROBLEM_DE = """\
In einem mandantenfähigen Backend lautet die übliche Antwort „immer nach
`tenant_id` filtern" — und die ist eine vergessene `WHERE`-Klausel von einem
Datenleck entfernt: in einem neuen Endpunkt, in einem schnell geschriebenen
`JOIN`, in einem `COUNT(*)` fürs Dashboard. Sie verlässt sich auf jede
Entwicklerin und jeden Entwickler, für immer, und sie versagt *offen*: Das
Symptom des Fehlers sind mehr Daten, nicht weniger. Nichts stürzt ab, und kein
Test schlägt fehl, solange niemand genau diesen Test geschrieben hat.
"""

_P6_BODY_DE = """\
Eine Datenbank, ein Schema, eine `tenant_id`-Spalte auf jeder mandantenbezogenen
Tabelle — durchgesetzt von PostgreSQL Row-Level Security. Die eine Behauptung
des Repositorys lautet: Eine Anfrage sieht ausschließlich den Workspace, den ihr
Token nennt. Die Testsuite existiert, um das zu widerlegen.

Drei Dinge machen die RLS echt statt dekorativ. **Die Anwendung verbindet sich
mit einer Rolle, die keiner Policy entkommen kann** — die erste Migration legt
sie mit `NOSUPERUSER` und `NOBYPASSRLS` an, denn „wir haben RLS" ist nichts
wert, solange man nicht sagen kann, mit welcher Rolle verbunden wird. **Jede
Policy ist `FORCE`d**, weil der Eigentümer einer Tabelle sonst von ihren eigenen
Policies ausgenommen ist — und genau als Eigentümer laufen Migrationen und
Seeds. **Der Mandant ist eine transaktionslokale Einstellung**, kein
Query-Parameter: Die Request-Dependency ruft
`set_config('app.current_tenant', …, true)`, der Wert stirbt also mit der
Transaktion und kann nicht auf die nächste Entnahme aus dem Pool durchsickern.

Jede Policy hat beide Hälften. `USING` ist der Grund, warum eine ID aus einem
fremden Workspace ins Leere läuft; `WITH CHECK` ist der Grund, warum ein
Service, der die falsche `tenant_id` berechnet hat, ein abgelehntes `INSERT`
bekommt statt still eine fremde Zeile zu schreiben. Und es versagt geschlossen:
Ohne gesetzte Einstellung ist das Prädikat `NULL`, eine ungebundene Session
liest also *null* Zeilen. Der Normalzustand einer Session, die vergessen hat,
sich auszuweisen, ist Blindheit.

Datenbank pro Mandant und Schema pro Mandant wurden beide geprüft und werden im
README begründet abgelehnt statt weggewischt — N Migrationsläufe pro Deploy,
eine Geschichte für Teilfehlschläge, `search_path` als tragende globale
Zustandsvariable. Auch der Preis des gewählten Wegs steht dort: Die Policies
sind im Python unsichtbar, wer neu dazukommt, liest eine Repository-Methode ohne
Mandantenfilter und muss *wissen*, dass die Datenbank einen hinzufügt. Deshalb
prüft die Suite die Rollenattribute, `pg_class` und `pg_policies` direkt.

Der Rest ist gewöhnliche Sicherheitsarbeit, ordentlich gemacht. Argon2id im
OWASP-Profil mit Rehash beim Login. **Refresh-Tokens sind keine JWTs** — sie
sind undurchsichtige Zufallsstrings, gespeichert als geschlüsselter
HMAC-Digest: Eine geleakte Tabelle ergibt keine brauchbare Anmeldung. Die
Rotation erkennt Wiederverwendung: Wer ein verbrauchtes Token vorlegt, hat eine
entwichene Kopie — also wird die ganze Familie widerrufen, und der rechtmäßige
Inhaber merkt es, statt still eine Sitzung mit einem Dieb zu teilen.
Access-Tokens bleiben zustandslos und trotzdem widerrufbar, über einen
`token_version`-Claim. Dazu UUID-Schlüssel, eine einzige Fehlermeldung für alle
Login-Ursachen samt Dummy-Verifikation auf dem Unbekannter-Nutzer-Pfad, und
404 statt 403 für fremde Daten — ein 403 beantwortet genau die Frage, die ein
Enumerator stellt.
"""

_P6_PROBLEM_FA = """\
در یک بک‌اند چندمستأجری، جواب همیشگی این است که «همیشه بر اساس `tenant_id`
فیلتر کن» — و این جواب فقط یک `WHERE` فراموش‌شده با یک نشت داده فاصله دارد: در
یک endpoint تازه، در یک `JOIN` که با عجله نوشته شده، در یک `COUNT(*)` برای
داشبورد. تکیه‌اش به این است که همه‌ی توسعه‌دهنده‌ها، تا ابد، یادشان بماند؛ و
*باز* خراب می‌شود: نشانه‌ی باگ، دادهٔ بیشتر است نه کمتر. پس چیزی crash نمی‌کند
و هیچ تستی قرمز نمی‌شود، مگر کسی دقیقاً همان تست را نوشته باشد.
"""

_P6_BODY_FA = """\
یک دیتابیس، یک اسکیما، یک ستون `tenant_id` روی هر جدولِ متعلق به مستأجر، و
Row-Level Security پستگرس که آن را تحمیل می‌کند. تنها ادعای این مخزن این است که
هر درخواست فقط همان کارگاهی را می‌بیند که توکنش نام برده — و مجموعه تست‌ها برای
شکستن همین ادعا نوشته شده‌اند.

سه چیز RLS را واقعی می‌کند، نه تزئینی. **اپلیکیشن با نقشی وصل می‌شود که
نمی‌تواند از policy فرار کند** — اولین migration آن نقش را با `NOSUPERUSER` و
`NOBYPASSRLS` می‌سازد، چون «ما RLS داریم» تا وقتی نتوانی بگویی با چه نقشی وصل
می‌شوی هیچ ارزشی ندارد. **همه‌ی policyها `FORCE` شده‌اند**، چون بدون آن مالکِ
جدول از policyهای خودش معاف است — و مالک دقیقاً همان نقشی است که migration و
seed با آن اجرا می‌شوند. **مستأجر یک تنظیم محدود به تراکنش است**، نه یک پارامتر
کوئری: وابستگیِ درخواست `set_config('app.current_tenant', …, true)` را اجرا
می‌کند، پس مقدار با تراکنش می‌میرد و روی برداشت بعدی از connection pool نشت
نمی‌کند.

هر policy هر دو نیمه را دارد. `USING` دلیل این است که یک شناسه از کارگاه دیگر
به هیچ نمی‌رسد؛ `WITH CHECK` دلیل این است که سرویسی که `tenant_id` را اشتباه
حساب کرده `INSERT`اش رد می‌شود، نه اینکه بی‌صدا یک سطرِ نشتی ذخیره کند. و
*بسته* خراب می‌شود: اگر تنظیم ست نشده باشد، گزاره `NULL` است و نشستِ نامقید
*صفر* سطر می‌خواند. حالت پیش‌فرضِ نشستی که یادش رفته خودش را معرفی کند، کوری است.

«یک دیتابیس به‌ازای هر مستأجر» و «یک اسکیما به‌ازای هر مستأجر» هر دو بررسی
شده‌اند و در README با دلیل رد شده‌اند، نه با دستِ رد: N بار اجرای migration در
هر دیپلوی، داستانِ شکستِ نیمه‌کاره، و `search_path` به‌عنوان حالت سراسریِ
باربر. هزینه‌ی واقعیِ راه انتخاب‌شده هم نوشته شده: policyها در کد پایتون دیده
نمی‌شوند، پس تازه‌وارد یک متد repository بدون فیلتر مستأجر می‌بیند و باید
*بداند* که دیتابیس دارد یکی اضافه می‌کند. برای همین تست‌ها مستقیم سراغ
attributeهای نقش و `pg_class` و `pg_policies` می‌روند.

بقیه‌اش کار امنیتیِ معمولی است که درست انجام شده. Argon2id با پروفایل OWASP و
rehash هنگام ورود. **توکن refresh جِی‌دابلیوتی نیست** — رشته‌ی تصادفیِ مبهمی است
که به‌شکل چکیده‌ی HMAC کلیددار ذخیره می‌شود، پس جدولِ نشت‌کرده هیچ اعتبارنامه‌ی
قابل استفاده‌ای نمی‌دهد؛ و چرخش، استفاده‌ی دوباره را می‌گیرد: ارائه‌ی توکنِ
مصرف‌شده یعنی نسخه‌ای فرار کرده، پس کل خانواده باطل می‌شود و صاحب واقعی متوجه
می‌شود، به‌جای اینکه بی‌صدا نشستش را با یک دزد شریک شود. توکن دسترسی بی‌حالت
می‌ماند و در عین حال با claimِ `token_version` قابل ابطال است. کلیدها UUID
هستند، پیام خطای ورود برای همه‌ی علت‌ها یکی است (به‌علاوه‌ی یک verify ساختگی در
مسیر کاربرِ ناشناس تا جواب از راه تأخیر لو نرود)، و برای دادهٔ کارگاهِ دیگری
پاسخ ۴۰۴ است نه ۴۰۳ — چون ۴۰۳ دقیقاً همان سؤالی را جواب می‌دهد که یک شمارشگر
می‌پرسد.
"""

# ── experience descriptions ────────────────────────────────────────────────
_E_SMARTX_EN = """\
Primary developer on a B2B2C customer loyalty and CRM platform holding ~25M
unique customers and 800M invoice records, owning architectural decisions and
implementation approach.

- Modernised .NET Framework 4.7 → .NET 8 → .NET 9 as a refactor, not a port.
- Rebuilt large parts of the SQL Server schema on a live database at that
  volume, working through repeated locking and blocking to a migration strategy
  that held.
- Systematic performance work; page data loads up to 30x faster.
- Led the move to a domain-split modular architecture — vertical slice over
  Clean Architecture, RabbitMQ and gRPC between services — ~70% complete at
  departure.
- Customer segmentation including RFM, multi-tenancy, event-driven flows.
- Onboarded and mentored the two engineers who joined the product later.
"""

_E_SMARTX_DE = """\
Hauptentwickler einer B2B2C-Loyalty- und CRM-Plattform mit rund 25 Mio.
eindeutigen Kunden und 800 Mio. Rechnungsdatensätzen; verantwortlich für
Architekturentscheidungen und Umsetzung.

- Modernisierung .NET Framework 4.7 → .NET 8 → .NET 9 als Refactoring, nicht
  als reine Portierung.
- Umbau großer Teile des SQL-Server-Schemas im laufenden Betrieb bei diesem
  Datenvolumen; über wiederholte Sperrprobleme hinweg zu einer tragfähigen
  Migrationsstrategie.
- Systematische Performance-Arbeit; Datenladezeiten bis zu 30-mal schneller.
- Federführung beim Umstieg auf eine nach Domänen geschnittene modulare
  Architektur — Vertical Slice auf Clean Architecture, RabbitMQ und gRPC
  zwischen den Services — bei Weggang zu rund 70 % abgeschlossen.
- Kundensegmentierung u. a. mit RFM, Mandantenfähigkeit, ereignisgesteuerte
  Abläufe.
- Einarbeitung und Mentoring der zwei später hinzugekommenen Entwickler.
"""

_E_SMARTX_FA = """\
توسعه‌دهنده‌ی اصلی یک پلتفرم باشگاه مشتریان و CRM از نوع B2B2C با حدود ۲۵ میلیون
مشتری یکتا و ۸۰۰ میلیون رکورد فاکتور؛ مسئول تصمیم‌های معماری و شیوه‌ی
پیاده‌سازی.

- مدرن‌سازی .NET Framework 4.7 → .NET 8 → .NET 9 به‌صورت بازنویسی، نه جابه‌جایی.
- بازطراحی بخش‌های بزرگی از اسکیمای SQL Server روی پایگاه داده‌ی زنده در این
  حجم؛ عبور از locking و blocking پی‌درپی تا رسیدن به راهبرد مهاجرتی که دوام
  آورد.
- کار سیستماتیک روی کارایی؛ بارگذاری داده‌ی صفحات تا ۳۰ برابر سریع‌تر.
- هدایت انتقال به معماری ماژولار دامنه‌محور — vertical slice روی Clean
  Architecture با RabbitMQ و gRPC — حدود ۷۰٪ کامل‌شده در زمان خروج.
- بخش‌بندی مشتریان از جمله با RFM، multi-tenancy، جریان‌های رویدادمحور.
- آنبوردینگ و منتورینگ دو مهندسی که بعدتر به محصول پیوستند.
"""

_E_FREELANCE_EN = """\
Backend work for clients alongside my main role: Python and FastAPI services,
REST integrations, and LLM API integration (OpenAI, Gemini), deployed with
Docker.
"""

_E_FREELANCE_DE = """\
Backend-Arbeit für Kunden parallel zur Hauptrolle: Python- und FastAPI-Services,
REST-Integrationen und LLM-API-Integration (OpenAI, Gemini), per Docker
ausgeliefert.
"""

_E_FREELANCE_FA = """\
کار بک‌اند برای مشتریان، موازی با نقش اصلی: سرویس‌های پایتون و FastAPI،
یکپارچه‌سازی‌های REST و اتصال به LLM API (OpenAI، Gemini)، با دیپلوی روی Docker.
"""

_E_BALA_EN = """\
Full-stack development on the company's web products, part-time alongside other
work. C# and .NET on the server, with the front end built against it.
"""

_E_BALA_DE = """\
Full-Stack-Entwicklung an den Webprodukten des Unternehmens, in Teilzeit neben
anderer Tätigkeit. C# und .NET auf der Serverseite, dazu das darauf aufbauende
Frontend.
"""

_E_BALA_FA = """\
توسعه‌ی فول‌استک روی محصولات وب شرکت، به‌صورت پاره‌وقت و موازی با کار دیگر. C#
و دات‌نت سمت سرور، به‌همراه فرانت‌اندی که روی آن ساخته می‌شد.
"""

# ── Smart Studio (content-studio) ───────────────────────────────────────────
_P7_PROBLEM_EN = """\
A content strategist runs ideas, scripts, the publishing calendar and the work
of a camera operator, an editor and a designer across several apps and
messenger groups. Foreign tools know neither the Jalali calendar nor Iranian
occasions — nobody warns that a cheerful post has landed on a day of mourning —
and inside Iran Google Play Services, FCM and Telegram are not things a
product can lean on.
"""

_P7_BODY_EN = """\
A FastAPI backend on PostgreSQL 16, a web panel in React 19 and TypeScript, and
a native Android app in Kotlin and Jetpack Compose.

**An idea in under two taps.** The idea inbox takes text, a voice note or a
photo, and fills from Android's Share sheet — from Instagram or any other app.

**One pipeline, from idea to analysis.** Idea, script, approval, shoot, edit,
review, schedule, publish, analyse — as a kanban board with a history of every
change. Script templates (hook, body, CTA, caption, hashtags) and shot lists;
tasks with deadlines for each team member; and 48 hours after publishing, a
reminder to log the numbers and a lesson learned.

**A calendar that knows the occasions.** Monthly and weekly Jalali views with
official, religious and marketing occasions, and a warning when cheerful content
falls on a day of mourning.

**Android, offline first.** A Room cache, delta sync and an outbox keyed for
idempotency, so work done on the metro is never recorded twice. Notifications
without Google Play Services, and builds for Cafe Bazaar, Myket and Google Play.

**A web panel for the desk.** Kanban and calendar with drag and undo, global
search on `Ctrl+K`, and autosave.

**One design system for two platforms.** Colour tokens come from one source for
web and Android, in light and dark, and the build fails if any of the 429 colour
pairs it checks falls below WCAG AA contrast.

**A multi-tenant backend** — organisation, brand, page — with roles and
permissions, a job queue on PostgreSQL itself, notifications through Bale and
Telegram bots, login codes from the Bale bot, and Persian search that tolerates
ی/ک variants, the half-space, digits and typos.
"""

_P7_PROBLEM_DE = """\
Eine Content-Strategie für Instagram verteilt sich über mehrere Apps und
Messenger-Gruppen: Ideen, Skripte, der Veröffentlichungskalender und die Arbeit
von Kamera, Schnitt und Design. Ausländische Werkzeuge kennen weder den
Jalali-Kalender noch iranische Anlässe — niemand warnt, wenn ein fröhlicher
Beitrag auf einen Trauertag fällt —, und im Iran sind Google Play Services, FCM
und Telegram nichts, worauf sich ein Produkt verlassen kann.
"""

_P7_BODY_DE = """\
Ein FastAPI-Backend auf PostgreSQL 16, ein Web-Panel in React 19 und TypeScript
und eine native Android-App in Kotlin und Jetpack Compose.

**Eine Idee in weniger als zwei Tippern.** Der Ideen-Eingang nimmt Text,
Sprachnachricht oder Foto und füllt sich über das Teilen-Menü von Android — aus
Instagram oder jeder anderen App.

**Eine Pipeline von der Idee bis zur Auswertung.** Idee, Skript, Freigabe,
Dreh, Schnitt, Review, Planung, Veröffentlichung, Analyse — als Kanban mit
Änderungsverlauf. Skriptvorlagen (Hook, Hauptteil, CTA, Caption, Hashtags) und
Shotlists; Aufgaben mit Fristen fürs Team; und 48 Stunden nach der
Veröffentlichung die Erinnerung, Zahlen und eine Lehre festzuhalten.

**Ein Kalender, der die Anlässe kennt.** Jalali-Monats- und Wochenansicht mit
offiziellen, religiösen und Marketing-Anlässen, und eine Warnung, wenn
fröhlicher Inhalt auf einen Trauertag fällt.

**Android, offline first.** Room-Cache, Delta-Sync und eine Outbox mit
Idempotenzschlüssel, damit unterwegs erledigte Arbeit nie doppelt ankommt.
Benachrichtigungen ohne Google Play Services, Builds für Cafe Bazaar, Myket und
Google Play.

**Ein Web-Panel für den Schreibtisch.** Kanban und Kalender mit Drag & Drop und
Rückgängig, globale Suche mit `Ctrl+K`, automatisches Speichern.

**Ein Designsystem für zwei Plattformen.** Die Farbtokens kommen aus einer
Quelle für Web und Android, hell und dunkel, und der Build schlägt fehl, sobald
eines der 429 geprüften Farbpaare unter den WCAG-AA-Kontrast fällt.

**Ein mandantenfähiges Backend** — Organisation, Marke, Seite — mit Rollen und
Rechten, einer Job-Queue direkt in PostgreSQL, Benachrichtigungen über Bale- und
Telegram-Bots, Login-Codes vom Bale-Bot und einer persischen Suche, die
ی/ک-Varianten, Halbleerzeichen, Ziffern und Tippfehler verzeiht.
"""

_P7_PROBLEM_FA = """\
یک استراتژیست محتوا ایده، سناریو، تقویم انتشار و کار فیلم‌بردار و تدوین‌گر و
طراح را بین چند اپ و چند گروه پیام‌رسان مدیریت می‌کند. ابزارهای خارجی تقویم
شمسی و مناسبت‌های ایرانی را نمی‌شناسند — کسی هشدار نمی‌دهد که محتوای شاد روی
روز عزاداری افتاده — و در ایران Google Play Services، FCM و تلگرام چیزی نیستند
که یک محصول بتواند رویشان حساب کند.
"""

_P7_BODY_FA = """\
بک‌اند FastAPI روی PostgreSQL 16، پنل وب با React 19 و TypeScript، و اپ
اندروید native با Kotlin و Jetpack Compose.

**ایده در کمتر از دو لمس.** صندوق ایده متن، پیام صوتی و عکس می‌گیرد، و از
منوی Share اندروید — از اینستاگرام یا هر اپ دیگری — هم پر می‌شود.

**یک پایپ‌لاین، از ایده تا تحلیل.** ایده، سناریو، تأیید، فیلم‌برداری، تدوین،
بازبینی، زمان‌بندی، انتشار و تحلیل، با نمای کانبان و تاریخچه‌ی تغییرات. قالب
سناریو (قلاب، بدنه، CTA، کپشن، هشتگ) و شات‌لیست؛ تسک با ددلاین برای هر عضو
تیم؛ و ۴۸ ساعت بعد از انتشار، یادآوری ثبت آمار و «درس آموخته».

**تقویمی که مناسبت‌ها را می‌شناسد.** تقویم جلالی ماهانه و هفتگی با مناسبت‌های
رسمی، مذهبی و بازاریابی، و هشدار وقتی محتوای شاد روی روز عزاداری می‌افتد.

**اندروید، آفلاین‌محور.** کش Room، همگام‌سازی دلتا و یک outbox با کلید
idempotency، تا کاری که در مترو انجام شده دو بار ثبت نشود. اعلان بدون Google
Play Services، و نسخه برای کافه‌بازار، مایکت و Google Play.

**پنل وب برای پشت میز.** کانبان و تقویم با drag و undo، جستجوی سراسری با
`Ctrl+K`، و ذخیره‌ی خودکار.

**یک سیستم طراحی برای دو پلتفرم.** توکن‌های رنگ از یک منبع به وب و اندروید
می‌رسند، در تم روشن و تیره، و اگر یکی از ۴۲۹ جفت رنگِ بررسی‌شده کنتراست WCAG AA
را نداشته باشد، build شکست می‌خورد.

**بک‌اند چندمستأجری** — سازمان، برند، صفحه — با نقش و مجوز، صف کار روی خود
PostgreSQL، اعلان از ربات بله و تلگرام، کد ورود از ربات بله، و جستجوی فارسی که
ی و ک، نیم‌فاصله، اعداد و غلط تایپی را تحمل می‌کند.
"""

# ── Salonyar ────────────────────────────────────────────────────────────────
_P8_PROBLEM_EN = """\
Salons take bookings by phone or in Instagram DMs, and the result is double
bookings, forgotten appointments and empty chairs. Off-the-shelf booking tools
assume two things that do not hold in Iran: that a customer will install an app
and sign up for one haircut, and that foreign SMS and push services reach the
phone. So a booking has to start from a link, finish in under a minute, and
rest on Bale and domestic SMS.
"""

_P8_BODY_EN = """\
A NestJS backend on PostgreSQL and Prisma, a BullMQ queue on Redis, and one
React front end that is both the web page and the Bale mini app.

**One link per salon.** `salonyar.ir/<slug>` renders the salon — name, address,
hours, services and prices — on the server (nginx SSI with a 30-second cache),
so a link shared on WhatsApp or Instagram previews the salon rather than an
empty page.

**One booking core, two doors.** Web and Bale go through the same flow: "any
stylist" is the default and the nearest free times come first. A customer
browses without signing in and is verified by a one-time code only at the
moment of booking. Inside Bale the number is confirmed through Bale's own
dialog, with nothing to type, and the web and Bale accounts become one
identity.

**The database refuses a double booking, not the code.** Create, cancel,
reschedule, confirm and decline, with a cancellation window per stylist. Two
simultaneous bookings for the same slot are stopped by a PostgreSQL exclusion
constraint, and a concurrency test checks exactly that.

**A mobile-first panel for the salon.** A calendar of every booking, phone
bookings entered by hand, and a printable link and QR. Salons sign themselves
up, and a wizard sets out default services, stylists and hours, then hands over
the web link, the QR, the Bale link and a line for the Instagram bio. Plans
come with a trial, a stylist limit per plan, and remaining days converted when
the plan changes.

**Against no-shows:** reminders in Bale with SMS as the fallback, and a deposit
through Bale's wallet. Notifications leave through BullMQ with an outbox; login
codes come from Bale's Safir service and Kavenegar SMS, rate-limited. The
production stack backs itself up daily and alerts to Bale, and the API refuses
to start with insecure settings.
"""

_P8_PROBLEM_DE = """\
Friseursalons nehmen Termine per Telefon oder Instagram-Direktnachricht an —
mit Doppelbuchungen, vergessenen Terminen und leeren Stühlen als Folge.
Fertige Buchungstools setzen zwei Dinge voraus, die im Iran nicht gelten: dass
jemand für einen Haarschnitt eine App installiert und sich registriert, und
dass ausländische SMS- und Push-Dienste das Telefon erreichen. Eine Buchung
muss also mit einem Link beginnen, in unter einer Minute fertig sein und auf
Bale und inländischer SMS aufbauen.
"""

_P8_BODY_DE = """\
Ein NestJS-Backend auf PostgreSQL und Prisma, eine BullMQ-Queue auf Redis und
ein React-Frontend, das zugleich Webseite und Bale-Mini-App ist.

**Ein Link pro Salon.** `salonyar.ir/<slug>` rendert den Salon — Name, Adresse,
Öffnungszeiten, Leistungen und Preise — auf dem Server (nginx SSI mit
30-Sekunden-Cache), sodass ein auf WhatsApp oder Instagram geteilter Link den
Salon zeigt statt einer leeren Seite.

**Ein Buchungskern, zwei Eingänge.** Web und Bale laufen durch denselben Ablauf:
„egal bei wem" ist voreingestellt, die nächsten freien Zeiten stehen oben. Man
stöbert ohne Anmeldung und bestätigt sich erst beim Buchen mit einem
Einmalcode. In Bale wird die Nummer über Bales eigenen Dialog bestätigt, ohne
Tippen, und Web- und Bale-Konto werden eine Identität.

**Die Datenbank verweigert die Doppelbuchung, nicht der Code.** Anlegen,
stornieren, verschieben, bestätigen und ablehnen, mit einem Stornofenster pro
Person. Zwei gleichzeitige Buchungen desselben Slots stoppt ein
Exclusion-Constraint in PostgreSQL, und ein Nebenläufigkeitstest prüft genau
das.

**Ein Mobile-first-Panel für den Salon.** Ein Kalender aller Termine,
telefonische Buchungen von Hand, ein druckbarer Link mit QR-Code. Salons
registrieren sich selbst, ein Assistent legt Standardleistungen, Personal und
Öffnungszeiten an und übergibt am Ende Weblink, QR-Code, Bale-Link und eine
Zeile für die Instagram-Bio. Tarife mit Testphase, Personal-Limit je Tarif und
Umrechnung der Resttage beim Wechsel.

**Gegen No-Shows:** Erinnerungen in Bale mit SMS als Rückfallebene und eine
Anzahlung über Bales Wallet. Benachrichtigungen gehen über BullMQ mit Outbox
raus; Login-Codes kommen von Bales Safir-Dienst und Kavenegar-SMS, mit
Rate-Limit. Der Produktions-Stack sichert sich täglich selbst, meldet Störungen
an Bale, und die API startet mit unsicheren Einstellungen gar nicht erst.
"""

_P8_PROBLEM_FA = """\
آرایشگاه‌ها نوبت را تلفنی یا در دایرکت اینستاگرام می‌گیرند، و نتیجه‌اش نوبت‌های
روی هم، مشتری‌ای که یادش می‌رود و صندلی‌ای است که خالی می‌ماند. ابزارهای آماده‌ی
نوبت‌دهی دو فرض دارند که در ایران جواب نمی‌دهد: اینکه مشتری برای یک نوبت اپ
نصب می‌کند و ثبت‌نام می‌کند، و اینکه پیامک و اعلانِ سرویس‌های خارجی به گوشی
می‌رسد. پس رزرو باید از یک لینک شروع شود، در کمتر از یک دقیقه تمام شود، و روی
بله و پیامک داخلی تکیه کند.
"""

_P8_BODY_FA = """\
بک‌اند NestJS روی PostgreSQL و Prisma، صف BullMQ روی Redis، و یک فرانت React که
هم صفحه‌ی وب است و هم مینی‌اپ بله.

**یک لینک برای هر سالن.** `salonyar.ir/<slug>` صفحه‌ی سالن — نام، آدرس، ساعت
کاری، خدمات و قیمت — را سمت سرور رندر می‌کند (nginx SSI با کش ۳۰ ثانیه‌ای)،
پس لینکی که در واتس‌اپ یا اینستاگرام فرستاده می‌شود خود سالن را نشان می‌دهد،
نه یک صفحه‌ی خالی.

**یک هسته‌ی رزرو، دو در ورودی.** وب و بله از یک مسیر می‌گذرند: «هر آرایشگری»
پیش‌فرض است و نزدیک‌ترین زمان‌های خالی اول می‌آیند. مشتری بدون ورود می‌گردد و
فقط لحظه‌ی ثبت با کد یک‌بارمصرف تأیید می‌شود. در بله شماره با دیالوگ خود بله
تأیید می‌شود، بدون تایپ، و حساب وب و بله یک هویت می‌شوند.

**رزرو تکراری را دیتابیس رد می‌کند، نه کد.** ایجاد، لغو، جابه‌جایی، تأیید و رد
نوبت، با پنجره‌ی لغو مخصوص هر آرایشگر. دو رزرو هم‌زمان روی یک زمان را یک
exclusion constraint در PostgreSQL متوقف می‌کند، و یک تست همزمانی دقیقاً همین را
می‌آزماید.

**پنل موبایل‌محور برای سالن.** تقویم همه‌ی نوبت‌ها، ثبت نوبت تلفنی، و لینک و QR
قابل چاپ. سالن خودش ثبت‌نام می‌کند و یک ویزارد خدمات پیش‌فرض، آرایشگرها و ساعت
کاری را می‌چیند و در پایان لینک وب، QR، لینک بله و متن بیوی اینستاگرام را تحویل
می‌دهد. پلن‌ها دوره‌ی آزمایشی دارند، سقف آرایشگر بر اساس پلن، و تبدیل روزهای
باقی‌مانده هنگام تغییر پلن.

**برای نیامدن مشتری:** یادآوری در بله با پیامک پشتیبان، و بیعانه با کیف پول
بله. اعلان‌ها از صف BullMQ با الگوی outbox می‌روند؛ کد ورود از سرویس «سفیر» بله
و پیامک کاوه‌نگار می‌آید، با محدودیت نرخ. استک production هر روز خودش بکاپ
می‌گیرد و هشدارهایش را به بله می‌فرستد، و API با تنظیمات ناامن اصلاً بالا
نمی‌آید.
"""

# ── GeekWare ────────────────────────────────────────────────────────────────
_P9_PROBLEM_EN = """\
Someone with an idea for a piece of software usually does not know how to write
it down, and a long form sends them away. After the order, it scatters across
phone calls, messengers and a spreadsheet: what state it is in, who answered,
whether the payment arrived. And a payment gateway and an SMS panel are, at the
start, a cost and a hassle that are not needed yet.
"""

_P9_BODY_EN = """\
Node.js and Express 5 rendering on the server, storage in JSON files, and
Bale's bot API — no front-end framework, installable as a PWA.

**An order in three steps, by voice if you like.** One three-step form, shared
by the order page and the MVP card on the home page, where recording a voice
message — with a choice of microphone — can replace typing.

**Two bots, one order.** The admin bot brings each order with its audio and
status buttons: message the customer, a private note, search, `/stats`. A
change in Bale shows in the panel at once, and the other way round. The
customer bot takes orders inside Bale (text or voice), shows their status and
carries messages to the team; after ordering on the site, one "track in Bale"
button links the customer's chat to that order.

**The admin's status is not the customer's.** Internal stages map onto a few
plain ones for the customer, and a public tracking page opens with the
tracking code.

**Payment without a gateway.** Card-to-card: the receipt comes from the site or
Bale, one button accepts or rejects it, and the order moves to "in progress" by
itself. Polite payment reminders go out on days 1, 3, 7 and 14, and only
between 10 am and 8 pm.

Around it: the admin panel, a blog, an FAQ, and a catalogue of software types
and plans.
"""

_P9_PROBLEM_DE = """\
Wer eine Idee für eine Software hat, weiß meist nicht, wie man sie aufschreibt,
und ein langes Formular schreckt ab. Nach der Bestellung zerfällt alles in
Anrufe, Messenger und eine Tabelle: In welchem Stand ist sie, wer hat
geantwortet, ist die Zahlung da? Und ein Zahlungs-Gateway oder ein SMS-Dienst
sind am Anfang Kosten und Aufwand, die es noch nicht braucht.
"""

_P9_BODY_DE = """\
Node.js und Express 5 mit Server-Rendering, Speicherung in JSON-Dateien und
Bales Bot-API — kein Frontend-Framework, als PWA installierbar.

**Eine Bestellung in drei Schritten, gern per Sprache.** Ein dreistufiges
Formular, geteilt von Bestellseite und MVP-Karte der Startseite, in dem eine
Sprachaufnahme — mit Mikrofonauswahl — das Tippen ersetzen kann.

**Zwei Bots, eine Bestellung.** Der Admin-Bot bringt jede Bestellung mit Audio
und Status-Buttons: Nachricht an den Kunden, interne Notiz, Suche, `/stats`.
Eine Änderung in Bale erscheint sofort im Panel und umgekehrt. Der Kunden-Bot
nimmt Bestellungen in Bale entgegen (Text oder Sprache), zeigt ihren Stand und
leitet Nachrichten ans Team weiter; nach einer Bestellung auf der Website
verknüpft ein Button „in Bale verfolgen" den Chat mit genau dieser Bestellung.

**Der Admin-Status ist nicht der Kunden-Status.** Interne Stufen werden auf
wenige einfache für den Kunden abgebildet, und eine öffentliche Seite zeigt den
Stand über den Tracking-Code.

**Zahlung ohne Gateway.** Überweisung von Karte zu Karte: Der Beleg kommt über
Website oder Bale, ein Button nimmt ihn an oder lehnt ihn ab, und die
Bestellung geht von selbst auf „in Arbeit". Höfliche Zahlungserinnerungen an
den Tagen 1, 3, 7 und 14, nur zwischen 10 und 20 Uhr.

Dazu: Admin-Panel, Blog, FAQ und ein Katalog von Softwarearten und Paketen.
"""

_P9_PROBLEM_FA = """\
کسی که ایده‌ی یک نرم‌افزار را دارد معمولاً نمی‌داند چطور بنویسدش، و فرم بلند
فراری‌اش می‌دهد. بعد از ثبت هم سفارش بین تلفن، پیام‌رسان و اکسل پخش می‌شود:
وضعیتش کجاست، چه کسی جواب داده، پرداخت رسیده یا نه. و درگاه پرداخت و پنل
پیامک، برای شروع کار، هزینه و دردسری است که هنوز لازم نیست.
"""

_P9_BODY_FA = """\
Node.js و Express 5 با رندر سمت سرور، ذخیره در فایل JSON، و Bot API بله — بدون
فریم‌ورک فرانت، و قابل نصب به‌عنوان PWA.

**سفارش در سه قدم، با صدا اگر بخواهی.** یک فرم سه‌مرحله‌ای، مشترک بین صفحه‌ی
سفارش و کارت MVP صفحه‌ی اصلی، که در آن ضبط پیام صوتی — با انتخاب میکروفون —
جای نوشتن را می‌گیرد.

**دو ربات، یک سفارش.** ربات ادمین هر سفارش را با فایل صوتی و دکمه‌های وضعیت
می‌آورد: پیام به مشتری، یادداشت داخلی، جستجو، `/stats`. هر تغییر در بله فوراً در
پنل دیده می‌شود و برعکس. ربات مشتری ثبت سفارش از داخل بله (متن یا ویس)، دیدن
وضعیت و پیام به تیم را ممکن می‌کند؛ و بعد از ثبت در سایت، دکمه‌ی «پیگیری سفارش
در بله» چت مشتری را به همان سفارش وصل می‌کند.

**وضعیت ادمین، وضعیت مشتری نیست.** مرحله‌های داخلی به چند مرحله‌ی ساده برای
مشتری نگاشت می‌شوند، و صفحه‌ی پیگیری عمومی با کد پیگیری باز می‌شود.

**پرداخت بدون درگاه.** کارت‌به‌کارت: رسید از سایت یا بله می‌رسد، با یک دکمه
تأیید یا رد می‌شود، و سفارش خودش به «در حال ساخت» می‌رود. یادآوری محترمانه‌ی
پرداخت در روزهای ۱، ۳، ۷ و ۱۴، و فقط بین ۱۰ صبح تا ۸ شب.

کنارش پنل ادمین، وبلاگ، سوالات رایج و کاتالوگ انواع نرم‌افزار و پلن‌ها.
"""

# ── Podcast Workspace ───────────────────────────────────────────────────────
_P10_PROBLEM_EN = """\
A podcast's raw material — voice notes, ideas, notes, episode files — scatters
across folders and messengers, and finding "that sentence in that episode"
means listening again. The fix had to stay on the podcaster's own computer and
work without the internet, transcription included.
"""

_P10_BODY_EN = """\
A Windows desktop app in Python 3.12 and PySide6, on SQLite through SQLAlchemy
and Alembic.

**Clean layers.** Domain, repositories, services and UI are separate, and every
heavy job — transcription, audio processing, import — runs off the UI thread,
so the window never freezes.

**Transcription on the machine.** faster-whisper turns audio into text locally,
and SQLite FTS5 makes every transcript and note searchable in Persian.

**A player made for notes.** A waveform, and notes pinned to an exact second
that jump back to it.

Episodes, seasons, ideas and tags in one place; voice notes imported from a
Bale bot; and a checklist before each episode is published.
"""

_P10_PROBLEM_DE = """\
Das Rohmaterial eines Podcasts — Sprachnotizen, Ideen, Notizen,
Episodendateien — verteilt sich über Ordner und Messenger, und „diesen Satz in
jener Episode" zu finden heißt, noch einmal zuzuhören. Die Lösung musste auf
dem eigenen Rechner bleiben und ohne Internet funktionieren, die Transkription
eingeschlossen.
"""

_P10_BODY_DE = """\
Eine Windows-Desktop-App in Python 3.12 und PySide6, auf SQLite über
SQLAlchemy und Alembic.

**Saubere Schichten.** Domain, Repositories, Services und UI sind getrennt, und
jede schwere Arbeit — Transkription, Audioverarbeitung, Import — läuft außerhalb
des UI-Threads, damit das Fenster nie einfriert.

**Transkription auf dem Rechner.** faster-whisper macht lokal Text aus Audio,
und SQLite FTS5 macht jedes Transkript und jede Notiz auf Persisch durchsuchbar.

**Ein Player für Notizen.** Eine Wellenform und Notizen, die an einer exakten
Sekunde hängen und dorthin zurückspringen.

Episoden, Staffeln, Ideen und Tags an einem Ort; Sprachnotizen aus einem
Bale-Bot importiert; und eine Checkliste vor jeder Veröffentlichung.
"""

_P10_PROBLEM_FA = """\
مواد خام یک پادکست — ویس، ایده، یادداشت، فایل اپیزود — بین پوشه‌ها و پیام‌رسان
پخش می‌شود، و پیدا کردن «آن جمله در آن اپیزود» یعنی دوباره گوش دادن. راه‌حل
باید روی کامپیوتر خود پادکستر بماند و بدون اینترنت کار کند، پیاده‌سازی متن هم.
"""

_P10_BODY_FA = """\
اپ دسکتاپ ویندوز با Python 3.12 و PySide6، روی SQLite از طریق SQLAlchemy و
Alembic.

**لایه‌های تمیز.** domain، repositories، services و ui از هم جدا هستند، و هر کار
سنگین — پیاده‌سازی متن، پردازش صدا، وارد کردن فایل — بیرون از UI thread اجرا
می‌شود تا پنجره هیچ‌وقت قفل نشود.

**پیاده‌سازی متن روی خود دستگاه.** faster-whisper صدا را به‌صورت محلی به متن
تبدیل می‌کند، و SQLite FTS5 هر متن و یادداشتی را به فارسی جستجوپذیر می‌کند.

**پلیری برای یادداشت.** waveform، و یادداشت‌هایی که روی ثانیه‌ی مشخص می‌نشینند
و با یک کلیک به همان‌جا برمی‌گردند.

اپیزودها، فصل‌ها، ایده‌ها و تگ‌ها در یک جا؛ وارد کردن ویس از ربات بله؛ و یک
چک‌لیست پیش از انتشار هر اپیزود.
"""
