import os
import urllib.parse
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as geomodels
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db import models

# TODO: Mv to config
FRONTEND_URL = "https://airborne-inventory.surge.sh/"
NOTES_INTERNAL_HELP_TEXT = "Free text notes for ADMG staff, this is NOT visible to the public."
NOTES_PUBLIC_HELP_TEXT = "Free text notes, this IS visible to the public."
UNIMPLEMENTED_HELP_TEXT = "*these will be images that would be either uploaded directly or URL to image would be provided...we don’t have this fully in curation process yet."


def select_related_distinct_data(queryset, related_data_string):
    """Selects related data from a given object using the related data string

    Args:
        queryset (QuerySet): A queryset of related objects. E.g. my_campaign.deployments
        related_data_string (str): Django-formatted string of related data. E.g. instrument__uuid
    """

    return queryset.select_related().values_list(related_data_string, flat=True).distinct()


def create_gcmd_str(categories):
    """Inputs a list of GCMD category strings and combines them with > if they exist.
    This is used in some GCMD models to make a better __str__ representation that shows
    the entire GCMD path.

    Args:
        categories (list): List of strings. ie: ['first', 'second', 'third']

    Returns:
        str: __str__ representation. ie: 'first > second > third'
    """

    return " > ".join(category for category in categories if category)


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
    ext = os.path.splitext(urllib.parse.urlparse(path).path)[1]
    return f"{instance.uuid}.{ext}"


class Image(BaseModel):
    image = models.ImageField(upload_to=get_file_path)
    title = models.CharField(max_length=1024, default="", blank=True)
    description = models.CharField(max_length=2048, default="", blank=True)
    owner = models.CharField(max_length=512, default="", blank=True)
    source_url = models.TextField(blank=True, default="")

    def __str__(self):
        return self.title or self.image.name


class LimitedInfo(BaseModel):
    short_name = models.CharField(max_length=256, blank=False, unique=True)
    long_name = models.CharField(max_length=512, default="", blank=True)
    notes_internal = models.TextField(default="", blank=True, help_text=NOTES_INTERNAL_HELP_TEXT)
    notes_public = models.TextField(default="", blank=True, help_text=NOTES_PUBLIC_HELP_TEXT)

    class Meta:
        abstract = True
        ordering = ("short_name",)


class LimitedInfoPriority(LimitedInfo):
    order_priority = models.PositiveIntegerField(unique=True, blank=True, null=True)

    class Meta:
        abstract = True


class PlatformType(LimitedInfoPriority):
    parent = models.ForeignKey(
        "PlatformType", on_delete=models.CASCADE, related_name="sub_types", null=True, blank=True
    )

    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default="")

    @property
    def patriarch(self):
        """Returns the highest level parent in the platform_type hierarchy

        Returns:
            [str]: short name of the highest level parent
        """

        if self.parent:
            return self.parent.patriarch
        else:
            return self.short_name

    class Meta(LimitedInfo.Meta):
        pass


class MeasurementType(LimitedInfoPriority):
    parent = models.ForeignKey(
        "MeasurementType", on_delete=models.CASCADE, related_name="sub_types", null=True, blank=True
    )
    example = models.CharField(max_length=1024, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class MeasurementStyle(LimitedInfoPriority):
    parent = models.ForeignKey(
        "MeasurementStyle",
        on_delete=models.CASCADE,
        related_name="sub_types",
        null=True,
        blank=True,
    )
    example = models.CharField(max_length=1024, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class HomeBase(LimitedInfoPriority):
    location = models.CharField(max_length=512, blank=True, default="")
    additional_info = models.CharField(max_length=2048, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class FocusArea(LimitedInfoPriority):
    url = models.CharField(max_length=256, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class Season(LimitedInfoPriority):
    class Meta(LimitedInfo.Meta):
        pass


class Repository(LimitedInfoPriority):
    gcmd_uuid = models.UUIDField(null=True, blank=True)

    class Meta(LimitedInfo.Meta):
        pass


class MeasurementRegion(LimitedInfoPriority):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class GeographicalRegion(LimitedInfoPriority):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class GeophysicalConcept(LimitedInfoPriority):
    gcmd_uuid = models.UUIDField(null=True, blank=True)
    example = models.CharField(max_length=1024, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class WebsiteType(LimitedInfoPriority):
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return self.long_name

    class Meta(LimitedInfo.Meta):
        pass


class Alias(BaseModel):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.UUIDField()
    parent_fk = GenericForeignKey("content_type", "object_id")

    # model_name = models.CharField(max_length=64, blank=False)
    short_name = models.CharField(max_length=512, blank=False)
    source = models.TextField(blank=True, default="")

    # def save(self, *args, **kwargs):
    #     """converts model_name field 'PartnerOrg' into a content type to support the
    #     GenericForeignKey relationship, which would otherwise require an arbitrary
    #     primary key to be passed in the post request"""
    #     self.content_type = ContentType.objects.get(
    #         app_label="data_models", model=self.model_name.lower()
    #     )
    #     return super(Alias, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Aliases"

    @property
    def model_name(self):
        return self.content_type.model_class


class PartnerOrg(LimitedInfoPriority):
    aliases = GenericRelation(Alias)

    website = models.CharField(max_length=256, blank=True, default="")

    class Meta(LimitedInfo.Meta):
        pass


class GcmdKeyword(BaseModel):
    def _get_casei_model(self):
        from kms import keyword_to_casei_map

        return keyword_to_casei_map[self.__class__.__name__.lower()]

    def _get_casei_attribute(self):
        from kms import keyword_casei_attribute_map

        return keyword_casei_attribute_map[self.__class__.__name__.lower()]

    # TODO: Ed and I think this should just change to attribute. Just have none value for parent class.
    @property
    def gcmd_path():
        raise NotImplementedError()

    casei_model = property(_get_casei_model)
    casei_attribute = property(_get_casei_attribute)

    class Meta:
        abstract = True


class GcmdProject(GcmdKeyword):
    short_name = models.CharField(max_length=256, blank=True, default="")
    long_name = models.CharField(max_length=512, blank=True, default="")
    bucket = models.CharField(max_length=256)
    gcmd_uuid = models.UUIDField(unique=True)
    gcmd_path = ["bucket", "short_name"]

    def __str__(self):
        categories = (self.short_name, self.long_name)
        return create_gcmd_str(categories)

    # TODO: Get rid of once this works.
    # @staticmethod
    # def gcmd_path():
    #     return ["bucket", "short_name"]

    class Meta:
        ordering = ("short_name",)


class GcmdInstrument(GcmdKeyword):
    short_name = models.CharField(max_length=256, blank=True, default="")
    long_name = models.CharField(max_length=512, blank=True, default="")
    # these make more sense without 'instrument', however class and type are
    # default variables so instrument was added to all 4 for consistency
    instrument_category = models.CharField(max_length=256, blank=True, default="")
    instrument_class = models.CharField(max_length=256, blank=True, default="")
    instrument_type = models.CharField(max_length=256, blank=True, default="")
    instrument_subtype = models.CharField(max_length=256, blank=True, default="")
    gcmd_uuid = models.UUIDField(unique=True)
    gcmd_path = [
        "instrument_category",
        "instrument_class",
        "instrument_type",
        "instrument_subtype",
        "short_name",
    ]

    def __str__(self):
        categories = (
            self.instrument_category,
            self.instrument_class,
            self.instrument_type,
            self.instrument_subtype,
            self.long_name,
            self.short_name,
        )
        return create_gcmd_str(categories)

    # @staticmethod
    # def gcmd_path():
    #     return [
    #         "instrument_category",
    #         "instrument_class",
    #         "instrument_type",
    #         "instrument_subtype",
    #         "short_name",
    #     ]

    class Meta:
        ordering = ("short_name",)


class GcmdPlatform(GcmdKeyword):
    short_name = models.CharField(max_length=256, blank=True, default="")
    long_name = models.CharField(max_length=512, blank=True, default="")
    category = models.CharField(max_length=256)
    series_entry = models.CharField(max_length=256, blank=True, default="")
    description = models.TextField(blank=True, default="")
    gcmd_uuid = models.UUIDField(unique=True)
    gcmd_path = ["category", "series_entry", "short_name"]

    def __str__(self):
        categories = (self.category, self.long_name, self.short_name)
        return create_gcmd_str(categories)

    # @staticmethod
    # def gcmd_path():
    #     return ["category", "series_entry", "short_name"]

    class Meta:
        ordering = ("short_name",)


class GcmdPhenomenon(GcmdKeyword):
    category = models.CharField(max_length=256)
    topic = models.CharField(max_length=256, blank=True, default="")
    term = models.CharField(max_length=256, blank=True, default="")
    variable_1 = models.CharField(max_length=256, blank=True, default="")
    variable_2 = models.CharField(max_length=256, blank=True, default="")
    variable_3 = models.CharField(max_length=256, blank=True, default="")
    gcmd_uuid = models.UUIDField(unique=True)
    gcmd_path = [
        "category",
        "topic",
        "term",
        "variable_1",
        "variable_2",
        "variable_3",
    ]

    def __str__(self):
        categories = (
            self.category,
            self.topic,
            self.term,
            self.variable_1,
            self.variable_2,
            self.variable_3,
        )
        return create_gcmd_str(categories)

    # @staticmethod
    # def gcmd_path():
    #     return [
    #         "category",
    #         "topic",
    #         "term",
    #         "variable_1",
    #         "variable_2",
    #         "variable_3",
    #     ]

    class Meta:
        verbose_name_plural = "Phenomena"


class Website(BaseModel):
    campaign = models.ForeignKey("Campaign", related_name="websites", on_delete=models.CASCADE)
    website_type = models.ForeignKey(WebsiteType, on_delete=models.CASCADE, related_name="websites")
    order_priority = models.PositiveIntegerField(null=True, blank=True)

    url = models.URLField(max_length=1024)
    title = models.TextField(default="", blank=True)
    description = models.TextField(default="", blank=True)
    notes_internal = models.TextField(default="", blank=True, help_text=NOTES_INTERNAL_HELP_TEXT)

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
        return ["short_name", "long_name"]

    @classmethod
    def search(cls, params):
        search_type = params.pop("search_type", "plain")
        search = params.pop("search", None)
        search_fields_param = params.pop("search_fields", None)
        if search_fields_param:
            search_fields = search_fields_param.split(",")
        else:
            search_fields = cls.search_fields()

        queryset = cls.objects.all()

        if search:
            vector = SearchVector(*search_fields)

            queryset = queryset.annotate(search=vector).filter(
                search=SearchQuery(search, search_type=search_type)
            )

        return queryset.filter(**params)


class Campaign(DataModel):
    description_long = models.TextField(
        default="",
        blank=True,
        verbose_name="Draft Description",
        help_text="Free text full campaign description including items such as the science or research objectives, regional location, supported mission(s), and equipment used",
    )
    description_short = models.TextField(
        default="",
        blank=True,
        verbose_name="Admin Description",
        help_text="Concise, shortened text description of the field investigation, follows a similar format for all campaigns",
    )
    aliases = GenericRelation(Alias)

    start_date = models.DateField(help_text="Start date of first deployment")
    end_date = models.DateField(blank=True, null=True, help_text="End date of last deployment")

    region_description = models.TextField(
        help_text="Free text words identifying the region/domain for the campaign"
    )
    spatial_bounds = geomodels.PolygonField(
        blank=True,
        null=True,
        help_text="Latitude & Longitude for domain bounding box; enter as N, S, E, W",
    )
    seasons = models.ManyToManyField(
        Season,
        related_name="campaigns",
        verbose_name="Season(s) of Study",
        help_text="Season(s) of campaign data collection - Include all that are appropriate",
    )
    focus_phenomena = models.CharField(
        max_length=1024,
        help_text="Free text identifying the focus of campaign’s science/research objective",
    )
    focus_areas = models.ManyToManyField(
        FocusArea,
        related_name="campaigns",
        verbose_name="NASA Earth Science Focus Area(s)",
        help_text="NASA ES Focus Area(s) supported by the field investigation",
    )
    geophysical_concepts = models.ManyToManyField(
        GeophysicalConcept,
        related_name="campaigns",
        help_text="Primary relevant geophysical concepts, based on the campaign’s science objectives",
    )
    nasa_missions = models.TextField(
        default="",
        blank=True,
        help_text="NASA Missions supported by the campaign. See https://www.nasa.gov/content/earth-missions-list",
    )
    lead_investigator = models.CharField(
        max_length=256,
        verbose_name="Principal Investigator",
        help_text="Name(s) of person/people leading the campaign (PI and/or Co-Is), or the name(s) of the NASA lead for NASA’s involvement in the campaign",
    )
    technical_contact = models.CharField(
        max_length=256,
        default="",
        blank=True,
        verbose_name="Data Management/Technical Contact",
        help_text="Name(s) of person/people for data management and/or technical concerns (often is a DAAC person)",
    )
    funding_agency = models.CharField(
        max_length=256,
        default="",
        blank=True,
        help_text="Name of agency funding the campaign (e.g. NASA, NOAA, NSF…)",
    )
    funding_program = models.CharField(
        max_length=256,
        default="",
        blank=True,
        help_text="Name of the NASA program(s) or mission(s) that funded the campaign",
    )
    funding_program_lead = models.CharField(
        max_length=256,
        default="",
        blank=True,
        help_text="Name(s) of the person/people leading the NASA funding program (at the time of campaign, if possible)",
    )
    campaign_doi = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        verbose_name="Campaign DOI",
        help_text="DOI assigned for the ENTIRE collection/group/set of campaign data.  This may not exist.",
    )
    gcmd_projects = models.ManyToManyField(
        GcmdProject,
        related_name="campaigns",
        default="",
        blank=True,
        verbose_name="Campaign’s GCMD Project Keyword",
        help_text="GCMD Project Keyword corresponding to this field investigation/campaign",
    )
    ongoing = models.BooleanField(verbose_name="Is this field investigation currently ongoing?")
    nasa_led = models.BooleanField(verbose_name="Is this a NASA-led field investigation?")

    platform_types = models.ManyToManyField(PlatformType, related_name="campaigns")

    partner_orgs = models.ManyToManyField(
        PartnerOrg,
        related_name="campaigns",
        default="",
        blank=True,
        verbose_name="Partner Organization(s)",
        help_text="Partner organizations involved in the campaign",
    )
    repositories = models.ManyToManyField(
        Repository,
        related_name="campaigns",
        verbose_name="Data Repository(ies)",
        help_text="Data repository (assigned archive repository) for the campaign (typically a NASA DAAC)",
    )
    number_data_products = models.PositiveIntegerField(null=True, blank=True)
    data_volume = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name="Campaign Total Data Storage Volume",
        help_text="Total volume of published campaign data products (in GB or TB)",
    )

    logo = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def website_details(self):
        websites = []
        for website in self.websites.all():
            website_type = website.website_type.long_name
            order_priority = self.campaign_websites.get(
                campaign=self.uuid, website=website
            ).order_priority
            websites.append(
                {
                    "title": website.title,
                    "url": website.url,
                    "website_type": website_type,
                    "order_priority": order_priority,
                }
            )
        return websites

    @property
    def significant_events(self):
        return select_related_distinct_data(self.deployments, "significant_events__uuid")

    @property
    def iops(self):
        return select_related_distinct_data(self.deployments, "iops__uuid")

    @property
    def number_ventures(self):
        venture_counts = list(
            self.deployments.select_related().values_list(
                "collection_periods__number_ventures", flat=True
            )
        )
        return sum(filter(None, venture_counts))

    @property
    def number_data_products(self):
        return self.dois.count()

    @property
    def number_deployments(self):
        return self.deployments.count()

    @property
    def instruments(self):
        return select_related_distinct_data(
            self.deployments, "collection_periods__instruments__uuid"
        )

    @property
    def platforms(self):
        return select_related_distinct_data(self.deployments, "collection_periods__platform__uuid")

    @staticmethod
    def search_fields():
        return ["short_name", "long_name", "description_short", "focus_phenomena"]

    def get_absolute_url(self):
        return urllib.parse.urljoin(FRONTEND_URL, f"/campaign/{self.uuid}/")


class Platform(DataModel):

    platform_type = models.ForeignKey(
        PlatformType,
        on_delete=models.SET_NULL,
        related_name="platforms",
        null=True,
        help_text="Assign the most specific type of platform possible from the list",
    )

    aliases = GenericRelation(Alias)
    description = models.TextField(help_text="Free text description of the platform")
    stationary = models.BooleanField(verbose_name="Is the platform stationary?")
    gcmd_platforms = models.ManyToManyField(
        GcmdPlatform,
        related_name="platforms",
        default="",
        blank=True,
        verbose_name="Platform’s GCMD Platform Keyword(s)",
        help_text="GCMD Platform/Source keyword(s) corresponding to this platform",
    )

    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    online_information = models.CharField(
        max_length=512,
        default="",
        blank=True,
        help_text="URL(s) for additional relevant online information for the platform",
    )

    @property
    def search_category(self):
        """Returns a custom defined search category based on the platform_type's
        highest level parent (patriarch) and the platform's stationary field.

        Returns:
            search_category [str]: One of 6 search categories
        """

        patriarch = self.platform_type.patriarch

        if patriarch == "Air Platforms":
            category = "Aircraft"

        elif patriarch == "Water Platforms":
            category = "Water-based platforms"

        elif patriarch == "Land Platforms":
            if self.stationary:
                category = "Stationary land sites"
            else:
                category = "Mobile land-based platforms"

        elif patriarch in ["Satellites", "Manned Spacecraft"]:
            category = "Spaceborne"

        else:
            category = "Special Cases"

        return category

    @property
    def campaigns(self):
        return select_related_distinct_data(self.collection_periods, "deployment__campaign__uuid")

    @property
    def instruments(self):
        return select_related_distinct_data(self.collection_periods, "instruments")

    @staticmethod
    def search_fields():
        return ["short_name", "long_name", "description"]

    def get_absolute_url(self):
        return urllib.parse.urljoin(FRONTEND_URL, f"/platform/{self.uuid}/")


class Instrument(DataModel):
    aliases = GenericRelation(Alias)

    measurement_style = models.ForeignKey(
        MeasurementStyle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instruments",
        help_text="Primary operation principle of the sensor",
    )
    measurement_type = models.ForeignKey(
        MeasurementType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instruments",
        help_text="Broad grouping for the type of measurements the instrument is used for",
    )

    description = models.TextField(help_text="Free text description of the instrument")
    lead_investigator = models.CharField(
        max_length=256,
        default="",
        blank=True,
        verbose_name="Instrument PI/Co-Is",
        help_text="Name(s) of person/people leading the development of the instrument (typically, the Principle Investigator and/or Co-Investigator)",
    )
    technical_contact = models.CharField(
        max_length=256,
        help_text="Name(s) of person/people leading the maintenance, integration, and/or operation of the instrument",
    )
    facility = models.CharField(
        max_length=256,
        default="",
        blank=True,
        verbose_name="Facility Instrument Location",
        help_text="If Facility Instrument give location or put 'retired', otherwise N/A",
    )
    gcmd_phenomena = models.ManyToManyField(
        GcmdPhenomenon,
        related_name="instruments",
        verbose_name="Measurements/Variables from GCMD Science Keywords",
        help_text="Select relevant measurements/variables items from GCMD Science Keywords for Earth Science",
    )
    funding_source = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        help_text="Program or Mission funding the development, maintenance, deployment, and/or operation of the instrument",
    )

    spatial_resolution = models.CharField(
        max_length=256,
        help_text="Horizontal and vertical resolution of the instrument’s measurements",
    )
    temporal_resolution = models.CharField(
        max_length=256, help_text="Temporal resolution of the instrument’s measurements"
    )
    radiometric_frequency = models.CharField(
        max_length=256, help_text="Operating frequency of the instrument"
    )
    measurement_regions = models.ManyToManyField(
        MeasurementRegion,
        related_name="instruments",
        verbose_name="Vertical Measurement Region",
        help_text="Name of the vertical region(s) observed by the instrument",
    )
    calibration_information = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        help_text="URL or DOI for instrument calibration info (may be a webpage or publication)",
    )
    instrument_manufacturer = models.CharField(
        max_length=512,
        default="",
        blank=True,
        help_text="Name of lab or company that makes or manufactures the instrument",
    )

    overview_publication = models.CharField(
        max_length=2048,
        default="",
        blank=True,
        verbose_name="Instrument Publication",
        help_text="Highest authority document describing the instrument (DOI or URL)",
    )
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    online_information = models.CharField(
        max_length=2048,
        default="",
        blank=True,
        help_text="URL(s) for additional relevant online information for the instrument",
    )
    gcmd_instruments = models.ManyToManyField(
        GcmdInstrument,
        related_name="instruments",
        default="",
        blank=True,
        help_text="GCMD Instrument/Sensor keyword(s) corresponding to this instrument",
    )
    instrument_doi = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        verbose_name="Instrument DOI",
        help_text="The DOI assigned to the instrument.  This may not exist.",
    )
    repositories = models.ManyToManyField(
        Repository, related_name="instruments", default="", blank=True
    )
    additional_metadata = models.JSONField(
        default=None,
        blank=True,
        null=True,
        verbose_name="Additional Metadata",
        help_text="An open item for potential extra metadata element(s)",
    )

    @property
    def campaigns(self):
        return select_related_distinct_data(self.collection_periods, "deployment__campaign__uuid")

    @property
    def platforms(self):
        return select_related_distinct_data(self.collection_periods, "platform__uuid")

    def get_absolute_url(self):
        return urllib.parse.urljoin(FRONTEND_URL, f"/instrument/{self.uuid}/")


class Deployment(DataModel):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="deployments")
    aliases = GenericRelation(Alias)

    start_date = models.DateField(help_text="Start date of deployment")
    end_date = models.DateField(help_text="End date of deployment.")

    geographical_regions = models.ManyToManyField(
        GeographicalRegion,
        related_name="deployments",
        default="",
        blank=True,
        help_text="Type of geographical area(s) over which this deployment occured.  Select all that apply.",
    )

    spatial_bounds = geomodels.PolygonField(blank=True, null=True)
    study_region_map = models.TextField(default="", blank=True, help_text=UNIMPLEMENTED_HELP_TEXT)
    ground_sites_map = models.TextField(default="", blank=True, help_text=UNIMPLEMENTED_HELP_TEXT)
    flight_tracks = models.TextField(default="", blank=True, help_text=UNIMPLEMENTED_HELP_TEXT)

    def __str__(self):
        return self.short_name

    @property
    def platforms(self):
        return select_related_distinct_data(self.collection_periods, "platform__uuid")


class IopSe(BaseModel):

    deployment = models.ForeignKey(
        Deployment,
        on_delete=models.CASCADE,
        related_name="iops",
        help_text="ADMG’s deployment identifier",
    )

    short_name = models.CharField(
        max_length=256,
        help_text="ADMG's text identifier for the IOP - format as 'XXX_IOP_#' with XXX as the campaign shortname and # as the integer number of the IOP within the campaign",
    )
    start_date = models.DateField(help_text="Start date of event")
    end_date = models.DateField(help_text="End date of event")
    description = models.TextField(help_text="Free text description of the event")
    region_description = models.TextField(
        verbose_name="Location Description",
        help_text="Free text words identifying the location of the event domain",
    )
    published_list = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        help_text="DOI or URL for location of published info noting this event within the campaign",
    )
    reports = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        verbose_name="Science/Flight Reports",
        help_text="DOI or URL for location of published IOP Science or Flight reports",
    )
    reference_file = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        verbose_name="Reference Granule/File",
        help_text="Text filename of a specific granule file for reference",
    )

    class Meta:
        abstract = True


class IOP(IopSe):
    deployment = models.ForeignKey(
        Deployment,
        on_delete=models.CASCADE,
        related_name="iops",
        help_text="ADMG’s deployment identifier",
    )


class SignificantEvent(IopSe):

    deployment = models.ForeignKey(
        Deployment,
        on_delete=models.CASCADE,
        related_name="significant_events",
        help_text="ADMG’s deployment identifier",
    )
    iop = models.ForeignKey(
        IOP,
        on_delete=models.CASCADE,
        related_name="significant_events",
        null=True,
        help_text="ADMG's IOP identifier, if this SE occurred within an IOP",
    )

    reports = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        verbose_name="Science/Flight Reports",
        help_text="DOI or URL for location of published info noting this Significant Event within the campaign",
    )


class CollectionPeriod(BaseModel):

    deployment = models.ForeignKey(
        Deployment, on_delete=models.CASCADE, related_name="collection_periods"
    )
    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="collection_periods"
    )

    platform_identifier = models.CharField(
        max_length=128,
        default="",
        blank=True,
        help_text="Optional platform identifier, such as an aircraft tail number or vessel registration number, if available",
    )
    number_ventures = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Total Number of CDCPs",
        help_text="Total number of Continuous Data Collection Periods (CDCPs) conducted by the platform during the deployment",
    )

    home_base = models.ForeignKey(
        HomeBase,
        on_delete=models.CASCADE,
        related_name="collection_periods",
        blank=True,
        null=True,
        help_text="ADMG’s identifying name for the platform.  *This should match one of the items in the “Platforms Active” element from Deployment Form.",
    )
    campaign_deployment_base = models.CharField(
        max_length=256,
        default="",
        blank=True,
        verbose_name="Platform Deployment Base",
        help_text="Deployment base/operating location for the p platform during the field investigation/deployment",
    )

    platform_owner = models.CharField(
        max_length=256, default="", blank=True, help_text="Organization that owns the platform"
    )
    platform_technical_contact = models.CharField(
        max_length=256,
        default="",
        blank=True,
        help_text="Name(s) of person/people leading the management, maintenance, integration, and/or operation of the platform",
    )

    instruments = models.ManyToManyField(
        Instrument,
        related_name="collection_periods",
        verbose_name="Instrument Package",
        help_text="ADMG’s Instrument Short Names for all sensors in the platform’s instrument package for this deployment",
    )
    instrument_information_source = models.CharField(
        max_length=1024,
        default="",
        blank=True,
        verbose_name="Instrument Package Information Source",
        help_text="DOI or URL for location of lists of instruments used on this platform for the deployment",
    )

    notes_internal = models.TextField(default="", blank=True, help_text=NOTES_INTERNAL_HELP_TEXT)
    notes_public = models.TextField(default="", blank=True, help_text=NOTES_PUBLIC_HELP_TEXT)

    auto_generated = models.BooleanField()

    def __str__(self):
        platform_id = f"({self.platform_identifier})" if self.platform_identifier else ""
        campaign = str(self.deployment.campaign)
        deployment = str(self.deployment).replace(campaign + "_", "")
        return f"{campaign} | {deployment} | {self.platform} {platform_id}"


class DOI(BaseModel):
    concept_id = models.CharField(max_length=512, unique=True)
    doi = models.CharField(max_length=512, null=True, blank=True, default="")
    long_name = models.TextField(blank=True, default="")

    cmr_short_name = models.CharField(max_length=512, blank=True, default="")
    cmr_entry_title = models.TextField(blank=True, default="")
    cmr_projects = models.JSONField(default=None, blank=True, null=True)
    cmr_dates = models.JSONField(default=None, blank=True, null=True)
    cmr_plats_and_insts = models.JSONField(default=None, blank=True, null=True)
    cmr_science_keywords = models.JSONField(default=None, blank=True, null=True)
    cmr_abstract = models.TextField(blank=True, default="")
    cmr_data_formats = ArrayField(
        models.CharField(max_length=512, blank=True, default=""), blank=True, default=list
    )

    date_queried = models.DateTimeField()

    campaigns = models.ManyToManyField(Campaign, related_name="dois")
    instruments = models.ManyToManyField(Instrument, blank=True, related_name="dois")
    platforms = models.ManyToManyField(Platform, blank=True, related_name="dois")
    collection_periods = models.ManyToManyField(CollectionPeriod, blank=True, related_name="dois")

    def __str__(self):
        return self.cmr_entry_title or self.cmr_short_name or self.doi or self.concept_id

    def get_absolute_url(self):
        return urllib.parse.urljoin("https://doi.org", self.doi)

    class Meta:
        verbose_name = "DOI"
