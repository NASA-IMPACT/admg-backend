import uuid

from django.contrib.gis.db import models as geomodels
from django.db import models


class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        abstract = True 


##################
# Limited Fields #
##################


class LimitedInfo(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, blank=True, default = '')
    notes_public = models.CharField(max_length=2048, blank=True, default = '')

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True


class NasaMission(LimitedInfo):
    pass

class PlatformType(LimitedInfo):
    example = models.CharField(max_length=256)


class AircraftType(LimitedInfo):
    gcmd_translation = models.UUIDField()
    

class InstrumentType(LimitedInfo):
    gcmd_translation = models.UUIDField()
    

class HomeBase(LimitedInfo):
    gcmd_translation = models.UUIDField()
    

class FocusArea(LimitedInfo):
    pass


class Season(LimitedInfo):
    pass


class Repository(LimitedInfo):
    gcmd_translation = models.UUIDField()
    

class MeasurementRegion(LimitedInfo):
    pass


class MeasurementKeyword(LimitedInfo):
    pass


class GeographicalRegion(LimitedInfo):
    pass


class GeophysicalConcepts(LimitedInfo):
    pass


class GcmdProject(LimitedInfo):
    bucket = models.CharField(max_length=256)
    gcmd_uuid = models.UUIDField()


class GcmdInstrument(LimitedInfo):
    instrument_category = models.CharField(max_length=256)
    instrument_class = models.CharField(max_length=256)
    instrument_type = models.CharField(max_length=256)
    instrument_subtype = models.CharField(max_length=256)
    gcmd_uuid = models.UUIDField()


class GcmdPlatform(LimitedInfo):
    category = models.CharField(max_length=256)
    series_entry = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    gcmd_version = models.CharField(max_length=256)
    source_link = models.CharField(max_length=256)
    gcmd_uuid = models.UUIDField()


class PartnerOrg(LimitedInfo):
    website = models.CharField(max_length=256)


class GcmdPhenomena(BaseModel):
    category = models.CharField(max_length=256)
    topic = models.CharField(max_length=256)
    term = models.CharField(max_length=256)
    variable_1 = models.CharField(max_length=256)
    variable_2 = models.CharField(max_length=256)
    variable_3 = models.CharField(max_length=256)
    gcmd_uuid = models.UUIDField()


###############
# Core Models #
###############


class DataModel(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512)
    notes_internal = models.CharField(max_length=2048, default = '', blank=True)
    notes_public = models.CharField(max_length=2048, default = '', blank=True)

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True


class Campaign(DataModel):
    description_short = models.CharField(max_length=2048, default = '', blank=True)
    description_long = models.CharField(max_length=2048, default = '', blank=True)
    focus_phenomena = models.CharField(max_length=1024)
    region_description = models.CharField(max_length=1024)
    spatial_bounds = geomodels.PolygonField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    funding_agency = models.CharField(max_length=256)
    funding_program = models.CharField(max_length=256, default='', blank=True)
    funding_program_lead = models.CharField(max_length=256, default='', blank=True)
    lead_investigator = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256, default='', blank=True)
    nonaircraft_platforms = models.CharField(max_length=1024, default='', blank=True)
    nonaircraft_instruments = models.CharField(max_length=1024, default='', blank=True)
    number_flights = models.PositiveIntegerField()
    doi = models.CharField(max_length=1024, default='', blank=True)
    number_data_products = models.PositiveIntegerField(null=True, blank=True)
    data_volume = models.CharField(max_length=256, null=True, blank=True)

    repository_website = models.CharField(max_length=512, default='', blank=True) # repository homepage
    project_website = models.CharField(max_length=512, default='', blank=True) # dedicated homepage
    publication_links = models.CharField(max_length=2048, default='', blank=True)
    other_resources = models.CharField(max_length=2048, default='', blank=True) # other urls

    is_ongoing = models.BooleanField()
    nasa_led = models.BooleanField()

    nasa_mission = models.CharField(PartnerOrg, related_name='campaigns', default='', blank=True)
    focus_areas = models.ManyToManyField(FocusArea, related_name='campaigns')
    seasons = models.ManyToManyField(Season, related_name='campaigns')
    repositories = models.ManyToManyField(Repository, related_name='campaigns')
    platform_types = models.ManyToManyField(PlatformType, related_name='campaigns')
    partner_orgs = models.ManyToManyField(PartnerOrg, related_name='campaigns', default='', blank=True)
    gcmd_phenomenas = models.ManyToManyField(GcmdPhenomena, related_name='campaigns')
    gcmd_project = models.ManyToManyField(GcmdProject, related_name='campaigns', default='', blank=True)

    def __str__(self):
        return self.short_name


    @property
    def significant_events(self):
        # TODO
        # significant_events = models.CharField(max_length=512)
        pass

    @property
    def number_deployments(self):
        return self.deployments.count()

    @property
    def instruments(self):
        instruments =  [
            inst 
                for dep in self.deployments.all()
                    for flight in dep.flights.all()
                        for inst in flight.instruments.all()  
        ]
        instruments = list(set(instruments))
        return instruments

    @property
    def platforms(self):
        platforms =  [
            flight.platform 
                for dep in self.deployments.all()
                    for flight in dep.flights.all()
        ]
        platforms = list(set(platforms))
        return platforms


class Platform(DataModel):

    platform_type = models.ForeignKey(
        AircraftType, on_delete=models.SET_NULL, related_name='platforms', null=True)

    platform_model = models.CharField(max_length=256)  # TODO: should we even be tracking this?
    desciption = models.CharField(max_length=256)
    online_information = models.CharField(max_length=512, default='', blank=True)
    image_url = models.CharField(max_length=256)

    gcmd_platform = models.ManyToManyField(GcmdPlatform, related_name='platforms', default='', blank=True)  # TODO: double check

    @property
    def campaigns(self):
        campaigns = list(set(flight.deployment.campaign for flight in self.flights.all()))
        return campaigns

    @property
    def instruments(self):
        instruments = [
            inst
                for flight in self.flights.all()
                    for inst in flight.instruments.all()
        ]
        [[instruments.append(inst) for inst in flight.instruments.all()] for flight in self.flights.all()]
        instruments = list(set(instruments))
        return instruments

    def __str__(self):
        return self.short_name


class Instrument(DataModel):
    description = models.CharField(max_length=256)
    lead_investigator = models.CharField(max_length=256, default='', blank=True)
    technical_contact = models.CharField(max_length=256)
    facility = models.CharField(max_length=256, default='', blank=True)
    funding_source = models.CharField(max_length=256, default='', blank=True)
    spatial_resolution = models.CharField(max_length=256)
    temporal_resolution = models.CharField(max_length=256)
    radiometric_frequency = models.CharField(max_length=256)
    calibration_information = models.CharField(max_length=1024, default='', blank=True)
    deployment_date = models.DateField(null=True, blank=True)
    dates_of_operation = models.CharField(max_length=512, default='', blank=True)
    data_products_per_level = models.CharField(max_length=256, default='', blank=True)
    instrument_manufacturer = models.CharField(max_length=512, default='', blank=True)
    online_information = models.CharField(max_length=2048, default='', blank=True)
    instrument_doi = models.CharField(max_length=1024, default='', blank=True)

    gcmd_instruments = models.ManyToManyField(GcmdInstrument, related_name='instruments', default='', blank=True)
    instrument_types = models.ManyToManyField(InstrumentType, related_name='instruments')
    measurement_keywords = models.ManyToManyField(MeasurementKeyword, related_name='instruments')
    measurement_regions = models.ManyToManyField(MeasurementRegion, related_name='instruments')
    repositories = models.ManyToManyField(Repository, related_name='instruments', default='', blank=True)
    geophysical_concepts = models.ManyToManyField(GeophysicalConcepts, related_name='instruments')

    @property
    def campaigns(self):
        return list(set(flight.deployment.campaign for flight in self.flights.all()))

    @property
    def platforms(self):
        return list(set(flight.deployment.platform for flight in self.flights.all()))

    def __str__(self):
        return self.short_name

The 
class Deployment(DataModel):

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='deployments')

    start_date = models.DateField()
    end_date = models.DateField()
    number_flights = models.PositiveIntegerField(null=True, blank=True)

    geographical_regions = models.ManyToManyField(
        GeographicalRegion, 
        related_name='deployments', 
        default='', blank=True
        )

    def __str__(self):
        return self.long_name


class IopSe(DataModel):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='iops')
    
    short_name = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.CharField(max_length=1024)
    region_description = models.CharField(max_length=512)
    published_list = models.CharField(max_length=1024, default='', blank=True)
    reports = models.CharField(max_length=1024, default='', blank=True)
    reference_file = models.CharField(max_length=1024, default='', blank=True)

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True 


class IOP(IopSe):
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='iops')
    

class SignificantEvent(IopSe):
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='significant_events')
    iop = models.ForeignKey(IOP, on_delete=models.CASCADE, related_name='significant_events', null=True) 
    

class Flight(BaseModel):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='flights')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='flights')

    asp_long_name = models.CharField(max_length=512, default='', blank=True)
    tail_number = models.CharField(max_length=128, default='', blank=True)
    home_base = models.CharField(max_length=256, default='', blank=True)
    campaign_deployment_base = models.CharField(max_length=256, default='', blank=True)
    platform_owner = models.CharField(max_length=256, default='', blank=True)
    platform_technical_contact = models.CharField(max_length=256, default='', blank=True)
    instrument_information_source = models.CharField(max_length=1024, default='', blank=True)
    notes_internal = models.CharField(max_length=2048, default='', blank=True)
    notes_public = models.CharField(max_length=2048, default='', blank=True)

    instruments = models.ManyToManyField(Instrument, related_name='flights')
