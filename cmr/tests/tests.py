# to run this test file, use 'pytest -k cmr'
from cmr.cmr import query_and_process_cmr
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
import json


@pytest.mark.django_db
class TestCMRRecommender:
    def setup_method(self):
        self.create_test_data()
        campaign = Campaign.objects.get(short_name='ACES')
        self.cmr_metadata = query_and_process_cmr('campaign', [campaign.short_name])
        self.aces_uuid = campaign.uuid

        self.all_fields = [f.name for f in DOI._meta.fields]
        self.fields_to_compare = DoiMatcher().fields_to_compare
        self.fields_to_merge = DoiMatcher().fields_to_merge
        # this is not a perfect list, it includes long_name and uuid
        self.fields_to_ignore = set(set(self.all_fields) - set(self.fields_to_compare)) - set(
            self.fields_to_merge
        )

    def get_aces_drafts(self):
        return Change.objects.of_type(DOI).filter(update__campaigns__contains=str(self.aces_uuid))

    @staticmethod
    def bulk_add_to_db(cmr_recommendations):
        for doi in cmr_recommendations:
            DoiMatcher().add_to_db(doi)

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
        assert Change.objects.of_type(Instrument).count() == 0
        instrument_draft = self.make_create_change_object(InstrumentFactory)
        assert Change.objects.of_type(Instrument).count() == 1

        platform_draft = self.make_create_change_object(PlatformFactory)
        assert Change.objects.of_type(Platform).count() == 1

        campaign_draft = self.make_create_change_object(CampaignFactory)
        assert Change.objects.of_type(Campaign).count() == 1

        deployment_draft = self.make_create_change_object(DeploymentFactory)
        assert Change.objects.of_type(Deployment).count() == 1

        collection_period_draft = self.make_create_change_object(CollectionPeriodFactory)
        assert Change.objects.of_type(CollectionPeriod).count() == 1
        assert Change.objects.of_type(Instrument).count() == 1
        assert Change.objects.of_type(Platform).count() == 1

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
        return DoiMatcher().supplement_metadata(self.cmr_metadata)

    @staticmethod
    def are_hashes_identical(original_hashes, new_hashes):
        assert len(original_hashes) == len(new_hashes)
        for uuid, original_hash in original_hashes.items():
            assert original_hash == new_hashes.get(uuid)

    def make_hash_dict(self, query_object):
        return {draft.uuid: hash(draft) for draft in query_object}

    def test_test_data(self):
        assert Change.objects.of_type(Instrument).count() == 1
        assert Change.objects.of_type(Platform).count() == 1
        assert Change.objects.of_type(Campaign).count() == 1
        assert Change.objects.of_type(Deployment).count() == 1
        assert Change.objects.of_type(CollectionPeriod).count() == 1

        assert Change.objects.of_type(Instrument).first().update["short_name"] == 'GPS'
        assert Change.objects.of_type(Platform).first().update["short_name"] == 'ALTUS'
        assert Change.objects.of_type(Campaign).first().update["short_name"] == 'ACES'

    def test_no_drafts(self):
        # tests that when we start with an empty database containing no DOI drafts and
        # run the recommender from scratch, we end up with exactly 6 unpublished create drafts
        aces_doi_drafts = self.get_aces_drafts()
        # before running the recommender, there should be no DOI drafts in the system
        assert len(aces_doi_drafts) == 0
        cmr_recommendations = self.make_cmr_recommendation()
        # six items should have come back from CMR
        assert len(cmr_recommendations) == 6
        self.bulk_add_to_db(cmr_recommendations)
        aces_doi_drafts = Change.objects.of_type(DOI).filter(
            update__campaigns__contains=str(self.aces_uuid)
        )
        # after running the recommender, we should have 6 drafts that correspond with the
        # six CMR items
        assert len(aces_doi_drafts) == 6
        # at this point, all the drafts should be CREATE drafts with an staus of CREATED
        assert set(draft.status for draft in aces_doi_drafts) == set([Change.Statuses.CREATED])
        assert set(draft.action for draft in aces_doi_drafts) == set([Change.Actions.CREATE])

    def test_unpublished_create(self):

        # run it for the first time
        aces_doi_drafts = self.get_aces_drafts()
        for draft in aces_doi_drafts:
            # this sets each draft to in_progress
            draft.save()
        assert len(aces_doi_drafts) == 0

        self.bulk_add_to_db(self.make_cmr_recommendation())

        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 6

        # do nothing and run it again
        hash_dictionary = self.make_hash_dict(aces_doi_drafts)
        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        # change a field to ignore and run it again
        field_to_ignore = 'cmr_plats_and_insts'
        assert field_to_ignore in self.fields_to_ignore
        for doi_draft in aces_doi_drafts:
            doi_draft.update[field_to_ignore] = json.dumps(['random and horrible'])
            doi_draft.save()

        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))


# cmr_recommendations = self.make_cmr_recommendation()
# # six items should have come back from CMR
# assert len(cmr_recommendations) == 6
# self.bulk_add_to_db(cmr_recommendations)

# with open('cmr_recommendations.json') as f:
#     data = json.load(f)
# for i in data:
#     matcher.add_to_db(i)
# print(len(hashes))
# new_hashes = self.make_hash_dict(
#     Change.objects.filter(content_type__model='doi').filter(
#         update__campaigns__contains=str(campaign_uuid)
#     )
# )
# assert len(hashes) == len(data)
# assert hashes == new_hashes

# query_object.first().update['cmr_plats_and_insts'] = 'new value'
# new_hashes1 = self.make_hash_dict(query_object)
# for i in data:
#     matcher.add_to_db(i)
# assert len(new_hashes) == len(data)
# assert hashes == new_hashes1

# query_object.first().update['instruments'].append('testinstrument')
# matcher.add_to_db(query_object.first().update)
# assert len(query_object) == 6

# query_object.first().update['cmr_short_name'] = 'testvalue'
# matcher.add_to_db(query_object.first().update)
# assert len(query_object) == 6


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
