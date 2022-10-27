from datetime import date

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from admg_webapp.users.models import User
from api_app.models import Change
from data_models.models import Campaign


class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign

    start_date = date(year=2022, month=1, day=1)
    region_description = "test"
    ongoing = True
    nasa_led = True
    lead_investigator = "test"
    focus_phenomena = "test"


class ChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Change


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name').generate()
    email = factory.Faker("email").generate()
    password = make_password("password")
    role = User.Roles.STAFF

    class Meta:
        model = get_user_model()
