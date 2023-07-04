from django.core.exceptions import ValidationError
from django.db.models import expressions, functions, UUIDField
from django.db.models.fields.json import KeyTextTransform
from django.contrib.gis.forms.fields import PolygonField
from django.forms import (
    MultipleChoiceField,
    ModelChoiceField,
    DateField,
    DateInput,
)
from django.utils.translation import gettext_lazy as _

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
        """
        Generate the queryset for all of the options elements in a select input. For the
        textual identifier of each option, we want to render the 'short_name' attribute
        of the published version of every draft. If the draft has never been published,
        we render the 'short_name' value from the 'update' attribute of the draft. As
        such, if any update to a record's 'short_name' was published, we will render that
        value. Otherwise, we will render the first 'short_name' it was ever assigned.
        """
        # Select which attributes are to be used when rendering string represntation of draft
        identifier_attrs = (
            ("campaign", "deployment", "platform", "update__platform_identifier")
            if dest_model is data_models.CollectionPeriod
            else ('short_name',)
        )

        # Get relevant drafts
        qs = (
            ChangeWithIdentifier(*identifier_attrs).objects.of_type(dest_model)
            # Only focus on Created drafts, so we can treat the `uuid` as the target model's uuid
            .filter(action=models.Change.Actions.CREATE)
            # Remove any drafts that have been successfully deleted
            .exclude(status=models.Change.Statuses.IN_TRASH)
            # Remove any records that have been successfully deleted
            .exclude(
                uuid__in=(
                    models.Change.objects.of_type(dest_model)
                    .filter(action="Delete", status=models.Change.Statuses.PUBLISHED)
                    .values("model_instance_uuid")
                )
            )
        )

        # Annotate QS with identifier attribute(s) to be used in dropdown
        if dest_model is data_models.CollectionPeriod:
            qs = (
                # Get Deployment short_name from related deployments
                qs.annotate_from_relationship(
                    of_type=data_models.Deployment,
                    to_attr="deployment",
                    uuid_from="deployment",
                )
                # Get Platform short_name from related platforms
                .annotate_from_relationship(
                    of_type=data_models.Platform,
                    to_attr="platform",
                    uuid_from="platform",
                )
                # Get Campaign short_name by looking up campaigns related to the deployments
                # related to this draft 🤕
                .annotate(
                    deployment_jsonb=models.Subquery(
                        models.Change.objects.of_type(data_models.Deployment).filter(
                            action=models.Change.Actions.CREATE,
                            uuid=expressions.OuterRef('deployment_uuid'),
                            # NOTE: the `deployment_uuid` attribute is generated behind the
                            # scenes via .annotate_from_relationship() when we populated the
                            # `deployment` attribute
                        )
                        # NOTE: We are extracting the 'update' JSONB values from deployments
                        # rather than 'update__campaign' because selecting attributes in the
                        # 'update' object strangely returns JSONB rather than TEXT, making
                        # it challenging/not-possible to later cast to a UUID
                        .values('update')[:1]
                    ),
                    # retrieve the campaign uuid as TEXT, cast to UUID
                    campaign_uuid=functions.Cast(
                        KeyTextTransform(
                            'campaign',
                            "deployment_jsonb",
                        ),
                        output_field=UUIDField(),
                    ),
                    # use campaign uuid to retrieve campaign create draft, extract its short_name
                    campaign=models.Subquery(
                        models.Change.objects.of_type(data_models.Campaign)
                        .filter(
                            action=models.Change.Actions.CREATE,
                            uuid=expressions.OuterRef('campaign_uuid'),
                        )
                        .values('update__short_name')[:1],
                    ),
                )
            )

        else:
            qs = (
                qs
                # We want to describe every option in the choice field by its short_name from
                # the *published* version of that record. However, if there is no published
                # version, we will fall back to the short_name from the updates object.
                .annotate_from_published(
                    dest_model,
                    to_attr="short_name",
                    # Attribute to use for textual description of field
                    identifier=(
                        'title'
                        if dest_model in [data_models.Image, data_models.Website]
                        else 'short_name'
                    ),
                )
            )

        # Order alphabetically by identifier attributes
        return qs.order_by(*identifier_attrs)


class ChangeMultipleChoiceField(ChangeChoiceMixin, MultipleChoiceField):
    """
    A MultipleChoiceField that renders Change models rather than the actual target models
    """

    ...


class ChangeChoiceField(ChangeChoiceMixin, ModelChoiceField):
    """
    A ModelChoiceField that renders Change models rather than the actual target models
    """

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
