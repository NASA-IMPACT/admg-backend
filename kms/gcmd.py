import logging
import uuid

# TODO: Figure out if we should be using Dict instead.
from typing import Optional, Set, Union, Type

from api_app.models import (
    Change,
    Recommendation,
)
from data_models.models import (
    Campaign,
    Instrument,
    Platform,
    Alias,
    GcmdProject,
    GcmdInstrument,
    GcmdPlatform,
    GcmdPhenomenon,
)
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)

Actions = Union[Change.Actions.CREATE, Change.Actions.UPDATE, Change.Actions.DELETE]
Models = Union[GcmdProject, GcmdInstrument, GcmdPlatform, GcmdPhenomenon]
Casei_Object = Union[Campaign, Instrument, Platform]

keyword_to_model_map = {
    "instruments": GcmdInstrument,
    "projects": GcmdProject,
    "platforms": GcmdPlatform,
    "sciencekeywords": GcmdPhenomenon,
}
keyword_to_casei_map = {
    "gcmdproject": Campaign,
    "gcmdplatform": Platform,
    "gcmdinstrument": Instrument,
    "gcmdphenomenon": Instrument,
}
keyword_casei_attribute_map = {
    "gcmdproject": "gcmd_projects",
    "gcmdplatform": "gcmd_platforms",
    "gcmdinstrument": "gcmd_instruments",
    "gcmdphenomenon": "gcmd_phenomenon",
}
short_name_priority = ["short_name", "variable_3", "variable_2", "variable_1", "term"]


def get_content_type(model: Type[Models]) -> ContentType:
    return ContentType.objects.get(app_label="data_models", model=model.__name__.lower())


def get_casei_keyword_set(casei_object: Casei_Object, content_type: str):
    set_attribute = keyword_casei_attribute_map[content_type.lower()]
    return getattr(casei_object, set_attribute)


def get_casei_model(content_type: str) -> Casei_Object:
    return keyword_to_casei_map[content_type.lower()]


def convert_keyword(record: dict, model: Type[Models]) -> dict:
    """Convert GCMD API record to match the format from the output of model_to_dict for each type of model."""
    record["gcmd_uuid"] = record.pop("UUID")
    if model == GcmdProject:
        pass
    elif model == GcmdInstrument:
        record["instrument_category"] = record.pop("Category")
        record["instrument_class"] = record.pop("Class")
        record["instrument_type"] = record.pop("Type")
        record["instrument_subtype"] = record.pop("Subtype")
    elif model == GcmdPlatform:
        record["category"] = record.pop("Basis")
        record["series_entry"] = record.pop("Category")
        record.pop("Sub_Category", None)
    elif model == GcmdPhenomenon:
        record.pop("Detailed_Variable", None)
        record["variable_1"] = record.pop("Variable_Level_1")
        record["variable_2"] = record.pop("Variable_Level_2")
        record["variable_3"] = record.pop("Variable_Level_3")
    record = dict((key.lower(), value) for key, value in record.items())
    return record


def compare_record_with_keyword(row: Models, keyword: dict) -> bool:
    row_dict = keyword_to_dict(row)
    return keyword == row_dict


def get_change(
    keyword: dict, model: Type[Models], action: Actions, model_uuid: Optional[str]
) -> Union[Change, None]:
    content_type = get_content_type(model)
    try:
        if action in [Change.Actions.CREATE] or model_uuid is None:
            uuid_query = {"update__gcmd_uuid": keyword["gcmd_uuid"]}
        else:
            uuid_query = {"model_instance_uuid": model_uuid}
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


def get_recommended_objects(keyword: dict, action: Actions, change_draft: Change) -> None:
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
        for rec_object in Alias.objects.filter(short_name=get_short_name(keyword)):
            recommendations.append(rec_object)

    return recommendations


def create_recommended_list(
    keyword: dict, model: Type[Models], action: Actions, change_draft: Change
) -> None:
    # Delete changes will always get rid of connections by default.
    default_result = None if action in [Change.Actions.CREATE, Change.Actions.UPDATE] else False

    for recommended_object in get_recommended_objects(keyword, model, action, change_draft):
        recommendation = Recommendation(
            change=change_draft, casei_object=recommended_object, result=default_result
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
    keyword: dict, model: Type[Models], action: Actions, model_uuid: Optional[str]
) -> None:
    # If a non-published Change already exists, just update the current one.
    change_draft = get_change(keyword, model, action, model_uuid)
    if change_draft:
        update_change(change_draft, keyword)

    else:
        if action is Change.Actions.CREATE:
            model_uuid = str(uuid.uuid4())
            # Create records reuse the change's uuid for the instance's uuid
            change_uuid = model_uuid
            update, previous = keyword, {}
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
                update = keyword
                logger.info(
                    f"Row '{keyword['gcmd_uuid']}' found with mismatching contents and change record not found, creating new 'UPDATE' change record '{change_draft}'"
                )
            elif action is Change.Actions.DELETE:
                update = {}
                logger.info(
                    f"Row '{keyword['gcmd_uuid']}' found that isn't in GCMD API, creating 'DELETE' change record '{change_draft}'"
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
        create_recommended_list(keyword, model, action, change_draft)


def delete_keywords_from_current_uuids(current_uuids: Set[str], gcmd_model: Type[Models]) -> None:
    for row in gcmd_model.objects.all().iterator():
        if str(row.gcmd_uuid) not in current_uuids:
            # If item in db but not in API, create "DELETE" change record
            create_change(
                {"gcmd_uuid": str(row.gcmd_uuid)}, gcmd_model, Change.Actions.DELETE, row.uuid
            )


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


def is_valid_keyword(record: dict, model: Type[Models]) -> bool:
    if model == GcmdProject:
        return is_valid_value(record.get("Short_Name"), record.get("Bucket")) and is_valid_uuid(
            record.get("UUID")
        )
    elif model == GcmdInstrument:
        return is_valid_value(record.get("Short_Name"), record.get("Class")) and is_valid_uuid(
            record.get("UUID")
        )
    elif model == GcmdPlatform:
        return is_valid_value(record.get("Short_Name")) and is_valid_uuid(record.get("UUID"))
    elif model == GcmdPhenomenon:
        return is_valid_value(record.get("Category")) and is_valid_uuid(record.get("UUID"))
    else:
        return False
