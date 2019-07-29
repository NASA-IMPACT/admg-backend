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


############### 
# Core Models #
###############

class Campaign(models.Model):

    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    region = models.CharField(max_length=256)
    # bounding_box = # TODO SPACIAL DATA HERE
    start_date = models.DateField()
    end_date = models.DateField()
    program_lead = models.CharField(max_length=256)
    campaign_lead = models.CharField(max_length=256)
    technical_contact = models.CharField(max_length=256)
    publication_links = models.CharField(max_length=256)
    online_resources = models.CharField(max_length=256)
    repository_link = models.CharField(max_length=256)
    partner_organizations = models.CharField(max_length=256)
    partner_websites = models.CharField(max_length=256)
    doi = models.CharField(max_length=256)

    focus_areas = models.ManyToManyField(FocusArea, related_name='campaigns')
    seasons = models.ManyToManyField(Season, related_name='campaigns')
    repositories = models.ManyToManyField(Repository, related_name='campaigns')
    platform_types = models.ManyToManyField(PlatformType, related_name='campaigns')

    comments = models.CharField(max_length=2500)

    public = models.BooleanField()
    ongoing = models.BooleanField()


    def __str__(self):
        return self.short_name


    def number_deployments(self):
        # TODO: add function that counts number of deplyments from the associated table
        return None


    def number_flights(self):
        # TODO: add function that counts number of flights from the associated table
        return None


class Instrument(models.Model):

    instrument_type = models.ForeignKey(InstrumentType, 
                                        on_delete=models.SET_NULL, 
                                        related_name='instruments', 
                                        null=True)

    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    online_information = models.CharField(max_length=256)

    def __str__(self):
        return self.short_name


class Platform(models.Model):

    home_base = models.ForeignKey(HomeBase, on_delete=models.SET_NULL, related_name='platforms', null=True)
    platform_type = models.ForeignKey(AircraftType, on_delete=models.SET_NULL, related_name='platforms', null=True)

    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    organization = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    online_information = models.CharField(max_length=256)
    tail_numbers = models.CharField(max_length=256)
    platform_model = models.CharField(max_length=256)

    def __str__(self):
        return self.short_name


class Flight(models.Model):
    
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='flights')

    instruments = models.ManyToManyField(Instrument, related_name='flights')

    # short_name = models.CharField(max_length=256, blank=False, unique=True) # maybe change to flight_number?
    
    # def __str__(self):
    #     return self.short_name


class Deployment(models.Model):
   
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='deployments')

    platforms = models.ManyToManyField(Platform, related_name='campaigns')

    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return self.short_name
