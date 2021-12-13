import logging
from typing import Dict, Optional, Set, Union

from celery import shared_task

from . import api
from api_app.models import Change, CREATE, UPDATE, DELETE, PATCH
from data_models import models
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)

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


def process_gcmd_record(record: dict, model: Models) -> dict:
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
            logger.debug(f"Row and change record didn't exist, creating new 'CREATE' change record '{change_object}'")
        elif action is UPDATE:
            change_object = Change(content_type=get_content_type(model),update=concept,model_instance_uuid=model_uuid,action=action)
            logger.debug(f"Row '{model_uuid}' found with mismatching contents and change record not found, creating new 'UPDATE' change record '{change_object}'")
        elif action is DELETE:
            change_object = Change(content_type=get_content_type(model),update={},model_instance_uuid=model_uuid,action=action)
            logger.debug(f"Row '{model_uuid}' found that isn't in GCMD API, creating 'DELETE' change record '{change_object}'")
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


@shared_task
def sync_gcmd(concept_scheme: str) -> str:
    """This function aims to sync the gcmd API with the gcmd database by doing the following:
        # If item not in local db but in API, create "ADD" change record
        # If item in local db but not in API, create "DELETE" change record
        # If item in local db and in API and they are not the same, create "UPDATE" change record
    """
    model = concept_to_model_map[concept_scheme]
    concepts = api.list_concepts(concept_scheme)
    uuids = set([concept.get("UUID") for concept in concepts])
    for concept in concepts:
        if not is_valid_record(concept, model):
            continue
        concept = process_gcmd_record(concept, model)

        try:
            row = model.objects.get(gcmd_uuid=concept["gcmd_uuid"])
        except model.DoesNotExist:
            # If item not in local db but in API, create "ADD" change record
            create_change(concept, model, CREATE, None)
        else:
            # If item in local db and in API and they are not the same, create "UPDATE" change record
            if not compare_record_with_concept(row, concept):
                create_change(concept, model, UPDATE, row.uuid)

    delete_old_gcmd_records(uuids, model)

    return f"Handled {len(concepts)} {concept_scheme}"


@shared_task
def trigger_gcmd_syncs() -> None:
    """
    Triggers tasks to sync each GCMD concept of interest. Tasks are scheduled
    in a staggered fashion to reduce load on systems.
    """
    offset = 5  # Use an offset to avoid overwhelming KMS API
    for i, concept in enumerate(concept_to_model_map):
        delay = i * offset
        logger.info(f"Scheduling task to sync {concept} in {delay} seconds")
        sync_gcmd.apply_async(args=(concept, ), countdown=delay, retry=False)
