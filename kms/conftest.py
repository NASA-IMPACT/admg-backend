import pytest

from django.core.management import call_command

# TODO: This needs to move
# More info: https://docs.pytest.org/en/latest/deprecations.html#pytest-plugins-in-non-top-level-conftest-files
# pytest_plugins = [
#     "kms.fixtures.gcmd_fixtures"
# ]
# TODO: Check to make sure this is the best way to import these (instead of pytest_plugins)
from kms.fixtures.gcmd_fixtures import *

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'admg_database.yaml')
