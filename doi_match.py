import requests

from cmr.doi_matching import DoiMatcher
from cmr.process_metadata import process_data_product
from data_models.models import DOI

def query_cmr_for_concept_id(concept_id):
    """Returns the cmr response given a concept_id

    Args:
        concept_id (string): concept_id

    Returns:
        cmr_data: Json containing the cmr response
        hits: Number of hits in the cmr page
    """
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?echo_collection_id="
    cmr_url = base_url + concept_id
    query_response = requests.get(cmr_url)
    cmr_data = query_response.json()["items"]
    hits = query_response.json()["hits"]
    query_response.close()

    return cmr_data, hits

def query_cmr_for_doi(doi):
    """Returns the cmr response given a doi

    Args:
        doi (string): doi

    Returns:
        cmr_data: Json containing the cmr response
        hits: Number of hits in the cmr page
    """
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?doi="
    cmr_url = base_url + doi
    query_response = requests.get(cmr_url)
    cmr_data = query_response.json()["items"]
    hits = query_response.json()["hits"]
    query_response.close()

    return cmr_data, hits

def convert_cmr_data_to_doi_recommendation(cmr_data):
    return process_data_product(cmr_data)


def update_entire_database():
    matcher = DoiMatcher()
    missing_dois = []
    for doi in DOI.objects.all():
        print(doi)
        cmr_data, hits = query_cmr_for_concept_id(doi.concept_id)
        if not cmr_data:
            cmr_data, hits = query_cmr_for_doi(doi.doi)
        # Check the number of hits
        if hits == 1:
            doi_recommendation = convert_cmr_data_to_doi_recommendation(cmr_data[0])
            matcher.add_to_db(doi_recommendation) 
        
        else:
            missing_dois.append(doi)
    # If there are any DOI's which are not updated
    if missing_dois:
        with open("dois_not_updated.txt", "w") as file:
            for doi in missing_dois:
                file.write(f"{doi}\n")


# def get_published_uuid(recent_draft):
#     if recent_draft.action == Change.Actions.UPDATE:
#         return recent_draft.model_instance_uuid
#     else:
#         # this must be a published create draft, who's uuid will match the published uuid
#         return recent_draft.uuid

# def make_update_draft(merged_draft, linked_object):
#     doi_obj = Change.objects.create(
#         content_type=ContentType.objects.get(model="doi"),
#         model_instance_uuid=linked_object,
#         update=merged_draft,
#         status=Change.Statuses.CREATED,
#         action=Change.Actions.UPDATE,
#     )
#     doi_obj = Change.objects.get(uuid=doi_obj.uuid)
#     return doi_obj