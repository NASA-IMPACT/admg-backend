from data_models.models import Campaign, Website
import django_tables2 as tables
from django_tables2 import A

from data_models.models import (
    Campaign,
    Platform,
    Website,
    Alias,
    Instrument,
    GcmdInstrument
)


class BasePublishedListTable(tables.Table):
    pass


class PublishedCampaignListTable(tables.Table):
    class Meta:
        model = Campaign
        fields = ["short_name", "long_name", "funding_agency"]


class PublishedPlatformListTable(BasePublishedListTable):
    class Meta:
        model = Platform


class PublishedBasicListTable(BasePublishedListTable):
    class Meta:
        model = GcmdInstrument


class PublishedWebsiteListTable(BasePublishedListTable):
    class Meta:
        model = Website


class PublishedAliasListTable(BasePublishedListTable):
    class Meta:
        model = Alias
