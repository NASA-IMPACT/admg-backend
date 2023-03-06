import requests
import json
from cmr.process_metadata import process_metadata_list
base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?echo_collection_id=" 
all_dois = DOI.objects.all()
notes = "abstract and thing updated by t…."
user = User.objects.get(username = "nimda")
for doi_item in all_dois:
    concept_id = doi_item.concept_id
    #print(concept_id)
    cmr_url = base_url + concept_id
    response = requests.get(cmr_url)
    concept_ids_nested = [collection["meta"]["concept-id"] for collection in response.json()["items"]]
    concept_id_data = response.json()["items"]
    processed_metadata_list = process_metadata_list(concept_id_data)
    #print(processed_metadata_list)
    # Check if processed meta data list is empty
    if processed_metadata_list:
        #print("List is not empty")
        json_str = {'cmr_abstract' : processed_metadata_list[0]['cmr_abstract'], 'cmr_data_formats' : processed_metadata_list[0]['cmr_data_formats']}
        json_obj = json.dumps(json_str)
        # This is the issue need to update model_instance_uuid
        draft = Change.objects.of_type(DOI).get(uuid = doi_item.uuid)
        model_instance_uuid = draft.model_instance_uuid
        # model_instance_uuid = Change.objects.of_type(DOI).get(uuid = doi_item.uuid)
        # Check if json_str and draft abstract and data formats are same

        doi_obj = Change(
                content_type=doi_item.uuid, 
                model_instance_uuid = model_instance_uuid,
                update=json.loads(json_obj),
                status=Change.Statuses.CREATED,
                action=Change.Actions.UPDATE,
                 )
        doi_obj.save()
        doi_obj.publish(user, notes=notes)





