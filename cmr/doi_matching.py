from cmr import purify_list, query_campaign
from api import Api
from config import server as SERVER


def filter_change_object(co, action=None, statuses=None, table_name=None, query_parameter=None, query_value=None):
    # statuses should be a list of integers
    
    # tests will default to True if the associate arg is not passed
    is_action, is_status, is_table_name, is_value = True

    if action:
        is_action = co['action'].lower()==action.lower()

    if statuses:
        is_status = co['staus'] in statuses

    if table_name:
        is_table_name = co['model_name'].lower().replace(' ', '_') == table_name.lower().replace(' ', '_')

    if query_value:
        is_value = co['update'].get(query_parameter, '').lower() == query_value.lower()

    return is_action and is_status and is_table_name and is_value:


def valid_object_list_generator(table_name):
    # table_name => list uuids
    # gets a list of all valid object uuids from any database table
    api = Api(SERVER)
    change_requests = api.get('change_request')['data']
    # get all create items of any approval status from the given table 
    creates = [c for c in change_requests if filter_change_object(c, 'create', [0,1,2], table_name)]
    deletes = [c for c in change_requests if filter_change_object(c, 'create', [0,1,2], table_name)]
    # look at all change objects
    # filter for create change objects
    # filter for desired table
    # second list of all approved delete change objects
    # remove any overlaps between approved delete and first filter
    # return final list

def campaign_recommender(doi_metadata):
    # extract all cmr_project_names
    cmr_project_names = []
    for project in doi_metadata.get('cmr_projects', []):
        cmr_project_names.append(project.get('ShortName'))
        cmr_project_names.append(project.get('LongName'))
    cmr_project_names = purify_list(cmr_project_names)

    # list of each campaign uuid with all it's names

    # compare the lists for matches and suppelent the metadata

    return doi_metadata

def instrument_recommender(doi_metadata):
    return doi_metadata

def platform_recommender(doi_metadata):
    return doi_metadata

def flight_recommender(doi_metadata):
    return doi_metadata


def supplement_campaign_metadata(campaign_metadata):
    supplemented_campaign_metadata = []
    for doi_metadata in campaign_metadata:
        doi_metadata = campaign_recommender(doi_metadata)
        doi_metadata = instrument_recommender(doi_metadata)
        doi_metadata = platform_recommender(doi_metadata)
        doi_metadata = flight_recommender(doi_metadata)

        supplemented_campaign_metadata.append(doi_metadata)
    
    return campaign_metadata


def anthony(campaign_short_name, fake_data=None):
    api = Api(SERVER)

    if fake_data:
        metadata = fake_data
    else:
        metadata = query_campaign(api, campaign_short_name)
    
    supplemented_metadata = supplement_campaign_metadata(metadata)

    return supplemented_metadata
