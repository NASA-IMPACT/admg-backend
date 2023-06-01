# to run this test file, use 'pytest -k cmr'

from data_models.models import Campaign, DOI
from api_app.models import Change
from cmr.doi_matching import DoiMatcher
import pytest
import json
from cmr.tests.generate_cmr_test_data import generate_cmr_response
from django.test import TestCase

EXPECTED_DOIS_IN_INITIAL_DATABSE = [
    {
        'cmr_short_name': 'ABoVE_ASCENDS_Backscatter_2051',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'cmr_short_name': 'ABoVE_ASCENDS_XCO2_2050',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
]

EXPECTED_DOIS_AFTER_SECOND_AND_THIRD_RUN = [
    {
        'cmr_short_name': 'ABoVE_ASCENDS_XCO2_2050',
        'action': Change.Actions.UPDATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'cmr_short_name': 'ABoVE_ASCENDS_Backscatter_2051',
        'action': Change.Actions.UPDATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'cmr_short_name': 'ABoVE_ASCENDS_Merge_2114',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.CREATED,
    },
    {
        'cmr_short_name': 'ASCENDS_AVOCET_CA_NV_Feb_2016_2115',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.CREATED,
    },
    {
        'cmr_short_name': 'ASCENDS_LAS_IN_Sept_2014_2116',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.CREATED,
    },
    {
        'cmr_short_name': 'ABoVE_ASCENDS_Backscatter_2051',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
    {
        'cmr_short_name': 'ABoVE_ASCENDS_XCO2_2050',
        'action': Change.Actions.CREATE,
        'status': Change.Statuses.PUBLISHED,
    },
]


class TestTestData(TestCase):
    @pytest.mark.usefixtures('load_test_data')
    def test_cmr_consistency(self):
        """a known database was downloaded from prod. it has a campaign who's existing DOIs will be updated, and which will have new dois added"""

        # take initial stock of what ascends dois we have in the database
        ascends_uuid = str(Campaign.objects.get(short_name='ASCENDS Airborne').uuid)
        ascends_doi_drafts = Change.objects.of_type(DOI).filter(
            update__contains={'campaigns': [ascends_uuid]}
        )

        # we should start with 2 existing published create drafts
        # for draft in ascends_doi_drafts:
        #     print(draft.uuid, draft.status, draft.action, draft.update['cmr_short_name'], draft.updated_at)
        """
        draft.status =  Create ABoVE_ASCENDS_Backscatter_2051 2022-12-20 14:56:38.091000+00:00
        draft.status =  Create ABoVE_ASCENDS_XCO2_2050 2022-12-20 14:56:27.026000+00:00
        """

        # confirm we have 2 published creates
        assert (
            ascends_doi_drafts.filter(
                action=Change.Actions.CREATE, status=Change.Statuses.PUBLISHED
            ).count()
            == 2
        )

        # Run the DOI Matcher for the first time
        matcher = DoiMatcher()
        matcher.generate_recommendations('campaign', ascends_uuid)
        ascends_doi_drafts = Change.objects.of_type(DOI).filter(
            update__contains={'campaigns': [ascends_uuid]}
        )

        # TODO: need to get a dump of the cmr data and use it instead of the actual cmr api call that's integrated into the matcher
        # after running the matcher once, we should see
        # -- the original 2 published creates
        # -- two new published updates against those og creates
        # -- three new new edit creates
        # for draft in ascends_doi_drafts:
        #     print(draft.uuid, draft.status, draft.action, draft.update['cmr_short_name'], draft.updated_at)

        assert ascends_doi_drafts.count() == 7
        assert (
            ascends_doi_drafts.filter(
                action=Change.Actions.CREATE, status=Change.Statuses.PUBLISHED
            ).count()
            == 2
        )
        assert (
            ascends_doi_drafts.filter(
                action=Change.Actions.UPDATE, status=Change.Statuses.PUBLISHED
            ).count()
            == 2
        )
        # TODO: this might endup being editing instead of created?
        assert (
            ascends_doi_drafts.filter(
                action=Change.Actions.CREATE,
                status__in=[Change.Statuses.CREATED, Change.Statuses.IN_PROGRESS],
            ).count()
            == 3
        )

        # if we re-run the matcher, absolutely nothing should change
        matcher = DoiMatcher()
        matcher.generate_recommendations('campaign', ascends_uuid)

        # Print all the drafts associated with ASCENDS
        ascends_doi_drafts = Change.objects.of_type(DOI).filter(
            update__contains={'campaigns': [ascends_uuid]}
        )
        for draft in ascends_doi_drafts:
            print(
                draft.uuid,
                draft.status,
                draft.action,
                draft.update['cmr_short_name'],
                draft.updated_at,
            )

        # No Changes in the drafts

        """
        db8cd0d8-e861-49fa-9170-4c5c43b15f63 6 Update ABoVE_ASCENDS_XCO2_2050 None
        912a4e79-ad20-4fe1-827b-9fac14bedc90 6 Update ABoVE_ASCENDS_Backscatter_2051 None
        60d323ed-2306-439f-990e-763fc50b6dad 0 Create ABoVE_ASCENDS_Merge_2114 2023-05-25 19:34:58.724672+00:00
        3fcc0f62-2162-4bf1-9dd8-36487549fee5 0 Create ASCENDS_AVOCET_CA_NV_Feb_2016_2115 2023-05-25 19:34:58.808318+00:00
        ddc02c09-b25d-42a0-b5cf-ce223536ae44 0 Create ASCENDS_LAS_IN_Sept_2014_2116 2023-05-25 19:34:58.891491+00:00
        2521a1a5-425a-4c74-ae60-1e6a8fba2ca2 6 Create ABoVE_ASCENDS_Backscatter_2051 2022-12-20 14:56:38.091000+00:00
        50152972-5c67-4aa2-babf-610a1885db81 6 Create ABoVE_ASCENDS_XCO2_2050 2022-12-20 14:56:27.026000+00:00
        """

        assert ascends_doi_drafts.count() == 7
        assert (
            ascends_doi_drafts.filter(
                action=Change.Actions.CREATE, status=Change.Statuses.PUBLISHED
            ).count()
            == 2
        )
        assert (
            ascends_doi_drafts.filter(
                action=Change.Actions.UPDATE, status=Change.Statuses.PUBLISHED
            ).count()
            == 2
        )
        # TODO: this might endup being editing instead of created?
        assert (
            ascends_doi_drafts.filter(
                action=Change.Actions.CREATE,
                status__in=[Change.Statuses.CREATED, Change.Statuses.IN_PROGRESS],
            ).count()
            == 3
        )
