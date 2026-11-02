"""Opt-in browser/media integration tests against an isolated Django test DB.

Run: python manage.py test backend.core.tests.test_browser
The browser microphone uses Chromium's synthetic audio input, not a physical device.
"""

import tempfile
from pathlib import Path
from django.test import LiveServerTestCase, override_settings
from django.conf import settings
from playwright.sync_api import sync_playwright, expect
from backend.core.models import User, Material, MaterialVersion
from .test_domain import wav_bytes


class BrowserFlow(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp = tempfile.TemporaryDirectory()
        cls.override = override_settings(PRIVATE_ROOT=Path(cls.temp.name))
        cls.override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        cls.temp.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.admin = User.objects.create_superuser(
            "teacher@example.test", "Browser-test-42!", name="Malika Ustoz"
        )
        self.student = User.objects.create_user(
            "aziza@example.test", "Browser-test-42!", name="Aziza Karimova"
        )
        material = Material.objects.create(
            title="Browser audio fixture",
            status="published",
            description="Synthetic test audio — integration fixture",
        )
        self.version = MaterialVersion.objects.create(
            material=material,
            number=1,
            level="A1-A2",
            script="This audio is used only for automated browser testing.\nListen and repeat.",
            file_key="browser.media",
            mime="audio/wav",
            duration=4,
        )
        material.current_version = self.version
        material.save()
        Path(self.temp.name, "browser.media").write_bytes(wav_bytes(4))
        self.artifacts = settings.BASE_DIR / "artifacts"
        self.artifacts.mkdir(exist_ok=True)
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
            ],
        )

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()
        super().tearDown()

    def login(self, page, email):
        page.goto(self.live_server_url)
        page.wait_for_load_state("networkidle")
        page.get_by_label("Email", exact=True).fill(email)
        page.get_by_label("Parol", exact=True).fill("Browser-test-42!")
        page.get_by_role("button", name="Hisobga kirish", exact=True).click()
        expect(page.get_by_role("heading", name="Salom,")).to_be_visible()

    def test_complete_learning_and_review_flow(self):
        context = self.browser.new_context(
            permissions=["microphone"], viewport={"width": 1440, "height": 1050}
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        self.login(page, self.student.email)
        page.screenshot(path=str(self.artifacts / "library-desktop.png"), full_page=True)
        page.get_by_role("button", name="Browser audio fixture").click()
        page.get_by_role("button", name="Ijro etish", exact=True).click()
        expect(page.get_by_text("Siz 1 marta to‘liq tinglagansiz")).to_be_visible(timeout=14000)
        page.get_by_role("button", name="Ijro etish", exact=True).click()
        expect(page.get_by_text("Siz 2 marta to‘liq tinglagansiz")).to_be_visible(timeout=14000)
        page.get_by_role("button", name="Ovoz yozish", exact=True).click()
        expect(page.get_by_text("Sizni tinglayapmiz…")).to_be_visible()
        page.wait_for_timeout(2100)  # Actual MediaRecorder must accumulate media.
        page.get_by_role("button", name="To‘xtatish", exact=True).click()
        expect(page.get_by_text("Yozuvingizni tinglab ko‘ring.")).to_be_visible()
        page.get_by_role("button", name="Saqlash", exact=True).click()
        expect(page.get_by_text("Ovozingiz saqlandi.")).to_be_visible(timeout=15000)
        page.screenshot(path=str(self.artifacts / "player-desktop.png"), full_page=True)
        self.assertEqual(
            page.request.get(self.live_server_url + "/api/recordings").json()[0]["status"], "saved"
        )
        page.locator(".recorder").get_by_role("button", name="My Records").click()
        expect(page.get_by_role("heading", name="My Records", exact=True)).to_be_visible()
        page.screenshot(path=str(self.artifacts / "records-desktop.png"), full_page=True)
        page.get_by_role("button", name="Tekshirishga yuborish", exact=True).click()
        page.get_by_role("dialog").get_by_role("button", name="Yuborish", exact=True).click()
        expect(page.get_by_text("Tekshirishda", exact=True)).to_be_visible()
        page.get_by_role("button", name="Hisobdan chiqish").click()
        self.login(page, self.admin.email)
        page.get_by_role("button", name="Admin maydoni", exact=True).click()
        page.get_by_role("button", name="Ovoz yozuvlari", exact=True).click()
        page.get_by_role("button", name="Yozuvni baholash").click()
        page.get_by_role("dialog").locator('select[name="score"]').select_option("4")
        page.get_by_label("Yozma izoh").fill(
            "Keep practising your rhythm. A clear first recording!"
        )
        page.get_by_role("dialog").get_by_role("button", name="Saqlash", exact=True).click()
        expect(page.get_by_role("dialog")).to_have_count(0)
        self.assertEqual(
            page.request.get(self.live_server_url + "/api/admin/recordings").json()[0]["review"][
                "score"
            ],
            4,
        )
        page.get_by_role("button", name="Hisobdan chiqish").click()
        self.login(page, self.student.email)
        page.get_by_role("button", name="My Records", exact=True).click()
        expect(
            page.get_by_text("Keep practising your rhythm. A clear first recording!")
        ).to_be_visible()
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=str(self.artifacts / "records-mobile.png"), full_page=True)
        self.assertFalse(page.evaluate("document.documentElement.scrollWidth > innerWidth"))
        self.assertEqual(errors, [])
        context.close()

    def test_admin_upload_groups_and_student_restriction(self):
        context = self.browser.new_context(viewport={"width": 1280, "height": 1000})
        page = context.new_page()
        self.login(page, self.admin.email)
        page.get_by_role("button", name="Admin maydoni", exact=True).click()
        page.get_by_role("button", name="Audio qo‘shish", exact=True).click()
        modal = page.get_by_role("dialog")
        modal.get_by_label("Sarlavha").fill("Uploaded in browser test")
        modal.locator('select[name="level"]').select_option("B1-B2")
        modal.locator('select[name="status"]').select_option("published")
        modal.locator('input[type="file"]').set_input_files(
            {"name": "fixture.wav", "mimeType": "audio/wav", "buffer": wav_bytes(2)}
        )
        modal.get_by_label("Audio skripti").fill("A second browser test fixture.")
        modal.get_by_role("button", name="Saqlash", exact=True).click()
        expect(modal).to_have_count(0)
        expect(page.get_by_text("Uploaded in browser test", exact=True)).to_be_visible()
        page.get_by_role("button", name="Guruhlar", exact=True).click()
        page.get_by_role("button", name="Guruh yaratish").click()
        page.get_by_role("dialog").get_by_label("Guruh nomi").fill("Browser Test Group")
        page.get_by_role("dialog").get_by_role("button", name="Saqlash", exact=True).click()
        expect(page.get_by_role("heading", name="Browser Test Group")).to_be_visible()
        page.get_by_role("button", name="Foydalanuvchilar", exact=True).click()
        page.get_by_role("checkbox", name="Aziza Karimovani tanlash").check()
        page.get_by_role("button", name="Guruhga ko‘chirish").click()
        modal = page.get_by_role("dialog")
        modal.locator('select[name="group_id"]').select_option(label="Browser Test Group")
        modal.get_by_role("button", name="Saqlash", exact=True).click()
        expect(modal).to_have_count(0)
        row = page.get_by_role("row").filter(has_text="aziza@example.test")
        expect(row.get_by_text("Browser Test Group", exact=True)).to_be_visible()
        row.get_by_role("button", name="Darajalar", exact=True).click()
        page.get_by_role("dialog").locator(".restriction-row").filter(has_text="A1-A2").get_by_role(
            "button", name="Yopish", exact=True
        ).click()
        expect(page.get_by_role("dialog")).to_have_count(0)
        page.screenshot(path=str(self.artifacts / "admin-desktop.png"), full_page=True)
        page.get_by_role("button", name="Hisobdan chiqish").click()
        self.login(page, self.student.email)
        expect(page.get_by_text("Browser audio fixture", exact=True)).to_have_count(0)
        expect(page.get_by_role("button", name="A1–A2", exact=True)).to_be_disabled()
        expect(page.get_by_text("Uploaded in browser test", exact=True)).to_be_visible()
        context.close()

    def test_registration_mobile_and_seek_rejection(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto(self.live_server_url)
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(self.artifacts / "login-mobile.png"), full_page=True)
        page.get_by_role("button", name="Ro‘yxatdan o‘tish", exact=True).click()
        page.get_by_label("Ismingiz").fill("New Learner")
        page.get_by_label("Email", exact=True).fill("learner@example.test")
        page.get_by_label("Parol", exact=True).fill("New-learner-42!")
        page.get_by_role("button", name="Hisob yaratish").click()
        expect(page.get_by_role("heading", name="Salom, New.")).to_be_visible()
        expect(page.get_by_role("button", name="Hisobdan chiqish")).to_be_visible()
        page.get_by_role("button", name="Browser audio fixture").click()
        page.get_by_role("button", name="Ijro etish", exact=True).click()
        page.wait_for_timeout(300)
        page.locator("#audio-position").fill("3.8")
        page.wait_for_timeout(1800)
        expect(page.get_by_text("Siz 0 marta to‘liq tinglagansiz")).to_be_visible()
        self.assertEqual(
            page.request.get(self.live_server_url + "/api/materials").json()[0]["count"], 0
        )
        self.assertFalse(page.evaluate("document.documentElement.scrollWidth > innerWidth"))
        context.close()

    def test_navigation_cancels_active_listening_attempt(self):
        context = self.browser.new_context()
        page = context.new_page()
        self.login(page, self.student.email)
        page.get_by_role("button", name="Browser audio fixture").click()
        page.get_by_role("button", name="Ijro etish", exact=True).click()
        expect(page.get_by_text("To‘liq tinglash serverda tekshirilmoqda…")).to_be_visible()
        with page.expect_response(lambda response: response.url.endswith("/cancel")) as cancelled:
            page.get_by_role("button", name="Kutubxona", exact=True).click()
        self.assertEqual(cancelled.value.status, 200)
        context.close()
