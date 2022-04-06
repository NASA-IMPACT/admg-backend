from django import template
from django.urls import reverse

from admin_ui.config import MODEL_CONFIG_MAP

register = template.Library()


@register.filter(name="zip")
def zip_lists(a, b):
    return zip(a, b)


@register.filter()
def get_display_name(value):
    if "display_name" in MODEL_CONFIG_MAP.get(value, {}):
        return MODEL_CONFIG_MAP[value]["display_name"]
    return value


# @register.filter
# def get_published_url(value):
#     reverse(f'published-{}-detail', args=(value.model_instance_uuid,))
#     MODEL_CONFIG_MAP[value]["display_name"]
