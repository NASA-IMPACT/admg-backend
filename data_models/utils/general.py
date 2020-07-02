import pandas as pd
import numpy as np


def sheet(excel_data, remap_data, sheet_name, remap_name, header_row, data_row):

    df = excel_data[sheet_name].copy()
    df.columns = df.iloc[header_row]
    df = df[data_row:]
    df.fillna(value='Information Not Available', inplace=True)

    df.rename(mapper=remap_data[remap_name], axis='columns', inplace=True)

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
    assert set(campaign_list) == set(db['campaign']['short_name'])

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
    print('\ncopy these platforms into a file for inventory folks\n')
    [print(thing) for thing in platform_filter]

    # instruments
    instrument_filter = list(set(list(db['collection_period']['instrument'])))
    db['instrument'] = db['instrument'][db['instrument']['short_name'].apply(lambda short: short in instrument_filter)]
    print('\ncopy these instruments into a file for inventory folks\n')
    [print(thing) for thing in instrument_filter]

    return db