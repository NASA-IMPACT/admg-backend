from django import template

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
