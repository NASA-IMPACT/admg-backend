import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from ..factories import UserFactory

from playwright.sync_api import sync_playwright


class CuratorWorkflowTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()

        cls.curator_user = UserFactory.create(username="curator")

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.webkit.launch(timeout=10000)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.browser.close()
        cls.playwright.stop()

    def test_login(self):
        url = reverse("account_login")
        page = self.browser.new_page()

        page.goto(
            f"{self.live_server_url}{url}?next=/",
        )
        page.locator("[name=login]").wait_for()
        page.fill("[name=login]", "curator")
        page.fill("[name=password]", "password")
        page.locator("[type=submit]").click()
        page.wait_for_url(f"{self.live_server_url}/")
        page.close()
