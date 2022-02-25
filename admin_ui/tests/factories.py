from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import factory


from api_app.models import Change


class ChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Change


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: "blah{0}".format(n))
    email = factory.Sequence(lambda n: "someone{0}@localhost".format(n))
    password = make_password("password")
    class Meta:
        model = get_user_model()
