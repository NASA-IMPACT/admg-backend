import requests
import json

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from api_app.models import Change
from data_models.models import DOI

def process_cmr(concept_id):
    """Queries CMR for a specific concept_id and returns
    the dictionary conatining cmr abstract and data_formats.

    Args:
        concept_id (str): concept_id of DOI

    Returns:
        dict: dict containing cmr_abstract and crm_data_formats
    """
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?echo_collection_id="
    cmr_url = base_url + concept_id
    query_response = requests.get(cmr_url)
    query_value = query_response.json()["items"]
    # Check if the Earth data returned anything
    if query_value:
        return {
            "cmr_abstract": query_value[0]["umm"].get("Abstract", ''),
            "cmr_data_formats": [
                info.get('Format', '')
                for info in query_value[0]["umm"]
                .get('ArchiveAndDistributionInformation', {})
                .get('FileDistributionInformation', [{}])
            ],
        }
    else:
        return {}


def make_update_publish_doi_draft(doi_uuid, update_value):
    """Creates a draft for a doi, using doi_uuid and update_vlaue which is dictonary and
    published the draft

    Args:
        doi_uuid (uuid): uuid of DOI
        update_value(json): json dict containing astract and data_formats

    Returns:
        None:
    """
    notes = "abstract and thing updated by t…."
    user = User.objects.get(username="nimda")
    draft = Change.objects.create(
        content_type=ContentType.objects.get_for_model(DOI),
        status=Change.Statuses.CREATED,
        action=Change.Actions.UPDATE,
        model_instance_uuid=doi_uuid,
        update=update_value,
    )
    draft.save()
    draft.publish(user, notes=notes)


def update_dois():
    """Queries the database for a uuid within a DOI table name, and
    queries CRM to get the dict and updates the main db
    """
    dois = DOI.objects.all()
    for doi in dois:
        processed_metadata_list = process_cmr(doi.concept_id)
        # Check if processed meta data list is not empty
        if processed_metadata_list:
            update_value = json.loads(json.dumps(processed_metadata_list))
            make_update_publish_doi_draft(doi.uuid, update_value)


# Run DOI Update
update_dois()
