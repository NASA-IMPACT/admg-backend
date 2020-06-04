
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as geomodels
from django.contrib.postgres.fields import JSONField
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


class LimitedInfo(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, blank=True, default='')
    notes_public = models.CharField(max_length=16384, blank=True, default='')

    class Meta:
        abstract = True


class PlatformType(LimitedInfo):
    parent = models.ForeignKey('PlatformType', on_delete=models.CASCADE, related_name='sub_types', null=True, blank=True)
    
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=256, blank=True, default='')


class NasaMission(LimitedInfo):
    pass

class InstrumentType(LimitedInfo):
    parent = models.ForeignKey('InstrumentType', on_delete=models.CASCADE, related_name='sub_types', null=True, blank=True)
    
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=256, blank=True, default='')
    

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
    example = models.CharField(max_length=256, blank=True, default='')


class GeographicalRegion(LimitedInfo):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=256, blank=True, default='')


class GeophysicalConcept(LimitedInfo):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=256, blank=True, default='')


class PartnerOrg(LimitedInfo):
    website = models.CharField(max_length=256)


class Alias(BaseModel):
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    parent_fk = GenericForeignKey('content_type', 'object_id')

    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, blank=True, default='')
    source = models.CharField(max_length=2048, blank=True, default='')

    class Meta:
        verbose_name_plural='Aliases'



class GcmdProject(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, blank=True, default='')
    bucket = models.CharField(max_length=256)
    gcmd_uuid = models.UUIDField()


class GcmdInstrument(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, blank=True, default='')
    instrument_category = models.CharField(max_length=256, blank=True, default='') # these make more sense without 'instrument'
    instrument_class = models.CharField(max_length=256, blank=True, default='') # however class and type are default variables
    instrument_type = models.CharField(max_length=256, blank=True, default='') # so instrument was added to all 4 for consistency
    instrument_subtype = models.CharField(max_length=256, blank=True, default='')
    gcmd_uuid = models.UUIDField()


class GcmdPlatform(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, blank=True, default='')
    category = models.CharField(max_length=256)
    series_entry = models.CharField(max_length=256)
    description = models.CharField(max_length=16384)
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
        # TODO: is there a cleaner way to do this?
        # display the most specific category which has a value
        if self.variable_3:
            return self.variable_3
        elif self.variable_2:
            return self.variable_2
        elif self.variable_1:
            return self.variable_1
        elif self.term:
            return self.term
        elif self.topic:
            return self.topic
        else:
            return self.category


###############
# Core Models #
###############


class DataModel(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512)
    notes_internal = models.CharField(max_length=16384, default='', blank=True)
    notes_public = models.CharField(max_length=16384, default='', blank=True)

    class Meta:
        abstract = True


class Campaign(DataModel):
    description_short = models.CharField(max_length=16384, default='', blank=True)
    description_long = models.CharField(max_length=16384, default='', blank=True)
    focus_phenomena = models.CharField(max_length=1024)
    region_description = models.CharField(max_length=16384)
    spatial_bounds = geomodels.PolygonField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    funding_agency = models.CharField(max_length=256)
    funding_program = models.CharField(max_length=256, default='', blank=True)
    funding_program_lead = models.CharField(max_length=256, default='', blank=True)
    lead_investigator = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256, default='', blank=True)
    # nonaircraft_platforms = models.CharField(max_length=1024, default='', blank=True)
    # nonaircraft_instruments = models.CharField(max_length=1024, default='', blank=True)
    number_collection_periods = models.PositiveIntegerField()
    doi = models.CharField(max_length=1024, default='', blank=True)
    number_data_products = models.PositiveIntegerField(null=True, blank=True)
    data_volume = models.CharField(max_length=256, null=True, blank=True)

    repository_website = models.CharField(max_length=512, default='', blank=True) # repository homepage
    project_website = models.CharField(max_length=512, default='', blank=True) # dedicated homepage
    tertiary_website = models.CharField(max_length=512, default='', blank=True) 
    publication_links = models.CharField(max_length=2048, default='', blank=True)
    other_resources = models.CharField(max_length=2048, default='', blank=True) # other urls

    ongoing = models.BooleanField()
    nasa_led = models.BooleanField()

    nasa_missions = models.ManyToManyField(NasaMission, related_name='campaigns', default='', blank=True)
    focus_areas = models.ManyToManyField(FocusArea, related_name='campaigns')
    seasons = models.ManyToManyField(Season, related_name='campaigns')
    repositories = models.ManyToManyField(Repository, related_name='campaigns')
    platform_types = models.ManyToManyField(PlatformType, related_name='campaigns')
    partner_orgs = models.ManyToManyField(PartnerOrg, related_name='campaigns', default='', blank=True)
    gcmd_phenomenas = models.ManyToManyField(GcmdPhenomena, related_name='campaigns')
    gcmd_projects = models.ManyToManyField(GcmdProject, related_name='campaigns', default='', blank=True)
    geophysical_concepts = models.ManyToManyField(GeophysicalConcept, related_name='campaigns')

    @property
    def significant_events(self):
        events = [
            event.uuid
                for dep in self.deployments.all()
                    for event in dep.significant_events.all()
        ]
        events = list(set(events))
        return events

    @property
    def iops(self):
        iops = [
            iop.uuid
                for dep in self.deployments.all()
                    for iop in dep.iops.all()
        ]
        iops = list(set(iops))
        return iops

    @property
    def number_deployments(self):
        return self.deployments.count()

    @property
    def instruments(self):
        instruments = [
            inst.uuid
                for dep in self.deployments.all()
                    for collection_period in dep.collection_periods.all()
                        for inst in collection_period.instruments.all()  
        ]
        instruments = list(set(instruments))
        return instruments

    @property
    def platforms(self):
        platforms = [
            collection_period.platform.uuid
                for dep in self.deployments.all()
                    for collection_period in dep.collection_periods.all()
        ]
        platforms = list(set(platforms))
        return platforms


class Platform(DataModel):

    platform_type = models.ForeignKey(PlatformType, on_delete=models.SET_NULL, related_name='platforms', null=True)

    description = models.CharField(max_length=16384)
    online_information = models.CharField(max_length=512, default='', blank=True)
    stationary = models.BooleanField()

    gcmd_platforms = models.ManyToManyField(GcmdPlatform, related_name='platforms', default='', blank=True)

    @property
    def campaigns(self):
        campaigns = list(set(collection_period.deployment.campaign.uuid for collection_period in self.collection_periods.all()))
        return campaigns

    @property
    def instruments(self):
        instruments = [
            inst.uuid
                for collection_period in self.collection_periods.all()
                    for inst in collection_period.instruments.all()
        ]
        instruments = list(set(instruments))
        return instruments


class Instrument(DataModel):
    description = models.CharField(max_length=16384)
    lead_investigator = models.CharField(max_length=256, default='', blank=True)
    technical_contact = models.CharField(max_length=256)
    facility = models.CharField(max_length=256, default='', blank=True)
    funding_source = models.CharField(max_length=256, default='', blank=True)
    spatial_resolution = models.CharField(max_length=256)
    temporal_resolution = models.CharField(max_length=256)
    radiometric_frequency = models.CharField(max_length=256)
    calibration_information = models.CharField(max_length=1024, default='', blank=True)
    instrument_manufacturer = models.CharField(max_length=512, default='', blank=True)
    online_information = models.CharField(max_length=2048, default='', blank=True)
    instrument_doi = models.CharField(max_length=1024, default='', blank=True)

    gcmd_instruments = models.ManyToManyField(GcmdInstrument, related_name='instruments', default='', blank=True)
    instrument_types = models.ManyToManyField(InstrumentType, related_name='instruments')
    gcmd_phenomenas = models.ManyToManyField(GcmdPhenomena, related_name='instruments')
    measurement_regions = models.ManyToManyField(MeasurementRegion, related_name='instruments')
    repositories = models.ManyToManyField(Repository, related_name='instruments', default='', blank=True)
    geophysical_concepts = models.ManyToManyField(GeophysicalConcept, related_name='instruments')

    @property
    def campaigns(self):
        return list(set(collection_period.deployment.campaign.uuid for collection_period in self.collection_periods.all()))

    @property
    def platforms(self):
        return list(set(collection_period.platform.uuid for collection_period in self.collection_periods.all()))

 
class Deployment(DataModel):

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='deployments')

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
    description = models.CharField(max_length=16384)
    region_description = models.CharField(max_length=16384)
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

    asp_long_name = models.CharField(max_length=512, default='', blank=True)
    platform_identifier = models.CharField(max_length=128, default='', blank=True)
    home_base = models.CharField(max_length=256, default='', blank=True)
    campaign_deployment_base = models.CharField(max_length=256, default='', blank=True)
    platform_owner = models.CharField(max_length=256, default='', blank=True)
    platform_technical_contact = models.CharField(max_length=256, default='', blank=True)
    instrument_information_source = models.CharField(max_length=1024, default='', blank=True)
    notes_internal = models.CharField(max_length=16384, default='', blank=True)
    notes_public = models.CharField(max_length=16384, default='', blank=True)

    num_ventures = models.PositiveIntegerField(null=True, blank=True)
    auto_generated = models.BooleanField()

    instruments = models.ManyToManyField(Instrument, related_name='collection_periods')

    def __str__(self):
        # TODO: maybe come up with something better? dep_plat_uuid?
        return str(self.uuid)


class Reccomendation(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    queried_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=256, blank=False, unique=True)
    metadata = JSONField()

