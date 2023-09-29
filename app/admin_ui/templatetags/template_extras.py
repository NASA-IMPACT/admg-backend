from django import template
from django.db.models import Q
from typing import Optional

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
def object_header_tabs(context, change: Change, canonical_change: Optional[Change] = None):
    """
    Reusable header for canonical object.
    """

    # fetch latest change object
    latest_change = (
        change
        if canonical_change
        else (
            Change.objects.filter(Q(uuid=change.uuid) | Q(model_instance_uuid=change.uuid))
            .order_by("-updated_at")
            .first()
        )
    )
    # use canonical change if present otherwise fall back to change
    change = canonical_change if canonical_change else change
    has_progress_draft = (
        Change.objects.exclude(status=Change.Statuses.PUBLISHED)
        .filter(Q(uuid=change.uuid) | Q(model_instance_uuid=change.uuid))
        .exists()
    )

    has_published_draft = Change.objects.filter(
        Q(uuid=change.uuid) | Q(model_instance_uuid=change.uuid), status=Change.Statuses.PUBLISHED
    ).exists()
    # print(f"\n\n*********************\n\n\n{has_published_draft=} {has_progress_draft=}")

    # TODO handle the case where we don't have a model_instance_uuid
    canonical_uuid = (
        change.model_instance_uuid
        if hasattr(change, "model_instance_uuid") and change.model_instance_uuid
        else change.uuid
    )

    draft_status = (
        "Published"
        if not hasattr(latest_change, "status")
        else Change.Statuses(latest_change.status).label
    )

    draft_status_class = f"draft-status-{draft_status.lower().replace(' ', '-')}"

    return {
        "object": change,
        "draft_status": draft_status,
        "draft_status_class": draft_status_class,
        "canonical_uuid": canonical_uuid,
        "draft_uuid": change.uuid,
        "has_progress_draft": has_progress_draft,
        "has_published_draft": has_published_draft,
        "request": context.get("request"),
        "view_model": context.get("view_model"),
    }
