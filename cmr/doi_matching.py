import json
import logging
import pickle
from datetime import datetime

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core import serializers

from admg_webapp.users.models import User
from api_app.models import Change, ApprovalLog
from cmr.cmr import query_and_process_cmr
from cmr.utils import clean_table_name, purify_list
from data_models.models import DOI

logger = logging.getLogger(__name__)


class DoiMatcher:
    def __init__(self):
        self.uuid_to_aliases = {}
        self.table_to_valid_uuids = {}
        self.core_cmr_fields = [
            'cmr_short_name',
            'cmr_entry_title',
            'cmr_projects',
            'cmr_dates',
            'cmr_plats_and_insts',
            'cmr_science_keywords',
            'cmr_abstract',
            'cmr_data_formats',
            'doi',  # TODO: do we want to not autopublish if this field is different?
        ]
        self.previously_curated_fields = [
            'campaigns',
            'instruments',
            'platforms',
            'collection_periods',
            'long_name',
        ]

    def universal_get(self, table_name, uuid):
        """Queries the database for a uuid within a table name, but searches
        the database propper as well as change objects, preferentially returning
        results from the main db.

        Args:
            table_name (str): table name such as 'gcmd_platform'
            uuid (str): uuid of the object

        Returns:
            data (dict): object from db or change table if not found
        """

        model = apps.get_model("data_models", table_name.replace("_", ""))
        # attempt to find the uuid as a published object
        try:
            obj = model.objects.get(uuid=uuid)
            data = json.loads(
                serializers.serialize(
                    "json",
                    [
                        obj,
                    ],
                )
            )[
                0
            ]["fields"]

        # if the published object isn't found, search the drafts
        except model.DoesNotExist:
            model = apps.get_model("api_app", "change")
            obj = model.objects.get(uuid=uuid)
            data = json.loads(
                serializers.serialize(
                    "json",
                    [
                        obj,
                    ],
                )
            )[0][
                "fields"
            ]["update"]
            data["uuid"] = uuid
            data["change_object"] = True

        return data

    def valid_object_list_generator(self, table_name, query_parameter=None, query_value=None):
        """Takes a table_name and outputs a list of the valid uuids for that table. Because objects
        might be in the draft stage or fully in the database, or have a create draft and an accepted
        delete, this function is needed to generate a list of all objects which valid candidates. This
        function can also filter objects on a query_parameter such as uuid or short_name.

        Args:
            table_name (str): Table name for which to generate uuid list
            query_parameter (str, optional): Name of the parameter to search. This should be
                a field in the object such as short_name or uuid. Defaults to None.
            query_value (str, optional): This is the expected value for the query_parameter,
                such as fall for short_name. Defaults to None.

        Returns:
            uuid_list (list): List of strings of uuids for the valid objects from a table
        """

        valid_objects = Change.objects.filter(
            content_type__model=table_name, action=Change.Actions.CREATE
        ).exclude(action=Change.Actions.DELETE, status=Change.Statuses.PUBLISHED)

        if query_parameter:
            query_parameter = "update__" + query_parameter
            kwargs = {query_parameter: query_value}
            valid_objects = valid_objects.filter(**kwargs)

        valid_object_uuids = [str(uuid) for uuid in valid_objects.values_list("uuid", flat=True)]

        return valid_object_uuids

    def universal_alias(self, table_name, uuid):
        """Every object has multiple forms of aliases such as long_names, gmcd names, and
        explicitly defined aliases. This function gathers all possible aliases whether in
        draft or fully created.

        Args:
            table_name (str): Table name such as platform.
            uuid (str): UUID of the obj for which aliases are desired. This can be a draft
                UUID or a database UUID.

        Returns:
            alias_set (set): Set containing lower-case aliases for the given UUID.
        """

        if aliases := self.uuid_to_aliases.get(table_name, {}).get(uuid):
            return aliases

        table_name = clean_table_name(table_name)
        obj = self.universal_get(table_name, uuid)

        alias_list = []
        alias_list.append(obj.get("short_name"))
        alias_list.append(obj.get("long_name"))

        # gets gcmd alias
        if table_name in ["campaign", "platform", "instrument"]:
            if table_name == "campaign":
                table_name = "project"

            gcmd_uuids = obj.get(f"gcmd_{table_name}s", [])
            for gcmd_uuid in gcmd_uuids:
                gcmd_obj = self.universal_get(f"gcmd_{table_name}", gcmd_uuid)
                alias_list.append(gcmd_obj.get("short_name"))
                alias_list.append(gcmd_obj.get("long_name"))

        # get alias that are still in draft
        linked_aliases = self.valid_object_list_generator("alias", "object_id", uuid)
        for alias_uuid in linked_aliases:
            alias = self.universal_get("alias", alias_uuid)
            alias_list.append(alias.get("short_name"))

        alias_set = purify_list(alias_list)

        # store alias set for faster lookups later
        self.uuid_to_aliases[table_name] = self.uuid_to_aliases.get(table_name, {})
        self.uuid_to_aliases[table_name][uuid] = alias_set

        return alias_set

    def campaign_recommender(self, doi_metadata):
        """Takes the metadata for a single dataproduct and returns a list of the UUIDs
        for each suggested campaign match from the database and drafts.

        Args:
            doi_metadata (dict): Data product metadata from CMR.

        Returns:
            campaign_recs (list): List of suggested UUID matches.
        """

        campaign_recs = []
        # extract all cmr_project_names
        cmr_project_names = []
        for project in doi_metadata.get("cmr_projects", []):
            cmr_project_names.append(project.get("ShortName"))
            cmr_project_names.append(project.get("LongName"))
        cmr_project_names = purify_list(cmr_project_names)

        # list of each campaign uuid with all it's names
        campaign_uuids = self.valid_object_list_generator("campaign")

        # compare the lists for matches and suppelent the metadata
        for campaign_uuid in campaign_uuids:
            camp_uuid_aliases = self.universal_alias("campaign", campaign_uuid)
            if cmr_project_names.intersection(camp_uuid_aliases):
                campaign_recs.append(campaign_uuid)

        return campaign_recs

    def instrument_recommender(self, doi_metadata):
        """Takes the metadata for a single dataproduct and returns a list of the UUIDs
        for each suggested instrument match from the database and drafts.

        Args:
            doi_metadata (dict): Data product metadata from CMR.

        Returns:
            instrument_recs (list): List of suggested UUID matches.
        """

        instrument_recs = []
        # extract all cmr instrument names
        cmr_instrument_names = []
        for platform_data in doi_metadata["cmr_plats_and_insts"]:
            for instrument_data in platform_data.get("Instruments", []):
                cmr_instrument_names.append(instrument_data.get("ShortName"))
                cmr_instrument_names.append(instrument_data.get("LongName"))
        cmr_instrument_names = purify_list(cmr_instrument_names)

        # list of each instrument uuid with all it's names
        instrument_uuids = self.valid_object_list_generator("instrument")

        # compare the lists for matches and suppelent the metadata
        for instrument_uuid in instrument_uuids:
            inst_uuid_aliases = self.universal_alias("instrument", instrument_uuid)
            if cmr_instrument_names.intersection(inst_uuid_aliases):
                instrument_recs.append(instrument_uuid)

        return instrument_recs

    def platform_recommender(self, doi_metadata):
        """Takes the metadata for a single dataproduct and returns a list of the UUIDs
        for each suggested platform match from the database and drafts.

        Args:
            doi_metadata (dict): Data product metadata from CMR.

        Returns:
            platform_recs (list): List of suggested UUID matches.
        """

        platform_recs = []
        # extract all cmr platform names
        cmr_platform_names = []
        for platform_data in doi_metadata["cmr_plats_and_insts"]:
            cmr_platform_names.append(platform_data.get("ShortName"))
            cmr_platform_names.append(platform_data.get("LongName"))
        cmr_platform_names = purify_list(cmr_platform_names)

        # list of each platform uuid with all it's names
        platform_uuids = self.valid_object_list_generator("platform")

        # compare the lists for matches and suppelent the metadata
        for platform_uuid in platform_uuids:
            plat_uuid_aliases = self.universal_alias("platform", platform_uuid)
            if cmr_platform_names.intersection(plat_uuid_aliases):
                platform_recs.append(platform_uuid)

        return platform_recs

    def flight_recommender(self, doi_metadata):
        """Takes the metadata for a single dataproduct and returns a list of the UUIDs
        for each suggested flight match from the database and drafts.

        Args:
            doi_metadata (dict): Data product metadata from CMR.

        Returns:
            flight_recs (list): List of suggested UUID matches.
        """

        # fully implemented in a separate PR
        flight_recs = []
        return flight_recs

    def supplement_metadata(self, metadata_list, development=False):
        """Takes a list of metadata dicts and supplements the metadata with UUID
        recommendations from the database and with the date_queried.

        Args:
            metadata_list (list): List of metadata dicts.
            development (bool): Bool which specifies whether in developement. If
                true, only 1 metadata object will be processed. Should be left as
                false during production. Defaults to False.

        Returns:
            supplemented_metadata_list (list): List of supplemented metadata dicts.
        """

        if development:
            metadata_list = metadata_list[0:1]

        supplemented_metadata_list = []
        for doi_metadata in metadata_list:
            doi_metadata["date_queried"] = datetime.now().isoformat()
            doi_metadata["campaigns"] = self.campaign_recommender(doi_metadata)
            doi_metadata["instruments"] = self.instrument_recommender(doi_metadata)
            doi_metadata["platforms"] = self.platform_recommender(doi_metadata)
            doi_metadata["collection_periods"] = self.flight_recommender(doi_metadata)

            supplemented_metadata_list.append(doi_metadata)

        return supplemented_metadata_list

    def is_core_metadata_changed(self, recent_draft, recommendation):
        """Takes a doi_recommendation that includes metadata from CMR and a doi_draft from
        the admg database and compares specific fields to find a mismatch.

        Args:
            recent_draft (dict): Change object of type model=doi
            recommendation (dict): metadata from cmr

        Returns:
            bool: True if there was a mismatch
        """

        return any(
            [
                recommendation.get(field) != recent_draft.update.get(field)
                for field in self.core_cmr_fields
            ]
        )

    @staticmethod
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

    def create_merged_draft(self, recent_draft, doi_recommendation):
        """Takes an existing doi draft and a newly generated doi_recommendation and
        returns a merged object that represents the most up-to-date data, retaining
        the originally curated fields but updating any core CMR values.
        """

        for field in self.previously_curated_fields:
            doi_recommendation[field] = recent_draft.update[field]

        return doi_recommendation

    @staticmethod
    def make_create_draft(doi_recommendation):
        doi_obj = Change(
            content_type=ContentType.objects.get(model="doi"),
            model_instance_uuid=None,
            update=doi_recommendation,
            status=Change.Statuses.CREATED,
            action=Change.Actions.CREATE,
        )
        doi_obj.save()
        return doi_obj

    @staticmethod
    def make_update_draft(merged_draft, linked_object):
        doi_obj = Change(
            content_type=ContentType.objects.get(model="doi"),
            model_instance_uuid=linked_object,
            update=merged_draft,
            status=Change.Statuses.CREATED,
            action=Change.Actions.UPDATE,
        )
        doi_obj.save()
        return doi_obj

    @staticmethod
    def get_published_uuid(recent_draft):
        if recent_draft.action == Change.Actions.UPDATE:
            return recent_draft.model_instance_uuid
        else:
            # this must be a published create draft, who's uuid will match the published uuid
            return recent_draft.uuid

    def add_to_db(self, doi_recommendation):
        """After cmr has been queried and each dataproduct has received recommended UUID
        matches, each of this is added to the database. Because DOIs might already exist
        as drafts or db objects, this function will create an update for existing DOIs or
        a second draft in the case of duplicates. When updating, freshly queried metadata
        is prioritized, but previously existing UUID links are preserved.

        Args:
            doi_recommendation (dict): DOI metadata dictionary containing original CMR metadata and recommended
                UUID links.

        Returns:
            str: String indicating action taken by the function
        """
        doi_recommendation = self.serialize_recommendation(doi_recommendation)
        # search db for the most recently worked on draft that matches our concept_id
        recent_draft = (
            Change.objects.filter(
                content_type__model='doi',
                action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
                update__concept_id=doi_recommendation['concept_id'],
            )
            .order_by("-updated_at")
            .first()
        )

        if not recent_draft:
            # no DOI draft exists yet for this concept_id, so we create one
            self.make_create_draft(doi_recommendation)

        # TODO: handle delete drafts?

        elif self.is_core_metadata_changed(recent_draft, doi_recommendation):
            # a doi draft of some kind exists, and it's different from the new data
            generic_admin_user = User.objects.get(username='nimda')
            merged = self.create_merged_draft(recent_draft, doi_recommendation)
            if recent_draft.status == Change.Statuses.PUBLISHED:
                # recommendations have been previously approved and we are just updating
                # to the latest CMR metadata
                published_uuid = self.get_published_uuid(recent_draft)
                doi_obj = self.make_update_draft(merged, published_uuid)
                doi_obj.publish(generic_admin_user, notes='CMR metadata updated')
            else:
                # an update or create draft is in progress and recommendations are
                # not yet approved, so we need to fix the in progress object
                recent_draft.update = merged
                recent_draft.status = Change.Statuses.CREATED
                recent_draft.save()
                approval_log = ApprovalLog.objects.create(
                    change=recent_draft,
                    user=generic_admin_user,
                    action=ApprovalLog.Actions.REJECT,
                    notes="New CMR metadata added, needs to be re-reviewed",
                )
                approval_log.save()

    def generate_recommendations(self, table_name, uuid, development=False):
        """This is the overarching parent function which takes a table_name and a uuid and
        then searches CMR for all the related dataproducts before finally searching the
        database drafts and objects for any possible matches. It will store all dataproducts
        and their possible matches as drafts.

        Args:
            table_name (str): Table name from `campaign`, `instrument`, `platform`.
            uuid (str): UUID of the object from the given table
            development (bool): Bool which specifies whether in developement. If
                true, only 1 metadata object will be processed and CMR metadata will be
                saved and reused to prevent repeated CMR queries. Defaults to False.

        Returns:
            supplemented_metadata_list (list): Function will return a list of dicts for each dataproduct's
                supplemented metadata. This return is for informational purposes only, as all dataproducts
                will have been added to the database as drafts already.
        """

        failed = False
        if development:
            try:
                metadata_list = pickle.load(open(f"metadata_{uuid}", "rb"))
                logger.debug("using cached CMR metadata")
            except FileNotFoundError:
                failed = True
                logger.debug("cached CMR data unavailable")

        aliases = self.universal_alias(table_name, uuid)

        if failed or not development:
            metadata_list = query_and_process_cmr(table_name, aliases)

        if development:
            pickle.dump(metadata_list, open(f"metadata_{uuid}", "wb"))

        supplemented_metadata_list = self.supplement_metadata(metadata_list, development)
        json.dump(supplemented_metadata_list, open('cmr_data.json', 'w'))
        for doi in supplemented_metadata_list:
            logger.debug(self.add_to_db(doi))

        return supplemented_metadata_list
