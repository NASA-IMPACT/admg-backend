import requests
import json
from io import BytesIO
from lxml import etree
from config import print_on as PRINT_ON
from datetime import datetime
from collections import namedtuple

def custom_print(obj=None):
    """Print wrapper that can be used for optional print functionality. Note
    that this functions takes in the global variable PRINT_ON from the config
    file.

    Args:
        obj (obj): Any printable Python object
    """

    if PRINT_ON:
        if obj:
            print(obj)
        else:
            print()


def calculate_num_returned(num_hits, page_size, page_num):
    naive = page_size*page_num
    if naive < num_hits:
        num_returned = naive
    else:
        num_returned = num_hits % naive

    return num_returned


def ingest_xml(url):
    response = requests.get(url)  # , headers={'Connection': 'close'})
    rdf_file = BytesIO(response.content)
    tree = etree.parse(rdf_file)  # could fail for a lot of reasons
    return tree


def ingest_json(url):
    response = requests.get(url).text
    try:
        data = json.loads(response)
    except:
        data = None
    return data


def ingest_campaign(short_name, page_num=1, page_size=2000):
    # page_size can be as high as 2000

    # TODO: handle a page_num that is too large
    # TODO: handle a short_name that has no results

    # retrieve search results
    url = f'https://cmr.earthdata.nasa.gov/search/collections?project={short_name}&page_size={page_size}'
    campaign_tree = ingest_xml(url)

    # calculate hits and returned
    num_hits = int(campaign_tree.find('hits').text)
    num_returned = calculate_num_returned(num_hits, page_size, page_num)

    custom_print(f'    Search for campaign {short_name} returned {num_hits} hits.')
    custom_print(f'    {num_returned} results returned.')
    if num_hits > 2000:
        print('OHHHHNOOOOOOO')

    return campaign_tree


def campaign_xlm_json(campaign_tree):

    campaign_metadata = []

    for references in campaign_tree.findall('references'):
        for reference in references:

            name = reference.find('name').text
            concept_id = reference.find('id').text

            url = f'https://cmr.earthdata.nasa.gov/search/concepts/{concept_id}.umm-json'

            metadata = ingest_json(url)

            campaign_metadata.append({'name': name,
                                      'concept_id': concept_id,
                                      'metadata': metadata})

            custom_print(f'name: {name}')
            custom_print(f'    concept_id: {concept_id}')
            custom_print()
    return campaign_metadata


def extract_inst_plat(campaign_metadata):

    platforms = {}
    for data_product in campaign_metadata:

        for platform_info in data_product['metadata']['Platforms']:
            platform_short_name = platform_info['ShortName']
            platforms[platform_short_name] = platforms.get(platform_short_name,[])
            
            # many satellites don't have instrument metadata
            if 'Instruments' in platform_info.keys():
                for instrument_info in platform_info['Instruments']:
                    instrument_short_name = instrument_info['ShortName']
                    platforms[platform_short_name].append(instrument_short_name)
            else:
                pass
                # print(f'{platform_short_name} has no instruments')
                # print()
    
    for platform_name in platforms.keys():
        platforms[platform_name]=set(platforms[platform_name])


    return platforms


def date_overlap(cmr_start, cmr_end, dep_start, dep_end):
    
    Range = namedtuple('Range', ['start', 'end'])

    cmr_range = Range(start=cmr_start, end=cmr_end,)
    dep_range = Range(start=dep_start, end=dep_end)

    latest_start = max(cmr_range.start, dep_range.start)
    earliest_end = min(cmr_range.end, dep_range.end)
    
    delta = (earliest_end - latest_start).days + 1
    overlap = max(0, delta)
    
    return overlap


def date_filter(metadata, dep_start, dep_end):
    filtered_metadata = []
    for reference in metadata:
        TemporalExtents = reference['metadata'].get('TemporalExtents',[{}])[0]
        cmr_start = TemporalExtents.get('RangeDateTimes',[{}])[0].get('BeginningDateTime','error')
        cmr_end = TemporalExtents.get('RangeDateTimes',[{}])[0].get('EndingDateTime','error')
        
        cmr_start = datetime.strptime(cmr_start, '%Y-%m-%dT%H:%M:%S.%fZ')
        cmr_end = datetime.strptime(cmr_end, '%Y-%m-%dT%H:%M:%S.%fZ')
        
        days_overlapping = date_overlap(cmr_start, cmr_end, dep_start, dep_end)
        if days_overlapping > 0:
            filtered_metadata.append(reference)
        
    return filtered_metadata


def project_filter(metadata, short_name):
    # might not be necessary
    filtered_metadata = []
    for reference in metadata:
        projects = reference['metadata'].get('Projects',[])
        print(projects)
        print()
        for project in projects:
            project_short_name = project.get('ShortName','')
            if short_name.lower() == project_short_name.lower():
                filtered_metadata.append(reference)
                break

    return filtered_metadata   

def general_extractor(metadata, field):
    data = []
    for reference in campaign_metadata:
        value = reference['metadata'].get(field,'')
        if value:
            data.append(value)
    return data    

def combine_spatial_extents(spatial_extents):
    # TODO: this should combine multiple spatial extents into a total coverage 
    pass
