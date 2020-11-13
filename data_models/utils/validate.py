import pandas as pd
import numpy as np
import collections
from fuzzywuzzy import fuzz
import datetime


def lan(data):
    if isinstance(data, str):
        return ''.join([char.lower() for char in data if char.isalnum()])
    else:
        return data


def fuzzy_match(string, choices, threshold=.9):   
    return [(test,x)  for test in choices if (x := fuzz.ratio(string, test))>=threshold]
    
    
def foreign_keys(db, data_table, data_index, data_column, foreign_table, foreign_column):
    # outputs dataframe of incorrect values with suggestions
    
    foreign_key_list = db[foreign_table][foreign_column]

    foreign_dict = {lan(key):key for key in foreign_key_list}
    
    bool_filter = db[data_table][data_column].apply(lambda x: lan(x) not in foreign_dict.keys() and x != 'Information Not Available')

    errors = db[data_table][bool_filter][[data_index, data_column]].copy()
    errors['suggestions'] = errors[data_column].apply(lambda x: [foreign_dict[match[0]] for match in fuzzy_match(lan(x), [lan(key) for key in foreign_dict.keys()], 75)])
    return errors


def lower_alpha_num(column):
    return [''.join([char for char in entry.lower() if char.isalnum()]) for entry in column]


def find_duplicates(db, table, column_name):
    column = [lan(entry) for entry in db[table][column_name]]
    duplicates = [short_name for short_name, count in collections.Counter(column).items() if count > 1] 
    return duplicates


def vali_date(before, after):
    if not(isinstance(before, datetime.datetime) and isinstance(after,datetime.datetime)):
        if not(before == 'Information Not Available' and after=='Information Not Available'):
            print(f'    non date-time detected: {before}, {after}')
        return False
    
    return before <= after


def vali_date_dep(root, test, date_type):
    if date_type=='start':
        return root <= test
    elif date_type=='end':
        return root >= test


def sheet_names(df):
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
