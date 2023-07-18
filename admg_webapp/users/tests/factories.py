from django.contrib.auth import get_user_model
import factory


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker("user_name")

    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)
