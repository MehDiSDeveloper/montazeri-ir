"""The admin's pictures and files say what they are doing.

A chosen file only travels when the form is saved; these pin that every file
field in the admin gets the widget that says so, that the profile form starts
with its pictures, that the save lands the file and the page it returns to
shows it, and that "clear" empties it.
"""

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.content.models import Post, Profile, Project

MEDIA = tempfile.mkdtemp()


def png(name="me.png"):
    buf = BytesIO()
    Image.new("RGB", (4, 4), "teal").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA, GEO_LANGUAGE_ENABLED=False)
class AdminUploadTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        user = get_user_model().objects.create_superuser("owner", "o@example.com", "pw")
        self.client.force_login(user)
        p = Profile.load()
        p.full_name_fa, p.headline_fa, p.intro_fa = "مهدی منتظری", "مهندس بک‌اند", "معرفی"
        p.save()
        self.url = f"/admin/content/profile/{p.pk}/change/"

    def form(self, **extra):
        return {
            "full_name_fa": "مهدی منتظری", "headline_fa": "مهندس بک‌اند", "intro_fa": "معرفی",
            "is_available": "on", **extra,
        }

    def test_the_list_opens_the_form(self):
        self.assertRedirects(self.client.get("/admin/content/profile/"), self.url)

    def test_the_form_starts_with_the_pictures_and_explains_itself(self):
        page = self.client.get(self.url).content.decode()
        self.assertIn("js/admin-upload.js", page)
        self.assertEqual(page.count("data-upload>"), 3)  # avatar, share picture, résumé
        self.assertLess(page.index('name="avatar"'), page.index('name="full_name_fa"'))
        self.assertIn("/card/", page)  # the avatar's help says where it shows
        self.assertEqual(page.count('name="_continue"'), 2)  # save_on_top

    def test_save_puts_the_picture_on_the_site_and_shows_it(self):
        response = self.client.post(self.url, self.form(avatar=png()), follow=True)
        self.assertEqual(response.status_code, 200)
        avatar = Profile.load().avatar
        self.assertTrue(avatar.name.startswith("profile/me"))
        self.assertContains(response, 'class="upload-live"')
        self.assertContains(response, avatar.url)
        self.assertContains(self.client.get("/"), avatar.url)

    def test_clear_removes_it(self):
        self.client.post(self.url, self.form(avatar=png()))
        self.client.post(self.url, self.form(**{"avatar-clear": "on"}))
        self.assertFalse(Profile.load().avatar)

    def test_a_file_that_is_not_a_picture_gets_no_thumbnail(self):
        pdf = SimpleUploadedFile("cv.pdf", b"%PDF-1.4\n", content_type="application/pdf")
        self.client.post(self.url, self.form(resume_file=pdf))
        self.assertTrue(Profile.load().resume_file)
        self.assertNotContains(self.client.get(self.url), 'class="upload-live"')

    def test_every_other_file_field_uses_the_widget(self):
        project = Project.objects.create(slug="p", title_fa="پروژه", summary_fa="خلاصه")
        post = Post.objects.create(slug="x", title_fa="نوشته", body_fa="متن")
        for url in (
            f"/admin/content/project/{project.pk}/change/",
            f"/admin/content/post/{post.pk}/change/",
        ):
            with self.subTest(url=url):
                page = self.client.get(url).content.decode()
                self.assertIn("js/admin-upload.js", page)
                self.assertIn("data-upload>", page)
                self.assertIn("با «ذخیره» اعمال می‌شود", page)
        # the post's own cover plus its body-image inline rows
        page = self.client.get(f"/admin/content/post/{post.pk}/change/").content.decode()
        self.assertIn('name="images-0-image"', page)
        self.assertGreaterEqual(page.count("data-upload>"), 2)
