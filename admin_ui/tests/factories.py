import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType

from admg_webapp.users.models import User
from api_app.models import Change


class ChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Change


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name')
    email = factory.Faker("email")
    password = make_password("password")
    role = User.Roles.STAFF

    class Meta:
        model = get_user_model()
