import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from admg_webapp.users.models import User
from api_app.models import Change


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
