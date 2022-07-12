from typing import Union
import importlib

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, fields
import factory

from data_models import models


def create_m2m_records(field_name: str, Factory: Union["BaseFactory", str]):
    """
    Helper to avoid boilerplace for creating post_generation handlers that
    add M2M records to a record.
    https://factoryboy.readthedocs.io/en/stable/recipes.html#simple-many-to-many-relationship
    """

    def post_generation(obj, create, extracted, **kwargs):
        # Lookup factory at runtime, allowing us to reference factories before defining them
        if isinstance(Factory, str):
            module = ".".join(Factory.split(".")[:-1])
            factory_name = Factory.split(".")[-1]
            _Factory = getattr(importlib.import_module(module), factory_name)
        else:
            _Factory = Factory

        if not isinstance(obj, dict):
            # Currently, only supporting situations where obj == dict (ie when
            # calling .as_change_dict()), consider supporting situations where obj
            # is a Model instance if needed in the future.
            return

        if extracted:
            # A list of records were passed in, use them
            obj.setdefault(field_name, extracted)
        else:
            # Create new record in DB
            obj.setdefault(field_name, _Factory.create_batch(1))

    return post_generation


class BaseFactory(factory.django.DjangoModelFactory):
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
        (ie UUID) rather than their model instance.
        """
        if not isinstance(value, Model):
            return value

        if _save:
            # Ensure all related models are saved to DB
            cls._ensure_saved(value)

        # For any foreign relations, we want the UUID of the FK, not the instance
        return str(getattr(value, "uuid", getattr(value, "pk")))

    @classmethod
    def as_dict(cls, **attrs):
        """
        Generate a dictionary representation of a model. Useful for
        passing to Change.update field.
        """
        return factory.build(dict, **attrs, FACTORY_CLASS=cls)

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
    repositories = factory.PostGeneration(
        create_m2m_records("repositories", f"{__name__}.RepositoryFactory")
    )
    platform_types = factory.PostGeneration(
        create_m2m_records("platform_types", f"{__name__}.PlatformTypeFactory")
    )
    geophysical_concepts = factory.PostGeneration(
        create_m2m_records("geophysical_concepts", f"{__name__}.GeophysicalConceptFactory")
    )
    seasons = factory.PostGeneration(create_m2m_records("seasons", f"{__name__}.SeasonFactory"))
    focus_areas = factory.PostGeneration(
        create_m2m_records("focus_areas", f"{__name__}.FocusAreaFactory")
    )

    class Meta:
        model = models.Campaign


class CollectionPeriodFactory(BaseFactory):
    deployment = factory.SubFactory(f"{__name__}.DeploymentFactory")
    platform = factory.SubFactory(f"{__name__}.PlatformFactory")
    auto_generated = factory.Faker("boolean")
    instruments = factory.PostGeneration(
        create_m2m_records("instruments", f"{__name__}.InstrumentFactory")
    )

    class Meta:
        model = models.CollectionPeriod


class DeploymentFactory(LimitedInfoBaseFactory):
    campaign = factory.SubFactory(f"{__name__}.CampaignFactory")
    start_date = factory.Faker("date")
    end_date = factory.Faker("date")

    class Meta:
        model = models.Deployment


class DOIFactory(BaseFactory):
    concept_id = factory.Faker("isbn10")
    date_queried = factory.Faker("iso8601")
    campaigns = factory.PostGeneration(
        create_m2m_records("campaigns", f"{__name__}.CampaignFactory")
    )

    class Meta:
        model = models.DOI


class FocusAreaFactory(LimitedInfoPriorityBaseFactory):
    class Meta:
        model = models.FocusArea


class GcmdBaseFactory(BaseFactory):
    gcmd_uuid = factory.Faker("uuid4")


class GcmdInstrumentFactory(GcmdBaseFactory):
    description = factory.Faker("paragraph")
    technical_contact = factory.Faker("name")
    spatial_resolution = factory.Faker("text")
    temporal_resolution = factory.Faker("text")
    radiometric_frequency = factory.Faker("text")
    gcmd_phenomena = factory.PostGeneration(
        create_m2m_records("gcmd_phenomena", f"{__name__}.GcmdPhenomenonFactory")
    )
    measurement_regions = factory.PostGeneration(
        create_m2m_records("measurement_regions", f"{__name__}.MeasurementRegionFactory")
    )

    class Meta:
        model = models.GcmdInstrument


class GcmdPhenomenonFactory(GcmdBaseFactory):
    category = factory.Faker("word")

    class Meta:
        model = models.GcmdPhenomenon


class GcmdPlatformFactory(GcmdBaseFactory):
    basis = factory.Faker("word")

    class Meta:
        model = models.GcmdPlatform


class GcmdProjectFactory(GcmdBaseFactory):
    bucket = factory.Faker("word")

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
    description = factory.Faker("paragraph")
    technical_contact = factory.Faker("name")
    spatial_resolution = factory.Faker("text")
    temporal_resolution = factory.Faker("text")
    radiometric_frequency = factory.Faker("text")
    gcmd_phenomena = factory.PostGeneration(
        create_m2m_records("gcmd_phenomena", f"{__name__}.GcmdPhenomenonFactory")
    )
    measurement_regions = factory.PostGeneration(
        create_m2m_records("measurement_regions", f"{__name__}.MeasurementRegionFactory")
    )

    class Meta:
        model = models.Instrument


class IOPFactory(BaseFactory):
    start_date = factory.Faker("date")
    end_date = factory.Faker("date")
    description = factory.Faker("sentence")
    region_description = factory.Faker("sentence")
    deployment = factory.SubFactory(f"{__name__}.DeploymentFactory")

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
    stationary = factory.Faker("boolean")
    description = factory.Faker("sentence")

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
    CollectionPeriodFactory,
    DeploymentFactory,
    DOIFactory,
    FocusAreaFactory,
    GcmdInstrumentFactory,
    GcmdPhenomenonFactory,
    GcmdPlatformFactory,
    GcmdProjectFactory,
    GeographicalRegionFactory,
    GeophysicalConceptFactory,
    HomeBaseFactory,
    ImageFactory,
    InstrumentFactory,
    IOPFactory,
    MeasurementRegionFactory,
    MeasurementStyleFactory,
    MeasurementTypeFactory,
    PartnerOrgFactory,
    PlatformFactory,
    PlatformTypeFactory,
    RepositoryFactory,
    SeasonFactory,
    SignificantEventFactory,
    WebsiteFactory,
    WebsiteTypeFactory,
]
