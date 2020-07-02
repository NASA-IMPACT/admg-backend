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
        db (dict): Dictionary of dataframes, where each key is the name of the intended
            table
        table_name (str): name of the table inside of which the values will be replaced
        column (str): name of the column (field) where the values will be replaced
        wrong_value (str): str value of the incorrect value
        correct_value (str): str value of the correct value
    """

    db[table_name][column] = db[table_name][column].apply(lambda x: x if x != wrong_value else correct_value)

    return db
