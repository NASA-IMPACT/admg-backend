import pandas as pd

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
        table[columns] = table[columns].apply(lambda x: x.strip() if isinstance(x, str) else x)

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