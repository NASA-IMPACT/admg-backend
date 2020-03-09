from django.db import models


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


class GCMD(models.Model):
    # TODO: Put more work into this later
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


###############
# Core Models #
###############

class Campaign(models.Model):
    short_name = models.CharField(max_length=128, blank=False, unique=True)
    long_name = models.CharField(max_length=512)
    description_edited = models.CharField(max_length=2048)
    description = models.CharField(max_length=2048)
    scientific_objective_focus_phenomena = models.CharField(max_length=512)
    region_description = models.CharField(max_length=512)
    # spatial_bounds = models.Lat/Lon # TODO: geostuff
    start_date = models.DateField()
    end_date = models.DateField()
    significant_events = models.CharField(max_length=512)
    funding_program = models.CharField(max_length=256)
    responsible_funding_program_lead = models.CharField(max_length=256)
    responsible_or_project_lead = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256)
    non_aircraft_platforms = models.CharField(max_length=512)
    non_airborne_instruments = models.CharField(max_length=512)
    total_flights = models.PositiveIntegerField()
    doi = models.CharField(max_length=1024)
    publication = models.CharField(max_length=1024)
    supported_nasa_mission = models.CharField(max_length=512)
    number_of_published_data_products = models.PositiveIntegerField()
    data_total_volume = models.CharField(max_length=256)
    project_data_repository_website = models.CharField(max_length=512)
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
    gcmd_project = models.ManyToManyField(GcmdProject, related_name='campaigns')  # TODO: double check

    def __str__(self):
        return self.short_name

    @property
    def number_deployments(self):
        # TODO: add function that counts number of deplyments from the associated table
        return None

    @property
    def instruments(self):
        # TODO: add function
        return []

    @property
    def platforms(self):
        # TODO: add function
        return []


class Platform(models.Model):

    home_base = models.ForeignKey(HomeBase, on_delete=models.SET_NULL,
                                  related_name='platforms', null=True)
    platform_type = models.ForeignKey(
        AircraftType, on_delete=models.SET_NULL, related_name='platforms', null=True)

    short_name = models.CharField(max_length=128, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    platform_model = models.CharField(max_length=256)  # TODO: should we even be tracking this?
    desciption = models.CharField(max_length=256)
    resource_urls = models.CharField(max_length=512)
    notes_public = models.CharField(max_length=2048)

    gcmd_platform = models.ManyToManyField(GcmdPlatform, related_name='platforms')  # TODO: double check

    @property
    def campaigns(self):
        # TODO: add function
        return []

    @property
    def instruments(self):
        # TODO: add function
        return []

    def __str__(self):
        return self.short_name


class Instrument(models.Model):
    short_name = models.CharField(max_length=128, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    instrument_description = models.CharField(max_length=256)
    instrument_pi = models.CharField(max_length=256)
    instrument_technical_contact = models.CharField(max_length=256)
    facility_instrument_location = models.CharField(max_length=256)
    funding_source = models.CharField(max_length=256)
    spatial_resolution = models.CharField(max_length=256)
    temporal_resolution = models.CharField(max_length=256)
    radiometric_frequency = models.CharField(max_length=256)
    calibration_information = models.CharField(max_length=1024)
    initial_deployment_date = models.DateField()
    dates_of_operation = models.CharField(max_length=512)
    typical_number_of_data_products_per_level = models.CharField(max_length=256)
    instrument_manufacturer = models.CharField(max_length=512)
    resource_urls = models.CharField(max_length=2048)
    instrument_doi = models.CharField(max_length=1024)
    notes_public = models.CharField(max_length=2048)

    gcmd_instruments = models.ManyToManyField(GcmdInstrument, related_name='instruments')
    instrument_type = models.ManyToManyField(InstrumentType, related_name='instruments')
    measurement_keywords = models.ManyToManyField(MeasurementKeyword, related_name='instruments')
    measurement_regions = models.ManyToManyField(MeasurementRegion, related_name='instruments')
    repositories = models.ManyToManyField(Repository, related_name='instruments')

    @property
    def campaigns(self):
        # TODO: add function
        return []

    @property
    def platforms(self):
        # TODO: add function
        return []

    def __str__(self):
        return self.short_name


class Deployment(models.Model):

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='deployments')

    short_name = models.CharField(max_length=128)  # this is the 'deployment_id'
    long_name = models.CharField(max_length=512)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_flights = models.PositiveIntegerField()
    notes_public = models.CharField(max_length=2048)

    geographical_regions = models.ManyToManyField(GeographicalRegion, related_name='deployments')

    def vali_date(self):
        # TODO: validate the dates
        return None

    def __str__(self):
        return self.long_name


class IopSe(models.Model):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='iops')

    is_iop = models.BooleanField()
    short_name = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    iop_description = models.CharField(max_length=1024)
    region_description = models.CharField(max_length=512)
    published_list = models.CharField(max_length=1024)
    reports = models.CharField(max_length=1024)
    reference_file = models.CharField(max_length=1024)

    def __str__(self):
        return self.short_name


class Flight(models.Model):

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='flights')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='flights')

    asp_longname = models.CharField(max_length=512)
    info_from_asp = models.CharField(max_length=128)
    home_base = models.CharField(max_length=256)
    campaign_deployment_base = models.CharField(max_length=256)
    owner = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256)
    deployment_instrument_information_source = models.CharField(max_length=1024)
    notes_public = models.CharField(max_length=2048)

    instruments = models.ManyToManyField(Instrument, related_name='flights')
