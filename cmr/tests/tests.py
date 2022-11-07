# to run this test file, use 'pytest -k cmr'
from argparse import Action
import pytest
from admg_webapp.users.tests.factories import UserFactory
from data_models.tests.factories import (
    InstrumentFactory,
    PlatformFactory,
    CampaignFactory,
    DeploymentFactory,
    CollectionPeriodFactory,
    # DATAMODELS_FACTORIES,
)
from data_models.tests.factories import *
from data_models.models import Instrument, Platform, Campaign, Deployment, CollectionPeriod
from api_app.models import Change
from cmr.doi_matching import DoiMatcher
from cmr.tasks import match_dois
import json


@pytest.mark.django_db
# @pytest.mark.parametrize("factory", DATAMODELS_FACTORIES)
class TestCMRRecommender:
    @staticmethod
    def draft_updater(draft, overrides):
        draft.update = {**draft.update, **overrides}
        draft.save()

    @staticmethod
    def make_create_change_object(factory):
        """make a Change.Actions.CREATE change object to use during testing"""
        content_type = ContentType.objects.get_for_model(factory._meta.model)

        return Change.objects.create(
            content_type=content_type,
            status=Change.Statuses.CREATED,
            action="Create",
            update=factory.as_change_dict(),
        )

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
                'instruments': [str(instrument_draft.uuid)],
                'platform': str(platform_draft.uuid),
                'deployment': str(deployment_draft.uuid),
            },
        )
        self.draft_updater(
            deployment_draft,
            {
                'campaign': str(campaign_draft.uuid),
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

        instrument_draft.publish(user=admin_user)
        platform_draft.publish(user=admin_user)
        campaign_draft.publish(user=admin_user)
        deployment_draft.publish(user=admin_user)
        collection_period_draft.publish(user=admin_user)

    def test_data(self):
        self.create_test_data()
        # test = Instrument.objects.get()
        assert Change.objects.of_type(Instrument).count() == 1
        assert Change.objects.of_type(Platform).count() == 1
        assert Change.objects.of_type(Campaign).count() == 1
        assert Change.objects.of_type(Deployment).count() == 1
        assert Change.objects.of_type(CollectionPeriod).count() == 1

        assert Change.objects.of_type(Instrument).first().update["short_name"] == 'GPS'
        assert Change.objects.of_type(Platform).first().update["short_name"] == 'ALTUS'
        assert Change.objects.of_type(Campaign).first().update["short_name"] == 'ACES'

    # def test_update(self):
    #     self.create_test_data()
    #     campaign_uuid = Campaign.objects.get(short_name="ACES").uuid
    #     recommendations = match_dois('campaign', str(campaign_uuid))
    #     existing_data = Change.objects.filter(update__campaigns__contains=str(campaign_uuid))
    #     print(existing_data)
    #     # doi_drafts = Change.objects.filter(
    #     #     action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
    #     #     update__concept_id=recommendations[0]['concept_id'],
    #     # )
    #     assert existing_data[0].action == 'Create'

    def test_add_to_db(self):
        self.create_test_data()
        matcher = DoiMatcher()
        campaign_uuid = Campaign.objects.get(short_name="ACES").uuid
        # campaign_uuid = (
        #     Change.objects.of_type(Campaign).all().filter(update__short_name="ACES")[0].uuid
        # )
        recommendations = match_dois('campaign', str(campaign_uuid))
        # existing_data = Change.objects.filter(update__campaigns__contains=str(campaign_uuid))

        # existing_data = Change.objects.of_type(Campaign).all()

        doi_drafts = Change.objects.filter(
            content_type__model='doi',
            action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
            update__concept_id=recommendations[0]['concept_id'],
        )

        if unpublished_creates := (
            doi_drafts.filter(action=Change.Actions.CREATE)
            .exclude(status=Change.Statuses.PUBLISHED)
            .first()
        ):
            for field in matcher.fields_to_compare:
                unpublished_creates.update[field] = recommendations[0][field]
            for field in matcher.fields_to_merge:
                unpublished_creates.update[field].append(recommendations[0][field])
            unpublished_creates.action = Change.Actions.CREATE
            unpublished_creates.save()

            assert unpublished_creates.action == Change.Actions.CREATE
        elif published_create := doi_drafts.filter(
            action=Change.Actions.CREATE, status=Change.Statuses.PUBLISHED
        ).first():
            for field in matcher.fields_to_compare:
                if published_create.update[field] != recommendations[0][field]:
                    doi_obj = Change(
                        content_type=ContentType.objects.get(model="doi"),
                        model_instance_uuid=published_create.uuid,
                        update=json.loads(json.dumps(recommendations[0])),
                        status=Change.Statuses.CREATED,
                        action=Change.Actions.UPDATE,
                    )
                    doi_obj.save()
                    break
            assert published_create.status == Change.Statuses.CREATED
            assert published_create.action == Change.Actions.UPDATE
        else:
            doi_obj = Change(
                content_type=ContentType.objects.get(model="doi"),
                update=json.loads(json.dumps(recommendations[0])),
                status=Change.Statuses.CREATED,
                action=Change.Actions.CREATE,
            )
            doi_obj.save()

            assert doi_obj.status == Change.Statuses.CREATED
            assert doi_obj.action == Change.Actions.CREATE
