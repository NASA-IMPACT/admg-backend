from django import template

from api_app.models import Change

register = template.Library()


@register.filter(name="zip")
def zip_lists(a, b):
    return zip(a, b)


@register.filter
def title(name):
    """
    Override Django's builtin title to ignore plural names that already contain
    capitalized letters.
    """
    return name.title() if name.islower() else name


@register.filter
def verbose_name(obj):
    return obj._meta.verbose_name


@register.filter
def verbose_name_plural(obj):
    return obj._meta.verbose_name_plural


@register.filter()
def keyvalue(dictionary, key):
    return dictionary[key]


@register.filter
def classname(obj):
    """
    Helper to retrieve the classname for a given model instance. Useful when needing to
    provide a classname to a url tag.
    """
    return obj.__class__.__name__


@register.inclusion_tag('snippets/object_header_tabs.html')
def object_header_tabs(change: Change):
    """ 
    Reusable header for canonical object.
    """
    published_uuid = (
        change.model_instance_uuid
        if change.model_instance_uuid
        else change.uuid
        if change.status == change.Statuses.PUBLISHED
        else None
    )
    return {"object": change, "published_uuid": published_uuid}
