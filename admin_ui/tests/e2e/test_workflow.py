import os
from typing import Optional
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from ..factories import (
    UserFactory,
    SeasonsFactory,
    FocusAreaFactory,
    GeophysicalConceptFactory,
    PlatformTypeFactory,
    RepositoryFactory,
    InstrumentFactory,
    GcmdPhenomenonFactory,
    MeasurementRegionFactory,
)

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

        cls.browser = cls.playwright.webkit.launch(timeout=10000)  # slow_mo=600

    def setUp(self):
        self.curator_user = UserFactory.create(username="curator")
        self.seasons_factory = SeasonsFactory.create(short_name="Summer")
        self.focus_area_factory = FocusAreaFactory.create(short_name="Weather")
        self.repository_factory = RepositoryFactory.create(short_name="Unpublished")
        self.geophysical_concepts_factory = GeophysicalConceptFactory.create(short_name="Clouds")
        self.platform_type_factory = PlatformTypeFactory.create(short_name="Jet")
        self.instrument_factory = InstrumentFactory.create(short_name="BBR")
        self.gcmd_phenomenon_factory = GcmdPhenomenonFactory.create(
            category="EARTH SCIENCE > AGRICULTURE > ANIMAL COMMODITIES",
            gcmd_uuid="a943a917-29e0-47e5-a94a-497136f44678",
        )
        self.gcmd_phenomenon_factory = MeasurementRegionFactory.create(
            example="Ionosphere",
            short_name="Ionosphere",
            gcmd_uuid="a943a917-29e0-47e5-a94a-497136f44678",
        )

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
        4. Click the validate button (validates that all required fields are filled out correctly)
            * check sucessful validation toast at the top of the page
        5. Click Save button
            * check that campaign had been successfully created
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

            """1. CREATE A NEW CAMPAIGN"""

            # Navigate to new campaign creation
            page.locator("a", has_text="Add New Campaign +").click()
            expect(page.locator("h1", has_text="Add new Campaign draft")).to_be_visible()

            # Fill in Campaign input fields
            page.fill("[name=model_form-short_name]", "Test Campaign")
            page.fill("[name=model_form-start_date]", "2022-12-22")
            page.fill("[name=model_form-region_description]", "region description")
            page.fill("[name=model_form-lead_investigator]", "Ali Gator")
            page.fill("[name=model_form-focus_phenomena]", "test focus phenomenon")

            # Select boolean dropdowns
            page.select_option("select#id_model_form-ongoing", label="Yes")
            page.select_option("select#id_model_form-nasa_led", label="Yes")

            # select dropdowns based on db options
            page.select_option("select#id_model_form-seasons", label="Summer")
            page.select_option("select#id_model_form-focus_areas", label="Weather")
            page.select_option("select#id_model_form-geophysical_concepts", label="Clouds")
            page.select_option("select#id_model_form-platform_types", label="Jet")
            page.select_option("select#id_model_form-repositories", label="Unpublished")

            # Save new campaign and check successful creation
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Campaign Test Campaign")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            """2. CREATE A DEPENDENT DEPLOYMENT"""

            # Add New Deployment
            page.locator("a", has_text="Add New Deployment +").click()
            expect(page.locator("h1", has_text="Add new Deployment draft")).to_be_visible()

            # Fill in Deployment fields
            page.fill("[name=model_form-short_name]", "Test Deployment")
            page.fill("[name=model_form-start_date]", "2022-12-23")
            page.fill("[name=model_form-end_date]", "2022-12-24")

            # Save new Deployment
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Deployment Test deployment")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            """3. CREATE IOP (Intense Operation Period)"""

            # Add New IOP
            page.locator("a", has_text="Add New IOP +").click()
            expect(page.locator("h1", has_text="Add new IOP draft")).to_be_visible()

            # Fill in Deployment fields
            page.fill("[name=model_form-short_name]", "Test IOP")
            page.fill("[name=model_form-start_date]", "2022-12-23")
            page.fill("[name=model_form-end_date]", "2022-12-24")
            page.fill("[name=model_form-description]", "New Description")
            page.fill("[name=model_form-region_description]", "New Region Description")

            # Save new Deployment
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Iop Test IOP")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            """4. CREATE Collection Period (CDPI)"""
            # Navigate back to test deployment
            page.locator("a.nav-link", has_text="Deployments").click()
            expect(page.locator("h1", has_text="Deployment Drafts")).to_be_visible()
            page.locator("a", has_text="Test Deployment").click()
            expect(page.locator("h1", has_text="Deployment Test deployment")).to_be_visible()

            # Add new Collection Period (CDPI)
            page.locator("a", has_text="Add New CDPI +").click()
            expect(page.locator("h1", has_text="Add new CollectionPeriod draft")).to_be_visible()

            # page.select_option("select#id_model_form-platform", label="Jet")
            # page.select_option("select#id_model_form-instruments", label="BBR")

            page.select_option("select#id_model_form-auto_generated", label="No")

            """5. Add a new Platform * Opens in a new tab"""
            with context.expect_page() as page_info:
                page.locator("a", has_text="+ Add new Platform").click(),
            platform_page = page_info.value
            expect(platform_page.locator("h1", has_text="Add new Platform draft")).to_be_visible()

            # Fill in the platform details
            platform_page.fill("[name=model_form-short_name]", "Brand New Platform")
            platform_page.fill(
                "[name=model_form-description]", "Really special and original description"
            )
            platform_page.select_option("select#id_model_form-stationary", label="No")

            """6. Add a new Instrument Draft"""
            # Navigate to instrument in new page
            page.locator("a.nav-link", has_text="Instruments").click()
            page.locator("a", has_text="Add New Instrument +").click()
            expect(page.locator("h1", has_text="Add new Instrument draft")).to_be_visible()

            # # Fill in the instrument details
            page.fill("[name=model_form-short_name]", "Fancy New Instrument")
            page.fill("[name=model_form-description]", "Brilliant and eloquent description")
            page.fill("[name=model_form-technical_contact]", "A. Vailability")
            page.select_option(
                "select#id_model_form-gcmd_phenomena",
                label="EARTH SCIENCE > AGRICULTURE > ANIMAL COMMODITIES",
            )
            page.fill("[name=model_form-spatial_resolution]", "High")
            page.fill("[name=model_form-temporal_resolution]", "High")

            page.fill("[name=model_form-radiometric_frequency]", "High")
            page.select_option(
                "select#id_model_form-measurement_regions",
                label="Ionosphere",
            )
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Instrument Fancy New Instrument")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            """7. Run DOI fetcher ???"""

            """8. Publish ???"""

    def test_login(self):
        with BrowserContextManager(
            self.browser, self.storage, base_url=self.live_server_url
        ) as context:
            page = context.new_page()
            page.goto("/")
            page.wait_for_url("/")
            assert (
                page.locator("h1", has_text=f"Welcome, {self.curator_user.username}").is_visible()
                is True
            )
            page.close()
