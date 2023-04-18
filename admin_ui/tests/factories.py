import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType

from admg_webapp.users.models import User
from api_app.models import Change


class ChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Change

    @staticmethod
    def make_create_change_object(factory, custom_fields={}):
        """make a Change.Actions.CREATE change object to use during testing"""
        content_type = ContentType.objects.get_for_model(factory._meta.model)

        # _meta.fields does not contain many to many
        model_field_names = {
            field.name
            for field in factory._meta.get_model_class()._meta._forward_fields_map.values()
        }
        overrides = {
            field: value for field, value in custom_fields.items() if field in model_field_names
        }

        return Change.objects.create(
            content_type=content_type,
            status=Change.Statuses.CREATED,
            action=Change.Actions.CREATE,
            update={**factory.as_change_dict(), **overrides},
        )

    @staticmethod
    def make_update_change_object(factory, create_draft, fields_to_keep=[]):
        """make a Change.Actions.CREATE change object to use during testing"""
        content_type = ContentType.objects.get_for_model(factory._meta.model)

        # we want the ability to keep the original's values, say short_name or concept_id
        # models can't take any field though, so this checks that the fields are real
        # TODO: move this to an error check?
        model_field_names = {
            field.name
            for field in factory._meta.get_model_class()._meta._forward_fields_map.values()
        }
        overrides = {
            field: create_draft.update[field]
            for field in fields_to_keep
            if field in model_field_names
        }

        return Change.objects.create(
            content_type=content_type,
            status=Change.Statuses.CREATED,
            action=Change.Actions.UPDATE,
            model_instance_uuid=create_draft.uuid,
            update={**factory.as_change_dict(), **overrides},
        )


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name')
    email = factory.Faker("email")
    password = make_password("password")
    role = User.Roles.STAFF

    class Meta:
        model = get_user_model()
