from helper_functions import * 
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
    pickle.dump(campaign_metadata, open(f'cmr_data-{short_name}','wb'))    

    return campaign_metadata

def get_campaign(short_name):


def get_deployment(campaign_metadata, dep_start, dep_end):



# user input
short_name='above'
dep_start = datetime(2015,1,2)
dep_end = datetime(2016,1,1)

# query api
# campaign_trees = ingest_campaign(short_name)
# campaign_metadata = campaign_xlm_json(campaign_trees)
campaign_metadata = pickle.load(open('cmr_data','rb'))

# TODO: replace this with save to database
pickle.dump(campaign_metadata, open('cmr_data','wb'))

