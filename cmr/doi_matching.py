import json
import logging
import pickle
from datetime import datetime
import uuid

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core import serializers

from api_app.models import Change
from cmr.cmr import query_and_process_cmr
from cmr.utils import clean_table_name, purify_list
from data_models.models import DOI

logger = logging.getLogger(__name__)


class DoiMatcher:
    def __init__(self):
        self.uuid_to_aliases = {}
        self.table_to_valid_uuids = {}
        self.fields_to_compare = [
            'cmr_short_name',
            'cmr_entry_title',
            'cmr_projects',
            'cmr_dates',
            'cmr_science_keywords',
            'abstract',
            'cmr_data_formats',
        ]
        self.fields_to_merge = ['campaigns', 'instruments', 'platforms', 'collection_periods']

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
            data = json.loads(serializers.serialize("json", [obj,]))[
                0
            ]["fields"]

        # if the published object isn't found, search the drafts
        except model.DoesNotExist:
            model = apps.get_model("api_app", "change")
            obj = model.objects.get(uuid=uuid)
            data = json.loads(serializers.serialize("json", [obj,]))[0][
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

    def merge_doi_update_draft(model_instance_uuid):
        return False

    def doi_mismatch(self, doi_recommendation, doi_draft):
        """Takes a doi_recommendation that includes metadata from CMR and a doi_draft from
        the admg database and compares specific fields to find a mismatch.

        Args:
            doi_recommendation (dict): metadata from cmr
            doi_draft (dict): Change object of type model=doi

        Returns:
            bool: True if there was a mismatch
        """

        # TODO: does this actually get the right stuff from the doi recommendation object?
        return any(
            [
                doi_recommendation.get(field) != doi_draft.update.get(field)
                for field in self.fields_to_compare
            ]
        )

    def add_to_db(self, doi_recommendation):
        """After cmr has been queried and each dataproduct has received recommended UUID
        matches, each of this is added to the database. Because DOIs might already exist
        as drafts or db objects, this function will create an update for existing DOIs or
        a second draft in the case of duplicates. When updating, freshly queried metadata
        is prioritized, but previously existing UUID links are preserved.

        Args:
            doi_recommendation (dict): DOI metadata dictionary containing original CMR metadata and recommended
                UUID links.

        Raises:
            ValueError: If objects have been added to the database outside of the expected
                approval workflow, it is possible to have a nonsensical object creation
                history and this error might be raised. This should only happen in local
                and staging environments and should never occur in production.

        Returns:
            str: String indicating action taken by the function
        """

        # search db for create drafts with concept_id
        doi_drafts = Change.objects.filter(
            content_type__model='doi',
            action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
            update__concept_id=doi_recommendation['concept_id'],
        )

        if (
            unpublished_update := doi_drafts.filter(action=Change.Actions.UPDATE)
            .exclude(status=Change.Statuses.PUBLISHED)
            .first()
        ):
            # there can only be one unpublished update at a time
            if self.doi_mismatch(doi_recommendation, unpublished_update):
                # merge the rec with the unpublished_update
                # completely replace the fields to compare (metadata from cmr)
                # append the recomendation fields (recommended by engine and hand modified by human)
                for field in self.fields_to_compare:
                    unpublished_update.update[field] = doi_recommendation[field]
                for field in self.fields_to_merge:
                    unpublished_update.update[field].append(doi_recommendation[field])
                unpublished_update.status = Change.Statuses.CREATED
                unpublished_update.save()

        elif doi_drafts.filter(
            action=Change.Actions.CREATE, status=Change.Statuses.PUBLISHED
        ).exists():
            # make a brand new update
            doi_obj = Change(
                content_type=ContentType.objects.get(model="doi"),
                model_instance_uuid=None,
                update=json.loads(json.dumps(doi_recommendation)),
                status=Change.Statuses.CREATED,
                action=Change.Actions.UPDATE,
            )
            doi_obj.save()

        elif (
            published_creates := doi_drafts.filter(action=Change.Actions.CREATE)
            .exclude(status=Change.Statuses.PUBLISHED)
            .exists()
        ):
            # call the add to draft function
            # there should only be one published create per concept_id, although maybe this is not true if stuff was deleted and
            # then recreated. this is a very fringe possiblity though
            # TODO: consider this possiblity and code for it
            published_create_draft = (
                doi_drafts.filter(action=Change.Actions.CREATE)
                .exclude(status=Change.Statuses.PUBLISHED)
                .first()
            )
            self.merge_doi_update_draft(model_instance_uuid=published_creates.first().uuid)
            # needs to be an update that points at published_creates.first().uuid
            # we are going to make a brand new item, but we are going to populate the update field with stuff that used to be in the
            # published_create update field and got merged with our recommendations
            merged_update = published_create_draft.update
            for field in self.fields_to_compare:
                merged_update[field] = doi_recommendation[field]
            for field in self.fields_to_merge:
                merged_update[field].append(doi_recommendation[field])

            new_thing = Change.objects.create(
                action=Change.Actions.UPDATE,
                status=Change.Status.CREATED,
                model_instance_uuid=published_create_draft.uuid,
                update=merged_update,
            )
            new_thing.save()

        else:
            doi_obj = Change(
                content_type=ContentType.objects.get(model="doi"),
                model_instance_uuid=None,
                update=json.loads(json.dumps(doi_recommendation)),
                status=Change.Statuses.CREATED,
                action=Change.Actions.CREATE,
            )
            doi_obj.save()
            return "Draft created for DOI"

        # TODO: CHANGE FROM HERE DOWN

        existing_doi = self.universal_get("doi", uuid)
        # TODO: don't we need to now check if there is also an update draft? before assuming this will work
        # TODO: OR this check can check that there are no updates and then
        # if item exists as a create draft, directly update using db functions with same methodology as above
        if existing_doi.get("change_object"):
            for field in ["campaigns", "instruments", "platforms", "collection_periods"]:
                doi_recommendation[field].extend(existing_doi.get(field))
                doi_recommendation[field] = list(set(doi_recommendation[field]))

            draft = Change.objects.get(uuid=uuid)
            draft.update = doi_recommendation
            draft.save()

            return f"DOI already exists as a draft. Existing draft updated. {uuid}"

        # if db item exists, replace cmr metadata fields and append suggestion fields as an update
        existing_doi = DOI.objects.get(uuid=uuid)
        existing_campaigns = [str(c.uuid) for c in existing_doi.campaigns.all()]
        existing_instruments = [str(c.uuid) for c in existing_doi.instruments.all()]
        existing_platforms = [str(c.uuid) for c in existing_doi.platforms.all()]
        existing_collection_periods = [str(c.uuid) for c in existing_doi.collection_periods.all()]

        doi_recommendation["campaigns"].extend(existing_campaigns)
        doi_recommendation["instruments"].extend(existing_instruments)
        doi_recommendation["platforms"].extend(existing_platforms)
        doi_recommendation["collection_periods"].extend(existing_collection_periods)

        for field in ["campaigns", "instruments", "platforms", "collection_periods"]:
            doi_recommendation[field] = list(set(doi_recommendation[field]))
        if self.doi_mismatch(self, doi_recommendation, doi_drafts):
            doi_obj = Change(
                content_type=ContentType.objects.get(model="doi"),
                model_instance_uuid=str(uuid),
                update=json.loads(json.dumps(doi_recommendation)),
                status=Change.Statuses.CREATED,
                action=Change.Actions.UPDATE,
            )

            doi_obj.save()

        return f"DOI already exists in database. Update draft created. {uuid}"

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

        for doi in supplemented_metadata_list:
            logger.debug(self.add_to_db(doi))

        return supplemented_metadata_list
