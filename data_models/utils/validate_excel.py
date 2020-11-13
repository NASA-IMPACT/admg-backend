import pandas as pd
import json
from data_models.utils.automated_ingest import ingest_2

from data_models.utils import validate
from data_models.utils.general import filter_gcmd_tables

# def validate_excel(path='inventory_data/inventory - 2020.11.12.xlsx'):

def validate_excel(excel_file):
    db = ingest_2(excel_file)

    validation_results = {}
    # short name validation
    results = {}
    for table_name in db.keys():
        if table_name == 'collection_period' or 'gcmd' in table_name:
            # collection_period is skipped because it has been broken out by instrument
            # and therefore it has duplicate short_names
            # gcmd entries are skipped because they are identified by uuid
            continue

        if 'short_name' in db[table_name].keys():
            duplicates = validate.find_duplicates(db, table_name, 'short_name')

            results[table_name] = {
                'errors': duplicates
            }

    validation_results['short_names'] = {
        'results': results,
        'description': "Confirms whether all short_names are unique within thier respective tables. GCMD tables are currently ignored."
    }


    foreign_data_tables = [table_name for table_name in db.keys() if '-to-' in table_name]
    try:
        primary_mapping = json.load(open('config/mapping_primary.json', 'r'))
    except:
        primary_mapping = json.load(open('data_models/utils/config/mapping_primary.json', 'r'))

    # many to many validation
    results = {}
    for data_table in foreign_data_tables:
        data_index = data_table.split('-')[0]
        data_column = foreign_table = data_table.split('-')[2]
        foreign_column = primary_mapping[foreign_table]

        errors = validate.foreign_keys(
            db,
            data_table=data_table,
            data_index=data_index,
            data_column=data_column,
            foreign_table=foreign_table,
            foreign_column=foreign_column
        )
        results[data_table] = {'errors':errors.to_dict()}

    validation_results['many_to_many'] = {
        'results': results,
        'description': "Some fields contain a value pulled from a limited table. This checks those fields to confirm that the given value actually exists in the correct limited table."
    }


    # foriegn key validation
    results = {}
    for table in db.keys():
        # linking is no longer important after collection period is made
        if table == 'linking':
            continue
        for column in db[table].keys():
            if 'foreign' in column:
                print(table)
                break
        for column in db[table].keys():
            if 'foreign' in column:            
                print('   ', column)
                        
                data_table = table
                data_index = 'short_name'
                data_column = column
                foreign_table = column.split('-')[1]
                foreign_column = 'short_name'
                
                errors = validate.foreign_keys(db, 
                                                data_table=data_table,
                                                data_index=data_index,
                                                data_column=data_column,
                                                foreign_table=foreign_table,
                                                foreign_column=foreign_column
                )
                results[data_table] = {'errors':errors.to_dict()}

    validation_results['foreign_keys'] = {
        'results': results,
        'description': "Some fields contain a value pulled from a limited table. This checks those fields to confirm that the given value actually exists in the correct limited table."
    }


    return validation_results