from celery import shared_task
from . import api


@shared_task
def sync_gcmd(concept_scheme: str):
    for concept in api.list_concepts(concept_scheme):
        print(concept)


@shared_task
def trigger_gcmd_syncs():
    gcmd_concepts = ["Projects", "Instruments", "Platforms", "Phenomena"]
    return [sync_gcmd.delay(concept) for concept in gcmd_concepts]
