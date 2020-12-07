import json
import pandas as pd
import os

try:
    from data_models.utils.df_processing import *
except ImportError:
    from df_processing import *

# except ImportError:
#     from . import validate
#     from .general import (many_to_many, many_cols)


CAMPAIGNS_TO_INGEST = 'test_campaign'


def rename_columns(db, table_name, remap_dict):
    table = db[table_name]
    table.rename(mapper=remap_dict[table_name], axis='columns', inplace=True)
    return table


def excel_to_df(path_or_excel_file):
    
    # this dict will hold all the database tables
    db = {}

    excel_data = pd.read_excel(path_or_excel_file, sheet_name=None, encoding='utf-8')

    # set the base path and attempt one load of data
    # this problem arrises because of difference between how python sees the files when running on the
    # command line vs running from withing the django application
    try: # django version of imports
        base_path = os.path.join(os.path.abspath('.'), 'data_models/utils/config')
        mapping_columns = json.load(open(os.path.join(base_path, 'mapping_columns.json'), 'r'))
    except: # command line version of imports
        base_path = os.path.join(os.path.abspath('.'), 'config')
        mapping_columns = json.load(open(os.path.join(base_path, 'mapping_columns.json'), 'r'))

    mapping_ingest = json.load(open(os.path.join(base_path, 'mapping_ingest.json'), 'r'))
    mapping_limited_sheets = json.load(open(os.path.join(base_path, 'mapping_limited_sheets.json'), 'r'))
    mapping_limited_cols = json.load(open(os.path.join(base_path, 'mapping_limited_cols.json'), 'r'))

    validate_sheet_names(excel_data)

    ######################
    ### LIMITED FIELDS ###
    ######################

    # initial cleaning
    # TODO: change this drop to be found from a list of total minus desired columns
    limited_columns = excel_data['Limited Fields'].columns
    if len(limited_columns)>8:
        drop = limited_columns[8:]
    else:
        drop = []
    limited = excel_data['Limited Fields'][3:].drop(drop, axis=1)
    limited.columns = ['Ingest Label',
                        'short_name',
                        'long_name',
                        'description',
                        'gcmd_translation',
                        'examples',
                        'notes',
                        'parent',]

    limited.fillna(value='Information Not Available', inplace=True)     
    # ingest all the limited fields 
    for table_name in mapping_limited_sheets.keys():
            db[table_name] = limited[limited['Ingest Label'] == mapping_limited_sheets[table_name]['ingest_label']].copy()
    
    # remap limited fields
    # TODO: consider moving this list to a dedicated file
    tables_to_remap = [
        'platform_type',
        'measurement_type',
        'measurement_style',
        'home_base',
        'repository',
        'focus_area',
        'season',
        'measurement_region',
        'geographical_region',
        'geophysical_concept',
    ]

    for table_name in tables_to_remap:
        db[table_name] = rename_columns(db, table_name, mapping_limited_cols)


    ###################
    ### DATA FIELDS ###
    ###################

    # ingest all the data_fields
    for table_name in mapping_ingest.keys():
            db[table_name] = sheet(excel_data=excel_data, 
                                    remap_dict=mapping_columns,
                                    sheet_name=mapping_ingest[table_name]['sheet_name'],
                                    remap_name=mapping_ingest[table_name]['remap_name'],
                                    header_row=mapping_ingest[table_name]['header_row'], 
                                    data_row=mapping_ingest[table_name]['data_row'])
    
    return {'excel_data':excel_data, 'database':db}


def process_df(db):

    ############
    # Cleaning #
    ############

    # change ignore_code field to be string
    db['gcmd_phenomena']['ignore_code'] = db['gcmd_phenomena']['ignore_code'].apply(lambda x: str(x))

    # # convert gcmd_uuid into string
    # db['instrument']['table-measurement_keywords-gcmd_uuid'] = db['instrument']['table-measurement_keywords-gcmd_uuid'].apply(lambda x: str(x))

    # convert gcmd_uuid into string
    db['instrument']['table-gcmd_phenomena-ignore_code'] = db['instrument']['table-gcmd_phenomena-ignore_code'].apply(lambda x: str(x))

    # remove extra NID from platform type
    db['platform_type'] = db['platform_type'][db['platform_type']['short_name']!='NID']

    # use booleans
    db['campaign']['nasa_led'].replace('YES', 'True', inplace=True)
    db['campaign']['nasa_led'].replace('Information Not Available', 'False', inplace=True)

    # use booleans inventory is backwards from db 'stationary' vs 'can move'
    db['platform']['stationary'].replace('Y', 'False', inplace=True)
    db['platform']['stationary'].replace('N', 'True', inplace=True)

    db = remove_NaN_columns(db)
    db = strip_all_columns(db)
    db = replace_nid(db)


    ##############################
    # Short Name Supplementation #
    ##############################

    # make unique shortname by combining the campaign name and the table sub short name

    db['deployment']['short_name'] = db['deployment']['foreign-campaign-short_name']+'_'+db['deployment']['ignore_deployment_id']
    db['iopse']['foreign-deployment-short_name']=db['iopse']['foreign-campaign-short_name']+'_'+db['iopse']['ignore_deployment']

    # create collection period table
    db['collection_period'] = many_to_many(db, 'linking', 'table-instrument-short_name', keep_all=True)
    db['collection_period']['short_name'] = db['collection_period']['foreign-campaign-short_name']+'_'+db['collection_period']['foreign-deployment-short_name']+'_'+db['collection_period']['foreign-platform-short_name']
    db['collection_period']['foreign-deployment-short_name']=db['collection_period']['foreign-campaign-short_name']+'_'+db['collection_period']['foreign-deployment-short_name']
    
    # correct column naming in collection_period table
    db['collection_period'].rename(columns={'instrument':'foreign-instrument-short_name'}, inplace=True)
    
    db['collection_period']['auto_generated']=True

    #################
    # Matching IOPS #
    #################

    # filter out missing rows on the iopse tab
    db['iopse'] = db['iopse'][db['iopse']['short_name']!='Information Not Available']
    # test for unexpected values in this column
    assert set(db['iopse']['type']) == {'IOP', 'SE'}

    # convert parent and short name to lower so they will match correctly
    db['iopse']['short_name'] = db['iopse']['short_name'].apply(lambda x: x.lower())
    db['iopse']['parent short_name'] = db['iopse']['parent short_name'].apply(lambda x: x.lower())

    db['iop'] = db['iopse'][db['iopse']['type']=='IOP']
    db['significant_event'] = db['iopse'][db['iopse']['type']=='SE']

    # remove unnecessary iopse table
    del db['iopse']

    ###################
    # Campaign Filter #
    ###################

    try:
        ingest_campaign_list = json.load(open('data_models/utils/config/ingest_campaign_list.json', 'r'))[CAMPAIGNS_TO_INGEST]
    except:
        ingest_campaign_list = json.load(open('config/ingest_campaign_list.json', 'r'))[CAMPAIGNS_TO_INGEST]

    db = filter_campaigns(db, ingest_campaign_list)

    # remove info not available
    db['instrument'] = db['instrument'][db['instrument']['short_name']!='Information Not Available']
    db['platform'] = db['platform'][db['platform']['short_name']!='Information Not Available']

    # log_short_names(db, 'instrument')
    # log_short_names(db, 'platform')


    #########################
    # Many to Many Creation #
    #########################

    main_table_names = ['campaign', 'platform', 'instrument', 'deployment']

    for table in main_table_names:
        print(table)
    #     print([col for col in db[table].keys() if isinstance(col,str) and 'table' in col])
        for column in [col for col in db[table].keys() if isinstance(col,str) and 'table' in col]:
            name = column.split('-')[1]
            new_table_name = f"{table}-to-{name}"
            db[new_table_name]=many_to_many(db, table, column)
            print(f'   {new_table_name} created')

    # filter gcmd tables
    db = filter_gcmd_tables(db)
    return db


def excel_to_processed_df(path_or_excel_file):
    db = excel_to_df(path_or_excel_file)['database']
    db = process_df(db)

    return db
