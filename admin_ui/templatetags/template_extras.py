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
    return obj.__class__.__name__.lower()


@register.inclusion_tag('snippets/object_header_tabs.html', takes_context=True)
def object_header_tabs(context, change: Change):
    """
    Reusable header for canonical object.
    """
    # TODO ask Anthony about the expected behavior here.
    # I have only seen change models with a model_instance_uuid of "None"
    print("\n*********", [f.name for f in change._meta.get_fields()], "\n*********")
    canonical_uuid = (
        # if we're passing in a model (i.e. a Campaign) instead of a change
        change.uuid
        # change.model_instance_uuid
        # if hasattr(change, "model_instance_uuid")
        # else change.uuid
        # if change.status == change.Statuses.PUBLISHED
        # else None
    )
    return {"object": change, "canonical_uuid": canonical_uuid, "request": context.get("request")}


@register.inclusion_tag('snippets/draft_breadcrumb_trail.html', takes_context=True)
def draft_breadcrumb_trail(context, change: Change):
    """
    Reusable header for canonical object.
    """
    # TODO there might be a cleaner way to get the string representation here
    status = (
        "Published"
        if not hasattr(change, "model_instance_uuid")
        else "Created"
        if change.status == change.Statuses.CREATED
        else "In Progress"
        if change.status == change.Statuses.IN_PROGRESS
        else "In Review"
        if change.status == change.Statuses.IN_REVIEW
        else "In Admin Review"
    )
    return {"object": change, "draft_status": status, "request": context.get("request")}
