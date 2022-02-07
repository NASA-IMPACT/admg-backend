import logging
from celery import shared_task

from . import api, gcmd
from api_app.models import Change, CREATE, UPDATE, DELETE, PATCH, IN_ADMIN_REVIEW_CODE 
from data_models import models

logger = logging.getLogger(__name__)

<<<<<<< HEAD
=======
concept_to_model_map = {
    "instruments": models.GcmdInstrument,
    "projects": models.GcmdProject,
    "platforms": models.GcmdPlatform,
    "sciencekeywords": models.GcmdPhenomena,
}

Models = Union[models.GcmdProject, models.GcmdInstrument, models.GcmdPlatform, models.GcmdPhenomena]
Actions = Union[CREATE, UPDATE, DELETE, PATCH]


def get_content_type(model: Models) -> ContentType:
    return ContentType.objects.get(app_label="data_models", model=model.__name__.lower())


def convert_gcmd_record(record: dict, model: Models) -> dict:
    """Convert GCMD API record to match the format from the output of model_to_dict for each type of model."""
    record["gcmd_uuid"] = record.pop("UUID")
    if model == models.GcmdProject:
        pass # GcmdProject doesn't have any attributes we need to convert
    elif model == models.GcmdInstrument:
        record["instrument_category"] = record.pop("Category")
        record["instrument_class"] = record.pop("Class")
        record["instrument_type"] = record.pop("Type")
        record["instrument_subtype"] = record.pop("Subtype")
    elif model == models.GcmdPlatform:
        record["series_entry"] = record.pop("Series_Entity")
    elif model == models.GcmdPhenomena:
        record.pop("Detailed_Variable")
        record["variable_1"] = record.pop("Variable_Level_1")
        record["variable_2"] = record.pop("Variable_Level_2")
        record["variable_3"] = record.pop("Variable_Level_3")
    record = dict((key.lower(), value) for key, value in record.items())
    return record


# TODO: Figure out what type row should be!
def compare_record_with_concept(row, concept: dict) -> bool:
    row_dict = model_to_dict(row)
    row_dict["gcmd_uuid"] = str(row_dict["gcmd_uuid"])
    return concept == row_dict


def delete_old_gcmd_records(uuids: Set[str], model: Models) -> None:
    for row in model.objects.all().iterator():
        if str(row.gcmd_uuid) not in uuids:
            # If item in local db but not in API, create "DELETE" change record
            create_change({}, model, DELETE, row.uuid)


def check_change_records(concept: dict, action: Actions, model: Models, model_uuid: Optional[str]) -> Union[Change, None]:
    content_type = get_content_type(model)
    if action in [CREATE]:
        rows = Change.objects.filter(content_type=content_type, action=action, update__gcmd_uuid=concept["gcmd_uuid"], status__lte=5)
    else:
        rows = Change.objects.filter(content_type=content_type, action=action, model_instance_uuid=model_uuid, status__lte=5)

    for row in rows:
        if row.update == concept:
            return row

    return rows[0] if rows else None


def create_change(concept: dict, model: Models, action: Actions, model_uuid: Optional[str]) -> None:
    change_object = check_change_records(concept, action, model, model_uuid)
    if change_object:
        if change_object.update != concept:
            change_object.update = concept
            change_object.save()
    else:
        if action is CREATE:
            change_object = Change(content_type=get_content_type(model),update=concept,action=action)
            logger.info(f"Row and change record didn't exist, creating new 'CREATE' change record '{change_object}'")
        elif action is UPDATE:
            change_object = Change(content_type=get_content_type(model),update=concept,model_instance_uuid=model_uuid,action=action)
            logger.info(f"Row '{model_uuid}' found with mismatching contents and change record not found, creating new 'UPDATE' change record '{change_object}'")
        elif action is DELETE:
            change_object = Change(content_type=get_content_type(model),update={},model_instance_uuid=model_uuid,action=action)
            logger.info(f"Row '{model_uuid}' found that isn't in GCMD API, creating 'DELETE' change record '{change_object}'")
        change_object.save()


def is_valid_record(record: dict, model: Models) -> bool:
    if model == models.GcmdProject:
        return not (record["Short_Name"] == "NOT APPLICABLE" or record["Bucket"] == "NOT APPLICABLE" or record["UUID"] == "")
    elif model == models.GcmdInstrument:
        return not (record["Category"] == "" or record["Class"] == "" or record["UUID"] == "")
    elif model == models.GcmdPlatform:
        return not (record["Short_Name"] == "NOT APPLICABLE" or record["UUID"] == "")
    elif model == models.GcmdPhenomena:
        return not (record["Category"] == "" or record["UUID"] == "")

>>>>>>> eada9a67e313bb8a8115b5dc0df4f518fc70abea

@shared_task
def sync_gcmd(concept_scheme: str) -> str:
    """This function aims to sync the gcmd API with the gcmd database by doing the following:
        # If item not in db but in API, create "ADD" change record
        # If item in db and in API do not match, create "UPDATE" change record
        # If item in db but not in API, create "DELETE" change record
    """
    model = gcmd.concept_to_model_map[concept_scheme]
    concepts = api.list_concepts(concept_scheme)
    print(f"Concepts: {concepts}")
    uuids = set([concept.get("UUID") for concept in concepts])
    for concept in concepts:
        if not gcmd.is_valid_concept(concept, model):
            continue
<<<<<<< HEAD
        concept = gcmd.convert_record(concept, model)
=======
        concept = convert_gcmd_record(concept, model)

>>>>>>> eada9a67e313bb8a8115b5dc0df4f518fc70abea
        try:
            row = model.objects.get(gcmd_uuid=concept["gcmd_uuid"])
        except model.DoesNotExist:
            # If item not in db but in API, create "ADD" change record
            gcmd.create_change(concept, model, CREATE, None)
        else:
            # Compare api record to record in db to see if they match. If they are the same, then we are done for this record.
            if not gcmd.compare_record_with_concept(row, concept):
                # If item in db and in API do not match, create "UPDATE" change record
                gcmd.create_change(concept, model, UPDATE, row.uuid)

    gcmd.delete_old_records(uuids, model)

    return f"Handled {len(concepts)} {concept_scheme}"


@shared_task
def trigger_gcmd_syncs() -> None:
    """
    Triggers tasks to sync each GCMD concept of interest. Tasks are scheduled
    in a staggered fashion to reduce load on systems.
    """
    offset = 5  # Use an offset to avoid overwhelming KMS API
    for i, concept in enumerate(gcmd.concept_to_model_map):
        delay = i * offset
        logger.info(f"Scheduling task to sync {concept} in {delay} seconds")
        sync_gcmd.apply_async(args=(concept, ), countdown=delay, retry=False)
