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


def get_json(cmr_url):
    """Takes a CMR query url and returns the response JSON as a dict. 

    Args:
        cmr_url (str): CMR query url

    Returns:
        data (dict): JSON response from the CMR query url
    """

    response = requests.get(cmr_url).text
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
    """The main CMR query is a bulk query that uses multiple aliases. This function
    queries CMR for the concept_ids associated with a single alias. They are aggregated
    by the intended calling function, aggregate_concept_id_queries().

    Args:
        query_parameter (str): CMR query parameter in ['project', 'instrument', 'platform']
        query_value (str): one alias associated with the parameter, such as 'ACES' for 'project'

    Returns:
        concept_id_list (list): list of concept_id strings returned from CMR
    """

    collections_json = universal_query(query_parameter, query_value)
    concept_ids = extract_concept_ids_from_universal_query(collections_json)

    return concept_ids


def aggregate_concept_ids_queries(query_parameter, query_value_list):
    """The main CMR query is a bulk query that uses multiple aliases. This function
    executes each alias query and aggergates the results and removes duplicates.

    Args:
        query_parameter (str): CMR query parameter in ['project', 'instrument', 'platform']
        query_value_list (list of str): list of alias strings associated with the parameter,
            such as 'ACES' for 'project'

    Returns:
        concept_id_list (list): list of concept_id strings returned from CMR
    """

    concept_id_list = []
    for query_value in query_value_list:
        concept_ids = individual_concept_ids_query(query_parameter, query_value)
        concept_id_list.extend(concept_ids)
    concept_id_list = purify_list(concept_id_list, lower=False)

    return concept_id_list


def bulk_cmr_query(query_parameter, query_value_list):
    """Primary CMR query function which takes a parameter and a list of aliases.
    Each alias is queried and the results are aggregated.

    Args:
        query_parameter (str): CMR query parameter in ['project', 'instrument', 'platform']
        query_value_list (list of str): list of alias strings associated with the parameter,
            such as 'ACES' for 'project'

    Returns:
        metadata_list (list): list of dataproduct metadata returned from CMR
    """

    concept_id_list = aggregate_concept_ids_queries(query_parameter, query_value_list)

    concept_ids_responses = universal_query('echo_collection_id[]', concept_id_list)
    metadata_list = [concept_id_data for page in [response['items'] for response in concept_ids_responses] for concept_id_data in page]

    return metadata_list


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


def query_and_process_cmr(table_name, aliases):
    """Takes a database table name and a list of aliases and runs cmr queries for each 
    alias, aggregating the results before filtering out the unused metadata.

    Args:
        query_parameter (str): CMR query parameter in ['project', 'instrument', 'platform']
        aliases (list of str): list of alias strings associated with the parameter,
            such as 'ACES' for 'project'

    Returns:
        processed_metadata_list (list): list of processed dataproduct metadata returned from CMR
    """

    query_parameter = cmr_parameter_transform(table_name)
    raw_metadata_list = bulk_cmr_query(query_parameter, aliases)

    processed_metadata_list = process_metadata_list(raw_metadata_list)

    return processed_metadata_list
