# load the django environment
import os
import django
import pprint
from tabulate import tabulate

# configure the django os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

# Shell Plus Model Imports
from admg_webapp.users.models import User
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from api_app.models import ApprovalLog, Change, Recommendation
from data_models.models import (
    Alias,
    Campaign,
    CollectionPeriod,
    DOI,
    Deployment,
    FocusArea,
    GcmdInstrument,
    GcmdPhenomenon,
    GcmdPlatform,
    GcmdProject,
    GeographicalRegion,
    GeophysicalConcept,
    HomeBase,
    IOP,
    Image,
    Instrument,
    MeasurementRegion,
    MeasurementStyle,
    MeasurementType,
    PartnerOrg,
    Platform,
    PlatformType,
    Repository,
    Season,
    SignificantEvent,
    Website,
    WebsiteType,
)
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.contrib.sites.models import Site
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    PeriodicTasks,
    SolarSchedule,
)
from django_celery_results.models import ChordCounter, GroupResult, TaskResult
from oauth2_provider.models import AccessToken, Application, Grant, IDToken, RefreshToken
from rest_framework.authtoken.models import Token, TokenProxy

# Shell Plus Django Imports
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Case, Count, F, Max, Min, Prefetch, Q, Sum, When
from django.utils import timezone
from django.urls import reverse
from django.db.models import Exists, OuterRef, Subquery

# pprint.pprint(dir(Change))
# pprint.pprint(dir(Campaign))


def get_campaigns():
    campaigns = Campaign.objects.all()
    table_data = []

    # build a table with the data
    for campaign in campaigns:
        table_data.append([campaign.short_name, campaign.uuid])

    table_headers = ['short_name', 'uuid']

    table = tabulate(table_data, headers=table_headers, tablefmt='fancy_grid')

    print(table)
    return table


def get_campaign():
    my_campaign = Campaign.objects.filter(short_name='issue-429')
    table_data = []
    # build a table with the data
    for info in my_campaign:
        table_data.append(
            [
                info.short_name,
                info.uuid,
                info.aliases,
            ]
        )

    table_headers = ['short_name', 'uuid', 'aliases']

    table = tabulate(table_data, headers=table_headers, tablefmt='fancy_grid')

    print(table)


def get_alias():
    pprint.pprint(dir(Alias))
    aliases = Alias.objects.all()
    table_data = []

    # build a table with the data
    for alias in aliases:
        table_data.append([alias.source, alias.uuid, alias.parent_fk, alias.short_name])

    table_headers = ['source', 'uuid', 'parent_fk', 'short_name']

    table = tabulate(table_data, headers=table_headers, tablefmt='fancy_grid')

    print(table)


if "__main__" == __name__:
    # get_campaigns()
    # get_campaign()
    get_alias()
