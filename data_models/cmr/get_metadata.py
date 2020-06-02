from helper_functions import (
    campaign_xlm_to_json,
    date_filter,
    extract_collection_periods,
    extract_daacs,
    extract_region_description,
    general_extractor,
    ingest_campaign,
) 
from datetime import datetime
import pickle


def query_api(short_name):
    """Queries the CMR api for a project short name, aggregates all the data from 
    the associated granules, and saves the raw output to the database.

    Args:
        short_name (str): Short name for the campaign

    Returns:
        dict: custom dict holding an aggregation of all the campaign metadata
    """

    campaign_trees = ingest_campaign(short_name)
    campaign_metadata = campaign_xlm_to_json(campaign_trees)

    # TODO: replace this with the final location in the db we decide on
    pickle.dump(campaign_metadata, open(f'cmr_data-{short_name}', 'wb'))    

    return campaign_metadata


def get_campaign(campaign_short_name):
    """Extracts partial campaign metadata from the cmr download. Note that the
    general_extractor can be used to extract additional metadata not currently
    used.

    Args:
        campaign_short_name (str): Project/Campaign short_name

    Returns:
        dict: dictionary containing campaign and top-level table metadata
    """

    # TODO: replace this with the final location in the db we decide on
    campaign_metadata = pickle.load(open(f'cmr_data-{campaign_short_name}', 'rb'))

    db = {'campaign':{}}

    db['campaign']['short_name'] = campaign_short_name

    db['campaign']['gcmd_region'] = extract_region_description(campaign_metadata)

    db['campaign']['repositories'] = extract_daacs(campaign_metadata)

    db['campaign']['spatial_bounds'] = general_extractor(campaign_metadata, 'SpatialExtent')

    db['campaign']['gcmd_phenomena'] = general_extractor(campaign_metadata, 'ScienceKeywords')

    db['campaign']['other_resources'] = general_extractor(campaign_metadata, 'RelatedUrls')    

    return db


def get_deployment_and_cp(campaign_short_name, dep_start, dep_end):
    """Filters the CMR campaign_metadata on a date range and then creates a deployment
    entry as well as a linked list of collection_periods with associated platform and
    instrument metadata.

    Args:
        campaign_metadata ([type]): [description]
        campaign_short_name (str): Project/Campaign short_name
        dep_start (datetime): deployment start date
        dep_end (datetime): deployment end date

    Returns:
        dict: dictionary containing deployment and collection period data
    """

    # TODO: replace this with the final location in the db we decide on
    campaign_metadata = pickle.load(open(f'cmr_data-{campaign_short_name}', 'rb'))

    db = {'deployment': {}}
    db['deployment']['short_name'] = '_&_'.join([campaign_short_name, str(dep_start), str(dep_end)])
    db['deployment']['foreign-campaign-short_name'] = campaign_short_name
    db['deployment']['start_date'] = dep_start
    db['deployment']['end_date'] = dep_end

    deployment_metadata = date_filter(campaign_metadata, dep_start, dep_end)

    db['collection_period'] = extract_collection_periods(deployment_metadata)
    db['collection_period']['foreign-deployment-short_name'] = db['deployment']['short_name']

    return db
