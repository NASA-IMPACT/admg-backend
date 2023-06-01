# to run this test file, use 'pytest -k cmr'

import json

import pytest
from django.test import TestCase

from api_app.models import Change
from cmr.doi_matching import DoiMatcher
from data_models.models import DOI, Campaign

EXPECTED_DOIS_IN_INITIAL_DATABASE = [
    {
        'update__cmr_short_name': 'ABoVE_ASCENDS_Backscatter_2051',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'update__cmr_short_name': 'ABoVE_ASCENDS_XCO2_2050',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
]

EXPECTED_DOIS_AFTER_SECOND_AND_THIRD_RUN = [
    {
        'update__cmr_short_name': 'ABoVE_ASCENDS_XCO2_2050',
        'action': Change.Actions.UPDATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'update__cmr_short_name': 'ABoVE_ASCENDS_Backscatter_2051',
        'action': Change.Actions.UPDATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'update__cmr_short_name': 'ABoVE_ASCENDS_Merge_2114',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.CREATED,
    },
    {
        'update__cmr_short_name': 'ASCENDS_AVOCET_CA_NV_Feb_2016_2115',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.CREATED,
    },
    {
        'update__cmr_short_name': 'ASCENDS_LAS_IN_Sept_2014_2116',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.CREATED,
    },
    {
        'update__cmr_short_name': 'ABoVE_ASCENDS_Backscatter_2051',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'update__cmr_short_name': 'ABoVE_ASCENDS_XCO2_2050',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
]


def convert_dict_list_to_set(list_of_dicts):
    """this sorts the list of dicts and sets it so it can be compared with other similar lists of dicts"""
    return set(tuple(sorted(d.items())) for d in list_of_dicts)


def compare_queryset_with_list(queryset, expected_values):
    """compares a queryset returned from the db with the expected values defined for the test"""
    queryset_values = list(queryset.values('update__cmr_short_name', 'action', 'status'))
    queryset_set = convert_dict_list_to_set(queryset_values)
    expected_set = convert_dict_list_to_set(expected_values)

    return queryset_set == expected_set


def get_campaign_doi_drafts(uuid):
    return Change.objects.of_type(DOI).filter(update__contains={'campaigns': [uuid]})


def add_dois_based_on_saved_cmr_data(saved_cmr_metadata):
    """
    This is equivalent to running DoiMatcher().generate_recommendation('campaign', uuid) except it bypasses
    the cmr api in favor of using previously saved cmr metadata
    """
    cmr_recommendations = DoiMatcher().supplement_metadata(saved_cmr_metadata)
    for doi in cmr_recommendations:
        DoiMatcher().add_to_db(doi)


class TestDoiGeneration(TestCase):
    @pytest.mark.usefixtures('load_test_data')
    def test_cmr_consistency(self):
        """a known database was downloaded from prod. it has a campaign who's existing DOIs will be updated, and which
        will have new dois added"""
        ascends_uuid = str(Campaign.objects.get(short_name='ASCENDS Airborne').uuid)
        saved_cmr_metadata = json.load(open('cmr/tests/cmr_response-ASCENDS.json', 'r'))

        # take initial stock of what ascends dois we have in the database
        ascends_doi_drafts = get_campaign_doi_drafts(ascends_uuid)

        assert compare_queryset_with_list(ascends_doi_drafts, EXPECTED_DOIS_IN_INITIAL_DATABASE)

        # Run the DOI Matcher for the first time
        add_dois_based_on_saved_cmr_data(saved_cmr_metadata)
        ascends_doi_drafts = get_campaign_doi_drafts(ascends_uuid)

        # there was a problem for a while where some drafts didn't get an updated_at
        for draft in ascends_doi_drafts:
            assert bool(draft.updated_at)

        assert compare_queryset_with_list(
            ascends_doi_drafts, EXPECTED_DOIS_AFTER_SECOND_AND_THIRD_RUN
        )

        # if we re-run the matcher, absolutely nothing should change
        add_dois_based_on_saved_cmr_data(saved_cmr_metadata)
        ascends_doi_drafts = get_campaign_doi_drafts(ascends_uuid)

        assert compare_queryset_with_list(
            ascends_doi_drafts, EXPECTED_DOIS_AFTER_SECOND_AND_THIRD_RUN
        )

        assert 'got to the end of doi generation' == 'no'
