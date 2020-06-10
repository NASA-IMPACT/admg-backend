import pandas as pd
import json
import validate
from general import many_to_many, many_cols
import ingest


def sheet(excel_data, remap_dict, sheet_name, remap_name, header_row, data_row):

    df = excel_data[sheet_name].copy()
    df.columns = df.iloc[header_row]
    df = df[data_row:]
    df.fillna(value='Information Not Available', inplace=True)

    if remap_name:
        df.rename(mapper=remap_dict[remap_name], axis='columns', inplace=True)

    return df  


def main():
    excel_data = pd.read_excel('ADMG Airborne Campaign Inventory.xlsx', sheet_name = None)
    
    column_mapping = json.load(open('column_mapping.json', 'r'))
    ingest_mapping = json.load(open('ingest_mapping.json', 'r'))
    limited_mapping = json.load(open('limited_mapping.json', 'r'))
    
    validate.sheet_names(excel_data)
    

    ### LIMITED FIELDS ###
    # initial cleaning
    limited = excel_data['Limited Fields'][2:].copy()
    limited.columns = ['Ingest Label', 
                            'short_name', 
                            'long_name', 
                            'description', 
                            'gcmd_translation', 
                            'examples', 
                            'notes']
    limited.fillna(value='Information Not Available', inplace=True)
    
    db = {}

    # ingest all the limited fields 
    for table_name in limited_mapping.keys():
            db[table_name] = limited[limited['Ingest Label'] == limited_mapping[table_name]['sheet_name']].copy()
    
    ### DATA FIELDS ###
    # ingest all the data_fields
    for table_name in ingest_mapping.keys():
            db[table_name] = sheet(excel_data=excel_data, 
                                    remap_dict=column_mapping,
                                    sheet_name=ingest_mapping[table_name]['sheet_name'],
                                    remap_name=ingest_mapping[table_name]['remap_name'],
                                    header_row=ingest_mapping[table_name]['header_row'], 
                                    data_row=ingest_mapping[table_name]['data_row'])
    
    return {'excel_data':excel_data, 'database':db}

