from api_app.models import Change
from django import template

register = template.Library()


@register.inclusion_tag("tags/change_list_item.html", takes_context=True)
def change_list_item(context, change):
    return {"change": change, "active": context["object"].uuid == change.uuid}


@register.inclusion_tag("tags/related_changes.html")
def related_changes(change):
    """
    Given a campaign change, return all descendent changes.  Each change will have its dependents
    add as a property following the below structure:
    - campaign
        - deployments
            - significant_events
            - iops
                - significant_events
            - collection_periods
                - platforms
                - homebases
                - instruments
    """
    # TODO: Handle case where change isn't Campaign but rather a child model

    # Follow relationships
    rel_deployments = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="deployment", update__campaign=str(change.uuid)
    )
    rel_iops = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="iop",
        update__deployment__in=[str(d.uuid) for d in rel_deployments],
    )
    rel_significant_events = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="significantevent",
        update__deployment__in=[str(d.uuid) for d in rel_deployments],
    )
    rel_collection_periods = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="collectionperiod",
        update__deployment__in=[str(d.uuid) for d in rel_deployments],
    )
    platform_ids = set()
    homebase_ids = set()
    instrument_ids = set()
    for collect_period in rel_collection_periods:
        update = collect_period.update
        platform_ids.add(update.get("platform"))
        homebase_ids.add(update.get("home_base"))
        instrument_ids.update(update.get("instruments", []))

    rel_platforms = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="platform", uuid__in=platform_ids
    )
    rel_homebases = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="homebase", uuid__in=homebase_ids
    )
    rel_instruments = Change.objects.select_related("content_type").filter(
        content_type__model__iexact="instrument", uuid__in=instrument_ids
    )

    # Build Tree
    change.deployments = [deployment for deployment in rel_deployments]
    for deployment in change.deployments:
        deployment.iops = [
            iop
            for iop in rel_iops
            if iop.update.get("deployment") == str(deployment.uuid)
        ]
        deployment.significant_events = [
            se
            for se in rel_significant_events
            if se.update.get("deployment") == str(deployment.uuid)
            and se.update.get("iop") is None
        ]
        for iop in deployment.iops:
            iop.significant_events = [
                se
                for se in rel_significant_events
                if se.update.get("iop") == str(iop.uuid)
            ]

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
                if str(i.uuid) in collection_period.update.get("instruments", [])
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


@register.inclusion_tag("tags/transition_form.html", takes_context=True)
def transition_form(context, description, *, state_change=1):
    return dict(
        uuid=context['object'].uuid,
        to=context['object'].status + state_change,
        description=description,
    )
