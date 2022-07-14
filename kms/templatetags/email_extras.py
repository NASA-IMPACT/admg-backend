from django import template
from kms import gcmd
from api_app.models import Change

register = template.Library()

@register.filter()
def gcmd_short_name(change: Change):
    return gcmd.get_short_name(change)

@register.filter()
def get_gcmd_path(change: Change):
    return gcmd.get_gcmd_path(change)