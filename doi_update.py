import requests
import json

# from django.contrib.auth.models import User
from admg_webapp.users.models import User
from data_models.models import DOI
from cmr.doi_matching import DoiMatcher
from cmr.process_metadata import process_data_product


def query_cmr_for_concept_id(concept_id):
    """Queries CMR for a specific concept_id and returns
    cmr response.

    Args:
        concept_id (str): concept_id of DOI

    Returns:
        dict: json dict containing cmr_abstract and crm_data_formats
    """
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?echo_collection_id="
    cmr_url = base_url + concept_id
    query_response = requests.get(cmr_url)
    cmr_data = query_response.json()["items"]
    query_response.close()
    return cmr_data


def convert_cmr_data_to_doi_recommendation(cmr_data):
    return process_data_product(cmr_data)


def update_entire_database():
    matcher = DoiMatcher()
    list_of_dois = DOI.objects.all()
    for doi in list_of_dois:
        cmr_data = query_cmr_for_concept_id(doi.concept_id)
        doi_recommendation = convert_cmr_data_to_doi_recommendation(cmr_data[0])
        try:
            matcher.add_to_db(doi_recommendation)
        except:
            print(doi.concept_id)


update_entire_database()
