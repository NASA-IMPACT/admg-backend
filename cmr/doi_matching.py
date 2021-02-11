from datetime import datetime
import pickle

from api_app.models import Change
from data_models.models import DOI

from cmr.api import Api
from cmr.cmr import aggregate_aliases, bulk_cmr_query
from cmr.config import server as SERVER
from cmr.utils import (
    clean_table_name,
    purify_list
)


class DoiMatcher():
    def __init__(self, server=SERVER):
        self.uuid_to_aliases = {}
        self.table_to_valid_uuids = {}
        self.change_requests = []
        self.api = Api(server)


    def universal_get(self, table_name, uuid):
        """Queries the database for a uuid within a table name, but searches
        the database propper as well as change objects, preferentially returning
        results from the main db.

        Args:
            api (class): api class
            table_name (str): table name such as 'gcmd_platform'
            uuid (str): uuid of the object

        Returns:
            data (dict): object from change table or None if not found
        """

        db_response = self.api.get(f'{table_name}/{uuid}')
        if db_response['success']:
            data = db_response['data']
        else:
            draft_response = self.api.get(f'change_request/{uuid}')
            if draft_response['success']:
                data = draft_response['data']['update']
                data['uuid'] = draft_response['data']['uuid']
                data['change_object'] = True
                data['change_object_action'] = draft_response['data']['action']
                data['change_object_status'] = draft_response['data']['status']
            else:
                data = None
        return data


    @staticmethod
    def filter_change_object(co, action=None, statuses=None, table_name=None, query_parameter=None, query_value=None):
        # statuses should be a list of integers

        # tests will default to True if the associate arg is not passed
        is_action, is_status, is_table_name, is_value = True, True, True, True

        if action:
            is_action = co['action'].lower()==action.lower()

        if statuses:
            is_status = co['status'] in statuses

        if table_name:
            is_table_name = clean_table_name(co['model_name']) == clean_table_name(table_name)

        if query_value:
            is_value = co['update'].get(query_parameter, '').lower() == query_value.lower()

        return is_action and is_status and is_table_name and is_value


    def get_change_requests(self):
        """Downloads all change requests from the DB. Can be set to use cached
        data that was previously queried, in order to improve speed.

        Args:
            use_cached_data (bool, optional): Set True to use cached data.

        Returns:
            change_requests (list): List of all change_requests from db
        """

        if not self.change_requests:
            self.change_requests = self.api.get('change_request')['data']
        return self.change_requests


    def valid_object_list_generator(self, table_name, query_parameter=None, query_value=None):
        # table_name => list uuids
        # gets a list of all valid object uuids from any database table

        # this improves speed during development
        change_requests = self.get_change_requests()

        # get all create items of any approval status from the given table
        created = [c for c in change_requests if self.filter_change_object(c, 'create', [1,2,3], table_name, query_parameter, query_value)]
        # get all approved deleted objects
        deleted = [c for c in change_requests if self.filter_change_object(c, 'delete', [3], table_name, query_parameter, query_value)]

        # filter out the approved deletes from the approved and in progress create list
        deleted_uuids = [d['model_instance_uuid'] for d in deleted]
        valid_objects = [c for c in created if c['uuid'] not in deleted_uuids]

        return [o['uuid'] for o in valid_objects]


    def universal_alias(self, table_name, uuid):

        if aliases:=self.uuid_to_aliases.get(table_name, {}).get(uuid):
            return aliases

        table_name = clean_table_name(table_name)
        obj = self.universal_get(table_name, uuid)

        alias_list = []
        alias_list.append(obj.get('short_name'))
        alias_list.append(obj.get('long_name'))

        # gets gcmd alias
        if table_name in ['campaign', 'platform', 'instrument']:
            if table_name == 'campaign':
                table_name = 'project'

            gcmd_uuids = obj.get(f'gcmd_{table_name}s', [])
            for gcmd_uuid in gcmd_uuids:
                gcmd_obj = self.universal_get(f'gcmd_{table_name}', gcmd_uuid)
                alias_list.append(gcmd_obj.get('short_name'))
                alias_list.append(gcmd_obj.get('long_name'))

        # get alias that are still in draft
        linked_aliases = self.valid_object_list_generator('alias', 'object_id', uuid)
        for alias_uuid in linked_aliases:
            alias = self.universal_get('alias', alias_uuid)
            alias_list.append(alias.get('short_name'))

        alias_set = purify_list(alias_list)

        # store alias set for faster lookups later
        self.uuid_to_aliases[table_name] = self.uuid_to_aliases.get(table_name, {})
        self.uuid_to_aliases[table_name][uuid] = alias_set

        return alias_set


    def campaign_recommender(self, doi_metadata):
        campaign_recs = []
        # extract all cmr_project_names
        cmr_project_names = []
        for project in doi_metadata.get('cmr_projects', []):
            cmr_project_names.append(project.get('ShortName'))
            cmr_project_names.append(project.get('LongName'))
        cmr_project_names = purify_list(cmr_project_names)

        # list of each campaign uuid with all it's names
        campaign_uuids = self.valid_object_list_generator('campaign')

        # compare the lists for matches and suppelent the metadata
        for campaign_uuid in campaign_uuids:
            camp_uuid_aliases = self.universal_alias('campaign', campaign_uuid)
            if cmr_project_names.intersection(camp_uuid_aliases):
                campaign_recs.append(campaign_uuid)

        return campaign_recs

    def instrument_recommender(self, doi_metadata):
        instrument_recs = []
        # extract all cmr instrument names
        cmr_instrument_names = []
        for platform_data in doi_metadata['cmr_plats_and_insts']:
            for instrument_data in platform_data.get('Instruments', []):
                cmr_instrument_names.append(instrument_data.get('ShortName'))
                cmr_instrument_names.append(instrument_data.get('LongName'))
        cmr_instrument_names = purify_list(cmr_instrument_names)

        # list of each instrument uuid with all it's names
        instrument_uuids = self.valid_object_list_generator('instrument')

        # compare the lists for matches and suppelent the metadata
        for instrument_uuid in instrument_uuids:
            inst_uuid_aliases = self.universal_alias('instrument', instrument_uuid)
            if cmr_instrument_names.intersection(inst_uuid_aliases):
                instrument_recs.append(instrument_uuid)

        return instrument_recs

    def platform_recommender(self, doi_metadata):
        platform_recs = []
        # extract all cmr platform names
        cmr_platform_names = []
        for platform_data in doi_metadata['cmr_plats_and_insts']:
            cmr_platform_names.append(platform_data.get('ShortName'))
            cmr_platform_names.append(platform_data.get('LongName'))
        cmr_platform_names = purify_list(cmr_platform_names)

        # list of each platform uuid with all it's names
        platform_uuids = self.valid_object_list_generator('platform')

        # compare the lists for matches and suppelent the metadata
        for platform_uuid in platform_uuids:
            plat_uuid_aliases = self.universal_alias('platform', platform_uuid)
            if cmr_platform_names.intersection(plat_uuid_aliases):
                platform_recs.append(platform_uuid)

        return platform_recs

    def flight_recommender(self, doi_metadata):
        flight_recs = []
        return flight_recs


    def supplement_campaign_metadata(self, campaign_metadata):
        supplemented_campaign_metadata = []
        for doi_metadata in campaign_metadata[0:1]: # TODO REMOVE INDEXING
            doi_metadata['date_queried'] = datetime.now().isoformat()
            doi_metadata['campaigns'] = self.campaign_recommender(doi_metadata)
            doi_metadata['instruments'] = self.instrument_recommender(doi_metadata)
            doi_metadata['platforms'] = self.platform_recommender(doi_metadata)
            doi_metadata['collection_periods'] = self.flight_recommender(doi_metadata)

            supplemented_campaign_metadata.append(doi_metadata)

        return supplemented_campaign_metadata


    def add_to_db(self, doi):
        # search db for existing items with concept_id
        existing_doi_uuids = self.valid_object_list_generator('doi', query_parameter='concept_id', query_value=doi['concept_id'])
        if len(existing_doi_uuids)>1:
            raise ValueError('There has been an internal database error')

        # if none exist add normally as a draft
        if not existing_doi_uuids:
            self.api.create('doi', doi, draft=True)
            return 'Draft created for DOI'

        uuid = existing_doi_uuids[0]
        existing_doi = self.universal_get('doi', uuid)
        # if item exists as a draft, directly update using db functions with same methodology as above
        if existing_doi.get('change_object'):
            for field in ['campaigns', 'instruments', 'platforms', 'collection_periods']:
                doi[field].extend(existing_doi.get(field))
                doi[field] = list(set(doi[field]))

            draft = Change.objects.all().filter(uuid=uuid).first()
            draft.update = doi
            draft.save()

            return f'DOI already exists as a draft. Existing draft updated. {uuid}'

        # if db item exists, replace cmr metadata fields and append suggestion fields as an update
        existing_doi = DOI.objects.all().filter(uuid=uuid).first()
        existing_campaigns = [str(c.uuid) for c in existing_doi.campaigns.all()]
        existing_instruments = [str(c.uuid) for c in existing_doi.instruments.all()]
        existing_platforms = [str(c.uuid) for c in existing_doi.platforms.all()]
        existing_collection_periods = [str(c.uuid) for c in existing_doi.collection_periods.all()]

        doi['campaigns'].extend(existing_campaigns)
        doi['instruments'].extend(existing_instruments)
        doi['platforms'].extend(existing_platforms)
        doi['collection_periods'].extend(existing_collection_periods)

        for field in ['campaigns', 'instruments', 'platforms', 'collection_periods']:
            doi[field] = list(set(doi[field]))

        self.api.update(f'doi/{uuid}', data=doi, draft=True)
        return f'DOI already exists in database. Update draft created. {uuid}'


    def anthony(self, table_name, uuid, use_cached_data=False):  

        failed = False
        if use_cached_data:
            try:
                metadata = pickle.load(open(f'metadata_{uuid}', 'rb'))
                print('using cached CMR metadata')
            except FileNotFoundError:
                failed=True
                print('cached CMR data unavailable')

        aliases = self.universal_alias(table_name, uuid)
        
        if failed or not(use_cached_data):
            metadata = bulk_cmr_query(table_name, aliases)
            pickle.dump(metadata, open(f'metadata_{uuid}', 'wb'))
    
        supplemented_metadata = self.supplement_campaign_metadata(metadata)

        for doi in supplemented_metadata:
            print(self.add_to_db(doi))

        return supplemented_metadata

