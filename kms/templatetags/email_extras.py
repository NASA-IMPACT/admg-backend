from api_app.models import Change
from django import template
from django.conf import settings
# from django.http import HttpRequest
from kms import gcmd
import urllib.parse

register = template.Library()

@register.filter()
def get_gcmd_short_name(change: Change):
    return gcmd.get_short_name(change)

@register.filter()
def get_gcmd_path(change: Change):
    return gcmd.get_gcmd_path(change)

# TODO: Ask Ed/Carson about how to fix config so it works in all environments
@register.filter()
def get_absolute_url(relative_path):
    absolute_url = urllib.parse.urljoin("http://" + settings.ALLOWED_HOSTS[0], relative_path)
    return absolute_url
