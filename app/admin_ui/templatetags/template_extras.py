from django import template

from admin_ui.utils import get_draft_status_class
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
def object_header_tabs(context, canonical_uuid: str):
    """
    Reusable header for canonical object.
    """
    latest_draft = Change.objects.related_drafts(canonical_uuid).order_by("status").first()

    return {
        "draft_status": latest_draft.get_status_display(),
        # check if the most recent related draft is a delete draft
        "is_deleted": Change.objects.is_deleted(canonical_uuid),
        "draft_status_class": get_draft_status_class(latest_draft.status),
        "canonical_uuid": canonical_uuid,
        "has_draft_in_progress": Change.objects.related_in_progress_drafts(
            uuid=canonical_uuid
        ).exists(),
        "has_published_draft": Change.objects.related_drafts(canonical_uuid)
        .filter(status=Change.Statuses.PUBLISHED, action=Change.Actions.CREATE)
        .exists(),
        "request": context.get("request"),
        "view_model": latest_draft.model_name_for_url,
    }
