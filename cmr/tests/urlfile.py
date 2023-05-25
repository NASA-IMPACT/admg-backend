from data_models.models import Campaign
from cmr.doi_matching import DoiMatcher

ascends_uuid = str(Campaign.objects.get(short_name = 'ASCENDS Airborne').uuid)
ascends_doi_drafts = Change.objects.of_type(DOI).filter(update__contains={'campaigns': [ascends_uuid]})
for draft in ascends_doi_drafts:
	print(draft.uuid, draft.status, draft.action, draft.update['cmr_short_name'], draft.updated_at)
	
"""
2521a1a5-425a-4c74-ae60-1e6a8fba2ca2 6 Create ABoVE_ASCENDS_Backscatter_2051 2022-12-20 14:56:38.091000+00:00
50152972-5c67-4aa2-babf-610a1885db81 6 Create ABoVE_ASCENDS_XCO2_2050 2022-12-20 14:56:27.026000+00:00
"""

# Run the DOI Matcher
matcher = DoiMatcher()
matcher.generate_recommendations('campaign', ascends_uuid)

# Print all the drafts associated with ASCENDS
ascends_doi_drafts = Change.objects.of_type(DOI).filter(update__contains={'campaigns': [ascends_uuid]})
for draft in ascends_doi_drafts:
	print(draft.uuid, draft.status, draft.action, draft.update['cmr_short_name'], draft.updated_at)
	
"""
db8cd0d8-e861-49fa-9170-4c5c43b15f63 6 Update ABoVE_ASCENDS_XCO2_2050 None
912a4e79-ad20-4fe1-827b-9fac14bedc90 6 Update ABoVE_ASCENDS_Backscatter_2051 None
60d323ed-2306-439f-990e-763fc50b6dad 0 Create ABoVE_ASCENDS_Merge_2114 2023-05-25 19:34:58.724672+00:00
3fcc0f62-2162-4bf1-9dd8-36487549fee5 0 Create ASCENDS_AVOCET_CA_NV_Feb_2016_2115 2023-05-25 19:34:58.808318+00:00
ddc02c09-b25d-42a0-b5cf-ce223536ae44 0 Create ASCENDS_LAS_IN_Sept_2014_2116 2023-05-25 19:34:58.891491+00:00
2521a1a5-425a-4c74-ae60-1e6a8fba2ca2 6 Create ABoVE_ASCENDS_Backscatter_2051 2022-12-20 14:56:38.091000+00:00
50152972-5c67-4aa2-babf-610a1885db81 6 Create ABoVE_ASCENDS_XCO2_2050 2022-12-20 14:56:27.026000+00:00
"""

# Re run the DOI Matcher
matcher = DoiMatcher()
matcher.generate_recommendations('campaign', ascends_uuid)

# Print all the drafts associated with ASCENDS
ascends_doi_drafts = Change.objects.of_type(DOI).filter(update__contains={'campaigns': [ascends_uuid]})
for draft in ascends_doi_drafts:
	print(draft.uuid, draft.status, draft.action, draft.update['cmr_short_name'], draft.updated_at)

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