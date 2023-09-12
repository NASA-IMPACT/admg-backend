import pytest
from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType


@pytest.fixture(scope='session')
def load_test_data(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        ContentType.objects.all().delete()
        call_command('loaddata', 'cmr/fixtures/stage_backup_2023.05.23.json')
