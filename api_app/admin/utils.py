from django.contrib.contenttypes.models import ContentType
from django.forms import modelform_factory, Field
from django.forms.models import ModelForm


def prefix_field(field: Field, field_name_prefix: str) -> None:
    """
    Mutate a provided field so that its rendered inputs have a name prefixed
    with the provided field name prefix.
    """
    renderer = field.widget.render

    def _widget_render_wrapper(name, *args, **kwargs):
        return renderer(f"{field_name_prefix}{name}", *args, **kwargs)

    field.widget.render = _widget_render_wrapper


def get_modelform_for_content_type(content_type: ContentType) -> ModelForm:
    """
    Returns a ModelForm for content object associated with a provided object.
    """
    return modelform_factory(content_type.model_class(), exclude=[])
