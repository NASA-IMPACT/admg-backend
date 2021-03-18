from django.db.models.fields.related import ForeignKey
from django.db.models import functions, expressions, aggregates, Max, TextField
from django.db.models.fields.json import KeyTextTransform
from django.forms import ModelChoiceField

from api_app.models import Change, CREATE


class ChangeChoiceField(ModelChoiceField):
    """
    A ModelChoiceField that renders Choice models rather than the actual target models
    """

    # TODO: Instances fail validation, customize to make message clear that the value simply isn't published yet

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = self.get_choices(self.queryset.model)

    @staticmethod
    def get_choices(dest_model):
        dest_model_name = dest_model._meta.model_name

        # Field to use for textual description of field
        identifier_field = {
            "image": "image",
        }.get(dest_model_name, "short_name")

        deleted_record_uuids = Change.objects.filter(
            action="Delete", status=6, content_type__model=dest_model_name
        ).values("model_instance_uuid")

        published_identifier_query = expressions.Subquery(
            dest_model.objects.filter(uuid=expressions.OuterRef("uuid"))[:1].values(
                identifier_field
            )
        )

        qs = (
            Change.objects
            # Only focus on Created drafts, so we can treat the `uuid` as the target model's uuid
            .filter(action="Create", content_type__model=dest_model_name)
            # Remove any Changes that have been successfully deleted
            .exclude(uuid__in=deleted_record_uuids)
            # Add identifier from published record (if available) or change.update.short_name
            .annotate(
                identifier=functions.Coalesce(
                    published_identifier_query,
                    KeyTextTransform(identifier_field, "update"),
                    output_field=TextField(),
                )
            )
        )

        return qs.values_list("uuid", "identifier").order_by("identifier")