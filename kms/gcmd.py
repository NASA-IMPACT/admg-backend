from admg_webapp.users.models import User
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
from dataclasses import dataclass, field
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict

from kms import api
import logging
from typing import Optional, Set, Union, Type, List
import uuid

logger = logging.getLogger(__name__)

Actions = Union[Change.Actions.CREATE, Change.Actions.UPDATE, Change.Actions.DELETE]
Models = Union[GcmdProject, GcmdInstrument, GcmdPlatform, GcmdPhenomenon]
Casei_Object = Union[Campaign, Instrument, Platform]

scheme_to_model_map = {
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
    "gcmdphenomenon": "gcmd_phenomena",
}
short_name_priority = ["short_name", "variable_3", "variable_2", "variable_1", "term"]

test = ["test1", "test2", "test3", "test4", "test5", "test6", "test7", "test8", "test9", "test10"]


def get_content_type(model: Type[Models]) -> ContentType:
    return ContentType.objects.get(app_label="data_models", model=model.__name__.lower())


def get_gcmd_model(gcmd_content_type: ContentType):
    for key, value in scheme_to_model_map.items():
        if gcmd_content_type.model_class() == value:
            return value


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
        record["basis"] = record.pop("Basis")
        record["category"] = record.pop("Category")
        record["subcategory"] = record.pop("Sub_Category")
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


def get_short_name(row: Union[Change, Models, dict]):
    # Order of attributes to look for short_name in
    priority = ["short_name", "variable_3", "variable_2", "variable_1", "term"]
    if isinstance(row, Change):
        for attribute in priority:
            if row.update.get(attribute):
                return row.update[attribute]
        for attribute in priority:
            if row.previous.get(attribute):
                return row.previous[attribute]
    elif isinstance(row, dict):
        for attribute in priority:
            if row.get(attribute):
                return row[attribute]
    elif isinstance(row, Models):
        for attribute in priority:
            if attribute in row:
                return row.attribute


def keyword_to_dict(keyword: Models) -> dict:
    keyword = model_to_dict(keyword)
    keyword["gcmd_uuid"] = str(keyword["gcmd_uuid"])
    keyword.pop("description", None)  # Attribute the database sometimes has that API doesn't
    return keyword


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


def _create_initial_path_dict(action):
    path = {"path": []}
    if action == Change.Actions.UPDATE:
        path["old_path"], path["new_path"] = True, True
    elif action == Change.Actions.DELETE:
        path["old_path"], path["new_path"] = True, False
    elif action == Change.Actions.CREATE:
        path["old_path"], path["new_path"] = False, True
    return path


def _format_path_keys(key):
    return key.replace("_", " ").title()


def _replace_empty_path_values(value):
    return "[NO VALUE]" if value in ["", " "] else value


def compare_gcmd_path_attribute(attribute, new_object, previous_object={}):
    return {
        "key": _format_path_keys(attribute),
        "old_value": _replace_empty_path_values(
            previous_object.get(attribute, "[NO VALUE]")
            if previous_object is not {}
            else '[NO VALUE]'
        ),
        "new_value": _replace_empty_path_values(new_object.get(attribute, '')),
        "has_changed": previous_object is {}
        or new_object is {}
        or not previous_object.get(attribute) == new_object.get(attribute),
    }


def get_gcmd_path(change) -> dict:
    try:
        path = _create_initial_path_dict(change.action)
        path_order = change.content_type.model_class().gcmd_path
        for attribute in path_order:
            path["path"].append(
                compare_gcmd_path_attribute(attribute, change.update, change.previous)
            )
        return path
    except AttributeError:
        print(f"Attribute Error Found, Change: {change}")


@dataclass
class GcmdSync:
    gcmd_scheme: str
    create_keywords: List[str] = field(default_factory=list)
    update_keywords: List[str] = field(default_factory=list)
    delete_keywords: List[str] = field(default_factory=list)
    published_keywords: List[str] = field(default_factory=list)
    model: Models = field(init=False)
    content_type: ContentType = field(init=False)

    def __post_init__(self):
        self.model = scheme_to_model_map[self.gcmd_scheme]
        self.content_type = get_content_type(self.model)

    @property
    def total_count(self):
        return len(self.create_keywords) + len(self.update_keywords) + len(self.delete_keywords)

    def sync_keywords(self):
        """This method aims to sync the gcmd public dataset with the gcmd database by doing the following:
        * If item not in db but in API, create "ADD" change record
        * If item in db and in API do not match, create "UPDATE" change record
        * If item in db but not in API, create "DELETE" change record
        """
        keywords = api.fetch_keyword_list(self.gcmd_scheme)
        uuids = set([keyword.get("UUID") for keyword in keywords])

        for x, keyword in enumerate(keywords):
            if not is_valid_keyword(keyword, self.model):
                continue
            keyword = convert_keyword(keyword, self.model)
            try:
                published_keyword = self.model.objects.get(gcmd_uuid=keyword["gcmd_uuid"])
            except self.model.DoesNotExist:
                # If item not in db but in API, create "ADD" change record
                self.create_change(keyword, Change.Actions.CREATE, None)
            else:
                # Compare api record to record in db to see if they match. If they are the same, then we are done for this record.
                if not compare_record_with_keyword(published_keyword, keyword):
                    # If item in db and in API do not match, create "UPDATE" change record
                    self.create_change(keyword, Change.Actions.UPDATE, published_keyword.uuid)

        self.delete_keywords_from_current_uuids(uuids, self.model)

        return (
            f"Successfully Synced {len(keywords)} {self.gcmd_scheme} gcmd keywords - "
            + f"{len(self.create_keywords)} Create, {len(self.update_keywords)} Update, "
            + f"{len(self.delete_keywords)} Delete Change records created!"
        )

    def _add_keyword_to_changed_list(self, change: Change, action: Actions):
        if action is Change.Actions.CREATE:
            self.create_keywords.append(change.uuid)
        elif action is Change.Actions.UPDATE:
            self.update_keywords.append(change.uuid)
        elif action is Change.Actions.DELETE:
            self.delete_keywords.append(change.uuid)

    def _add_keyword_to_published_list(self, change: Change):
        self.published_keywords.append(change.uuid)

    def get_recommended_objects(self, keyword: dict, action: Actions, change_draft: Change) -> None:
        recommendations = []

        # Get any CASEI objects that are connected to the current keyword (UPDATE & DELETE only).
        if action in [Change.Actions.UPDATE, Change.Actions.DELETE]:
            casei_model = change_draft.content_object.casei_model
            casei_attribute = change_draft.content_object.casei_attribute
            existing_related_objects = casei_model.objects.filter(
                **{casei_attribute: change_draft.content_object}
            )
            for casei_object in existing_related_objects:
                recommendations.append(casei_object)

        # If keyword isn't being deleted, look in alias table for other recommendations.
        if action in [Change.Actions.CREATE, Change.Actions.UPDATE]:
            for alias in Alias.objects.filter(
                short_name=get_short_name(keyword),
                content_type=ContentType.objects.get(
                    model=keyword_to_casei_map[self.content_type.model].__name__.lower()
                ),
            ):
                recommendations.append(alias.parent_fk)

        return recommendations

    def create_recommended_list(self, keyword: dict, action: Actions, change_draft: Change) -> None:
        # Delete changes will always get rid of connections by default.
        default_result = None if action in [Change.Actions.CREATE, Change.Actions.UPDATE] else False

        for recommended_object in self.get_recommended_objects(keyword, action, change_draft):
            if not Recommendation.objects.filter(
                change=change_draft, object_uuid=recommended_object.uuid
            ).exists():
                recommendation = Recommendation(
                    change=change_draft, casei_object=recommended_object, result=default_result
                )
                recommendation.save()

    def create_change(self, keyword: dict, action: Actions, model_uuid: Optional[str]) -> None:
        change_draft = get_change(keyword, self.model, action, model_uuid)
        # If a non-published Change already exists, just update the current one.
        if change_draft:
            self.update_change(change_draft, keyword)
            self.create_recommended_list(keyword, action, change_draft)
            self._add_keyword_to_changed_list(change_draft, action)
        else:
            if action is Change.Actions.CREATE:
                model_uuid = str(uuid.uuid4())
                # Create records reuse the change's uuid for the instance's uuid
                change_uuid = model_uuid
                update, previous = keyword, {}
                log_message = (
                    "Keyword in API wasn't found in database, created 'CREATE' change record: "
                )
            else:
                # Get the published keyword and convert it to a dictionary.
                change_uuid = uuid.uuid4()
                previous = keyword_to_dict(self.model.objects.get(uuid=model_uuid))
                if action is Change.Actions.UPDATE:
                    update = keyword
                    log_message = f"Keyword with gcmd_uuid '{keyword['gcmd_uuid']}' found with mismatching attributes compared to GCMD API, created new 'UPDATE' change record: "
                elif action is Change.Actions.DELETE:
                    update = {}
                    log_message = f"Keyword with gcmd_uuid '{keyword['gcmd_uuid']}' found that doesn't exist in GCMD API, created new 'DELETE' change record: "

            change_draft = Change(
                uuid=change_uuid,
                content_type=self.content_type,
                update=update,
                previous=previous,
                model_instance_uuid=model_uuid,
                action=action,
                status=Change.Statuses.CREATED,
            )
            change_draft.save(post_save=True)
            self.create_recommended_list(keyword, action, change_draft)
            self._add_keyword_to_changed_list(change_draft, action)
            logger.info(log_message + f"'{change_draft}'")
            # Only publish if keyword is created/deleted and has no recommended objects.
            if (
                action in [Change.Actions.CREATE, Change.Actions.DELETE]
                and len(change_draft.recommendation_set.all()) == 0
            ):
                # TODO: Check with Carson and make sure this is the username we should be autopublishing with.
                change_draft.publish(User.objects.get(username='admin'))
                self._add_keyword_to_published_list(change_draft)

    @staticmethod
    def update_change(change_draft: Change, new_update: dict):
        if change_draft.update != new_update:
            change_draft.update = new_update
            change_draft.save()

    def delete_keywords_from_current_uuids(
        self, current_uuids: Set[str], gcmd_model: Type[Models]
    ) -> None:
        for row in gcmd_model.objects.all().iterator():
            if str(row.gcmd_uuid) not in current_uuids:
                # If item in db but not in API, create "DELETE" change record
                self.create_change(
                    {"gcmd_uuid": str(row.gcmd_uuid)}, Change.Actions.DELETE, row.uuid
                )

    def send_email_update(self):
        from kms import tasks

        tasks.email_gcmd_sync_results.apply_async(args=(self,), retry=False)
