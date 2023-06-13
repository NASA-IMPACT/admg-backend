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




# ########
# concept_id = 'C1581605783-ORNL_DAAC'
# doi = DOI.objects.get(concept_id = concept_id)

# recent_drafts =  Change.objects.filter( content_type__model='doi',
#                                             action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
#                                             update__concept_id=doi.concept_id)

# ins_draft = Change.objects.of_type(Instrument).filter(model_instance_uuid='648b7718-f8cd-486a-a15f-df5135e825f0').order_by("-updated_at").first()
# ins_name = ins_draft.update['short_name']

# contains = []
# for doi in DOI.objects.all():
#     cmr_plats_and_insts = doi.cmr_plats_and_insts
#     cmr_plats_and_insts = cmr_plats_and_insts.replace("'", '"')
#     data = json.loads(cmr_plats_and_insts)
#     instruments = []
#     if isinstance(data, list) and len(data) > 0:
#         instruments_data = data[0].get('Instruments', [])
#         instruments = [instrument['ShortName'] for instrument in instruments_data]
    
#     if ins_name in instruments:
#         contains.append(doi)


# def serialize_recommendation(doi_recommendation):
#     fields_to_convert = [
#         'cmr_short_name',
#         'cmr_entry_title',
#         'cmr_projects',
#         'cmr_dates',
#         'cmr_plats_and_insts',
#         'cmr_science_keywords',
#         'cmr_abstract',
#         'cmr_data_formats',
#     ]
#     for field in fields_to_convert:
#         doi_recommendation[field] = str(doi_recommendation[field])
#     return doi_recommendation


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


