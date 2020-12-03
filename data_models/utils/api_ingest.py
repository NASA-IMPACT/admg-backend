import pickle
import json
import requests
import numpy as np
import datetime
import pandas as pd
from api import Api


def pluralize_table_name(table_name):
    if table_name == 'repository':
        plural = 'repositories'
    else:
        plural = table_name + 's'
    return plural


def remove_ignored_data(data):
    print('\n ----- Removing Ignored Data')
    
    retval = {}
    for key, value in data.items():
        if key == "ignore_code":
            retval[key] = value
        elif 'ignore' not in key:
            retval[key] = value
        
        try:
            if np.isnan(value):
                retval[key] = 0
        except Exception:
            pass 
        
        if isinstance(value, datetime.datetime):
            retval[key] = value.isoformat().split('T')[0]
            
            
    return retval


def update_uuid_map(primary_key_map, foreign_key_uuid_map, table_name, data, create_response):
    uuid = create_response['data']['action_info']['uuid_changed']

    primary_key = primary_key_map[table_name] # gets the correct column, usually short_name
    primary_value = data[primary_key] # finds the actual value for the primary key, usually the short_name

    foreign_key_uuid_map[table_name][primary_value] = uuid

    return foreign_key_uuid_map


def resolve_many_to_many_keys(table_name, data, validation=False):
    print('\n ----- Resolving Many to Many')
    
    # data should be json of the row
   
    primary_key = primary_key_map[table_name]
    primary_value = data[primary_key]
    tables = [key for key in db[table_name].keys() if "table-" in key]
    
    print(f'{primary_key=}')
    print(f'{primary_value=}')
    print(f'{tables=}')
    
    print('foriegn info -----')
    for table in tables:
        _, foreign_table, foreign_key = table.split("-")
        linking_table = f"{table_name}-to-{foreign_table}"
#         if linking_table not in ignore_tables:
#         print(linking_table, table_name, primary_value, foreign_table)
        foreign_values = db[linking_table][db[linking_table][table_name] == primary_value][foreign_table]
        
        if validation:
            mapped_uuids = [i for i in foreign_values] # is actually just short names, not uuids
        else:
            mapped_uuids = [
                foreign_key_uuid_map[foreign_table][val] 
                    for val in foreign_values 
                        if val != "Information Not Available" and foreign_key_uuid_map[foreign_table].get(val)
            ]

        plural_field = pluralize_table_name(foreign_table)
        
        data[plural_field] = mapped_uuids
        if data.get(table):
            del data[table]
            
        print(f'{foreign_table=}')
        print(f'{foreign_key=}')
        print(f'{linking_table=}')
        print(f'{foreign_values=}')
        print(f'{mapped_uuids=}')
        print()


def resolve_foreign_keys(table_name, data, validation=False):
    print('\n ----- Resolving Foreign Keys')
    # data should be json of the row

    try:
        fields = [key for key in data.keys() if "foreign-" in key]
    except:
        import ipdb; ipdb.set_trace()
        assert False
    for field in fields:

        _, foreign_table, foreign_key = field.split("-")
        foreign_value = data[field]

        print()
        print(f'{foreign_value=}')
        print(f'{fields=}')
            
        if validation:
                if table_name in ['platform_type', 'instrument_type', 'measurement_type', 'measurement_style']:
                    foreign_table='parent'
                data[foreign_table] = foreign_value
        else:
                if foreign_key_uuid_map[foreign_table].get(foreign_value):
                    mapped_uuid = foreign_key_uuid_map[foreign_table][foreign_value]   
                    if table_name in ['platform_type', 'instrument_type', 'measurement_type', 'measurement_style']:
                        foreign_table='parent'
                    data[foreign_table] = mapped_uuid
        del data[field]


def remove_nones(data):
    print('\n ----- Removing Nones')
    return {key:value for key, value in data.items() if value != 'none' and value != "Information Not Available"}


def correct_values(db, table_name, column, wrong_value, correct_value):
    db[table_name][column]=db[table_name][column].apply(lambda x: x if x!=wrong_value else correct_value)


def correct_gmcd(db):
    # remove multiple gcmd links. This will need to be properly implemented in the future
    correct_values(
        db=db,
        table_name = 'platform_type',
        column = 'gcmd_uuid',
        wrong_value = '227d9c3d-f631-402d-84ed-b8c5a562fc27, 06e037ed-f463-4fa3-a23e-8f694b321eb1',
        correct_value = '227d9c3d-f631-402d-84ed-b8c5a562fc27')

    correct_values(
        db=db,
        table_name = 'platform_type',
        column = 'gcmd_uuid',
        wrong_value = '57b7373d-5c21-4abb-8097-a410adc2a074, 491d3fcc-c097-4357-b1cf-39ccf359234, 2219e7fa-9fd0-443d-ab1b-62d1ccf41a89',
        correct_value = '57b7373d-5c21-4abb-8097-a410adc2a074')

    correct_values(
        db=db,
        table_name = 'geographical_region',
        column = 'gcmd_uuid',
        wrong_value = 'd40d9651-aa19-4b2c-9764-7371bb64b9a7, 3fedcf7c-7b0c-4b51-abd2-2c54de713061',
        correct_value = 'd40d9651-aa19-4b2c-9764-7371bb64b9a7')

    correct_values(
        db=db,
        table_name = 'geophysical_concept',
        column = 'gcmd_uuid',
        wrong_value = '0611b9fd-fd92-4c4d-87bb-bc2f22c548bc, 4dd22dc9-1db4-4187-a2b7-f5b76d666055',
        correct_value = '0611b9fd-fd92-4c4d-87bb-bc2f22c548bc')

    correct_values(
        db=db,
        table_name = 'geophysical_concept',
        column = 'gcmd_uuid',
        wrong_value = 'c9e429cb-eff0-4dd3-9eca-527e0081f65c, 62019831-aaba-4d63-a5cd-73138ccfa5d0',
        correct_value = 'c9e429cb-eff0-4dd3-9eca-527e0081f65c')

    correct_values(
        db=db,
        table_name = 'geophysical_concept',
        column = 'gcmd_uuid',
        wrong_value = '0af72e0e-52a5-4695-9eaf-d6fbb7991039, 637ac172-e624-4ae0-aac4-0d1adcc889a2',
        correct_value = '0af72e0e-52a5-4695-9eaf-d6fbb7991039')

    return db


def get_foreign_key_map(reload=True):
    # TODO: can I remove the loading of saved maps once it runs smoothly?
    reset_map = True
    if reset_map:
        foreign_key_uuid_map = {
            'platform_type': {},
            'home_base': {},
            'repository': {},
            'focus_area': {},
            'season': {},
            'measurement_type': {},
            'measurement_style': {},
            'measurement_region': {},
            'geographical_region': {},
            'geophysical_concept': {},
            'campaign': {},
            'platform': {},
            'instrument': {},
            'deployment': {},
            'iop': {},
            'significant_event': {},
            'partner_org': {},
            'collection_period': {},
            'gcmd_phenomena': {},
            'gcmd_project': {},
            'gcmd_platform': {},
            'gcmd_instrument': {},
            'measurement_keywords': {},
        }   
    else:
        foreign_key_uuid_map = pickle.load(open('foreign_key_uuid_map','rb'))

    return foreign_key_uuid_map   


def handle_blank_values(db):

    # add the default note for blank values
    columns_to_replace = [
        'description',
        'technical_contact',
        'spatial_resolution',
        'temporal_resolution',
        'radiometric_frequency'
    ]

    for column in columns_to_replace:
        correct_values(
            db=db,
            table_name = 'instrument',
            column = column,
            wrong_value = 'Information Not Available',
            correct_value = 'This data will be added in future versions'
        )

    # add the default note for blank values
    columns_to_replace = [
        'description',
        'technical_contact',
        'spatial_resolution',
        'temporal_resolution',
        'radiometric_frequency'
    ]

    for column in columns_to_replace:
        correct_values(
            db=db,
            table_name = 'instrument',
            column = column,
            wrong_value = 'Information Not Available',
            correct_value = 'This data will be added in future versions'
        )

    return db


def order_tables(db):

    # order tables
    # ingest these first
    first = db['platform_type'][db['platform_type']['foreign-platform_type-short_name']=='none']

    # ingest these second
    second = db['platform_type'][db['platform_type']['foreign-platform_type-short_name']!='none']

    # correctly ordered
    db['platform_type'] = pd.concat([first, second])

    # ingest these first
    first = db['measurement_type'][db['measurement_type']['foreign-measurement_type-short_name']=='none']

    # ingest these second
    second = db['measurement_type'][db['measurement_type']['foreign-measurement_type-short_name']!='none']

    # correctly ordered
    db['measurement_type'] = pd.concat([first, second])

    # ingest these first
    first = db['measurement_style'][db['measurement_style']['foreign-measurement_style-short_name']=='none']

    # ingest these second
    second = db['measurement_style'][db['measurement_style']['foreign-measurement_style-short_name']!='none']

    # correctly ordered
    db['measurement_style'] = pd.concat([first, second])

    return db


def filter_validation_results(validation_dict):
    
    ignore_codes = ['unique', 'does_not_exist']
    ignore_messages = ['valid UUID']
    
    filtered_dict = validation_dict.copy()
    for field, validation_results in validation_dict.items():
        for result in validation_results:
            # codes
            for code in ignore_codes:
                if code in result['code']:
                    filtered_dict.pop(field)
            # messages
            for message in ignore_messages:
                if message in result['message']:
                    filtered_dict.pop(field)
    return filtered_dict


def prepare_db():
    api = Api('test')

    db = pickle.load(open('ingest_data/db_20201028', 'rb')) # fresh_data_filtered

    primary_key_map = json.load(open("config/mapping_primary.json"))
    ingest_order = json.load(open("config/ingest_order.json"))
    foreign_key_uuid_map = get_foreign_key_map(reload=True)

    db = correct_gmcd(db)

    db = handle_blank_values(db)

    db = order_tables(db)

    return db


def remove_field(data, field_name, field_value=None):
    """Accepts json data of fields and field values, along with a 
    field_value to be removed and an optional field_value to narrow
    the removal criteria.

    Args:
        data (dict): dict of field_names: field_values
        field_name (str): field name or column header from sheets
        field_value (str/int/?, optional): value to match against as a pre
            requisite for field removeal. Defaults to None which will execute
            a broad match.

    Returns:
        dict: dict with the removed field
    """
    if field_name in data.keys():
        if field_value:
            if data[field_name]==field_value:
                data.pop(field_name)
        else:
            data.pop(field_name)
    return data

def format_table_name(table_name):
    """Table names need a special format to go through the validation endpoint:
    PartnerOrg instead of partner_org. This function handles this conversion as
    well as some exceptions.

    Args:
        table_name (str): table name in format partner_org

    Returns:
        str: table name in format PartnerOrg
    """

    exceptions = {
        'Iop': 'IOP',
        'Doi': 'DOI'
    }

    formatted_table_name = ''.join([word.capitalize() for word in table_name.split('_')])
    formatted_table_name = exceptions.get(formatted_table_name, formatted_table_name)

    return formatted_table_name


# ingests everything except for collection period
all_validation = {}
with open("result.txt", "w") as f:
    for table_name in ingest_order:
        all_validation[table_name]=[]
    # for table_name in ["platform_type"]:
        for index, row in db[table_name].iterrows():
            print(table_name, index)
            api_data = row.to_dict()
            print(api_data)
            api_data = remove_ignored_data(api_data)
            api_data = remove_nones(api_data)
            primary_key = primary_key_map[table_name]
            primary_value = api_data.get(primary_key)
            if primary_value:
                resolve_many_to_many_keys(table_name, api_data, True)
                resolve_foreign_keys(table_name, api_data, True)           
                
                api_data = remove_field(api_data, 'end_date', 'ongoing')
                        
#                 if data.get('short_name')=='D3R':
#                     import ipdb; ipdb.set_trace()
                formatted_table_name = format_table_name(table_name)

                try:
                    validation_response = api.validate_json(formatted_table_name, api_data, False)
                except:
                    import ipdb; ipdb.set_trace()
                    assert False    
                validation_dict = json.loads(validation_response.content)
                
                all_validation[table_name].append({
                    'original_data':api_data,
                    'validation_results':validation_dict,
                })
    
#                 api_response = api.create(table_name, api_data)
#                 if not(api_response['success']):
#                     if 'unique' in api_response['message']:
#                         f.write(f'{table_name}, {primary_value}, not ingested because of duplication\n')
#                     else:
#                         f.write(f'{table_name}, {primary_value}, not ingested because unknown error\n')
#                         f.write(f"{table_name}: {primary_value}, {json.dumps(api_data)}\n")
#                         f.write(f"{table_name}: {primary_value}, {json.dumps(api_response)}\n")
#                 else:
#                     print(table_name)
#                     foreign_key_uuid_map = update_uuid_map(primary_key_map, foreign_key_uuid_map, table_name, api_data, api_response)
#                     f.write(f"{json.dumps(api_response)}\n")
#                 #####
#             else:
#                 f.write(f"{table_name}: {primary_key}, {json.dumps(api_data)}\n")





# filtered_validation = {}
# for table_name, table_values in all_validation.items():
#     filtered_validation[table_name]=[]
#     for entry in table_values:
#         # filter if necessary
#         if entry['validation_results'].get('success', True):
#             validation_dict = {}
#         else:
#             print(entry)
#             validation_dict = json.loads(entry['validation_results']['message'])
#             validation_dict = filter_validation_results(validation_dict)
        
#         if validation_dict:
#             filtered_validation[table_name].append({
#                 'original_data': entry['original_data'],
#                 'validation_results': validation_dict
#             })


import pickle

if __name__ == "__main__":
    db = prepare_db()
    pickle.dump(db, open('test_db_pre_ingest', 'wb'))
