# to run this test file, use 'pytest -k cmr'
from nis import match
import pytest
from django.contrib.contenttypes.models import ContentType
from admg_webapp.users.tests.factories import UserFactory
from data_models.tests.factories import (
    InstrumentFactory,
    PlatformFactory,
    CampaignFactory,
    DeploymentFactory,
    CollectionPeriodFactory,
)
from data_models.models import Instrument, Platform, Campaign, Deployment, CollectionPeriod, DOI
from api_app.models import Change
from cmr.doi_matching import DoiMatcher
from cmr.tasks import match_dois
import json


@pytest.mark.django_db
class TestCMRRecommender:
    @staticmethod
    def draft_updater(draft, overrides):
        """overrides the test data created"""
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

    def make_cmr_recommendation(self):
        campaign_uuid = Campaign.objects.get(short_name="ACES").uuid
        recommendations = match_dois('campaign', str(campaign_uuid))
        # data_file = open('datarecommended.txt', 'wt')
        # for i in recommendations:
        #     data_file.write(json.dumps(i))
        # data_file.close()
        file_path = 'cmr_recommendations.json'
        json.dump(recommendations, open(file_path, 'w'))

    def make_hashes(self, query_object):
        return {draft.uuid: hash(draft) for draft in query_object}

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

    def test_no_drafts(self):
        self.create_test_data()
        campaign_uuid = Campaign.objects.get(short_name="ACES").uuid
        aces_doi_data = Change.objects.filter(content_type__model='doi').filter(
            update__campaigns__contains=str(campaign_uuid)
        )
        assert len(aces_doi_data) == 0
        self.make_cmr_recommendation()
        data = json.load(open('cmr_recommendations.json', 'r'))
        assert len(data) == 6

    def test_unpublished_create(self):
        self.test_no_drafts()
        matcher = DoiMatcher()
        campaign_uuid = Campaign.objects.get(short_name="ACES").uuid
        query_object = Change.objects.of_type(DOI).filter(
            update__campaigns__contains=str(campaign_uuid)
        )
        hashes = self.make_hashes(query_object)
        with open('cmr_recommendations.json') as f:
            data = json.load(f)
        for i in data:
            matcher.add_to_db(i)
        print(len(hashes))
        new_hashes = self.make_hashes(
            Change.objects.filter(content_type__model='doi').filter(
                update__campaigns__contains=str(campaign_uuid)
            )
        )
        assert len(hashes) == len(data)
        assert hashes == new_hashes

        query_object.first().update['cmr_plats_and_insts'] = 'new value'
        new_hashes1 = self.make_hashes(query_object)
        for i in data:
            matcher.add_to_db(i)
        assert len(new_hashes) == len(data)
        assert hashes == new_hashes1

        query_object.first().update['instruments'].append('testinstrument')
        matcher.add_to_db(query_object.first().update)
        assert len(query_object) == 6

        query_object.first().update['cmr_short_name'] = 'testvalue'
        matcher.add_to_db(query_object.first().update)
        assert len(query_object) == 6


"""
    def test_add_to_db(self):
        self.create_test_data()
        self.make_cmr_recommendation()
        matcher = DoiMatcher()
        campaign_uuid = Campaign.objects.get(short_name="ACES").uuid
        # campaign_uuid = (
        #     Change.objects.of_type(Campaign).all().filter(update__short_name="ACES")[0].uuid
        # )

        # existing_data = Change.objects.filter(update__campaigns__contains=str(campaign_uuid))

        # existing_data = Change.objects.of_type(Campaign).all()

        doi_drafts = Change.objects.filter(
            content_type__model='doi',
            action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
            update__concept_id=recommendations['concept_id'],
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
            assert doi_obj.action == Change.Actions.CREATE"""
