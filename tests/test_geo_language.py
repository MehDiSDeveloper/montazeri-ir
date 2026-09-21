"""The first-visit language redirect. No database needed: the view is stubbed.

Runs under `manage.py test tests` today and under pytest-django unchanged.
"""

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from apps.core.geo import country_for
from apps.core.middleware import GeoLanguageMiddleware

GEO = {"GEO_COUNTRY_HEADER": "HTTP_CF_IPCOUNTRY", "GEO_DATABASE_PATH": None, "DEBUG": True}
BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/130.0"


@override_settings(**GEO)
class GeoLanguageMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = GeoLanguageMiddleware(lambda request: HttpResponse("page"))

    def visit(self, path="/", country=None, ua=BROWSER, cookies=None, **extra):
        headers = {"HTTP_USER_AGENT": ua, **extra}
        if country is not None:
            headers["HTTP_CF_IPCOUNTRY"] = country
        request = self.factory.get(path, **headers)
        request.COOKIES.update(cookies or {})
        return self.middleware(request)

    def assertStays(self, response):
        self.assertEqual(response.status_code, 200)

    def test_iran_stays_on_persian(self):
        self.assertStays(self.visit(country="IR"))

    def test_germany_goes_to_german(self):
        response = self.visit(country="DE")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/de/")

    def test_anywhere_else_goes_to_english(self):
        self.assertEqual(self.visit(country="US")["Location"], "/en/")

    def test_deep_link_keeps_page_and_query(self):
        self.assertEqual(self.visit("/projects/?tag=django", country="FR")["Location"], "/en/projects/?tag=django")

    def test_unknown_country_changes_nothing(self):
        self.assertStays(self.visit())
        self.assertStays(self.visit(country="XX"))

    def test_explicit_language_url_is_respected(self):
        self.assertStays(self.visit("/en/", country="IR"))
        self.assertStays(self.visit("/de/", country="US"))

    def test_decides_only_once(self):
        response = self.visit(country="DE")
        self.assertIn("montazeri_geo", response.cookies)
        self.assertStays(self.visit(country="DE", cookies={"montazeri_geo": "1"}))

    def test_cookie_is_set_even_without_a_redirect(self):
        self.assertIn("montazeri_geo", self.visit("/en/", country="DE").cookies)

    def test_click_inside_the_site_is_not_redirected(self):
        self.assertStays(self.visit(country="DE", HTTP_REFERER="http://testserver/de/"))

    def test_crawlers_are_never_redirected(self):
        self.assertStays(self.visit(country="US", ua="Mozilla/5.0 (compatible; Googlebot/2.1)"))

    def test_machine_endpoints_are_left_alone(self):
        self.assertStays(self.visit("/sitemap.xml", country="US"))
        self.assertStays(self.visit("/admin/", country="US"))

    def test_redirect_is_not_publicly_cacheable(self):
        response = self.visit(country="US")
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("Cookie", response["Vary"])

    def test_post_is_never_redirected(self):
        request = self.factory.post("/contact/", HTTP_USER_AGENT=BROWSER, HTTP_CF_IPCOUNTRY="US")
        self.assertStays(self.middleware(request))

    @override_settings(GEO_LANGUAGE_ENABLED=False)
    def test_switch_off(self):
        self.assertStays(self.visit(country="US"))


@override_settings(GEO_COUNTRY_HEADER="", GEO_DATABASE_PATH=None, GEO_CLIENT_IP_HEADER="")
class CountryResolutionTests(SimpleTestCase):
    def test_nothing_configured_is_unknown(self):
        request = RequestFactory().get("/", REMOTE_ADDR="5.160.0.1")
        self.assertIsNone(country_for(request))

    @override_settings(GEO_COUNTRY_HEADER="HTTP_CF_IPCOUNTRY")
    def test_header_is_normalised(self):
        request = RequestFactory().get("/", HTTP_CF_IPCOUNTRY=" de ")
        self.assertEqual(country_for(request), "DE")
