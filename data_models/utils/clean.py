import pandas as pd

def remove_NaN_columns(db):
    for table_name in db.keys():
        table = db[table_name]
        
        table = table[[col for col in table.keys() if isinstance(col, str)]]
        db[table_name]=table
        
    return db
        
def strip_all_columns(db):
    for table_name in db.keys():
        table = db[table_name]
        text_col_df = table.select_dtypes(['object'])
        columns = [col for col in text_col_df.columns if 'date' not in col]
        table[columns] = table[columns].apply(lambda x: x.str.strip())
        
        db[table_name]=table
        if table_name == 'iopse':
            print(columns)
    return db
    