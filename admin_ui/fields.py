from django.core.exceptions import ValidationError
from django.db.models.fields.related import ForeignKey
from django.db.models import functions, expressions, aggregates, Max, TextField
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

        deleted_record_uuids = Change.objects.filter(
            action="Delete", status=PUBLISHED_CODE, content_type__model=dest_model_name
        ).values("model_instance_uuid")

        published_identifier_query = expressions.Subquery(
            dest_model.objects.filter(uuid=expressions.OuterRef("uuid"))[:1].values(
                identifier_field
            )
        )

        return (
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
            .select_related('content_type')
            .order_by('identifier')
        )

    def prepare_value(self, value):
        if value:
            if hasattr(value, 'uuid'):
                return value.uuid
            return value
        return super().prepare_value(value)

    def label_from_instance(self, obj):
        return obj.identifier

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            Change.objects.get(**{key: value})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
        return self.dest_model(**{key: value})
    
    # def save_form_data(self, instance, data):
    #     setattr(instance, self.name, data)

    # def _post_clean(self):
    #     return
    #     opts = self._meta

    #     exclude = self._get_validation_exclusions()

    #     # Foreign Keys being used to represent inline relationships
    #     # are excluded from basic field value validation. This is for two
    #     # reasons: firstly, the value may not be supplied (#12507; the
    #     # case of providing new values to the admin); secondly the
    #     # object being referred to may not yet fully exist (#12749).
    #     # However, these fields *must* be included in uniqueness checks,
    #     # so this can't be part of _get_validation_exclusions().
    #     for name, field in self.fields.items():
    #         if isinstance(field, InlineForeignKeyField):
    #             exclude.append(name)

    #     try:
    #         self.instance = construct_instance(self, self.instance, opts.fields, opts.exclude)
    #     except ValidationError as e:
    #         self._update_errors(e)

    #     try:
    #         self.instance.full_clean(exclude=exclude, validate_unique=False)
    #     except ValidationError as e:
    #         self._update_errors(e)

    #     # Validate uniqueness if needed.
    #     if self._validate_unique:
    #         self.validate_unique()