from django.forms import ModelForm
from .config import MODEL_CONFIG_MAP


def GenericFormClass(model_name="", model=None):
    MainModel = model_name and MODEL_CONFIG_MAP[model_name]["model"] or model

    class MyFormClass(ModelForm):

        @staticmethod
        def add_classes(value, arg):
            '''
            Add provided classes to form field
            :param value: form field
            :param arg: string of classes seperated by ' '
            :return: edited field
            '''
            css_classes = value.widget.attrs.get('class', '')
            css_classes = css_classes.split(' ') if css_classes else []
            css_classes = list(set(css_classes).union(set(arg.split(' '))))
            value.widget.attrs['class'] = " ".join(css_classes)

        def is_valid(self) -> bool:
            unique_fields =  ["short_name", "order_priority", "gcmd_uuid", "url", "concept_id"]
            unique_error_message = "with this {} already exists."
            # unique_together = [("campaign", "website"), ("campaign", "order_priority")]

            # TODO: check if it has other errors and don't just return True
            is_valid = super().is_valid()
            errors = dict(self.errors)
            for field in errors:
                error_message = unique_error_message.format(self[field].label)
                if (
                    field in unique_fields and
                    len(errors[field]) == 1 and
                    error_message in errors[field][0]
                ):
                    self.errors.pop(field)

            return True

        class Meta:
            model = MainModel
            fields = '__all__'

    return MyFormClass
