import json
from collections import namedtuple
from datetime import datetime
from urllib.parse import urlencode

import requests

from cmr.api import Api
from cmr.config import server as SERVER
from cmr.process_metadata import process_metadata_list
from cmr.utils import purify_list


class QueryCounter:
    def __init__(self, page_num=1, page_size=100):
        self.page_num = page_num
        self.page_size = page_size
        self.finished = False

    def calculate_num_returned(self, num_hits, naive):
        """Calculates number of hits returned in the current CMR page

        Args:
            num_hits (int): num hits from api call metadata
            page_size (int): page size from user query
            page_num (int): page number from user query
            naive (bool): selects for naive calculation

        Returns:
            int: number of results on current page
        """

        if naive:
            num_returned = self.page_num * self.page_size
        else:
            num_returned = self.page_size * self.page_num
            if num_returned < num_hits:
                num_returned = num_hits % num_returned

        return num_returned

    def iterate(self, num_hits):
        """Updates self.page_num and self.finished after a new page with new hits
        is returned.

        Args:
            num_hits (int): number of hits returned from the most recent query
        """
        num_returned_naive = self.calculate_num_returned(num_hits, naive=True)
        if num_returned_naive < num_hits:
            self.page_num += 1
        else:
            self.finished = True


def get_json(url):
    response = requests.get(url).text
    data = json.loads(response)
    return data


def universal_query(query_parameter, query_value):
    """Queries CMR for a specific query_parameter and value and aggergates
    all the collection metadata.

    Args:
        query_parameter (str): 'project', 'instrument', 'platform'
        query_value (str): value associated with parameter such as a
            campaign short_name, 'ABOVE' for query_parameter='project'

    Returns:
        list: list of xml_trees
    """

    # set initial variables
    counter = QueryCounter()
    base_url = 'https://cmr.earthdata.nasa.gov/search/collections.umm_json?'
    results = []

    while not counter.finished:
        # make inital query and append results
        parameters = urlencode({query_parameter: query_value,
                                'page_size': counter.page_size,
                                'page_num': counter.page_num},
                                doseq=True)
        url = base_url + parameters

        # retrieve and append results
        response = get_json(url)
        results.append(response)

        # iterate counter
        num_hits = int(response['hits'])
        counter.iterate(num_hits)

    return results


def extract_concept_ids_from_universal_query(collections_json):
    """Takes the results from an initial collections query and extracts each
    concept_id mentioned, with the intent that they are subsequently queried
    individually for their detailed metadata.

    Args:
        collections_json (dict): Python dict generated from the json from
            universal_query()

    Returns:
        list: list of concept_id strings
    """
    concept_ids_nested = [[collection['meta']['concept-id'] for collection in page['items']] for page in collections_json]
    concept_ids = [concept_id for sublist in concept_ids_nested for concept_id in sublist]
    concept_ids = purify_list(concept_ids, lower=False)
    return concept_ids


def individual_concept_ids_query(query_parameter, query_value):

    collections_json = universal_query(query_parameter, query_value)
    concept_ids = extract_concept_ids_from_universal_query(collections_json)

    return concept_ids


def aggregate_concept_ids_queries(query_parameter, query_value_list):
    # aggregate all concept_ids for all query_values
    concept_id_list = []
    for query_value in query_value_list:
        concept_ids = individual_concept_ids_query(query_parameter, query_value)
        concept_id_list.extend(concept_ids)
    concept_id_list = purify_list(concept_id_list, lower=False)

    return concept_id_list


def query_cmr(query_parameter, query_value_list):
    # this is the main cmr query function that takes a table and a list of aliases
    # we want to feed all aliases at this stage because if two alias return the same
    # list of concept_ids then we only want those concept_ids to be queried ONCE

    # query value list is intended to take a list of aliases

    concept_id_list = aggregate_concept_ids_queries(query_parameter, query_value_list)

    # query cmr with list of concept ids
    concept_ids_responses = universal_query('echo_collection_id[]', concept_id_list)
    metadata_list = [concept_id_data for page in [response['items'] for response in concept_ids_responses] for concept_id_data in page]

    # filter metadata
    # filtered_metadata = filter_cmr_metadata(metadata)

    return metadata_list


def filter_co(co, table_name, query_parameter='short_name', query_value=None):
    # TODO: refactor to use more general doi_matching.filter_change_object() 
    is_create = co['action'] ==  'Create'
    is_unapproved = co['status']==0 or co['status']==1
    is_table = co['model_name'].lower().replace(' ', '_') == table_name.lower().replace(' ', '_')
    # TODO: exclude rejected ones
    if query_value:
        is_value = co['update'].get(query_parameter) == query_value
    else:
        is_value = True
        
    if is_create and is_unapproved and is_table and is_value:
        return True
    else:
        return False

def cmr_parameter_transform(input_str, reverse=False):
    """Takes a table name from the database and transforms it into the
    associated cmr query parameter. Also throws an error for invalid names.

    Args:
        input_str (str): db table_name in ['project', 'instrument', 'platform']
        reverse (bool): When true, function will convert backwards

    Raises:
        ValueError: Raises an error if input_str is not in ['project', 'instrument', 'platform']

    Returns:
        query_parameter (str): cmr query parameter matching the input_str
    """

    mapping = {
        'instrument': 'instrument',
        'platform': 'platform',
        'campaign': 'project',
    }

    input_str = input_str.lower()

    if reverse:
        if input_str not in [cmr_param for table_name, cmr_param in mapping.items()]:
            raise ValueError('cmr_param must be project, instrument, or platform')
        result = {v:k for k,v in mapping.items()}[input_str]
    else:
        if input_str not in [table_name for table_name, cmr_param in mapping.items()]:
            raise ValueError('table_name must be campaign, instrument, or platform')
        result = mapping[input_str]

    return result


def aggregate_aliases(query_parameter, query_value, prequeried={}):
    api = Api(SERVER)

    table_name = cmr_parameter_transform(query_parameter, reverse=True)
        
    if prequeried.get(table_name, {}).get(query_value):
        return prequeried.get(query_value)

    all_aliases = [query_value]

    # query exists in regular database
    response = api.get(f'{table_name}?short_name={query_value}')['data']
    filtered_db = {}
    if response:
        filtered_db = response[0]

    all_aliases.append(filtered_db.get('short_name'))
    all_aliases.append(filtered_db.get('long_name'))

    db_alias_uuids = filtered_db.get('aliases', [])
    for uuid in db_alias_uuids:
        alias = api.get(f'alias/{uuid}')['data']['short_name']
        all_aliases.append(alias)

    gcmd_table = 'gcmd_project'
    gcmd_uuids = filtered_db.get(gcmd_table + 's', [])
    for gcmd_uuid in gcmd_uuids:
        gcmd_project = api.get(f'{gcmd_table}/{gcmd_uuid}')['data']
        all_aliases.append(gcmd_project.get('short_name'))
        all_aliases.append(gcmd_project.get('long_name'))
        
    # search drafts for many cmr query object (such as campaign)
    change_response = api.get('change_request')['data']
    filtered_drafts = [co for co in change_response if filter_co(co, table_name, query_value=query_value)]

    # loop through every result in drafts for main query object
    for draft in filtered_drafts:
        all_aliases.append(draft['update'].get('short_name'))
        all_aliases.append(draft['update'].get('long_name'))
        
        # search draft aliases for matches to each main query object uuid
        draft_aliases = [co for co in change_response if filter_co(co, 'alias', 'object_id', draft['uuid'])]
        for alias in draft_aliases:
            all_aliases.append(alias['update'].get('short_name'))
        
        # GCMD items are not expected to ever be in the draft stage, so only the db propper is queried
        gcmd_table = 'gcmd_project'
        gcmd_uuids = draft['update'].get(gcmd_table + 's', [])
        for gcmd_uuid in gcmd_uuids:
            gcmd_project = api.get(f'{gcmd_table}/{gcmd_uuid}')['data']
            all_aliases.append(gcmd_project.get('short_name'))
            all_aliases.append(gcmd_project.get('long_name'))

    all_aliases = purify_list(all_aliases)

    return all_aliases


def bulk_cmr_query(table_name, aliases):
    query_parameter = cmr_parameter_transform(table_name)
    raw_metadata_list = query_cmr(query_parameter, aliases)

    processed_metadata_list = process_metadata_list(raw_metadata_list)

    return processed_metadata_list

####################################################################################################################################################################################


def general_extractor(campaign_metadata, field):
    """Extracts and aggregates a specific top level item from the campaign_metadata.

    Args:
        campaign_metadata (dict): this is a custom dict generated by campagin_xml_json
        field (str): Key value for the desired field name

    Returns:
        list: Aggregated list of the values in the requested field.
    """

    data = []
    for reference in campaign_metadata:
        value = reference['metadata'].get(field, '')
        if value:
            data.append(value)
    return data


def extract_daacs(campaign_metadata):
    """Extracts and aggregates all the daacs from a single campaign.

    Args:
        campaign_metadata ([type]): [description]

    Returns:
        list: list of daac names
    """

    # TODO: inventory team should specify which role they are most concerned with
    role_filter=['ARCHIVER', 'DISTRIBUTOR', 'PROCESSOR', 'ORIGINATOR']

    mega_daac_list=general_extractor(campaign_metadata, 'DataCenters')
    daacs = [
        daac['ShortName']
            for daac_list in mega_daac_list
                for daac in daac_list
                    if daac['Roles'][0] in role_filter
            ]

    return daacs


def extract_region_description(campaign_metadata):
    """Extracts the GCMD LocationKeywords from the metadata. These will be
    used as a proxy for region_description at the campaign level.

    Args:
        campaign_metadata ([type]): [description]

    Returns:
        list: [{'Category': value, 'Type': value, 'Subregion1': value, 'Subregion2': value}]
    """

    nested_regions = general_extractor(campaign_metadata, 'LocationKeywords')

    # json.dumps allows us to take the set of the dictionaries
    # the list comprehension is unpacking the nested entries
    regions_json = set([json.dumps(region)
                    for region_list in nested_regions
                        for region in region_list])
    regions_dict = [json.loads(region) for region in regions_json]

    return regions_dict


def extract_collection_periods(campaign_metadata):
    """Extracts platforms as a proxy for collection_periods and aggregates the metadata

    Args:
        campaign_metadata (dict): this is a custom dict generated by campagin_xml_json

    Returns:
        dict: A dict containing each unique platform and its aggregated metadata, including
            DOIs, short and long names, platform identifiers, and instruments.
    """

    platforms = {}
    for data_product in campaign_metadata:
        print(data_product)

        # TODO: refactor the error handling in this loop 
        for platform_info in data_product['metadata'].get('Platforms', [{}]):
            # generate reference name
            platform_short_name = platform_info.get('ShortName', '')
            platform_long_name = platform_info.get('LongName', '')

            platform_chars = data_product['metadata']['Platforms'][0].get('Characteristics', [])
            platform_identifiers = [char.get('Value', '') for char in platform_chars if char.get('Name') == 'AircraftID']

            platform_reference = '_&_'.join([platform_short_name, platform_long_name] + platform_identifiers)

            # get instruments
            instruments = {}
            if platform_info.get('Instruments'):
                for instrument_info in platform_info.get('Instruments', []):
                    instrument_short_name = instrument_info.get('ShortName', '')
                    instrument_long_name = instrument_info.get('LongName', '')
                    instrument_reference = '_&_'.join([instrument_short_name, instrument_long_name])

                    instruments[instrument_reference] = {
                        'short_name': instrument_short_name,
                        'long_name': instrument_long_name,
                    }

            if platforms.get(platform_reference):
                platforms[platform_reference]['instruments'] = {
                    **platforms[platform_reference]['instruments'],
                    **instruments}
                platforms[platform_reference]['dois'].append(data_product.get('metadata',{}).get('DOI'))

            else:
                platforms[platform_reference] = {
                    'platform_names': {
                        'short_name': platform_short_name,
                        'long_name': platform_long_name},
                    'platform_identifiers': platform_identifiers,
                    'instrument_information_source': 'cmr_api',
                    'auto_generated': True,
                    'instruments': instruments,
                    'dois': [data_product.get('metadata',{}).get('DOI')]
                }

    return platforms


def date_overlap(cmr_start, cmr_end, dep_start, dep_end):
    """Takes two date ranges and returns the number of days of overlap.

    Args:
        cmr_start (datetime): Start date for CMR data
        cmr_end (datetime): End date for CMR data
        dep_start (datetime): Start date for deployment
        dep_end (datetime): End date for deployment

    Returns:
        int: Number of days of overlap of the two date ranges, or 0 if None.
    """

    Range = namedtuple('Range', ['start', 'end'])

    cmr_range = Range(start=cmr_start, end=cmr_end)
    dep_range = Range(start=dep_start, end=dep_end)

    latest_start = max(cmr_range.start, dep_range.start)
    earliest_end = min(cmr_range.end, dep_range.end)

    delta = (earliest_end - latest_start).days + 1
    overlap = max(0, delta)

    return overlap


def date_filter(campaign_metadata, dep_start, dep_end):
    """This function is intended to filter the returned CMR metadata based on a
        date range. It is expected to be used to generate deployment metadata, since
        CMR does not distinguish deployments and the user must input this data.

    Args:
        campaign_metadata (dict): this is a custom dict generated by campagin_xml_json
        dep_start (datetime): Start date for deployment
        dep_end (datetime): End date for deployment

    Returns:
        dict: This is a filtered version of the original metadata given to the function.
    """

    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    filtered_metadata = []
    for reference in campaign_metadata:
        temporal_extents = reference['metadata'].get('TemporalExtents', [{}])[0]

        cmr_start = temporal_extents.get('RangeDateTimes', [{}])[0].get('BeginningDateTime', 'error')
        cmr_end = temporal_extents.get('RangeDateTimes', [{}])[0].get('EndingDateTime', 'error')
      
        if cmr_start == 'error' or cmr_end == 'error':
            print('        ', reference['concept_id'], "failed (full date couldn't be extracted)")
            continue

        try:
            cmr_start = datetime.strptime(cmr_start, date_format)
            cmr_end = datetime.strptime(cmr_end, date_format)
            print('        ', reference['concept_id'], 'success')            
        except ValueError:
            # might be able to update the code to capture some of these incorrectly formatted dates
            # example: time data '2002-03-21T00:00:00Z' does not match format '%Y-%m-%dT%H:%M:%S.%fZ'
            print('        ', reference['concept_id'], "failed (date was in wrong format)")
            continue

        days_overlapping = date_overlap(cmr_start, cmr_end, dep_start, dep_end)
        if days_overlapping > 0:
            filtered_metadata.append(reference)

    return filtered_metadata


def project_filter(campaign_metadata, short_name):
    """Filters the campaign_metadata on a given project short_name.

    Args:
        campaign_metadata (dict): this is a custom dict generated by campagin_xml_json
        short_name (str): Project short name

    Returns:
        dict: This is a filtered version of the original metadata given to the function.
    """
    # TODO: does it make sense to use any()?
    filtered_metadata = []
    for reference in campaign_metadata:
        projects = reference['metadata'].get('Projects', [])
        for project in projects:
            project_short_name = project.get('ShortName', '')
            if short_name.lower() == project_short_name.lower():
                filtered_metadata.append(reference)
                break
    return filtered_metadata


def combine_spatial_extents(spatial_extents):
    # TODO: this should combine multiple spatial extents into a total coverage 
    pass
