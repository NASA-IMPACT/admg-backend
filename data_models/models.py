from django.db import models
from django.contrib.gis.db import models as geomodels

##################
# Limited Fields #
##################


class LimitedInfo(models.Model):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    gcmd_translation = models.CharField(max_length=256)

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True


class PlatformType(LimitedInfo):
    pass


class AircraftType(LimitedInfo):
    pass


class InstrumentType(LimitedInfo):
    pass


class HomeBase(LimitedInfo):
    pass


class FocusArea(LimitedInfo):
    pass


class Season(LimitedInfo):
    pass


class Repository(LimitedInfo):
    pass


class MeasurementRegion(LimitedInfo):
    pass


class MeasurementKeyword(LimitedInfo):
    pass


class GeographicalRegion(LimitedInfo):
    pass


class GeophysicalConcepts(LimitedInfo):
    pass


class GCMD(models.Model):
    # TODO: GCMD can be handled differently
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    uuid = models.UUIDField()

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True


class GcmdPhenomena(GCMD):
    pass


class GcmdProject(GCMD):
    pass


class GcmdPlatform(GCMD):
    pass


class GcmdInstrument(GCMD):
    pass


# doesn't inherit
class PartnerOrg(models.Model):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    website = models.CharField(max_length=256)
    notes_public = models.CharField(max_length=2048)

    def __str__(self):
        return self.short_name


class EventType(models.Model):
    short_name = models.CharField(max_length=128, blank=Flase, unique=True)

###############
# Core Models #
###############

class Campaign(models.Model):
    short_name = models.CharField(max_length=128, blank=False, unique=True)
    long_name = models.CharField(max_length=512)
    description_edited = models.CharField(max_length=2048)
    description = models.CharField(max_length=2048)
    focus_phenomena = models.CharField(max_length=512)
    region_description = models.CharField(max_length=512)
    spatial_bounds = geomodels.PolygonField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    funding_agency = models.CharField(max_length=256)
    funding_program = models.CharField(max_length=256)
    program_lead = models.CharField(max_length=256)
    project_lead = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256)
    nonaircraft_platforms = models.CharField(max_length=512)
    nonaircraft_instruments = models.CharField(max_length=512)
    number_flights = models.PositiveIntegerField()
    doi = models.CharField(max_length=1024)
    publication_links = models.CharField(max_length=1024)
    nasa_mission = models.CharField(max_length=512)
    number_data_products = models.PositiveIntegerField()
    data_volume = models.CharField(max_length=256)
    repository_link = models.CharField(max_length=512)
    other_resources = models.CharField(max_length=2048)
    is_ongoing = models.BooleanField()
    notes_public = models.CharField(max_length=2048)
    notes_internal = models.CharField(max_length=2048)

    focus_areas = models.ManyToManyField(FocusArea, related_name='campaigns')
    seasons = models.ManyToManyField(Season, related_name='campaigns')
    repositories = models.ManyToManyField(Repository, related_name='campaigns')
    platform_types = models.ManyToManyField(PlatformType, related_name='campaigns')
    partner_orgs = models.ManyToManyField(PartnerOrg, related_name='campaigns')
    gcmd_phenomenas = models.ManyToManyField(GcmdPhenomena, related_name='campaigns')
    gcmd_project = models.ManyToManyField(GcmdProject, related_name='campaigns')

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
        instruments = []
        [[[instruments.append(inst) for inst in flight.instruments.all()]
          for flight in dep.flights.all()] for dep in self.deployments.all()]
        instruments = list(set(instruments))
        return instruments

    @property
    def platforms(self):
        platforms = []
        [[platforms.append(flight.platform) for flight in dep.flights.all()]
         for dep in self.deployments.all()]
        platforms = list(set(platforms))
        return platforms


class Platform(models.Model):

    # home_base = models.ForeignKey(HomeBase, on_delete=models.SET_NULL,
    #                               related_name='platforms', null=True)
    platform_type = models.ForeignKey(
        AircraftType, on_delete=models.SET_NULL, related_name='platforms', null=True)

    short_name = models.CharField(max_length=128, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    platform_model = models.CharField(max_length=256)  # TODO: should we even be tracking this?
    desciption = models.CharField(max_length=256)
    online_information = models.CharField(max_length=512)
    notes_internal = models.CharField(max_length=2048)
    notes_public = models.CharField(max_length=2048)
    image_url = models.CharField(max_length=256)

    gcmd_platform = models.ManyToManyField(GcmdPlatform, related_name='platforms')  # TODO: double check

    @property
    def campaigns(self):
        campaigns = list(set([flight.deployment.campaign for flight in self.flights.all()]))
        return campaigns

    @property
    def instruments(self):
        instruments = []
        [[instruments.append(inst) for inst in flight.instruments.all()] for flight in self.flights.all()]
        instruments = list(set(instruments))
        return instruments

    def __str__(self):
        return self.short_name


class Instrument(models.Model):
    short_name = models.CharField(max_length=128, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    lead_investigator = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256)
    facility = models.CharField(max_length=256)
    funding_source = models.CharField(max_length=256)
    spatial_resolution = models.CharField(max_length=256)
    temporal_resolution = models.CharField(max_length=256)
    radiometric_frequency = models.CharField(max_length=256)
    calibration_information = models.CharField(max_length=1024)
    deployment_date = models.DateField()
    dates_of_operation = models.CharField(max_length=512)
    data_products_per_level = models.CharField(max_length=256)
    instrument_manufacturer = models.CharField(max_length=512)
    online_information = models.CharField(max_length=2048)
    instrument_doi = models.CharField(max_length=1024)
    notes_internal = models.CharField(max_length=2048)
    notes_public = models.CharField(max_length=2048)

    gcmd_instruments = models.ManyToManyField(GcmdInstrument, related_name='instruments')
    instrument_types = models.ManyToManyField(InstrumentType, related_name='instruments')
    measurement_keywords = models.ManyToManyField(MeasurementKeyword, related_name='instruments')
    measurement_regions = models.ManyToManyField(MeasurementRegion, related_name='instruments')
    repositories = models.ManyToManyField(Repository, related_name='instruments')
    geophysical_concepts = models.ManyToManyField(GeophysicalConcepts, related_name='instruments')

    @property
    def campaigns(self):
        return list(set([flight.deployment.campaign for flight in self.flights.all()]))

    @property
    def platforms(self):
        return list(set([flight.deployment.platform for flight in self.flights.all()]))

    def __str__(self):
        return self.short_name


class Deployment(models.Model):

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='deployments')

    short_name = models.CharField(max_length=128)  # this is the 'deployment_id'
    long_name = models.CharField(max_length=512)
    start_date = models.DateField()
    end_date = models.DateField()
    number_flights = models.PositiveIntegerField()
    notes_internal = models.CharField(max_length=2048)
    notes_public = models.CharField(max_length=2048)

    geographical_regions = models.ManyToManyField(GeographicalRegion, related_name='deployments')

    def __str__(self):
        return self.long_name


class IopSe(models.Model):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='iops')
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, related_name='iops') 
    
    short_name = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.CharField(max_length=1024)
    region_description = models.CharField(max_length=512)
    published_list = models.CharField(max_length=1024)
    reports = models.CharField(max_length=1024)
    reference_file = models.CharField(max_length=1024)

    def __str__(self):
        return self.short_name


class Flight(models.Model):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='flights')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='flights')

    asp_long_name = models.CharField(max_length=512)
    tail_number = models.CharField(max_length=128)
    home_base = models.CharField(max_length=256)
    campaign_deployment_base = models.CharField(max_length=256)
    platform_owner = models.CharField(max_length=256)
    platform_technical_contact = models.CharField(max_length=256)
    instrument_information_source = models.CharField(max_length=1024)
    notes_internal = models.CharField(max_length=2048)
    notes_public = models.CharField(max_length=2048)

    instruments = models.ManyToManyField(Instrument, related_name='flights')
