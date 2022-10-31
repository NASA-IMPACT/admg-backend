# to run this test file, use 'pytest -k cmr'

from admg_webapp.users.tests.factories import UserFactory
from data_models.tests.factories import (
    InstrumentFactory,
    PlatformFactory,
    CampaignFactory,
    DeploymentFactory,
    CollectionPeriodFactory,
    DATAMODELS_FACTORIES,
)
from data_models.tests.factories import *
from data_models.models import Instrument, Platform, Campaign, Deployment, CollectionPeriod


@pytest.mark.django_db
@pytest.mark.parametrize("factory", DATAMODELS_FACTORIES)
class TestCMRRecommender:
    @staticmethod
    def draft_updater(draft, overrides):
        draft.update = {**draft.update, **overrides}
        draft.save()

    @staticmethod
    def create_test_data(self):
        instrument_draft = self.make_create_change_object(InstrumentFactory)
        platform_draft = self.make_create_change_object(PlatformFactory)
        campaign_draft = self.make_create_change_object(CampaignFactory)
        deployment_draft = self.make_create_change_object(DeploymentFactory)
        collection_period_draft = self.make_create_change_object(CollectionPeriodFactory)

        Instrument.objects.all().delete()
        Platform.objects.all().delete()
        Campaign.objects.all().delete()
        Deployment.objects.all().delete()
        CollectionPeriod.objects.all().delete()

        self.draft_updater(
            collection_period_draft,
            {
                'instruments': [instrument_draft.uuid],
                'platform': platform_draft.uuid,
                'deployment': deployment_draft.uuid,
            },
        )
        self.draft_updater(
            deployment_draft,
            {
                'campaign': campaign_draft.uuid,
            },
        )
        self.draft_updater(
            platform_draft,
            {
                'short_name': 'ALTUS',
            },
        )
        self.draft_updater(
            instrument_draft,
            {
                'short_name': 'GPS',
            },
        )
        self.draft_updater(
            campaign_draft,
            {
                'short_name': 'ACES',
            },
        )

        # look in the admg_webapp/users/models.py to find this stuff
        admin_user = UserFactory(role=1)

        instrument_draft.publish(admin_user=admin_user)
        platform_draft.publish(admin_user=admin_user)
        campaign_draft.publish(admin_user=admin_user)
        deployment_draft.publish(admin_user=admin_user)
        collection_period_draft.publish(admin_user=admin_user)
