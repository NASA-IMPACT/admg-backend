from data_models.models import Image
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def get_full_url(filename: str):
    """
    Given an image's filename, generate full URL.
    """
    return Image(image=filename).image.url
