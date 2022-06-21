import logging
import uuid

from typing import Dict, Optional, Set, Union, Type

from api_app.models import (
    Change,
    Recommendation,
)

from data_models.models import Campaign, Instrument, Platform, Alias
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from data_models import models

logger = logging.getLogger(__name__)

Models = Union[
    models.GcmdProject, models.GcmdInstrument, models.GcmdPlatform, models.GcmdPhenomenon
]
Casei_Object = Union[Campaign, Instrument, Platform]
Actions = Union[Change.Actions.CREATE, Change.Actions.UPDATE, Change.Actions.DELETE]

# TODO: Change back
# concept_to_model_map = {
#     "instruments": models.GcmdInstrument,
#     "projects": models.GcmdProject,
#     "platforms": models.GcmdPlatform,
#     "sciencekeywords": models.gcmdphenomenon,
# }
concept_to_model_map = {
    # "gcmdprojects": models.GcmdProject,
    "gcmdphenomenon": models.GcmdPhenomenon,
}
keyword_to_casei_map = {
    "gcmdproject": Campaign,
    "gcmdplatform": Platform,
    "gcmdinstrument": Instrument,
    "gcmdphenomenon": Instrument,
}
casei_gcmdkeyword_set_map = {
    "gcmdproject": "gcmd_projects",
    "gcmdplatform": "gcmd_platforms",
    "gcmdinstrument": "gcmd_instruments",
    "gcmdphenomenon": "gcmd_phenomenon",
}
path_order = {
    "gcmdproject": ["bucket", "short_name"],
    "gcmdplatform": ["category", "series_entry", "short_name"],
    "gcmdinstrument": [
        "instrument_category",
        "instrument_class",
        "instrument_type",
        "instrument_subtype",
        "short_name",
    ],
    "gcmdphenomenon": [
        "category",
        "topic",
        "term",
        "variable_1",
        "variable_2",
        "variable_3",
    ],
}


def get_content_type(model: Type[Models]) -> ContentType:
    return ContentType.objects.get(app_label="data_models", model=model.__name__.lower())


def get_casei_keyword_set(casei_object: Casei_Object, content_type: str):
    set_attribute = casei_gcmdkeyword_set_map[content_type.lower()]
    print(f"CASEI OBJECT: {type(casei_object)}, {casei_object}")
    print(f"Set Attribute: {type(set_attribute)}, {set_attribute}")
    return getattr(casei_object, set_attribute)


def get_casei_model(content_type: str) -> Casei_Object:
    return keyword_to_casei_map[content_type.lower()]


def get_path_order(content_type: str) -> list:
    print(f"CONTENT TYPE PATH ORDER: {content_type}")
    return path_order[content_type.lower()]


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
        # Not currently in use by GCMD (left blank for all values) also not in database so skipping for now.
        record.pop("Sub_Category", None)
        # record["sub_category"] = record.pop("Sub_Category")
        # record["series_entry"] = record.pop("Series_Entity") # This is the conversion we did on old GCMD csv.
    elif model == models.gcmdphenomenon:
        record.pop("Detailed_Variable", None)
        record["variable_1"] = record.pop("Variable_Level_1")
        record["variable_2"] = record.pop("Variable_Level_2")
        record["variable_3"] = record.pop("Variable_Level_3")
    record = dict((key.lower(), value) for key, value in record.items())
    return record


def compare_record_with_concept(row: Models, concept: dict) -> bool:
    row_dict = keyword_to_dict(row)
    return concept == row_dict


def delete_old_records(uuids: Set[str], model: Type[Models]) -> None:
    for row in model.objects.all().iterator():
        if str(row.gcmd_uuid) not in uuids:
            print(f"Found row to delete: {row}")
            # If item in db but not in API, create "DELETE" change record
            create_change({"gcmd_uuid": str(row.gcmd_uuid)}, model, Change.Actions.DELETE, row.uuid)


# TODO: We only use "gcmd_uuid" of concept, change so model_uuid is use instead.
def get_change(
    concept: dict, model: Type[Models], action: Actions, model_uuid: Optional[str]
) -> Union[Change, None]:
    content_type = get_content_type(model)
    try:
        if action in [Change.Actions.CREATE] or model_uuid is None:
            uuid_query = {"update__gcmd_uuid": concept["gcmd_uuid"]}
        else:
            uuid_query = {"model_instance_uuid": model_uuid}
        # TODO: Get rid of this!
        # print(f"UUID QUERY: {uuid_query}")
        return Change.objects.get(
            content_type=content_type,
            action=action,
            status__lte=Change.Statuses.IN_ADMIN_REVIEW,
            **uuid_query,
        )
    except Change.DoesNotExist:
        return None


def get_short_name(row: Union[Models, dict]):
    # Order of attributes to look for short_name in
    priority = ["short_name", "variable_3", "variable_2", "variable_1", "term"]
    try:
        if isinstance(row, dict):
            for attribute in priority:
                if row.get(attribute):
                    return row[attribute]
        elif isinstance(row, Models):
            for attribute in priority:
                if attribute in row:
                    return row.attribute
    # Change causes TypeError: Subscripted generics
    except TypeError:
        for attribute in priority:
            if row.update.get(attribute):
                return row.update[attribute]
        for attribute in priority:
            if row.previous.get(attribute):
                return row.previous[attribute]


def get_recommended_objects(
    concept: dict, model: Type[Models], action: Actions, change_draft: Change
) -> None:
    recommendations = []

    # Get any CASEI objects that are connected to the current keyword (UPDATE & DELETE only).
    if action in [Change.Actions.UPDATE, Change.Actions.DELETE]:
        casei_model = change_draft.content_object.casei_model
        casei_attribute = change_draft.content_object.casei_attribute
        recommendations = casei_model.objects.filter(
            **{casei_attribute: change_draft.content_object}
        )

    # If keyword isn't being deleted, look in alias table for other recommendations.
    if action in [Change.Actions.CREATE, Change.Actions.UPDATE]:
        for rec_object in Alias.objects.filter(short_name=get_short_name(concept)):
            recommendations.append(rec_object)

    return recommendations


def create_recommended_list(
    concept: dict, model: Type[Models], action: Actions, change_draft: Change
) -> None:
    # Delete changes will always get rid of connections by default.
    default_result = None if action in [Change.Actions.CREATE, Change.Actions.UPDATE] else False

    resolved_list = ResolvedList(change=change_draft, submitted=False)
    resolved_list.save()

    for recommended_object in get_recommended_objects(concept, model, action, change_draft):
        print(f"Recommended Object: {recommended_object}")
        recommendation = Recommendation(
            parent_fk=recommended_object, result=default_result, resolved_log=resolved_list
        )
        recommendation.save()


def keyword_to_dict(keyword: Models) -> dict:
    keyword = model_to_dict(keyword)
    keyword["gcmd_uuid"] = str(keyword["gcmd_uuid"])
    return keyword


def update_change(change_draft: Change, new_update: dict):
    if change_draft.update != new_update:
        change_draft.update = new_update
        change_draft.save()


def create_change(
    concept: dict, model: Type[Models], action: Actions, model_uuid: Optional[str]
) -> None:
    change_draft = get_change(concept, model, action, model_uuid)
    print(f"GET CHANGE RETURN: {change_draft}")
    # If a change object already exists, just update the current one.
    if change_draft:
        update_change(change_draft, concept)
    else:
        if action is Change.Actions.CREATE:
            model_uuid = str(uuid.uuid4())
            change_uuid = (
                model_uuid  # Create records reuse the change's uuid for the instance's uuid
            )
            update, previous = concept, {}
            status = Change.Statuses.PUBLISHED
            logger.info(
                f"Row and change record didn't exist, creating new 'CREATE' change record '{change_draft}'"
            )
        else:
            # Get the published keyword and convert it to a dictionary.
            change_uuid = uuid.uuid4()
            previous = keyword_to_dict(model.objects.get(uuid=model_uuid))
            status = Change.Statuses.CREATED

            if action is Change.Actions.UPDATE:
                update = concept
                logger.info(
                    f"Row '{concept['gcmd_uuid']}' found with mismatching contents and change record not found, creating new 'UPDATE' change record '{change_draft}'"
                )
            elif action is Change.Actions.DELETE:
                update = {}
                logger.info(
                    f"Row '{concept['gcmd_uuid']}' found that isn't in GCMD API, creating 'DELETE' change record '{change_draft}'"
                )

        change_draft = Change(
            uuid=change_uuid,
            content_type=get_content_type(model),
            update=update,
            previous=previous,
            model_instance_uuid=model_uuid,
            action=action,
            status=status,
        )
        change_draft.save(post_save=True)
        create_recommended_list(concept, model, action, change_draft)


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


def is_valid_concept(record: dict, model: Type[Models]) -> bool:
    if model == models.GcmdProject:
        return is_valid_value(record.get("Short_Name"), record.get("Bucket")) and is_valid_uuid(
            record.get("UUID")
        )
    elif model == models.GcmdInstrument:
        return is_valid_value(record.get("Short_Name"), record.get("Class")) and is_valid_uuid(
            record.get("UUID")
        )
    elif model == models.GcmdPlatform:
        return is_valid_value(record.get("Short_Name")) and is_valid_uuid(record.get("UUID"))
    elif model == models.gcmdphenomenon:
        return is_valid_value(record.get("Category")) and is_valid_uuid(record.get("UUID"))
    else:
        return False
