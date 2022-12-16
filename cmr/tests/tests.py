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
import os


def generate_cmr_response():
    """Many of our processes rely on first getting information from the CMR API.
    This function is only run once and it saves a sample CMR file to the repository.
    All test functions that rely on CMR will use this file, and there is a separate test
    that evaluates whether CMR still gives the same response.

    To run this function and generate the file, use a manage.py shell
    """

    cmr_metadata = query_and_process_cmr('campaign', ['ACES'])
    json.dump(cmr_metadata, open(os.path.dirname(__file__) + '/cmr_response_aces.json', 'w'))


@pytest.mark.django_db
class TestCMRRecommender:
    def setup_method(self):
        self.create_test_data()
        # TODO: HOW DOES THIS WORK, MUST FIX
        campaign = Change.objects.of_type(Campaign).get(update__short_name='ACES')
        self.cmr_metadata = json.load(
            open(os.path.dirname(__file__) + '/cmr_response_aces.json', 'r')
        )
        self.aces_uuid = campaign.uuid

        self.all_fields = [f.name for f in DOI._meta.fields]
        self.fields_to_compare = DoiMatcher().fields_to_compare
        self.fields_to_merge = DoiMatcher().fields_to_merge
        # this is not a perfect list, it includes long_name and uuid
        self.fields_to_ignore = set(set(self.all_fields) - set(self.fields_to_compare)) - set(
            self.fields_to_merge
        )

    def get_aces_drafts(self, action=None):
        if action:
            return Change.objects.of_type(DOI).filter(
                update__campaigns__contains=str(self.aces_uuid), action=action
            )
        else:
            return Change.objects.of_type(DOI).filter(
                update__campaigns__contains=str(self.aces_uuid)
            )

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
        """creating the test data"""
        instrument_draft = self.make_create_change_object(InstrumentFactory)
        instrument_draft_2 = self.make_create_change_object(InstrumentFactory)

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
            instrument_draft_2,
            {
                'short_name': 'fake',
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
        """
        Assert the created test data
        """
        assert Change.objects.of_type(Instrument).count() == 2
        assert Change.objects.of_type(Platform).count() == 1
        assert Change.objects.of_type(Campaign).count() == 1
        assert Change.objects.of_type(Deployment).count() == 1
        assert Change.objects.of_type(CollectionPeriod).count() == 1

        assert Change.objects.of_type(Instrument).get(update__short_name='GPS')
        assert Change.objects.of_type(Platform).get(update__short_name='ALTUS')
        assert Change.objects.of_type(Campaign).get(update__short_name='ACES')

    def test_no_drafts(self):
        """
        start with an empty database containing no DOI drafts.
        run the recommender, end up with exactly 6 unpublished create drafts
        """
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
        """
        If there is an unpublished create draft, compare specific existing fields to CMR.
        If different, edit the create draft with new metadata. If same, do nothing
        """

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

        test_concept_id = ''
        for test_doi in aces_doi_drafts:
            if 'GPS' in test_doi.update['instruments']:
                test_concept_id = test_doi.update['concept_id']

        # change a field to merge
        for doi_draft in aces_doi_drafts:
            fake_instrument = Change.objects.of_type(Instrument).get(update__short_name='fake')
            # delete the old instrument, add a new fake one
            doi_draft.update['instruments'] = [fake_instrument.update['short_name']]
            doi_draft.save()

        # run recommender and add to db
        self.bulk_add_to_db(self.make_cmr_recommendation())
        # check that five of the drafts still have the added fake instrument
        for doi_draft in aces_doi_drafts:
            assert 'fake' in doi_draft.update['instruments']
            # one of the drafts should have fake_instrument AND should have added GPS
            if 'GPS' in doi_draft.update['instruments']:
                if 'fake' in doi_draft.update['instruments']:
                    assert test_concept_id == doi_draft.update['concept_id']

        # change in fields to compare
        field_to_compare = 'cmr_short_name'
        assert field_to_compare in self.fields_to_compare
        for doi_drafts in aces_doi_drafts:
            doi_draft.update[field_to_compare] = json.dumps(['randomtest'])
            doi_draft.save()
        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 6

    def test_unpublished_update(self):
        """
        If there is an unpublished update draft, compare specific existing fields to CMR.
        If different, edit the update draft with new metadata. If same, do nothing

        run recommender
        publish the results
        make an update draft against a doi
            which fields are they going to change
            we probably need to test all the fields: merge fields, ingnore fields, etc
        """
        # make sure there were no prior doi drafts
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 0

        # run it for the first time and get the doi drafts made
        self.bulk_add_to_db(self.make_cmr_recommendation())
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 6

        # publish all our create drafts
        admin_user = UserFactory(role=1)
        for draft in aces_doi_drafts:
            draft.publish(admin_user)

        # make an unpublished update draft
        aces_dois = DOI.objects.filter(campaigns__uuid=self.aces_uuid)  # something like this
        uuid_to_update = aces_dois.first().uuid
        doi_content_type = ContentType.objects.get_for_model(DOI)
        update_draft = Change.objects.create(
            content_type=doi_content_type,
            action=Change.Actions.UPDATE,
            model_instance_uuid=uuid_to_update,
            update=json.dumps({"short_name": "ACES"}),
        )
        update_draft.save()

        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 6

        # do nothing and run it again
        hash_dictionary = self.make_hash_dict(aces_doi_drafts)
        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        # change a field to ignore and run it again
        field_to_ignore = 'cmr_plats_and_insts'
        assert field_to_ignore in self.fields_to_ignore
        for doi_draft in self.get_aces_drafts():
            doi_draft.update[field_to_ignore] = json.dumps(['random and horrible'])
            doi_draft.save()

        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        test_concept_id = ''
        for test_doi in self.get_aces_drafts():
            if 'GPS' in test_doi.update['instruments']:
                test_concept_id = test_doi.update['concept_id']

        # change a field to merge
        for doi_draft in self.get_aces_drafts():
            fake_instrument = Change.objects.of_type(Instrument).get(update__short_name='fake')
            # delete the old instrument, add a new fake one
            doi_draft.update['instruments'] = [fake_instrument.update['short_name']]
            doi_draft.save()

        # run recommender
        # run add to db
        self.bulk_add_to_db(self.make_cmr_recommendation())
        # check that five of the drafts still have the added fake instrument
        for doi_draft in self.get_aces_drafts():
            assert len(self.get_aces_drafts()) == 6
            assert 'fake' in doi_draft.update['instruments']
            # one of the drafts should have fake_instrument AND should have added GPS
            if 'GPS' in doi_draft.update['instruments']:
                if 'fake' in doi_draft.update['instruments']:
                    assert test_concept_id == doi_draft.update['concept_id']

        # change in fields to compare
        field_to_compare = 'cmr_short_name'
        assert field_to_compare in self.fields_to_compare
        for doi_drafts in self.get_aces_drafts():
            doi_drafts.update[field_to_compare] = json.dumps('randomtest')
            doi_drafts.save()
        assert len(self.get_aces_drafts()) == 6
        assert len(self.get_aces_drafts(action=Change.Actions.CREATE)) == 6

        self.bulk_add_to_db(self.make_cmr_recommendation())
        assert len(self.get_aces_drafts()) == 12
        assert len(self.get_aces_drafts(action=Change.Actions.CREATE)) == 6
        assert len(self.get_aces_drafts(action=Change.Actions.UPDATE)) == 6
        for doi_draft in self.get_aces_drafts(action=Change.Actions.CREATE):
            assert doi_draft.update['cmr_short_name'] == json.dumps('randomtest')

    def test_published_create(self):
        """
        If there is an published create draft.
        compare specific existing fields to CMR.
        If different, add the new update draft with new metadata. If same, do nothing
        """
        admin_user = UserFactory(role=1)

        # run it for the first time
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 0

        self.bulk_add_to_db(self.make_cmr_recommendation())

        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 6
        # change the status to publish
        for draft in aces_doi_drafts:
            draft.publish(admin_user)
            draft.save()

        for test_draft in aces_doi_drafts:
            assert test_draft.status == Change.Statuses.PUBLISHED
            assert test_draft.action == Change.Actions.CREATE

        self.bulk_add_to_db(self.make_cmr_recommendation())
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 6

        hash_dictionary = self.make_hash_dict(aces_doi_drafts)
        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        field_to_ignore = 'cmr_plats_and_insts'
        assert field_to_ignore in self.fields_to_ignore
        for doi_draft in aces_doi_drafts:
            doi_draft.update[field_to_ignore] = json.dumps(['random and horrible'])
            doi_draft.save()

        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        field_to_compare = 'cmr_short_name'
        assert field_to_compare in self.fields_to_compare
        for doi_drafts in aces_doi_drafts:
            doi_drafts.update[field_to_compare] = json.dumps(['randomtest'])
            doi_drafts.save()

        self.bulk_add_to_db(self.make_cmr_recommendation())

        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 12

        for doi_draft in aces_doi_drafts:
            if doi_drafts.update[field_to_compare] == 'randomtest':
                assert doi_draft.action == Change.Actions.UPDATE
