from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import factory


from api_app.models import Change
from data_models.models import (
    Campaign,
    Season,
    FocusArea,
    GeophysicalConcept,
    PlatformType,
    Repository,
)


class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign

    start_date = date(year=2022, month=1, day=1)
    region_description = "test"
    ongoing = True
    nasa_led = True
    lead_investigator = "test"
    focus_phenomena = "test"


class SeasonsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Season


class FocusAreaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FocusArea


class GeophysicalConceptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GeophysicalConcept


class PlatformTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlatformType


class RepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repository


class ChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Change


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: "blah{0}".format(n))
    email = factory.Sequence(lambda n: "someone{0}@localhost".format(n))
    password = make_password("password")

    class Meta:
        model = get_user_model()
