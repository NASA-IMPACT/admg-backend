from django.core.exceptions import ValidationError
from django.db.models.fields.related import ForeignKey
from django.db.models import functions, expressions, Max, TextField
from django.db.models.fields.json import KeyTextTransform
from django.forms import ModelChoiceField
from django.contrib.gis.forms import fields

from api_app.models import Change, CREATE, PUBLISHED_CODE
from .widgets import BoundingBoxWidget


class ChangeChoiceField(ModelChoiceField):
    """
    A ModelChoiceField that renders Choice models rather than the actual target models
    """

    def __init__(self, *args, dest_model, **kwargs):
        super().__init__(*args, **kwargs)
        self.dest_model = dest_model

    @staticmethod
    def get_queryset_for_model(dest_model):
        """ Helper to get QS of valid choices """
        dest_model_name = dest_model._meta.model_name

        # Field to use for textual description of field
        identifier_field = {
            "image": "image",
        }.get(dest_model_name, "short_name")

        published_identifier_query = expressions.Subquery(
            dest_model.objects.filter(uuid=expressions.OuterRef("uuid"))[:1].values(
                identifier_field
            )
        )

        return (
            Change.objects
            # Only focus on Created drafts, so we can treat the `uuid` as the target model's uuid
            .filter(action=CREATE, content_type__model=dest_model_name)
            # Remove any Changes that have been successfully deleted
            .exclude(
                uuid__in=Change.objects.of_type(dest_model)
                .filter(action="Delete", status=PUBLISHED_CODE)
                .values("model_instance_uuid")
            )
            # Add identifier from published record (if available) or change.update.short_name
            .annotate(
                identifier=functions.Coalesce(
                    published_identifier_query,
                    KeyTextTransform(identifier_field, "update"),
                    output_field=TextField(),
                )
            )
            .select_related("content_type")
            .order_by("identifier")
        )

    def label_from_instance(self, obj):
        """
        Override label to use the 'identifier' annotation we add to the queryset
        """
        return obj.identifier

    def to_python(self, value):
        """
        Override the lookup for the models to perform a lookup in the Change model
        table rather than the destination model.
        """
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or "pk"
            Change.objects.get(**{key: value})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist) as e:
            raise ValidationError(
                self.error_messages["invalid_choice"], code="invalid_choice"
            ) from e
        return self.dest_model(**{key: value})


class BboxField(fields.PolygonField):
    widget = BoundingBoxWidget

    # def to_python(self, value):
    #     """Transform the value to a Geometry object."""
    #     if value in self.empty_values:
    #         return None

    #     return super().to_python(value)