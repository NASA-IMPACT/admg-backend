import os
import uuid

from django.apps import apps
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as geomodels
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db import models


class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True


##################
# Limited Fields #
##################

def get_file_path(instance, path):
    return f'{instance.uuid}{os.path.splitext(path)[1]}'


class Image(BaseModel):
    image = models.ImageField(upload_to=get_file_path)
    description = models.CharField(max_length=1024, default='', blank=True)
    owner = models.CharField(max_length=512, default='', blank=True)
    source_url = models.TextField(blank=True, default='')

    def __str__(self):
        return self.image.name


class LimitedInfo(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, default='', blank=True)
    notes_internal = models.TextField(default='', blank=True)
    notes_public = models.TextField(default='', blank=True)

    class Meta:
        abstract = True


class PlatformType(LimitedInfo):
    parent = models.ForeignKey('PlatformType', on_delete=models.CASCADE, related_name='sub_types', null=True, blank=True)

    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default='')


class MeasurementType(LimitedInfo):
    parent = models.ForeignKey('MeasurementType', on_delete=models.CASCADE, related_name='sub_types', null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default='')


class MeasurementStyle(LimitedInfo):
    parent = models.ForeignKey('MeasurementStyle', on_delete=models.CASCADE, related_name='sub_types', null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default='')


class HomeBase(LimitedInfo):
    location = models.CharField(max_length=512, blank=True, default='')
    additional_info = models.CharField(max_length=2048, blank=True, default='')


class FocusArea(LimitedInfo):
    url = models.CharField(max_length=256, blank=True, default='')


class Season(LimitedInfo):
    pass


class Repository(LimitedInfo):
    gcmd_uuid = models.UUIDField(null=True, blank=True)


class MeasurementRegion(LimitedInfo):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default='')


class GeographicalRegion(LimitedInfo):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default='')


class GeophysicalConcept(LimitedInfo):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default='')


class WebsiteType(models.Model):
    long_name = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.long_name


class Alias(BaseModel):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.UUIDField()
    parent_fk = GenericForeignKey('content_type', 'object_id')

    model_name = models.CharField(max_length=64, blank=False)
    short_name = models.CharField(max_length=512, blank=False)
    source = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        """converts model_name field 'PartnerOrg' into a content type to support the
        GenericForeignKey relationship, which would otherwise require an arbitrary
        primary key to be passed in the post request"""
        self.content_type = ContentType.objects.get(app_label="data_models", model=self.model_name.lower())
        return super(Alias, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural='Aliases'


class PartnerOrg(LimitedInfo):
    aliases = GenericRelation(Alias)

    website = models.CharField(max_length=256, blank=True, default='')


class GcmdProject(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, blank=True, default='')
    bucket = models.CharField(max_length=256)
    gcmd_uuid = models.UUIDField()


class GcmdInstrument(BaseModel):
    short_name = models.CharField(max_length=256, blank=True, unique=False)
    long_name = models.CharField(max_length=512, blank=True, default='')
    instrument_category = models.CharField(max_length=256, blank=True, default='') # these make more sense without 'instrument'
    instrument_class = models.CharField(max_length=256, blank=True, default='') # however class and type are default variables
    instrument_type = models.CharField(max_length=256, blank=True, default='') # so instrument was added to all 4 for consistency
    instrument_subtype = models.CharField(max_length=256, blank=True, default='')
    gcmd_uuid = models.UUIDField()

    def __str__(self):
        return self.short_name or self.long_name or self.instrument_subtype or self.instrument_type or self.instrument_class or self.instrument_category


class GcmdPlatform(BaseModel):
    short_name = models.CharField(max_length=256, blank=True, default='')
    long_name = models.CharField(max_length=512, blank=True, default='')
    category = models.CharField(max_length=256)
    series_entry = models.CharField(max_length=256, blank=True, default='')
    description = models.TextField(blank=True, default='')
    gcmd_uuid = models.UUIDField()


class GcmdPhenomena(BaseModel):
    category = models.CharField(max_length=256)
    topic = models.CharField(max_length=256, blank=True, default='')
    term = models.CharField(max_length=256, blank=True, default='')
    variable_1 = models.CharField(max_length=256, blank=True, default='')
    variable_2 = models.CharField(max_length=256, blank=True, default='')
    variable_3 = models.CharField(max_length=256, blank=True, default='')
    gcmd_uuid = models.UUIDField()

    def __str__(self):
        return self.variable_3 or self.variable_2 or self.variable_1 or self.term or self.topic or self.category


class Website(models.Model):
    url = models.TextField()
    title = models.TextField()
    description = models.TextField(default='', blank=True)
    website_type = models.ManyToManyField(WebsiteType, related_name='websites')

    def __str__(self):
        return self.title


###############
# Core Models #
###############


class DataModel(LimitedInfo):
    class Meta:
        abstract = True

    @staticmethod
    def search_fields():
        return ['short_name', 'long_name']

    @classmethod
    def search(cls, params):
        search_type = params.pop('search_type', 'plain')
        search = params.pop('search', None)
        search_fields_param = params.pop('search_fields', None)
        if search_fields_param:
            search_fields = search_fields_param.split(',')
        else:
            search_fields = cls.search_fields()

        queryset = cls.objects.all()

        if search:
            vector = SearchVector(*search_fields)

            queryset = queryset.annotate(
                search=vector
            ).filter(
                search=SearchQuery(search, search_type=search_type)
            )

        return queryset.filter(**params)


class Campaign(DataModel):
    logo = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    aliases = GenericRelation(Alias)

    description_short = models.TextField(default='', blank=True)
    description_long = models.TextField(default='', blank=True)
    focus_phenomena = models.CharField(max_length=1024)
    region_description = models.TextField()
    spatial_bounds = geomodels.PolygonField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    funding_agency = models.CharField(max_length=256)
    funding_program = models.CharField(max_length=256, default='', blank=True)
    funding_program_lead = models.CharField(max_length=256, default='', blank=True)
    lead_investigator = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256, default='', blank=True)
    number_collection_periods = models.PositiveIntegerField()
    campaign_doi = models.CharField(max_length=1024, default='', blank=True)
    number_data_products = models.PositiveIntegerField(null=True, blank=True)
    data_volume = models.CharField(max_length=256, null=True, blank=True)

    ongoing = models.BooleanField()
    nasa_led = models.BooleanField()
    nasa_missions = models.TextField(default='', blank=True)

    focus_areas = models.ManyToManyField(FocusArea, related_name='campaigns')
    seasons = models.ManyToManyField(Season, related_name='campaigns')
    repositories = models.ManyToManyField(Repository, related_name='campaigns')
    platform_types = models.ManyToManyField(PlatformType, related_name='campaigns')
    partner_orgs = models.ManyToManyField(PartnerOrg, related_name='campaigns', default='', blank=True)
    gcmd_projects = models.ManyToManyField(GcmdProject, related_name='campaigns', default='', blank=True)
    geophysical_concepts = models.ManyToManyField(GeophysicalConcept, related_name='campaigns')
    websites = models.ManyToManyField(Website, related_name='campaigns')

    @property
    def significant_events(self):
        return list(set([
            event.uuid
                for dep in self.deployments.all()
                    for event in dep.significant_events.all()
        ]))

    @property
    def iops(self):
        return list(set([
            iop.uuid
                for dep in self.deployments.all()
                    for iop in dep.iops.all()
        ]))

    @property
    def number_deployments(self):
        return self.deployments.count()

    @property
    def instruments(self):
        return list(set([
            inst.uuid
                for dep in self.deployments.all()
                    for collection_period in dep.collection_periods.all()
                        for inst in collection_period.instruments.all()
        ]))

    @property
    def platforms(self):
        return list(set([
            collection_period.platform.uuid
                for dep in self.deployments.all()
                    for collection_period in dep.collection_periods.all()
        ]))

    @staticmethod
    def search_fields():
        return [
            'short_name',
            'long_name',
            'description_short',
            'description_long',
            'focus_phenomena',
        ]


class Platform(DataModel):

    platform_type = models.ForeignKey(PlatformType, on_delete=models.SET_NULL, related_name='platforms', null=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    aliases = GenericRelation(Alias)

    description = models.TextField()
    online_information = models.CharField(max_length=512, default='', blank=True)
    stationary = models.BooleanField()

    gcmd_platforms = models.ManyToManyField(GcmdPlatform, related_name='platforms', default='', blank=True)

    @property
    def campaigns(self):
        return list(set(collection_period.deployment.campaign.uuid for collection_period in self.collection_periods.all()))

    @property
    def instruments(self):
        return list(set(
            inst.uuid
                for collection_period in self.collection_periods.all()
                    for inst in collection_period.instruments.all()
        ))

    @staticmethod
    def search_fields():
        return [
            'short_name',
            'long_name',
            'description',
        ]


class Instrument(DataModel):
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.SET_NULL, null=True, blank=True, related_name='instruments')
    measurement_style = models.ForeignKey(MeasurementStyle, on_delete=models.SET_NULL, null=True, blank=True, related_name='instruments')
    aliases = GenericRelation(Alias)

    description = models.TextField()
    lead_investigator = models.CharField(max_length=256, default='', blank=True)
    technical_contact = models.CharField(max_length=256)
    facility = models.CharField(max_length=256, default='', blank=True)
    funding_source = models.CharField(max_length=1024, default='', blank=True)
    spatial_resolution = models.CharField(max_length=256)
    temporal_resolution = models.CharField(max_length=256)
    radiometric_frequency = models.CharField(max_length=256)
    calibration_information = models.CharField(max_length=1024, default='', blank=True)
    instrument_manufacturer = models.CharField(max_length=512, default='', blank=True)
    overview_publication = models.CharField(max_length=2048, default='', blank=True)
    online_information = models.CharField(max_length=2048, default='', blank=True)
    instrument_doi = models.CharField(max_length=1024, default='', blank=True)
    arbitrary_characteristics = models.JSONField(default=None, blank=True, null=True)

    gcmd_instruments = models.ManyToManyField(GcmdInstrument, related_name='instruments', default='', blank=True)
    gcmd_phenomenas = models.ManyToManyField(GcmdPhenomena, related_name='instruments')
    measurement_regions = models.ManyToManyField(MeasurementRegion, related_name='instruments')
    repositories = models.ManyToManyField(Repository, related_name='instruments', default='', blank=True)

    @property
    def campaigns(self):
        return list(set(collection_period.deployment.campaign.uuid for collection_period in self.collection_periods.all()))

    @property
    def platforms(self):
        return list(set(collection_period.platform.uuid for collection_period in self.collection_periods.all()))


class Deployment(DataModel):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='deployments')
    aliases = GenericRelation(Alias)

    study_region_map = models.TextField(default='', blank=True)
    ground_sites_map = models.TextField(default='', blank=True)
    flight_tracks = models.TextField(default='', blank=True)

    start_date = models.DateField()
    end_date = models.DateField()
    number_collection_periods = models.PositiveIntegerField(null=True, blank=True)

    geographical_regions = models.ManyToManyField(
        GeographicalRegion,
        related_name='deployments',
        default='', blank=True
        )

    def __str__(self):
        return self.short_name

    @property
    def platforms(self):
        return list(set(collection_period.platform.uuid for collection_period in self.collection_periods.all()))


class IopSe(BaseModel):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='iops')

    short_name = models.CharField(max_length=256)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    region_description = models.TextField()
    published_list = models.CharField(max_length=1024, default='', blank=True)
    reports = models.CharField(max_length=1024, default='', blank=True)
    reference_file = models.CharField(max_length=1024, default='', blank=True)

    class Meta:
        abstract = True


class IOP(IopSe):
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='iops')


class SignificantEvent(IopSe):
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='significant_events')
    iop = models.ForeignKey(IOP, on_delete=models.CASCADE, related_name='significant_events', null=True)


class CollectionPeriod(BaseModel):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='collection_periods')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='collection_periods')
    home_base = models.ForeignKey(HomeBase, on_delete=models.CASCADE, related_name='collection_periods', null=True)

    asp_long_name = models.CharField(max_length=512, default='', blank=True)
    platform_identifier = models.CharField(max_length=128, default='', blank=True)
    campaign_deployment_base = models.CharField(max_length=256, default='', blank=True)
    platform_owner = models.CharField(max_length=256, default='', blank=True)
    platform_technical_contact = models.CharField(max_length=256, default='', blank=True)
    instrument_information_source = models.CharField(max_length=1024, default='', blank=True)
    notes_internal = models.TextField(default='', blank=True)
    notes_public = models.TextField(default='', blank=True)

    num_ventures = models.PositiveIntegerField(null=True, blank=True)
    auto_generated = models.BooleanField()

    instruments = models.ManyToManyField(Instrument, related_name='collection_periods')

    def __str__(self):
        # TODO: maybe come up with something better? dep_plat_uuid?
        return str(self.uuid)


class DOI(BaseModel):
    concept_id = models.CharField(max_length=512, unique=True)
    doi = models.CharField(max_length=512, blank=True, default='')
    long_name = models.TextField(blank=True, default='')

    cmr_short_name = models.CharField(max_length=512, blank=True, default='')
    cmr_entry_title = models.TextField(blank=True, default='')
    cmr_projects = models.JSONField(default=None, blank=True, null=True)
    cmr_dates = models.JSONField(default=None, blank=True, null=True)
    cmr_plats_and_insts = models.JSONField(default=None, blank=True, null=True)

    date_queried = models.DateTimeField()

    campaigns = models.ManyToManyField(Campaign, related_name='dois')
    instruments = models.ManyToManyField(Instrument, blank=True, related_name='dois')
    platforms = models.ManyToManyField(Platform, blank=True, related_name='dois')
    collection_periods = models.ManyToManyField(CollectionPeriod, blank=True, related_name='dois')

    def __str__(self):
        return self.cmr_entry_title or self.cmr_short_name or self.doi or self.concept_id

    class Meta:
        verbose_name = "DOI"
