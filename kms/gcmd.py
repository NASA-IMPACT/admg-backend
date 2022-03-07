import logging
import uuid

from typing import Dict, Optional, Set, Union, Type
# TODO: Take out actions 
from api_app.models import Change, CREATE, UPDATE, DELETE, PATCH, IN_ADMIN_REVIEW_CODE 
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from data_models import models

logger = logging.getLogger(__name__)

Models = Union[models.GcmdProject, models.GcmdInstrument, models.GcmdPlatform, models.GcmdPhenomena]
Actions = Union[CREATE, UPDATE, DELETE, PATCH]


concept_to_model_map = {
    "instruments": models.GcmdInstrument,
    "projects": models.GcmdProject,
    "platforms": models.GcmdPlatform,
    "sciencekeywords": models.GcmdPhenomena,
}


def get_content_type(model: Models) -> ContentType:
    return ContentType.objects.get(app_label="data_models", model=model.__name__.lower())


def convert_concept(record: dict, model: Type[Models]) -> dict:
    """Convert GCMD API record to match the format from the output of model_to_dict for each type of model."""
    record["gcmd_uuid"] = record.pop("UUID")
    if model == models.GcmdProject:
        # GcmdProject doesn't have any attributes we need to convert
        pass
    elif model == models.GcmdInstrument:
        record["instrument_category"] = record.pop("Category")
        record["instrument_class"] = record.pop("Class")
        record["instrument_type"] = record.pop("Type")
        record["instrument_subtype"] = record.pop("Subtype")
    # TODO: Figure out what to do with new GCMD csv format. Had to switch basis back to category like in old csv and changed Category back to series_entry.
    elif model == models.GcmdPlatform:
        record["category"] = record.pop("Basis")
        record["series_entry"] = record.pop("Category")
        record.pop("Sub_Category")                             # Not currently in use by GCMD (left blank for all values) also not in database so skipping for now.
        # record["sub_category"] = record.pop("Sub_Category")
        # record["series_entry"] = record.pop("Series_Entity") # This is the conversion we did on old GCMD csv.
    elif model == models.GcmdPhenomena:
        record.pop("Detailed_Variable")
        record["variable_1"] = record.pop("Variable_Level_1")
        record["variable_2"] = record.pop("Variable_Level_2")
        record["variable_3"] = record.pop("Variable_Level_3")
    record = dict((key.lower(), value) for key, value in record.items())
    return record


# TODO: Figure out what type row should be!
def compare_record_with_concept(row: Models, concept: dict) -> bool:
    row_dict = model_to_dict(row)
    row_dict["gcmd_uuid"] = str(row_dict["gcmd_uuid"])
    return concept == row_dict


def delete_old_records(uuids: Set[str], model: Models) -> None:
    for row in model.objects.all().iterator():
        if str(row.gcmd_uuid) not in uuids:
            # If item in db but not in API, create "DELETE" change record
            create_change({"gcmd_uuid": str(row.gcmd_uuid)}, model, DELETE, row.uuid)


def get_change(concept: dict, model: Models, action: Actions, model_uuid: Optional[str]) -> Union[Change, None]:
    content_type = get_content_type(model)
    try:
        if action in [CREATE] or model_uuid is None:
            return Change.objects.get(content_type=content_type, action=action, update__gcmd_uuid=concept["gcmd_uuid"], status__lte=IN_ADMIN_REVIEW_CODE)
        else:
            return Change.objects.get(content_type=content_type, action=action, model_instance_uuid=model_uuid, status__lte=IN_ADMIN_REVIEW_CODE)
    except Change.DoesNotExist:
        return None


def create_change(concept: dict, model: Models, action: Actions, model_uuid: Optional[str]) -> None:
    change_object = get_change(concept, model, action, model_uuid)
    if change_object:
        # If a change object already exists, just update the current one.
        if change_object.update != concept:
            change_object.update = concept
            change_object.save()
    else:
        if action is CREATE:
            change_object = Change(content_type=get_content_type(model),update=concept,action=action)
            logger.info(f"Row and change record didn't exist, creating new 'CREATE' change record '{change_object}'")
        elif action is UPDATE:
            change_object = Change(content_type=get_content_type(model),update=concept,model_instance_uuid=model_uuid,action=action)
            logger.info(f"Row '{concept['gcmd_uuid']}' found with mismatching contents and change record not found, creating new 'UPDATE' change record '{change_object}'")
        elif action is DELETE:
            change_object = Change(content_type=get_content_type(model),update={},model_instance_uuid=model_uuid,action=action)
            logger.info(f"Row '{concept['gcmd_uuid']}' found that isn't in GCMD API, creating 'DELETE' change record '{change_object}'")
        change_object.save()


def is_valid_value(*values: str) -> bool:
    nonvalid_values = ["", "NOT APPLICABLE"]
    for value in values:
        if value is None or value.strip().upper() in nonvalid_values:
            return False
    return True


def is_valid_uuid(uuid_str: str, version: str = 4) -> bool:
    if uuid_str is None:
        return False
    try:
        return bool(uuid.UUID(uuid_str, version=version))
    except ValueError:
        return False


def is_valid_concept(record: dict, model: Models) -> bool:
    if model == models.GcmdProject:
        return is_valid_value(record.get("Short_Name"),record.get("Bucket")) and is_valid_uuid(record.get("UUID"))
    elif model == models.GcmdInstrument:
        return is_valid_value(record.get("Short_Name"),record.get("Class")) and is_valid_uuid(record.get("UUID"))
    elif model == models.GcmdPlatform:
        return is_valid_value(record.get("Short_Name")) and is_valid_uuid(record.get("UUID"))
    elif model == models.GcmdPhenomena:
        return is_valid_value(record.get("Category")) and is_valid_uuid(record.get("UUID"))
    else:
        return False
