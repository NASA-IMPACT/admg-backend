from data_models.models import DOI
from doi_update import query_cmr_for_concept_id, query_cmr_for_doi
from cmr.process_metadata import process_data_product
from api_app.models import Change

# doi = DOI.objects.first()
# concept_id = doi.concept_id
# cmr_data, hits = query_cmr_for_concept_id(dois.concept_id)
# doi_recommendation = process_data_product(cmr_data[0])

# Get all Instrument and Platforms
# plats_insts = doi_recommendation['cmr_plats_and_insts']
# for rec in plats_insts:
#     instruments = rec['Instruments']
#     for instrument in instruments:
#         print(instrument['ShortName'])

# recent_draft = (Change.objects.filter(
#                 content_type__model='doi',
#                 action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
#                 update__concept_id=doi_recommendation['concept_id'],
#             )
#             .order_by("-updated_at")
#             .first())
    
def serialize_recommendation(doi_recommendation):
        fields_to_convert = [
            'cmr_short_name',
            'cmr_entry_title',
            'cmr_projects',
            'cmr_dates',
            'cmr_plats_and_insts',
            'cmr_science_keywords',
            'cmr_abstract',
            'cmr_data_formats',
        ]
        for field in fields_to_convert:
            doi_recommendation[field] = str(doi_recommendation[field])
        return doi_recommendation

previously_curated_fields = [
            'campaigns',
            'instruments',
            'platforms',
            'collection_periods',
            'long_name',
        ]


def create_merged_draft(recent_draft, doi_recommendation):

    for field in previously_curated_fields:
        if recent_draft.update.get(field):
            doi_recommendation[field] = recent_draft.update[field]

    return doi_recommendation


def get_missing_doi():
    missing = []
    for doi in DOI.objects.all():
        cmr_data, hits = query_cmr_for_concept_id(doi.concept_id)
        if not cmr_data:
            cmr_data, hits = query_cmr_for_doi(doi.doi)
        # Check the number of hits
        if hits == 1:
            doi_recommendation = process_data_product(cmr_data[0])
        else:
          missing.append(doi)
    return missing
          
          
def get_deleted_inst():
    deleted_doi = []
    deleted_inst = []
    for doi in DOI.objects.all():
        cmr_data, hits = query_cmr_for_concept_id(doi.concept_id)
        if not cmr_data:
            cmr_data, hits = query_cmr_for_doi(doi.doi)
        # Check the number of hits
        if hits == 1:
            doi_recommendation = process_data_product(cmr_data[0])
            # Serialize recommendation
            doi_recommendation = serialize_recommendation(doi_recommendation)
            # Get recent_draft
            recent_draft = (
            Change.objects.filter(
                content_type__model='doi',
                action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
                update__concept_id=doi_recommendation['concept_id'],
            )
            .order_by("-updated_at")
            .first())
            merged = create_merged_draft(recent_draft, doi_recommendation)
            print(merged)
            insts = merged['instruments']
            for inst in insts:
                dr = Change.objects.of_type(Instrument).filter(model_instance_uuid=inst.uuid, action=Change.Actions.DELETE)
                if dr:
                    deleted_doi.append(doi)
                    deleted_inst.append(dr)
    return deleted_doi, deleted_inst
                





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