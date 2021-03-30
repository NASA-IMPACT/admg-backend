from django.core.exceptions import ValidationError
from django.db.models.fields.related import ForeignKey
from django.db.models import functions, expressions, Max, TextField
from django.db.models.fields.json import KeyTextTransform
from django.forms import ModelChoiceField

from api_app.models import Change, CREATE, PUBLISHED_CODE


class ChangeChoiceField(ModelChoiceField):
    """
    A ModelChoiceField that renders Choice models rather than the actual target models
    """

    def __init__(self, *args, dest_model, **kwargs):
        super().__init__(*args, **kwargs)
        self.dest_model = dest_model

    # TODO: Instances fail validation, customize to make message clear that the value simply isn't published yet
    @staticmethod
    def get_queryset_for_model(dest_model):
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

    def prepare_value(self, value):
        if value:
            if hasattr(value, "uuid"):
                return value.uuid
            return value
        return super().prepare_value(value)

    def label_from_instance(self, obj):
        return obj.identifier

    def to_python(self, value):
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
