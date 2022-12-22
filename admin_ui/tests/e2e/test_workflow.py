import os
from typing import Optional
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from ..factories import UserFactory

from playwright.sync_api import Browser, StorageState, sync_playwright, expect


class BrowserContextManager:
    def __init__(
        self, browser: Browser, storage_state: StorageState, base_url: Optional[str] = None
    ):
        self.browser = browser
        self.storage_state = storage_state
        self.base_url = base_url

        print(f"Storage cookies")
        print(storage_state)

    def __enter__(self):
        self.context = self.browser.new_context(
            storage_state=self.storage_state, base_url=self.base_url, record_video_dir="videos/"
        )
        print("Context cookies")
        print(self.context.cookies())
        return self.context

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.context.close()


class CuratorWorkflowTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        print("setting up test data")

        cls.playwright = sync_playwright().start()

        cls.browser = cls.playwright.webkit.launch(timeout=10000)

    def setUp(self):
        self.curator_user = UserFactory.create(username="curator")
        self.storage = self.login(
            self.browser,
            self.curator_user.username,
            "password",
        )

    @classmethod
    def login(cls, browser: Browser, username: str, password: str, next_path="/") -> StorageState:
        url = reverse("account_login")
        context = browser.new_context()
        page = context.new_page()

        page.goto(
            f"{cls.live_server_url}{url}?next={next_path}",
        )
        page.locator("[name=login]").wait_for()
        page.fill("[name=login]", username)
        page.fill("[name=password]", password)
        page.locator("[type=submit]").click()
        page.wait_for_url(f"{cls.live_server_url}/")
        storage_state = context.storage_state()
        page.close()
        context.close()
        return storage_state

    def test_create_campaign(self):
        """
        Create a draft Campaign.

        Steps:

        1. Click Campaigns in nav
        2. Click Add New Campaign link
        3. Fill in required fields:
            * Campaign Short Name
            * Start date
            * Region description
            * Focus phenomena
            * Principal Investigator
            * Is this field investigation currently ongoing?
            * Is this a NASA-led field investigation?

            * Season(s) of Study
            * NASA Earth Science Focus Area(s)
            * Geophysical concepts
            * Platform types
            * Data Repository(ies)
        4. Click Save button
        """
        with BrowserContextManager(
            self.browser, self.storage, base_url=self.live_server_url
        ) as context:
            page = context.new_page()
            page.goto("/")
            page.locator("a.nav-link", has_text="Campaigns").click()
            page.wait_for_url(
                f"{self.live_server_url}{reverse('change-list', kwargs={'model':'campaign'})}"
            )
            # Navigate to new campaign creation
            page.locator("a", has_text="Add New Campaign +").click()
            expect(page.locator("h1", has_text="Add new Campaign draft")).to_be_visible()

            # Fill in Campaign input fields
            page.fill("[name=model_form-short_name]", "test_campaign")
            page.fill("[name=model_form-start_date]", "2022-12-22")
            page.fill("[name=model_form-region_description]", "region description")
            page.fill("[name=model_form-lead_investigator]", "Ali Gator")
            page.fill("[name=model_form-focus_phenomena]", "test focus phenomenon")

            # Select boolean dropdowns
            page.select_option("select#id_model_form-ongoing", label="Yes")
            page.select_option("select#id_model_form-nasa_led", label="Yes")

            # select dropdowns based on db options
            # page.select_option("select#id_model_form-seasons", label="?")
            # page.select_option("select#id_model_form-focus_areas", label="?")
            # page.select_option("select#id_model_form-geophysical_concepts", label="?")
            # page.select_option("select#id_model_form-platform_types", label="?")
            # page.select_option("select#id_model_form-repositories", label="?")

    def test_login(self):
        with BrowserContextManager(
            self.browser, self.storage, base_url=self.live_server_url
        ) as context:
            page = context.new_page()
            resp = page.goto("/")
            print(resp.status)
            page.wait_for_url("/")
            assert (
                page.locator("h1", has_text=f"Welcome, {self.curator_user.username}").is_visible()
                is True
            )
            page.close()
