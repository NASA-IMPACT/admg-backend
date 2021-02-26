from api_app.models import Change
from django import template

register = template.Library()


@register.inclusion_tag("tags/change_list_item.html", takes_context=True)
def change_list_item(context, change):
    return {"change": change, "active": context["object"].uuid == change.uuid}


@register.inclusion_tag("tags/related_changes.html")
def related_changes(change):
    rel_deployments = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="deployment", update__campaign=str(change.uuid)
    )
    rel_collection_periods = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="collectionperiod",
        update__deployment__in=[
            str(d.uuid) for d in rel_deployments
        ],  # TODO: Using a queryset for the lookup may be more performant
    )
    platform_ids = set()
    homebase_ids = set()
    instrument_ids = set()
    for collect_period in rel_collection_periods:
        update = collect_period.update
        platform_ids.add(update.get("platform"))
        homebase_ids.add(update.get("home_base"))
        instrument_ids.update(update.get("instruments"))

    rel_platforms = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="platform", uuid__in=platform_ids
    )
    rel_homebases = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="homebase", uuid__in=homebase_ids
    )
    rel_instruments = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="instrument", uuid__in=instrument_ids
    )

    """
    Given a campaign, inject related Changes to follow the following dependencies:
    - campaign
    - deployments
        - collection_periods
        - platforms
        - homebases
        - instruments
    """
    change.deployments = [deployment for deployment in rel_deployments]
    for deployment in change.deployments:
        deployment.collection_periods = [
            cp
            for cp in rel_collection_periods
            if cp.update.get("deployment") == str(deployment.uuid)
        ]
        for collection_period in deployment.collection_periods:
            collection_period.platforms = [
                p
                for p in rel_platforms
                if str(p.uuid) == collection_period.update.get("platform")
            ]
            collection_period.homebases = [
                hb
                for hb in rel_homebases
                if str(hb.uuid) == collection_period.update.get("home_base")
            ]
            collection_period.instruments = [
                i
                for i in rel_instruments
                if str(i.uuid) in collection_period.update.get("instruments")
            ]

    return {
        "object": change,
        "deployments": rel_deployments,
        "collection_periods": rel_collection_periods,
        "platforms": rel_platforms,
        "homebases": rel_homebases,
        "deployments": rel_deployments,
        "instruments": rel_instruments,
    }


@register.inclusion_tag("tags/related_approval_logs.html")
def related_approval_logs(approval_logs):
    return {"approval_logs": approval_logs}

