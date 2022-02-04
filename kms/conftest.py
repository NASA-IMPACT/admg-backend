import pytest
import json
import pickle

from django.core.management import call_command

pytest_plugins = [
    "kms.fixtures.gcmd_fixtures"
]

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'admg_database.yaml')

@pytest.fixture
def open_json_file(filepath):
    return json.load(open(filepath, 'r'))

@pytest.fixture
def open_pickle_file(filepath):
    return pickle.load(open(filepath, 'rb'))

