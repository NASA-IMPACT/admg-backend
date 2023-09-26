import os
from typing import Optional

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from celery.contrib.testing.worker import start_worker

from admg_webapp.users.models import User
from config.celery_app import app
from playwright.sync_api import Browser, StorageState, sync_playwright, expect
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


class BrowserContextManager:
    def __init__(
        self, browser: Browser, storage_state: StorageState, base_url: Optional[str] = None
    ):
        self.browser = browser
        self.storage_state = storage_state
        self.base_url = base_url

    def __enter__(self):
        self.context = self.browser.new_context(
            storage_state=self.storage_state, base_url=self.base_url, record_video_dir="videos/"
        )
        return self.context

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.context.close()


class CuratorWorkflowTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.webkit.launch(timeout=10000)  # slow_mo=600
        cls.celery_worker = start_worker(app, perform_ping_check=False)
        cls.celery_worker.__enter__()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.celery_worker.__exit__(None, None, None)

    def setUp(self):
        self.curator_user = UserFactory.create(username="curator", role=User.Roles.ADMIN)
        self.seasons_factory = SeasonsFactory.create(short_name="Test_Summer")
        self.focus_area_factory = FocusAreaFactory.create(short_name="Test_Stormsystem")
        self.repository_factory = RepositoryFactory.create(short_name="Test_Unpubished")
        self.geophysical_concepts_factory = GeophysicalConceptFactory.create(
            short_name="Test_Clouds"
        )
        self.platform_type_factory = PlatformTypeFactory.create(short_name="Test_Jet")
        self.instrument_factory = InstrumentFactory.create(short_name="Test_BBR")
        self.gcmd_phenomenon_factory = GcmdPhenomenonFactory.create(
            category="TEST > EARTH SCIENCE > AGRICULTURE > ANIMAL COMMODITIES",
            gcmd_uuid="a943a917-29e0-47e5-a94a-497136f44678",
        )
        self.gcmd_phenomenon_factory = MeasurementRegionFactory.create(
            example="Test Ionosphere",
            short_name="Test Ionosphere",
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
                f"{self.live_server_url}{reverse('canonical-list', kwargs={'model':'campaign'})}"
            )

            """1. CREATE A NEW CAMPAIGN"""

            # Navigate to new campaign creation
            page.locator("a", has_text="New Campaign").click()
            expect(page.locator("h1", has_text="Add new Campaign draft")).to_be_visible()

            # Fill in Campaign input fields
            page.fill("[name=model_form-short_name]", "Test Campaign")
            page.fill("[name=model_form-start_date]", "2022-12-22")
            page.fill("[name=model_form-end_date]", "2022-12-31")
            page.fill("[name=model_form-region_description]", "region description")
            page.fill("[name=model_form-lead_investigator]", "Ali Gator")
            page.fill("[name=model_form-focus_phenomena]", "test focus phenomenon")

            # Select boolean dropdowns
            page.select_option("select#id_model_form-ongoing", label="Yes")
            page.select_option("select#id_model_form-nasa_led", label="Yes")

            # select dropdowns based on db options
            page.select_option("select#id_model_form-seasons", label="Test_Summer")
            page.select_option("select#id_model_form-focus_areas", label="Test_Stormsystem")
            page.select_option("select#id_model_form-geophysical_concepts", label="Test_Clouds")
            page.select_option("select#id_model_form-platform_types", label="Test_Jet")
            page.select_option("select#id_model_form-repositories", label="Test_Unpubished")

            # Save new campaign and check successful creation
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Test Campaign")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            """2. CREATE A DEPENDENT DEPLOYMENT"""

            # Add New Deployment
            page.locator("a", has_text="Add New Deployment +").click()
            expect(page.locator("h1", has_text="Add new Deployment draft")).to_be_visible()

            # Fill in Deployment fields
            page.fill("[name=model_form-short_name]", "Test Deployment")
            page.fill("[name=model_form-start_date]", "2022-12-23")
            page.fill("[name=model_form-end_date]", "2022-12-24")
            page.fill("[name=model_form-spatial_bounds]", "0,0,0,0")

            # Save new Deployment
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Test deployment")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            """3. CREATE IOP (Intense Operation Period)"""

            # Add New IOP
            page.locator("a", has_text="Add New IOP +").click()
            expect(page.locator("h1", has_text="Add new IOP draft")).to_be_visible()

            # Fill in IOP fields
            page.fill("[name=model_form-short_name]", "Test IOP")
            page.fill("[name=model_form-start_date]", "2022-12-23")
            page.fill("[name=model_form-end_date]", "2022-12-24")
            page.fill("[name=model_form-description]", "New Description")
            page.fill("[name=model_form-region_description]", "New Region Description")

            # Save new IOP
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Test IOP")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            # """4. CREATE Collection Period (CDPI)"""
            # # Navigate to test deployment tab
            page.locator("a.nav-link", has_text="Campaigns").click()
            page.locator("a", has_text="Test Campaign").first.click()
            page.locator("a.nav-link", has_text="Details").click()
            # expect(page.locator("h4", has_text="Deployments")).to_be_visible()
            # page.locator("a", has_text="Test Deployment").click()
            # expect(page.locator("h1", has_text="Test deployment")).to_be_visible()

            # # Add new Collection Period (CDPI)
            # page.locator("a", has_text="Add New CDPI +").click()
            # expect(page.locator("h1", has_text="Add new CollectionPeriod draft")).to_be_visible()

            # page.select_option("select#id_model_form-platform", label="Test_Jet")
            # page.select_option("select#id_model_form-instruments", label="Test_BBR")

            # page.select_option("select#id_model_form-auto_generated", label="No")

            """5. Add a new Platform * Opens in a new tab"""
            page.locator("a.nav-link:visible", has_text="Platforms").click()
            page.locator("a", has_text="New Platform").click()
            # platform_page = page_info.value
            expect(page.locator("h1", has_text="Add new Platform draft")).to_be_visible()

            # Fill in the platform details
            page.fill("[name=model_form-short_name]", "Brand New Platform")
            page.fill("[name=model_form-description]", "Really special and original description")
            page.select_option("select#id_model_form-stationary", label="No")
            page.locator('button:has-text("Save")').click()

            page.locator("a.nav-link:visible", has_text="Platforms").click()
            # expect(page.locator("a", has_text="Brand New Platform")).to_be_visible()

            """6. Add a new Instrument Draft"""
            # Navigate to instrument in new page
            page.locator("a.nav-link:visible", has_text="Instruments").click()
            page.locator("a", has_text="New Instrument").click()
            expect(page.locator("h1", has_text="Add new Instrument draft")).to_be_visible()

            # # Fill in the instrument details
            page.fill("[name=model_form-short_name]", "Fancy New Instrument")
            page.fill("[name=model_form-description]", "Brilliant and eloquent description")
            page.fill("[name=model_form-technical_contact]", "A. Vailability")
            page.select_option(
                "select#id_model_form-gcmd_phenomena",
                label="TEST > EARTH SCIENCE > AGRICULTURE > ANIMAL COMMODITIES",
            )
            page.fill("[name=model_form-spatial_resolution]", "High")
            page.fill("[name=model_form-temporal_resolution]", "High")

            page.fill("[name=model_form-radiometric_frequency]", "High")
            page.select_option(
                "select#id_model_form-measurement_regions",
                label="Test Ionosphere",
            )
            page.locator('button:has-text("Save")').click()
            expect(page.locator("h1", has_text="Fancy New Instrument")).to_be_visible()
            expect(page.locator(".alert-success", has_text="Successfully saved")).to_be_visible()

            """7. Run DOI fetcher"""
            # Navigate to DOI dashboard tab
            page.locator("a.nav-link", has_text="Campaigns").click()
            page.locator("a", has_text="Test Campaign").first.click()
            expect(page.locator("h1", has_text="Test Campaign")).to_be_visible()
            # Run DOI fetcher (filter out nav_links with properties :hidden)
            page.locator("a:visible").get_by_text("DOIs").click()
            expect(page.locator("h2", has_text="Generate DOI Recommendations")).to_be_visible()
            page.locator("button", has_text="Generate DOIs +").click()

            expect(page.locator("h5", has_text="STARTED")).to_be_visible()

            # Polling of DOIs fetcher until complete (will time out after 10 sec)
            # check every 500 ms.

            def dois_complete():
                fetch_complete = page.locator("h5", has_text="SUCCESS")

                try:
                    fetch_complete.wait_for(timeout=500)
                    return True
                except:  # noqa: E722
                    return False

            retry_limit = 20
            retry_attempts = 0

            while not dois_complete() and retry_limit > retry_attempts:
                retry_attempts += 1
                page.reload()
                print("DOIs have not completed fetching. Retrying...")

            expect(page.locator("h5", has_text="SUCCESS")).to_be_visible()

            """8. Publish Campaign"""
            # Navigate back to campaign
            page.locator("a.nav-link", has_text="Campaigns").click()
            page.locator("a", has_text="Test Campaign").first.click()

            # Publication steps
            # 8.1 Ready for staff Review
            page.locator('button:has-text("Approval Actions")').click()
            page.get_by_label("Ready for staff review").check()
            page.locator('button', has_text="Submit").click()

            # 8.2 Claim for Staff Review
            page.locator('button:has-text("Approval Actions")').click()
            page.get_by_label("Claim for Staff Review").check()
            page.locator('button', has_text="Submit").click()

            # 8.3 Ready for Admin Review
            page.locator('button:has-text("Approval Actions")').click()
            page.get_by_label("Ready for Admin Review").check()
            page.locator('button', has_text="Submit").click()

            # 8.4 Claim for Admin Review
            page.locator('button:has-text("Approval Actions")').click()
            page.get_by_label("Claim for Admin Review").check()
            page.locator('button', has_text="Submit").click()

            # 8.5 Publish to production
            page.locator('button:has-text("Approval Actions")').click()
            page.get_by_label("Publish to production").check()
            page.locator('button', has_text="Submit").click()

            # Navigate back to overview
            page.locator("a.nav-link", has_text="Campaigns").click()
