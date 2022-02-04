import json
import pickle
import pytest

def open_json_file(filepath):
    return json.load(open(filepath, 'r'))

def open_pickle_file(filepath):
    return pickle.load(open(filepath, 'rb'))

@pytest.fixture
def convert_record_input():
    return {
        "Bucket": "A-C",
        "Short_Name": "Test123",
        "Long_Name": "LongName123",
        "UUID": "07a12d76-3794-4d1f-8db3-96a4c9814d54"
    }

@pytest.fixture
def convert_record_result():
    return {
        "bucket": "A-C",
        "short_name": "Test123",
        "long_name": "LongName123",
        "gcmd_uuid": "07a12d76-3794-4d1f-8db3-96a4c9814d54"
    }

@pytest.fixture
def 