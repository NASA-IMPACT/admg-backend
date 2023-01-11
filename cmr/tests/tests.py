# to run this test file, use 'pytest -k cmr'

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
from generate_cmr_test_data import generate_cmr_response


class TestTestData:
    def test_cmr_consistency():
        """in order to test the actual functions and not CMR itself, most of these tests rely on a
        hardcopy of the CMR api response. however, if cmr ever experiences a change, we also want
        to be alerted, as that could impact the application. this test compares our hard copy with
        cmr's present output"""

        saved_cmr_response = json.load(open('cmr/tests/testdata-cmr_response_aces.json', 'r'))
        generated_cmr_response = generate_cmr_response()
        assert saved_cmr_response == generated_cmr_response


@pytest.mark.django_db
class TestCMRRecommender:
    def setup_method(self):
        self.create_test_data()
        self.cmr_metadata = json.load(open('cmr/tests/testdata-cmr_response_aces.json', 'r'))
        self.num_test_dois = len(self.cmr_metadata)
        campaign = Change.objects.of_type(Campaign).get(update__short_name='ACES')
        self.aces_uuid = campaign.uuid

        self.all_fields = [f.name for f in DOI._meta.fields]
        self.fields_to_compare = DoiMatcher().fields_to_compare
        self.fields_to_merge = DoiMatcher().fields_to_merge
        # TODO: look at this more closely
        # this is not a perfect list, it includes long_name and uuid
        self.fields_to_ignore = set(set(self.all_fields) - set(self.fields_to_compare)) - set(
            self.fields_to_merge
        )

    def get_aces_drafts(self, action=None):
        """Gets the list of ACES objects

        Args:
            action (String, optional): Should be one of the built in actions, such as
            Change.Actions.CREATE or Change.Actions.UPDATE
            Defaults to None.

        Returns:
            returns a queryset with a list of ACES doi objects
        """

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
        """This method adds a each doi draft to database. To do that we need to
        call a function add_to_db() from DoiMatcher class from doi_matching.py

        Args:
            cmr_recommendations (list): List of metadata dicts.
        """
        for doi in cmr_recommendations:
            DoiMatcher().add_to_db(doi)

    @staticmethod
    def draft_updater(draft, overrides):
        """takes a fake draft with random data in each field and takes an override dictionary
        then uses the data in the override dictionary to overwrite certain desired fields with
        specific field data for testing purposes"""

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
        """In this method we create the test data.
        For every draft, it will be having campaigns,instruments,platforms,
        collection_periods
        By using the factory method we make a Change.Actions.CREATE change object
        to use during testing
        """

        # these statements will make unpublished change objects, but also published (with no change object history)
        # supporting objects where necessary.
        instrument_draft = self.make_create_change_object(InstrumentFactory)
        instrument_draft_2 = self.make_create_change_object(
            InstrumentFactory
        )  # allows us to merge a random instrument as a second field
        platform_draft = self.make_create_change_object(PlatformFactory)
        campaign_draft = self.make_create_change_object(CampaignFactory)
        deployment_draft = self.make_create_change_object(DeploymentFactory)
        collection_period_draft = self.make_create_change_object(CollectionPeriodFactory)

        # removes all primary published objects while leaving supporting objects (such as seasons)
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
                'short_name': 'ALTUS',  # these are specific short_names found in the test data for ACES, cmr_response_aces.json
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

        # publishing the test data as a admin user
        # we do not publish instrument_draft_2 because it is used to test
        # fields_to_merge, so it needs to be a Change object
        instrument_draft.publish(user=admin_user)
        platform_draft.publish(user=admin_user)
        campaign_draft.publish(user=admin_user)
        deployment_draft.publish(user=admin_user)
        collection_period_draft.publish(user=admin_user)

    def make_cmr_recommendation(self):
        """This looks at the cmr data file and makes the cmr_recommendations

        Returns:
            list of metadata dicts for dataproduct
        """
        return DoiMatcher().supplement_metadata(self.cmr_metadata)

    @staticmethod
    def are_hashes_identical(original_hashes, new_hashes):
        """compare the hash values of existing aces doi drafts with new aces doi drafts

        Args:
            original_hashes (hash values): existing queryset of aces doi drafts
            new_hashes (hash values): new queryset of aces doi drafts
        """
        assert len(original_hashes) == len(new_hashes)
        for uuid, original_hash in original_hashes.items():
            assert original_hash == new_hashes.get(uuid)

    def make_hash_dict(self, query_object):
        """converts the aces drafts to hash values

        Args:
            query_object: queryset with a list of aces doi objects

        Returns:
            Integer values of objects

        """
        return {draft.uuid: hash(draft) for draft in query_object}

    def test_test_data(self):
        """This method is making sure that no random data is present.
        Assert the created test data.
        """
        assert Change.objects.of_type(Instrument).count() == 2
        assert Change.objects.of_type(Platform).count() == 1
        assert Change.objects.of_type(Campaign).count() == 1
        assert Change.objects.of_type(Deployment).count() == 1
        assert Change.objects.of_type(CollectionPeriod).count() == 1

        assert Change.objects.of_type(Instrument).get(update__short_name='GPS')
        assert Change.objects.of_type(Instrument).get(update__short_name='fake')
        assert Change.objects.of_type(Platform).get(update__short_name='ALTUS')
        assert Change.objects.of_type(Campaign).get(update__short_name='ACES')

    def test_no_drafts(self):
        """
        start with an empty database containing no DOI drafts.
        run the recommender, assert that with exactly 6 unpublished create drafts exists
        assert the unpublished create drafts status is Change.Statuses.CREATED
        and action is Change.Actions.CREATE
        """
        # tests that when we start with an empty database containing no DOI drafts and
        # run the recommender from scratch, we end up with exactly 6 unpublished create drafts
        aces_doi_drafts = self.get_aces_drafts()
        # before running the recommender, there should be no DOI drafts in the system
        assert len(aces_doi_drafts) == 0
        cmr_recommendations = self.make_cmr_recommendation()
        # six items should have come back from CMR
        assert len(cmr_recommendations) == self.num_test_dois
        self.bulk_add_to_db(cmr_recommendations)
        aces_doi_drafts = Change.objects.of_type(DOI).filter(
            update__campaigns__contains=str(self.aces_uuid)
        )
        # after running the recommender, we should have 6 drafts that correspond with the
        # six CMR items
        assert len(aces_doi_drafts) == self.num_test_dois
        # at this point, all the drafts should be CREATE drafts with an staus of CREATED
        assert set(draft.status for draft in aces_doi_drafts) == set([Change.Statuses.CREATED])
        assert set(draft.action for draft in aces_doi_drafts) == set([Change.Actions.CREATE])

    def test_unpublished_create(self):
        """In this test case we are checking the different scenarios as follows

        start with an empty database.
        run the recommender, assert that with exactly 6 unpublished create drafts exists.

        Change a field to ignore - cmr_plats_and_insts to "random and horrible" and save the drafts.
        run the recommender and assert the hash values of drafts.

        Change field to merge, here we are using the fakeinstrument which we have created and
        updating the draft.
        run the recommender and add to db
        assert the 'fake' instrument in aces doi drafts.
        assert one of the drafts should have fake_instrument and should have GPS

        Change a field to compare, cmr_short_name to 'randomtest' and save the drafts.
        run the recommender and add to db, assert that with exactly 6 unpublished create drafts exists.
        assert that the hash values are identical.
        """

        # TODO: remove all this?
        # for draft in aces_doi_drafts:
        #     # this sets each draft to in_progress
        #     draft.save()

        assert len(self.get_aces_drafts()) == 0

        self.bulk_add_to_db(self.make_cmr_recommendation())

        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == self.num_test_dois

        # we are making a hash at this point because with unedited creates, running the doi recommender
        # again should produce identical dois. additionally, if we add a field to ignore, it should create
        # unchanged dois
        hash_dictionary = self.make_hash_dict(aces_doi_drafts)
        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        # TODO: this should really test all the fields to ignore, not just one of them
        # change a field to ignore and run it again
        field_to_ignore = 'cmr_plats_and_insts'
        assert field_to_ignore in self.fields_to_ignore
        for doi_draft in self.get_aces_drafts():
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
            # one of the drafts should have fake_instrument and should have added GPS
            if 'GPS' in doi_draft.update['instruments']:
                if 'fake' in doi_draft.update['instruments']:
                    assert test_concept_id == doi_draft.update['concept_id']

        # change in fields to compare
        field_to_compare = 'cmr_short_name'
        assert field_to_compare in self.fields_to_compare
        for doi_drafts in aces_doi_drafts:
            doi_drafts.update[field_to_compare] = json.dumps(['randomtest'])
            doi_drafts.save()

        # run recommender and add to db
        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == self.num_test_dois

    def test_unpublished_update(self):
        """In this test case we are checking the different scenarios as follows

        start with an empty database.
        run the recommender and add to db, assert that with exactly 6 unpublished create drafts exists.

        publish the create drafts and make an unpublished update drafts
        assert the hash values are identical

        Change a field to ignore - cmr_plats_and_insts to "random and horrible" and save the drafts.
        run the recommender and assert the hash values of drafts are identical.

        Change field to merge, here we are using the fakeinstrument which we have created and
        updating the draft.
        run the recommender and add to db.
        assert the 'fake' instrument in all aces doi drafts.
        assert one of the drafts should have fake_instrument and should have 'GPS'

        Change a field to compare, cmr_short_name to 'randomtest' and save the drafts.
        run the recommender and add to db, assert that with exactly 6 unpublished create drafts exists.

        run the recommender again and add to db
        assert that 12 drafts exists.
        assert that with exactly 6 drafts with Change.Actions.CREATE exists.
        assert that with exactly 6 drafts with Change.Actions.UPDATE exists.
        assert that Change.Actions.CREATE drafts is having cmr_short_name as 'randomtest'
        """
        # make sure there were no prior doi drafts
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 0

        # run it for the first time and get the doi drafts made
        self.bulk_add_to_db(self.make_cmr_recommendation())
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == self.num_test_dois

        # publish all our create drafts
        admin_user = UserFactory(role=1)
        for draft in aces_doi_drafts:
            draft.publish(admin_user)

        # make an unpublished update draft
        aces_dois = DOI.objects.filter(campaigns__uuid=self.aces_uuid)
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
        assert len(aces_doi_drafts) == self.num_test_dois

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
            assert len(self.get_aces_drafts()) == self.num_test_dois
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

        assert len(self.get_aces_drafts()) == self.num_test_dois
        assert len(self.get_aces_drafts(action=Change.Actions.CREATE)) == self.num_test_dois

        self.bulk_add_to_db(self.make_cmr_recommendation())
        # total 12 drafts should be present
        # Actions of 6 drafts should be create and 6 drafts should be as update
        assert len(self.get_aces_drafts()) == self.num_test_dois * 2
        assert len(self.get_aces_drafts(action=Change.Actions.CREATE)) == self.num_test_dois
        assert len(self.get_aces_drafts(action=Change.Actions.UPDATE)) == self.num_test_dois
        # check that create drafts is still have the randomtest as cmr_short_name
        for doi_draft in self.get_aces_drafts(action=Change.Actions.CREATE):
            assert doi_draft.update['cmr_short_name'] == json.dumps('randomtest')

    def test_published_create(self):
        """In this test case we are checking the different scenarios as follows

        start with an empty database.
        run the recommender and add to db, assert that with exactly 6 unpublished create drafts exists.

        publish the aces doi drafts.
        assert that all aces doi drafts status is Change.Statuses.PUBLISHED
        assert that all aces doi drafts action is Change.Actions.CREATE

        run the recommender and add to db
        assert that still the number of drafts exists is 6 exactly
        assert the hash values are identical

        Change a field to ignore - cmr_plats_and_insts to "random and horrible" and save the drafts.
        run the recommender and assert the hash values of drafts are identical.

        Change a field to compare, cmr_short_name to 'randomtest' and save the drafts.
        assert that the cmr_short_name is in fields_to_compare
        run the recommender and add to db
        assert that 12 drafts exists.
        assert that if aces doi draft is having 'randomtest', its action is Change.Actions.UPDATE
        """
        admin_user = UserFactory(role=1)

        # run it for the first time
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == 0

        # run the recommender and add to db
        self.bulk_add_to_db(self.make_cmr_recommendation())

        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == self.num_test_dois
        # change the status to publish
        for draft in aces_doi_drafts:
            draft.publish(admin_user)
            draft.save()

        for test_draft in aces_doi_drafts:
            assert test_draft.status == Change.Statuses.PUBLISHED
            assert test_draft.action == Change.Actions.CREATE

        # run the recommender and add to db
        self.bulk_add_to_db(self.make_cmr_recommendation())
        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == self.num_test_dois

        hash_dictionary = self.make_hash_dict(aces_doi_drafts)
        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        # change a field to ignore
        field_to_ignore = 'cmr_plats_and_insts'
        assert field_to_ignore in self.fields_to_ignore
        for doi_draft in aces_doi_drafts:
            doi_draft.update[field_to_ignore] = json.dumps(['random and horrible'])
            doi_draft.save()

        self.bulk_add_to_db(self.make_cmr_recommendation())
        self.are_hashes_identical(hash_dictionary, self.make_hash_dict(self.get_aces_drafts()))

        # change a field to compare
        field_to_compare = 'cmr_short_name'
        assert field_to_compare in self.fields_to_compare
        for doi_drafts in aces_doi_drafts:
            doi_drafts.update[field_to_compare] = json.dumps(['randomtest'])
            doi_drafts.save()

        self.bulk_add_to_db(self.make_cmr_recommendation())

        aces_doi_drafts = self.get_aces_drafts()
        assert len(aces_doi_drafts) == self.num_test_dois * 2

        for doi_draft in aces_doi_drafts:
            if doi_drafts.update[field_to_compare] == 'randomtest':
                assert doi_draft.action == Change.Actions.UPDATE
