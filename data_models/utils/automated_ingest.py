import pandas as pd
import json
import validate
from general import correct_values, many_to_many, many_cols, filter_gcmd_tables
import ingest
import clean
from config.paths import INVENTORY_PATH
from general import filter_campaigns, log_short_names


def ingest_2(inventory_path=INVENTORY_PATH):

    data = ingest.main(inventory_path)

    excel_data = data['excel_data']
    db = data['database']


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
    db['campaign']['nasa_led'].replace('Information Not Available', 'False',  inplace=True)

    # use booleans inventory is backwards from db 'stationary' vs 'can move'
    db['platform']['stationary'].replace('Y', 'False', inplace=True)
    db['platform']['stationary'].replace('N', 'True', inplace=True)

    db = clean.remove_NaN_columns(db)
    db = clean.strip_all_columns(db)
    db = clean.replace_nid(db)


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

    ingest_campaign_list = json.load(open('config/ingest_campaign_list.json', 'r'))['new_list']

    db = filter_campaigns(db, ingest_campaign_list)

    log_short_names(db, 'instrument')
    log_short_names(db, 'platform')


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

    return db







