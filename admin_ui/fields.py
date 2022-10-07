from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce
from django.contrib.gis.forms.fields import PolygonField
from django.forms import (
    MultipleChoiceField,
    ModelChoiceField,
    DateField,
    DateInput,
)
from django.forms.models import ModelChoiceIterator, ModelChoiceIteratorValue
from django.utils.translation import gettext_lazy as _
from itertools import groupby

from api_app import models
from data_models import models as data_models
from data_models.serializers import get_geojson_from_bb
from .widgets import BoundingBoxWidget


def get_attr(data, path):
    [attr, *parts] = path.split("__")
    if parts:
        return get_attr(data[attr], "__".join(parts))
    return data.get(attr)


def ChangeWithIdentifier(*fields):
    """
    Generate a Change model with a string representation based on the provided fields.
    This is necessary to have Change models that use annotated fields in their
    display, such as when rendering selection widgets.
    """

    class DynamicIdentifierChange(models.Change):
        def __str__(self):
            return (
                " | ".join(str(get_attr(self.__dict__, field) or "") for field in fields)
                or f"missing identifier ({self.__dict__.get('uuid', '')})"
            )

        class Meta:
            proxy = True

    return DynamicIdentifierChange


class ChangeChoiceMixin:
    def __init__(self, *args, dest_model, **kwargs):
        super().__init__(*args, **kwargs)
        self.dest_model = dest_model

    @classmethod
    def get_queryset_for_model(cls, dest_model):
        """Helper to get QS of valid choices"""
        if dest_model == data_models.CollectionPeriod:
            return cls.get_queryset_for_collection_period()

        dest_model_name = dest_model._meta.model_name

        # Field to use for textual description of field
        identifier_field = {"image": "title", "website": "title"}.get(dest_model_name, "short_name")

        changes = (
            models.Change.objects.filter(content_type__model=dest_model_name)
            .exclude(status=models.Change.Statuses.IN_TRASH)
            .add_updated_at()
            .annotate(effective_uuid=Coalesce("model_instance_uuid", "uuid"))
            .order_by("effective_uuid", "-updated_at")
        )

        latest_change_uuids = []
        for u, changes in groupby(changes, lambda change: change.effective_uuid):
            latest_change_uuids.append(list(changes)[0].uuid)

        return (
            ChangeWithIdentifier("short_name")
            .objects.filter(uuid__in=latest_change_uuids)
            .annotate_from_published(dest_model, to_attr="short_name", identifier=identifier_field)
            .select_related("content_type")
            .order_by("short_name")
            .annotate(effective_uuid=Coalesce("model_instance_uuid", "uuid"))
        )

    @staticmethod
    def get_queryset_for_collection_period():
        """Helper to get QS of valid choices"""
        return (
            ChangeWithIdentifier(
                "campaign", "deployment", "platform", "update__platform_identifier"
            )
            .objects.of_type(data_models.CollectionPeriod)
            # Only focus on Created drafts, so we can treat the `uuid` as the target model's uuid
            .filter(action=models.Change.Actions.CREATE)
            # Remove any Changes that have been successfully deleted
            .exclude(
                uuid__in=models.Change.objects.of_type(data_models.CollectionPeriod)
                .filter(action="Delete", status=models.Change.Statuses.PUBLISHED)
                .values("model_instance_uuid")
            )
            # Get Deployment short_name from related deployments
            .annotate_from_relationship(
                of_type=data_models.Deployment, to_attr="deployment", uuid_from="deployment"
            )
            # Get Campaign short_name from related campaigns
            .annotate_from_relationship(
                of_type=data_models.Campaign,
                to_attr="campaign",
                # Not sure why this exists in "update", as CollectionPeriod model
                # doesn't support campaigns. It would be safer to go through the
                # "deployment" relationship, however that's more complex as we would
                # need to join on the "deployment__uuid" property annotation created
                # when getting the deployment short_name.
                uuid_from="campaign",
            )
            # Get Platform short_name from related platforms
            .annotate_from_relationship(
                of_type=data_models.Platform, to_attr="platform", uuid_from="platform"
            )
            .select_related("content_type")
            .order_by("deployment")
        )


class ChangeMultipleChoiceField(ChangeChoiceMixin, MultipleChoiceField):
    """
    A MultipleChoiceField that renders Choice models rather than the actual target models
    """

    ...


class ChangeChoiceIterator(ModelChoiceIterator):
    def choice(self, obj):
        return (
            ModelChoiceIteratorValue(obj.effective_uuid, obj),
            self.field.label_from_instance(obj),
        )


class ChangeChoiceField(ChangeChoiceMixin, ModelChoiceField):
    """
    A ModelChoiceField that renders Choice models rather than the actual target models
    """

    iterator = ChangeChoiceIterator

    def to_python(self, value):
        """
        Override the lookup for the models to perform a lookup in the Change model
        table rather than the destination model.
        """
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or "pk"
            models.Change.objects.get(**{key: value})
        except (ValueError, TypeError, models.Change.DoesNotExist) as e:
            raise ValidationError(
                self.error_messages["invalid_choice"], code="invalid_choice"
            ) from e
        return self.dest_model(**{key: value})


class BboxField(PolygonField):
    widget = BoundingBoxWidget
    default_error_messages = {
        **PolygonField.default_error_messages,
        "invalid_geom": _(
            "Invalid geometry value. "
            "Geometry should be provided in the following format: "
            "MaxLat, MinLat, MaxLon, MinLon"
        ),
    }

    def clean(self, value):
        if value:
            try:
                value = get_geojson_from_bb(value)
            except ValueError as e:
                raise ValidationError(
                    self.error_messages["invalid_geom"], code="invalid_geom"
                ) from e

        return super().clean(value)


class CustomDateField(DateField):
    widget = DateInput(
        attrs={"class": "datepicker", "placeholder": "Select a date", "type": "date"}
    )
