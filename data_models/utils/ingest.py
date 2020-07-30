import json
import pandas as pd
import os

try:
    import validate
    from general import (many_to_many, many_cols)
except ImportError:
    from . import validate
    from .general import (many_to_many, many_cols)

def rename_columns(db, table_name, remap_dict):
    table = db[table_name]
    table.rename(mapper=remap_dict[table_name], axis='columns', inplace=True)
    return table


def sheet(excel_data, remap_dict, sheet_name, remap_name, header_row, data_row):

    df = excel_data[sheet_name].copy()
    df.columns = df.iloc[header_row]
    df = df[data_row:]
    df.fillna(value='Information Not Available', inplace=True)

    if remap_name:
        df.rename(mapper=remap_dict[remap_name], axis='columns', inplace=True)

    return df  


def main(file_path):
    
    # this dict will hold all the database tables
    db = {}

    excel_data = pd.read_excel(file_path, sheet_name = None)

    base_path = os.path.join(os.path.abspath('.'), 'config')
    
    mapping_columns = json.load(open(os.path.join(base_path, 'mapping_columns.json'), 'r'))
    mapping_ingest = json.load(open(os.path.join(base_path, 'mapping_ingest.json'), 'r'))
    mapping_limited_sheets = json.load(open(os.path.join(base_path, 'mapping_limited_sheets.json'), 'r'))
    mapping_limited_cols = json.load(open(os.path.join(base_path, 'mapping_limited_cols.json'), 'r'))

    validate.sheet_names(excel_data)

    ######################
    ### LIMITED FIELDS ###
    ######################

    # initial cleaning
    limited = excel_data['Limited Fields'][3:].copy()
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
        'instrument_type',
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

