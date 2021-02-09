import pickle

from api import Api
from cmr import aggregate_aliases, query_campaign
from config import server as SERVER
from utils import (
    clean_table_name,
    purify_list
)

def universal_get(table_name, uuid):
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

    api = Api(SERVER)

    db_response = api.get(f'{table_name}/{uuid}')
    if db_response['success']:
        data = db_response['data']
    else:
        draft_response = api.get(f'change_request/{uuid}')
        if draft_response['success']:
            data = draft_response['data']['update']
            data['uuid'] = draft_response['data']['uuid']
            data['change_object'] = True
            data['change_object_action'] = draft_response['data']['action']
            data['change_object_status'] = draft_response['data']['status']
        else:
            data = None
    return data


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


def get_change_requests(use_cached_data=False):
    """Downloads all change requests from the DB. Can be set to use cached
    data that was previously queried, in order to improve speed.

    Args:
        use_cached_data (bool, optional): Set True to use cached data.

    Returns:
        change_requests (list): List of all change_requests from db
    """
    api = Api(SERVER)

    failed = False
    if use_cached_data:
        try:
            change_requests = pickle.load(open('change_request', 'rb'))
        except FileNotFoundError:
            failed = True
            
    if failed or not(use_cached_data):
        change_requests = api.get('change_request')['data']
        pickle.dump(change_requests, open('change_request', 'wb'))

    return change_requests 


def valid_object_list_generator(table_name, query_parameter=None, query_value=None, use_cached_data=False):
    # table_name => list uuids
    # gets a list of all valid object uuids from any database table

    api = Api(SERVER)
    # this improves speed during development
    change_requests = get_change_requests(use_cached_data)

    # get all create items of any approval status from the given table
    created = [c for c in change_requests if filter_change_object(c, 'create', [1,2,3], table_name, query_parameter, query_value)]
    # get all approved deleted objects
    deleted = [c for c in change_requests if filter_change_object(c, 'delete', [3], table_name, query_parameter, query_value)]

    # filtere out the approved deletes from the approved and in progress create list
    deleted_uuids = [d['model_instance_uuid'] for d in deleted]
    valid_objects = [c for c in created if c['uuid'] not in deleted_uuids]

    return [o['uuid'] for o in valid_objects]


def universal_alias(table_name, uuid):
    table_name = clean_table_name(table_name)
    obj = universal_get(table_name, uuid)

    alias_list = []
    alias_list.append(obj.get('short_name'))
    alias_list.append(obj.get('long_name'))

    # gets gcmd alias
    if table_name in ['campaign', 'platform', 'instrument']:
        if table_name == 'campaign':
            table_name = 'project'
        
        gcmd_uuids = obj.get(f'gcmd_{table_name}s')
        for gcmd_uuid in gcmd_uuids:
            gcmd_obj = universal_get(f'gcmd_{table_name}', gcmd_uuid)
            alias_list.append(gcmd_obj.get('short_name'))
            alias_list.append(gcmd_obj.get('long_name'))

    # get alias that are still in draft
    linked_aliases = valid_object_list_generator('alias', 'object_id', uuid)
    for alias_uuid in linked_aliases:
        alias = universal_get('alias', alias_uuid)
        alias_list.append(alias.get('short_name'))
    
    return purify_list(alias_list)


def campaign_recommender(doi_metadata):
    campaign_recs = []
    # extract all cmr_project_names
    cmr_project_names = []
    for project in doi_metadata.get('cmr_projects', []):
        cmr_project_names.append(project.get('ShortName'))
        cmr_project_names.append(project.get('LongName'))
    cmr_project_names = purify_list(cmr_project_names)

    # list of each campaign uuid with all it's names
    campaign_uuids = valid_object_list_generator('campaign')

    # compare the lists for matches and suppelent the metadata
    for campaign_uuid in campaign_uuids:
        camp_uuid_aliases = universal_alias('campaign', campaign_uuid)
        if cmr_project_names.intersection(camp_uuid_aliases):
            campaign_recs.append(campaign_uuid)

    return campaign_recs

def instrument_recommender(doi_metadata):
    instrument_recs = []
    return instrument_recs

def platform_recommender(doi_metadata):
    platform_recs = []
    return platform_recs

def flight_recommender(doi_metadata):
    flight_recs = []
    return flight_recs


def supplement_campaign_metadata(campaign_metadata):
    supplemented_campaign_metadata = []
    for doi_metadata in campaign_metadata:
        doi_metadata['campaign_suggestions'] = campaign_recommender(doi_metadata)
        doi_metadata['instrument_suggestions'] = instrument_recommender(doi_metadata)
        doi_metadata['platform_suggestions'] = platform_recommender(doi_metadata)
        doi_metadata['flight_suggestions'] = flight_recommender(doi_metadata)

        supplemented_campaign_metadata.append(doi_metadata)

    return campaign_metadata


def anthony(campaign_short_name, use_cached_data=False):
    api = Api(SERVER)

    failed = False
    if use_cached_data:
        try:
            metadata = pickle.load(open(f'metadata_{campaign_short_name}', 'rb'))
        except:
            failed=True
    if failed or not(use_cached_data):
        metadata = query_campaign(campaign_short_name)
        pickle.dump(metadata, open(f'metadata_{campaign_short_name}', 'wb'))
  
    supplemented_metadata = supplement_campaign_metadata(metadata)

    return supplemented_metadata
