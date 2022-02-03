from django.contrib.auth import get_user_model
import factory


from api_app.models import Change


class ChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Change


class UserFactor(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
