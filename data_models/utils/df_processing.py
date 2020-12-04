import collections
import datetime

import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz


def sheet(excel_data, remap_dict, sheet_name, remap_name, header_row, data_row):

    df = excel_data[sheet_name].copy()
    df.columns = df.iloc[header_row]
    df = df[data_row:]
    df.fillna(value='Information Not Available', inplace=True)

    if remap_name:
        df.rename(mapper=remap_dict[remap_name], axis='columns', inplace=True)

    return df


def many_cols(col_names):
    return [col for col in col_names if 'table' in col]


def many_to_many(db, table_name, many_col, keep_all=False):
    name = many_col.split('-')[1]

    if keep_all:
        df = db[table_name].copy()
    else:
        df = db[table_name][['short_name',many_col]].copy()
    
    # this line is only necessary if the data is not already a proper list
    df[many_col]=df[many_col].apply(lambda x: [item.strip() for item in x.split(',')])
    
    result =  pd.DataFrame({
           col:np.repeat(df[col].values, df[many_col].str.len())
           for col in df.columns.drop(many_col)}
        ).assign(**{many_col:np.concatenate(df[many_col].values)})[df.columns]
    
    result.rename(columns={'short_name':table_name, many_col:name}, inplace=True)    
    
    return result


def correct_values(db, table_name, column, wrong_value, correct_value):
    """Simple find and replace to correct values prior to import

    Args:
        db (dict): Dictionary of dataframes, where each key is the name of the database
            table
        table_name (str): name of the table inside of which the values will be replaced
        column (str): name of the column (field) where the values will be replaced
        wrong_value (str): str value of the incorrect value
        correct_value (str): str value of the correct value

    Returns:
        db (dict): Dictionary of dataframes, where each key is the name of the database table
    """

    db[table_name][column] = db[table_name][column].apply(lambda x: x if x != wrong_value else correct_value)

    return db


def filter_campaigns(db, campaign_list):
    """Takes a pre-database dataframe and a list of campaigns and filters all the related tables to only 
    contain data linked to those campaigns.

    Args:
        db (dict): Dictionary of dataframes, where each key is the name of the database table
        campaign_list (list): list of campaign short names

    Returns:
        db (dict): Dictionary of dataframes, where each key is the name of the database table
    """

    # campaigns
    db['campaign'] = db['campaign'][db['campaign']['short_name'].apply(lambda x: x in campaign_list)]

    # deployments
    db['deployment'] = db['deployment'][db['deployment']['foreign-campaign-short_name'].apply(lambda short: short in campaign_list)]

    # collection periods
    db['collection_period'] = db['collection_period'][db['collection_period']['foreign-campaign-short_name'].apply(lambda short: short in campaign_list)]

    # iop
    db['iop'] = db['iop'][db['iop']['foreign-campaign-short_name'].apply(lambda short: short in campaign_list)]

    # sig events
    db['significant_event'] = db['significant_event'][db['significant_event']['foreign-campaign-short_name'].apply(lambda short: short in campaign_list)]

    # platforms
    platform_filter = list(set(list(db['collection_period']['foreign-platform-short_name'])))
    db['platform'] = db['platform'][db['platform']['short_name'].apply(lambda short: short in platform_filter)]

    # instruments
    instrument_filter = list(set(list(db['collection_period']['foreign-instrument-short_name'])))
    db['instrument'] = db['instrument'][db['instrument']['short_name'].apply(lambda short: short in instrument_filter)]

    return db


def filter_gcmd_tables(db):
    # delete INA in all GCMD tables

    db['campaign-to-gcmd_project'] = db['campaign-to-gcmd_project'][db['campaign-to-gcmd_project']['gcmd_project']!='Information Not Available']
    db['platform-to-gcmd_platform'] = db['platform-to-gcmd_platform'][db['platform-to-gcmd_platform']['gcmd_platform']!='Information Not Available']
    db['instrument-to-gcmd_instrument'] = db['instrument-to-gcmd_instrument'][db['instrument-to-gcmd_instrument']['gcmd_instrument']!='Information Not Available']
    db['instrument-to-gcmd_phenomena'] = db['instrument-to-gcmd_phenomena'][db['instrument-to-gcmd_phenomena']['gcmd_phenomena']!='Information Not Available']

    gcmd_phenomena_filter = list(set(list(db['instrument-to-gcmd_phenomena']['gcmd_phenomena'])))
    db['gcmd_phenomena'] = db['gcmd_phenomena'][db['gcmd_phenomena']['ignore_code'].apply(lambda short: short in gcmd_phenomena_filter)]

    gcmd_instrument_filter = list(set(list(db['instrument-to-gcmd_instrument']['gcmd_instrument'])))
    db['gcmd_instrument'] = db['gcmd_instrument'][db['gcmd_instrument']['gcmd_uuid'].apply(lambda short: short in gcmd_instrument_filter)]

    gcmd_platform_filter = list(set(list(db['platform-to-gcmd_platform']['gcmd_platform'])))
    db['gcmd_platform'] = db['gcmd_platform'][db['gcmd_platform']['gcmd_uuid'].apply(lambda short: short in gcmd_platform_filter)]

    gcmd_project_filter = list(set(list(db['campaign-to-gcmd_project']['gcmd_project'])))
    db['gcmd_project'] = db['gcmd_project'][db['gcmd_project']['gcmd_uuid'].apply(lambda short: short in gcmd_project_filter)]

    return db


def log_short_names(db, table_name):
    """Saves a log file containing the short_names from a specified table. This functionality is designed
    primarily for use with instruments and platforms so that the Inventory Team can more easily identify
    which objects are linked to which campaigns. Typically the input database will have been filtered on 
    some criteria.

    Args:
        db (dict): Dictionary of dataframes, where each key is the name of the database table
        table_name (str): name of the table from which the short_names will be logged
    """

    with open(f'logs/short_names-{table_name}.log', 'w') as f:
        f.write(f'this file contains the short_names of every {table_name} in the pre-ingested database\n')
        f.writelines(f'{item}\n' for item in db[table_name]['short_name'].values)


def lan(data):
    if isinstance(data, str):
        return ''.join([char.lower() for char in data if char.isalnum()])
    else:
        return data


def fuzzy_match(string, choices, threshold=.9):   
    return [(test,x)  for test in choices if (x := fuzz.ratio(string, test))>=threshold]
    
    
def validate_foreign_keys(db, data_table, data_index, data_column, foreign_table, foreign_column):
    # outputs dataframe of incorrect values with suggestions
    
    foreign_key_list = list(db[foreign_table][foreign_column])

    if data_table==foreign_table:
        # if a table is heirarchical, this will give a none value to allow parentless ojbects
        foreign_key_list.append('none')

    foreign_dict = {lan(key):key for key in foreign_key_list}
    
    bool_filter = db[data_table][data_column].apply(lambda x: lan(x) not in foreign_dict.keys() and x != 'Information Not Available')
    filtered_df = db[data_table][bool_filter].copy()
    if filtered_df.empty:
        # if the dataframe is empty after filtering, the else code fails
        # makes an empty datafame, preserving the column names
        errors = pd.DataFrame(columns=db[data_table].columns)
    else:
        errors = filtered_df[[data_index, data_column]].copy()
        errors['suggestions'] = errors[data_column].apply(lambda x: [foreign_dict[match[0]] for match in fuzzy_match(lan(x), [lan(key) for key in foreign_dict.keys()], 75)])

    return errors


def lower_alpha_num(column):
    return [''.join([char for char in entry.lower() if char.isalnum()]) for entry in column]


def find_duplicates(db, table, column_name):
    column = [lan(entry) for entry in db[table][column_name]]
    duplicates = [short_name for short_name, count in collections.Counter(column).items() if count > 1] 
    return duplicates


def vali_date(before, after):
    if not(isinstance(before, datetime.datetime) and isinstance(after, datetime.datetime)):
        if not(before == 'Information Not Available' and after == 'Information Not Available'):
            print(f'    non date-time detected: {before}, {after}')
        return False

    return before <= after


def vali_date_dep(root, test, date_type):
    if date_type == 'start':
        return root <= test
    elif date_type == 'end':
        return root >= test


def validate_sheet_names(df):
    """takes in a df of the raw excel dump and validates that is contains the desired sheets"""
    error = False
    expected_sheet_names = ['Limited Fields',
                            'NASA Campaigns',
                            'Platforms',
                            'Instruments',
                            'Deployments',
                            'IOPSE',
                            'Partner Orgs',
                            'CampDepPlatfmInstmnt']

    for expected in expected_sheet_names:
        if expected not in df.keys():
            print(f"There is no sheet named '{expected}' in the excel file")
            error = True
            
    if error:
        raise ValueError('There are missing or incorrectly named sheets in the imported document')    


def remove_NaN_columns(db):
    for table_name in db.keys():
        table = db[table_name]

        table = table[[col for col in table.keys() if isinstance(col, str)]]
        db[table_name] = table

    return db


def strip_all_columns(db):
    for table_name in db.keys():
        table = db[table_name]
        text_col_df = table.select_dtypes(['object'])
        columns = [col for col in text_col_df.columns if 'date' not in col]
        table[columns] = table[columns].applymap(lambda x: x.strip() if isinstance(x, str) else x)

        db[table_name] = table

    return db

def replace_nid(db):
    """Replaces all instances of 'NID' with 'Information Not Available'

    Args:
        db (dict): Dictionary of pandas dataframes representing the inventory import

    Returns:
        dict: replaced version of the input db
    """
    
    for table_name in db.keys():
        db[table_name].replace('NID', 'Information Not Available', inplace=True)

    return db
