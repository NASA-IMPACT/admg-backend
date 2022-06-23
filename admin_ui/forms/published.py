from django.forms import ModelForm

from ..config import MODEL_CONFIG_MAP
from ..mixins import formfield_callback


def published_modelform_factory(model_name):
    class PublishedModelForm(ModelForm):
        formfield_callback = formfield_callback

        def is_valid(self) -> bool:
            unique_fields = ["short_name", "order_priority", "gcmd_uuid", "url", "concept_id"]
            unique_error_message = "with this {} already exists."
            # unique_together = [("campaign", "website"), ("campaign", "order_priority")]

            is_valid = super().is_valid()
            # if the form is valid, we don't need to perform custom validation
            if is_valid:
                return is_valid

            # check here to see if the validation is just about the unique field
            errors = dict(self.errors)
            for field in errors:
                error_message = unique_error_message.format(self[field].label)
                if (
                    field in unique_fields
                    and len(errors[field]) == 1
                    and error_message in errors[field][0]
                ):
                    self.errors.pop(field)

            return len(self.errors) == 0

        class Meta:
            model = MODEL_CONFIG_MAP[model_name]["model"]
            fields = "__all__"

    return PublishedModelForm
