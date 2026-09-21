"""Every page answers, the services offer works, and posts tell search engines the truth.

These need a database, so they are TestCase rather than SimpleTestCase — still
the stock Django class, which pytest-django runs unchanged.
"""

from django.test import TestCase, override_settings

from apps.content.models import Post, Profile, Service
from apps.core.templatetags.site_tags import md_breaks_field


@override_settings(GEO_LANGUAGE_ENABLED=False, SITE_URL="https://montazeri.ir")
class PageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        p = Profile.load()
        p.full_name_fa, p.full_name_en = "مهدی منتظری", "Mahdi Montazeri"
        p.headline_fa, p.intro_fa = "مهندس بک‌اند", "معرفی"
        p.offer_title_fa, p.offer_title_en = "پروژه از صفر تا صد", "Projects end to end"
        p.offer_lede_fa = "توضیح"
        p.save()
        Service.objects.create(title_fa="از صفر تا صد", body_fa="همه‌ی مسیر", icon="layers")
        cls.fa_post = Post.objects.create(slug="both", title_fa="نوشته", body_fa="متن", title_en="Post", body_en="Text")
        cls.en_post = Post.objects.create(
            slug="english-only",
            title_en="English only",
            body_en="See https://example.com/x.",
            original_url="https://www.linkedin.com/posts/abc",
        )

    def test_every_page_answers_in_every_language(self):
        pages = ["", "about/", "services/", "contact/", "card/", "resume/", "projects/", "blog/", "blog/both/", "blog/english-only/"]
        for prefix in ("/", "/en/", "/de/"):
            for page in pages:
                with self.subTest(url=prefix + page):
                    self.assertEqual(self.client.get(prefix + page).status_code, 200)

    def test_services_disappear_without_an_offer(self):
        Profile.objects.update(offer_title_fa="", offer_title_en="")
        self.assertEqual(self.client.get("/services/").status_code, 404)
        self.assertNotContains(self.client.get("/"), 'href="/services/"')

    def test_start_a_project_fills_the_subject(self):
        self.assertContains(self.client.get("/en/contact/?topic=project"), 'value="Project enquiry"')

    def test_hreflang_and_canonical_ignore_the_query_string(self):
        html = self.client.get("/en/projects/?tag=python").content.decode()
        self.assertIn('<link rel="canonical" href="https://montazeri.ir/en/projects/">', html)
        self.assertIn('hreflang="x-default" href="https://montazeri.ir/projects/"', html)
        self.assertNotIn("?tag=python\"", html.split("</head>")[0])

    def test_untranslated_post_points_canonical_at_its_real_language(self):
        html = self.client.get("/blog/english-only/").content.decode()
        self.assertIn('<link rel="canonical" href="https://montazeri.ir/en/blog/english-only/">', html)
        # The language switcher in the body still links to /blog/…; only the head's alternates must not.
        self.assertNotIn('<link rel="alternate" hreflang="fa"', html)
        self.assertIn('<link rel="alternate" hreflang="en"', html)
        self.assertIn('lang="en" dir="ltr"', html)

    def test_post_links_to_its_original(self):
        response = self.client.get("/en/blog/english-only/")
        self.assertContains(response, 'href="https://www.linkedin.com/posts/abc"')
        self.assertContains(response, "Originally posted on LinkedIn")
        self.assertContains(response, '"@type":"BlogPosting"')

    def test_sitemap_lists_a_post_only_in_its_languages(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        # The host is the request's (testserver here); the paths are the point.
        self.assertEqual(xml.count("blog/english-only/</loc>"), 1)
        self.assertIn("/en/blog/english-only/</loc>", xml)
        self.assertIn("/services/</loc>", xml)

    def test_post_needs_one_complete_language(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Post(slug="empty").clean()
        with self.assertRaises(ValidationError):
            Post(slug="half", title_de="Titel").clean()


class MarkdownTests(TestCase):
    def test_bare_links_line_breaks_and_images(self):
        post = Post(title_en="t", body_en="line one\nline two https://example.com/a.\n\n![pic](/media/p.png)")
        html = str(md_breaks_field(post, "body"))
        self.assertIn("<br", html)
        self.assertIn('<a href="https://example.com/a" rel="noopener" target="_blank">https://example.com/a</a>.', html)
        self.assertIn('loading="lazy"', html)
