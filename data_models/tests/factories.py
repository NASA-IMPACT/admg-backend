from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, fields
import factory

from data_models import models


class BaseFactory(factory.django.DjangoModelFactory):
    @classmethod
    def as_dict(cls, **attrs):
        """
        Generate a dictionary representation of a model. Useful for
        passing to Change.update field.
        """
        return factory.build(dict, **attrs, FACTORY_CLASS=cls)

    @classmethod
    def _ensure_saved(cls, value):
        """
        Recursively traverse through all properties of a dict/model and
        ensure that all of its related models are saved to DB
        """
        if isinstance(value, dict):
            for v in value.values():
                cls._ensure_saved(v)

        elif isinstance(value, Model):
            # Make sure any related models that this model depends on are saved first
            for field in value._meta.get_fields():
                if not isinstance(field, fields.related.ForeignKey):
                    continue
                cls._ensure_saved(getattr(value, field.name))

            # Save this model
            value.save()

    @classmethod
    def _transform_to_identifier(cls, value, _save=True):
        """
        For Change models, we want to store records as their identifiers
        (ie UUDI) rather than their model instance.
        """
        if not isinstance(value, Model):
            return value

        if _save:
            # Ensure all related models are saved to DB
            cls._ensure_saved(value)

        # For any foreign relations, we want the UUID of the FK, not the instance
        return str(getattr(value, "uuid", getattr(value, "pk")))

    @classmethod
    def as_change_dict(cls, *, _save=True, **attrs):
        """
        Generate a dictionary representation of a model with all related
        models stored as UUIDs
        """
        change_dict = cls.as_dict(**attrs)

        for k, v in change_dict.items():
            if isinstance(v, list):
                change_dict[k] = [cls._transform_to_identifier(_v) for _v in v]
            elif isinstance(v, Model):
                change_dict[k] = cls._transform_to_identifier(v)

        return change_dict


class LimitedInfoBaseFactory(BaseFactory):
    short_name = factory.Faker("text", max_nb_chars=20)


class LimitedInfoPriorityBaseFactory(LimitedInfoBaseFactory):
    order_priority = factory.Sequence(lambda n: n)


class AliasFactory(BaseFactory):
    parent_fk = factory.SubFactory(f"{__name__}.CampaignFactory")

    class Meta:
        model = models.Alias

    @factory.post_generation
    def set_generic_relation_fields(self, create: bool, extracted, **kwargs):
        if isinstance(self, dict):
            parent_fk = self["parent_fk"]
            if "content_type" not in self:
                self["content_type"] = ContentType.objects.get_for_model(parent_fk)
            self.setdefault("object_id", str(parent_fk.uuid))


class CampaignFactory(LimitedInfoBaseFactory):
    start_date = factory.Faker("date")
    ongoing = factory.Faker("boolean")
    nasa_led = factory.Faker("boolean")

    region_description = factory.Faker("sentence")
    focus_phenomena = factory.Faker("sentence")
    lead_investigator = factory.Faker("name")

    class Meta:
        model = models.Campaign

    @factory.post_generation
    def repositories(self, create, extracted, **kwargs):
        if isinstance(self, dict):
            self.setdefault("repositories", [RepositoryFactory()])

        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of repositories were passed in, use them
            for repository in extracted:
                self["repositories"].add(repository)

    @factory.post_generation
    def platform_types(self, create, extracted, **kwargs):
        if isinstance(self, dict):
            self.setdefault("platform_types", [PlatformTypeFactory()])

        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of platform_types were passed in, use them
            for platform_type in extracted:
                self["platform_types"].add(platform_types)

    @factory.post_generation
    def geophysical_concepts(self, create, extracted, **kwargs):
        if isinstance(self, dict):
            self.setdefault("geophysical_concepts", [GeophysicalConceptFactory()])

        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of geophysical_concepts were passed in, use them
            for geophysical_concept in extracted:
                self["geophysical_concepts"].add(geophysical_concept)

    @factory.post_generation
    def seasons(self, create, extracted, **kwargs):
        if isinstance(self, dict):
            self.setdefault("seasons", [SeasonFactory()])

        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of seasons were passed in, use them
            for season in extracted:
                self["seasons"].add(season)

    @factory.post_generation
    def focus_areas(self, create, extracted, **kwargs):
        if isinstance(self, dict):
            self.setdefault("focus_areas", [FocusAreaFactory()])

        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of focus_areas were passed in, use them
            for focus_area in extracted:
                self["focus_areas"].add(focus_area)


class CollectionPeriodFactory(BaseFactory):
    class Meta:
        model = models.CollectionPeriod


class DeploymentFactory(LimitedInfoBaseFactory):
    campaign = factory.SubFactory(f"{__name__}.CampaignFactory")
    start_date = factory.Faker("date")
    end_date = factory.Faker("date")

    class Meta:
        model = models.Deployment


class DOIFactory(BaseFactory):
    class Meta:
        model = models.DOI


class FocusAreaFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.FocusArea


class GcmdInstrumentFactory(BaseFactory):
    class Meta:
        model = models.GcmdInstrument


class GcmdPhenomenaFactory(BaseFactory):
    class Meta:
        model = models.GcmdPhenomena


class GcmdPlatformFactory(BaseFactory):
    class Meta:
        model = models.GcmdPlatform


class GcmdProjectFactory(BaseFactory):
    class Meta:
        model = models.GcmdProject


class GeographicalRegionFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.GeographicalRegion


class GeophysicalConceptFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.GeophysicalConcept


class HomeBaseFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.HomeBase


class ImageFactory(BaseFactory):
    image = factory.Faker("file_name", category="image")

    class Meta:
        model = models.Image


class InstrumentFactory(LimitedInfoBaseFactory):
    class Meta:
        model = models.Instrument


class IOPFactory(BaseFactory):
    class Meta:
        model = models.IOP


class MeasurementRegionFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.MeasurementRegion


class MeasurementStyleFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.MeasurementStyle


class MeasurementTypeFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.MeasurementType


class PartnerOrgFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.PartnerOrg


class PlatformFactory(LimitedInfoBaseFactory):
    class Meta:
        model = models.Platform


class PlatformTypeFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.PlatformType


class RepositoryFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.Repository


class SeasonFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.Season


class SignificantEventFactory(BaseFactory):
    start_date = factory.Faker("date")
    end_date = factory.Faker("date")
    description = factory.Faker("sentence")
    region_description = factory.Faker("sentence")
    deployment = factory.SubFactory(f"{__name__}.DeploymentFactory")

    class Meta:
        model = models.SignificantEvent


class WebsiteFactory(BaseFactory):
    url = factory.Faker("url")
    campaign = factory.SubFactory(f"{__name__}.CampaignFactory")
    website_type = factory.SubFactory(f"{__name__}.WebsiteTypeFactory")

    class Meta:
        model = models.Website


class WebsiteTypeFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.WebsiteType


DATAMODELS_FACTORIES = [
    AliasFactory,
    CampaignFactory,
    # CollectionPeriodFactory,
    DeploymentFactory,
    # DOIFactory,
    # FocusAreaFactory,
    # GcmdInstrumentFactory,
    # GcmdPhenomenaFactory,
    # GcmdPlatformFactory,
    # GcmdProjectFactory,
    # GeographicalRegionFactory,
    # GeophysicalConceptFactory,
    # HomeBaseFactory,
    ImageFactory,
    # InstrumentFactory,
    # IOPFactory,
    # MeasurementRegionFactory,
    # MeasurementStyleFactory,
    # MeasurementTypeFactory,
    # PartnerOrgFactory,
    # PlatformFactory,
    # PlatformTypeFactory,
    # RepositoryFactory,
    # SeasonFactory,
    SignificantEventFactory,
    WebsiteFactory,
    WebsiteTypeFactory,
]
