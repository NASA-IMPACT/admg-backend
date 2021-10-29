from django import template

from admin_ui.config import MODEL_CONFIG_MAP

register = template.Library()

@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)

@register.filter()
def get_display_name(value):
    return MODEL_CONFIG_MAP[value]["display_name"]
